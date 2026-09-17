from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from wife_system.api.app import create_app, get_probe_service
from wife_system.probes import ProbeRecord, ProbeResult, ProbeService, SHANGHAI_TIMEZONE


PROBE_PATH = "/api/v1/probes"


def client_for(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def post_probe(app: FastAPI, *, key: str, challenge: str = "V001") -> Any:
    with client_for(app) as client:
        return client.post(
            PROBE_PATH,
            headers={"Idempotency-Key": key},
            json={"challenge": challenge},
        )


def assert_safe_error(response: Any, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status
    payload = response.json()
    assert set(payload) == {"request_id", "error"}
    uuid.UUID(payload["request_id"])
    assert payload["error"]["code"] == code
    assert payload["error"]["retryable"] is False
    assert isinstance(payload["error"]["message"], str)
    assert "Traceback" not in response.text
    return payload


class ExplodingService:
    def create(self, **kwargs: Any) -> ProbeResult:
        del kwargs
        raise AssertionError("health endpoint touched probe service")


def test_h01_health_is_exact_and_does_not_touch_service() -> None:
    app = create_app(probe_service=ExplodingService())  # type: ignore[arg-type]

    with client_for(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "wife-system"}


def test_h02_openapi_freezes_header_and_strict_body_schema() -> None:
    with client_for(create_app()) as client:
        schema = client.get("/openapi.json").json()

    operation = schema["paths"][PROBE_PATH]["post"]
    header = next(item for item in operation["parameters"] if item["name"] == "Idempotency-Key")
    assert header["in"] == "header"
    assert header["required"] is True
    assert header["schema"]["minLength"] == 1
    assert header["schema"]["maxLength"] == 256
    body_ref = operation["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    body_schema = schema["components"]["schemas"][body_ref.rsplit("/", 1)[-1]]
    assert body_schema["required"] == ["challenge"]
    assert body_schema["additionalProperties"] is False
    challenge_schema = body_schema["properties"]["challenge"]
    assert challenge_schema["type"] == "string"
    assert challenge_schema["minLength"] == 1
    assert challenge_schema["maxLength"] == 128


@pytest.mark.parametrize(
    ("headers", "content"),
    [
        ({}, json.dumps({"challenge": "V001"})),
        ({"Idempotency-Key": ""}, json.dumps({"challenge": "V001"})),
        ({"Idempotency-Key": "   "}, json.dumps({"challenge": "V001"})),
        ({"Idempotency-Key": "k" * 257}, json.dumps({"challenge": "V001"})),
        ({"Idempotency-Key": "missing"}, json.dumps({})),
        ({"Idempotency-Key": "null"}, json.dumps({"challenge": None})),
        ({"Idempotency-Key": "integer"}, json.dumps({"challenge": 1})),
        ({"Idempotency-Key": "empty"}, json.dumps({"challenge": ""})),
        ({"Idempotency-Key": "blank"}, json.dumps({"challenge": " \t"})),
        ({"Idempotency-Key": "long"}, json.dumps({"challenge": "x" * 129})),
        (
            {"Idempotency-Key": "extra"},
            json.dumps({"challenge": "V001", "secret": "C2-B2-EXTRA-CANARY"}),
        ),
        ({"Idempotency-Key": "malformed"}, '{"challenge":'),
    ],
)
def test_h02_invalid_header_or_body_is_safe_422(
    headers: dict[str, str], content: str
) -> None:
    with client_for(create_app()) as client:
        response = client.post(
            PROBE_PATH,
            headers={**headers, "Content-Type": "application/json"},
            content=content,
        )

    assert_safe_error(response, 422, "invalid_request")
    assert "C2-B2-EXTRA-CANARY" not in response.text


def test_h02_maximum_length_header_and_challenge_are_accepted() -> None:
    response = post_probe(create_app(), key="k" * 256, challenge="c" * 128)

    assert response.status_code == 200
    assert response.json()["challenge"] == "c" * 128


def test_w02_w03_server_generates_unique_ids_receipts_and_shanghai_times() -> None:
    app = create_app()
    responses = [
        post_probe(app, key="event-random-1", challenge="same challenge"),
        post_probe(app, key="event-random-2", challenge="same challenge"),
    ]

    assert all(response.status_code == 200 for response in responses)
    payloads = [response.json() for response in responses]
    for payload in payloads:
        uuid.UUID(payload["request_id"])
        assert payload["challenge"] == "same challenge"
        assert payload["receipt"].startswith("POC-")
        assert len(payload["receipt"]) == len("POC-") + 24
        assert datetime.fromisoformat(payload["created_at"]).utcoffset() == timedelta(hours=8)
        assert payload["replayed"] is False
    assert payloads[0]["request_id"] != payloads[1]["request_id"]
    assert payloads[0]["receipt"] != payloads[1]["receipt"]


def test_h03_w05_sequential_replay_reuses_the_complete_first_record() -> None:
    app = create_app()
    first = post_probe(app, key="sequential", challenge="payload")
    replay = post_probe(app, key="sequential", challenge="payload")

    assert first.status_code == replay.status_code == 200
    assert first.json()["replayed"] is False
    assert replay.json() == {**first.json(), "replayed": True}


def test_h05_w05_concurrent_replay_creates_one_record() -> None:
    receipt_calls = 0
    receipt_lock = threading.Lock()

    def receipt_factory() -> str:
        nonlocal receipt_calls
        with receipt_lock:
            receipt_calls += 1
        return "POC-000000000000000000000001"

    app = create_app(probe_service=ProbeService(receipt_factory=receipt_factory))
    with ThreadPoolExecutor(max_workers=12) as pool:
        responses = list(
            pool.map(
                lambda _: post_probe(app, key="concurrent", challenge="payload"),
                range(24),
            )
        )

    assert all(response.status_code == 200 for response in responses)
    payloads = [response.json() for response in responses]
    assert receipt_calls == 1
    assert len({payload["request_id"] for payload in payloads}) == 1
    assert len({payload["created_at"] for payload in payloads}) == 1
    assert sum(payload["replayed"] is False for payload in payloads) == 1
    assert sum(payload["replayed"] is True for payload in payloads) == 23


def test_h04_w07_same_key_different_payload_conflicts_without_creation() -> None:
    receipt_calls = 0

    def receipt_factory() -> str:
        nonlocal receipt_calls
        receipt_calls += 1
        return "POC-000000000000000000000002"

    app = create_app(probe_service=ProbeService(receipt_factory=receipt_factory))
    first = post_probe(app, key="conflict", challenge="first")
    conflict = post_probe(app, key="conflict", challenge="second")

    assert first.status_code == 200
    conflict_payload = assert_safe_error(conflict, 409, "duplicate_request_conflict")
    assert conflict_payload["request_id"] == first.json()["request_id"]
    assert receipt_calls == 1


def test_w06_distinct_keys_with_same_challenge_are_independent() -> None:
    app = create_app()
    first = post_probe(app, key="source-event-a", challenge="identical")
    second = post_probe(app, key="source-event-b", challenge="identical")

    assert first.status_code == second.status_code == 200
    assert first.json()["request_id"] != second.json()["request_id"]
    assert first.json()["receipt"] != second.json()["receipt"]


def test_h07_h08_internal_failure_is_safe_and_same_key_can_recover(
    caplog: pytest.LogCaptureFixture,
) -> None:
    calls = 0
    failure_canary = "C2_B2_PRIVATE_EXCEPTION_CANARY"

    def fail_once() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError(failure_canary)
        return "POC-000000000000000000000003"

    caplog.set_level("INFO", logger="wife_system.api")
    app = create_app(probe_service=ProbeService(receipt_factory=fail_once))
    failed = post_probe(app, key="recover-after-failure")
    recovered = post_probe(app, key="recover-after-failure")

    failed_payload = assert_safe_error(failed, 500, "internal_error")
    assert recovered.status_code == 200
    assert recovered.json()["replayed"] is False
    assert recovered.json()["request_id"] != failed_payload["request_id"]
    assert calls == 2
    combined_logs = "\n".join(record.getMessage() for record in caplog.records)
    assert failure_canary not in failed.text
    assert failure_canary not in combined_logs
    assert "Traceback" not in combined_logs


def test_http_dependency_can_be_replaced_without_changing_route() -> None:
    class SpyService:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        def create(self, **kwargs: Any) -> ProbeResult:
            self.calls.append(kwargs)
            return ProbeResult(
                record=ProbeRecord(
                    request_id=kwargs["candidate_request_id"],
                    challenge=kwargs["challenge"],
                    receipt="POC-000000000000000000000004",
                    created_at=datetime(2026, 9, 14, 16, 30, tzinfo=SHANGHAI_TIMEZONE),
                ),
                replayed=False,
            )

    spy = SpyService()
    app = create_app()
    app.dependency_overrides[get_probe_service] = lambda: spy
    response = post_probe(app, key="dependency-override", challenge="delegated")

    assert response.status_code == 200
    assert response.json()["challenge"] == "delegated"
    assert len(spy.calls) == 1
    assert spy.calls[0]["idempotency_key"] == "dependency-override"
    assert spy.calls[0]["challenge"] == "delegated"
    uuid.UUID(spy.calls[0]["candidate_request_id"])


def test_logs_are_json_and_omit_private_inputs_and_internal_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    private_key = "wx-user-C2-B2-ORIGINAL-IDEMPOTENCY-CANARY"
    private_challenge = "C2-B2 complete private challenge canary"
    exception_canary = "C2-B2 exception message and D:\\private\\service.py"

    def failure() -> str:
        raise RuntimeError(exception_canary)

    caplog.set_level("INFO", logger="wife_system.api")
    successful_app = create_app()
    assert post_probe(successful_app, key=private_key, challenge=private_challenge).status_code == 200
    assert post_probe(successful_app, key=private_key, challenge=private_challenge).status_code == 200
    assert post_probe(successful_app, key=private_key, challenge="different").status_code == 409
    with client_for(create_app()) as client:
        assert client.post(
            PROBE_PATH,
            headers={"Idempotency-Key": private_key},
            json={"challenge": private_challenge, "extra": private_challenge},
        ).status_code == 422
    assert post_probe(
        create_app(probe_service=ProbeService(receipt_factory=failure)),
        key=private_key,
        challenge=private_challenge,
    ).status_code == 500

    messages = [record.getMessage() for record in caplog.records]
    parsed = [json.loads(message) for message in messages]
    serialized = json.dumps(parsed, ensure_ascii=False)
    assert private_key not in serialized
    assert private_challenge not in serialized
    assert exception_canary not in serialized
    assert "Traceback" not in serialized
    assert "service.py" not in serialized
    assert "D:\\private" not in serialized
    assert all("request_id" in event for event in parsed)
    assert any("idempotency_key_hash" in event for event in parsed)


def _unused_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _delayed_receipt() -> str:
    time.sleep(0.4)
    return "POC-000000000000000000000005"


disconnect_test_app = create_app(
    probe_service=ProbeService(receipt_factory=_delayed_receipt)
)


def _start_uvicorn(
    port: int, target: str = "wife_system.api.app:app"
) -> subprocess.Popen[str]:
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            target,
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "error",
        ],
        cwd=os.getcwd(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        creationflags=creation_flags,
    )


def _wait_for_health(process: subprocess.Popen[str], base_url: str) -> None:
    deadline = time.monotonic() + 8
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            stderr = process.stderr.read() if process.stderr is not None else ""
            raise AssertionError(f"uvicorn exited during startup: {stderr}")
        try:
            response = httpx.get(f"{base_url}/healthz", timeout=0.25)
            if response.status_code == 200:
                return
        except httpx.TransportError as exc:
            last_error = exc
        time.sleep(0.05)
    raise AssertionError(f"uvicorn did not become healthy: {last_error}")


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_h06_client_timeout_then_retry_replays_completed_record() -> None:
    port = _unused_loopback_port()
    base_url = f"http://127.0.0.1:{port}"
    headers = {"Idempotency-Key": "client-disconnect-retry"}
    process = _start_uvicorn(
        port, "tests.independent.test_c2_b2_api:disconnect_test_app"
    )
    try:
        _wait_for_health(process, base_url)
        with pytest.raises(httpx.ReadTimeout):
            httpx.post(
                f"{base_url}{PROBE_PATH}",
                headers=headers,
                json={"challenge": "disconnect"},
                timeout=0.05,
            )
        time.sleep(0.6)

        replay = httpx.post(
            f"{base_url}{PROBE_PATH}",
            headers=headers,
            json={"challenge": "disconnect"},
            timeout=2,
        )
        replay_again = httpx.post(
            f"{base_url}{PROBE_PATH}",
            headers=headers,
            json={"challenge": "disconnect"},
            timeout=2,
        )
        assert replay.status_code == replay_again.status_code == 200
        assert replay.json()["replayed"] is True
        assert replay_again.json() == replay.json()
        assert replay.json()["receipt"] == "POC-000000000000000000000005"
    finally:
        _stop_process(process)


def test_w04_and_restart_boundary_over_real_loopback_http() -> None:
    port = _unused_loopback_port()
    base_url = f"http://127.0.0.1:{port}"
    headers = {"Idempotency-Key": "restart-process-local"}
    process = _start_uvicorn(port)
    restarted: subprocess.Popen[str] | None = None
    try:
        _wait_for_health(process, base_url)
        first = httpx.post(
            f"{base_url}{PROBE_PATH}",
            headers=headers,
            json={"challenge": "restart"},
            timeout=2,
        )
        assert first.status_code == 200
        _stop_process(process)

        with pytest.raises(httpx.TransportError):
            httpx.post(
                f"{base_url}{PROBE_PATH}",
                headers=headers,
                json={"challenge": "restart"},
                timeout=0.5,
            )

        restarted = _start_uvicorn(port)
        _wait_for_health(restarted, base_url)
        after_restart = httpx.post(
            f"{base_url}{PROBE_PATH}",
            headers=headers,
            json={"challenge": "restart"},
            timeout=2,
        )
        assert after_restart.status_code == 200
        assert after_restart.json()["replayed"] is False
        assert after_restart.json()["request_id"] != first.json()["request_id"]
        assert after_restart.json()["receipt"] != first.json()["receipt"]
    finally:
        _stop_process(process)
        if restarted is not None:
            _stop_process(restarted)
