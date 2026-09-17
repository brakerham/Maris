from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from wife_system.api.app import create_app
from wife_system.probes import ProbeService


PROBE_PATH = "/api/v1/probes"


def client_for(app: FastAPI) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def send_probe(
    app: FastAPI,
    *,
    key: str,
    challenge: str = "V001",
) -> Any:
    with client_for(app) as client:
        return client.post(
            PROBE_PATH,
            headers={"Idempotency-Key": key},
            json={"challenge": challenge},
        )


def assert_safe_error(response: Any, *, status: int, code: str) -> dict[str, Any]:
    assert response.status_code == status
    payload = response.json()
    assert set(payload) == {"request_id", "error"}
    assert isinstance(payload["request_id"], str) and payload["request_id"]
    assert payload["error"]["code"] == code
    assert isinstance(payload["error"]["message"], str)
    assert payload["error"]["retryable"] is False
    assert "Traceback" not in response.text
    return payload


def test_healthz_is_exact_and_does_not_touch_the_probe_service() -> None:
    calls = 0

    def forbidden_receipt() -> str:
        nonlocal calls
        calls += 1
        raise AssertionError("healthz called the probe service")

    app = create_app(probe_service=ProbeService(receipt_factory=forbidden_receipt))

    with client_for(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "wife-system"}
    assert calls == 0


def test_openapi_marks_the_idempotency_header_as_required() -> None:
    with client_for(create_app()) as client:
        schema = client.get("/openapi.json").json()

    operation = schema["paths"][PROBE_PATH]["post"]
    matching = [
        parameter
        for parameter in operation["parameters"]
        if parameter["in"] == "header"
        and parameter["name"].lower() == "idempotency-key"
    ]
    assert len(matching) == 1
    assert matching[0]["required"] is True


def test_two_distinct_events_generate_distinct_server_values_and_aware_times() -> None:
    app = create_app()

    first = send_probe(app, key="c2-b2-distinct-1")
    second = send_probe(app, key="c2-b2-distinct-2")

    assert first.status_code == second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    for payload in (first_payload, second_payload):
        assert set(payload) == {
            "request_id",
            "challenge",
            "receipt",
            "created_at",
            "replayed",
        }
        assert payload["challenge"] == "V001"
        assert payload["receipt"].startswith("POC-")
        assert payload["replayed"] is False
        created_at = datetime.fromisoformat(payload["created_at"])
        assert created_at.utcoffset() is not None
        assert abs((datetime.now(timezone.utc) - created_at.astimezone(timezone.utc)).total_seconds()) < 30
    assert first_payload["request_id"] != second_payload["request_id"]
    assert first_payload["receipt"] != second_payload["receipt"]


def test_challenge_is_returned_without_silent_normalization() -> None:
    response = send_probe(
        create_app(), key="c2-b2-original-challenge", challenge="  V001  "
    )

    assert response.status_code == 200
    assert response.json()["challenge"] == "  V001  "


@pytest.mark.parametrize(
    ("headers", "content", "media_type"),
    [
        ({}, json.dumps({"challenge": "V001"}), "application/json"),
        ({"Idempotency-Key": ""}, json.dumps({"challenge": "V001"}), "application/json"),
        ({"Idempotency-Key": "   "}, json.dumps({"challenge": "V001"}), "application/json"),
        ({"Idempotency-Key": "c2-missing"}, json.dumps({}), "application/json"),
        ({"Idempotency-Key": "c2-null"}, json.dumps({"challenge": None}), "application/json"),
        ({"Idempotency-Key": "c2-int"}, json.dumps({"challenge": 1}), "application/json"),
        ({"Idempotency-Key": "c2-list"}, json.dumps({"challenge": []}), "application/json"),
        ({"Idempotency-Key": "c2-empty"}, json.dumps({"challenge": ""}), "application/json"),
        ({"Idempotency-Key": "c2-blank"}, json.dumps({"challenge": " \t"}), "application/json"),
        ({"Idempotency-Key": "c2-long"}, json.dumps({"challenge": "x" * 129}), "application/json"),
        (
            {"Idempotency-Key": "c2-extra"},
            json.dumps({"challenge": "V001", "private": "C2_EXTRA_CANARY"}),
            "application/json",
        ),
        ({"Idempotency-Key": "c2-malformed"}, '{"challenge":', "application/json"),
        ({"Idempotency-Key": "c2-array-body"}, json.dumps([]), "application/json"),
    ],
)
def test_invalid_inputs_have_one_safe_422_contract(
    headers: dict[str, str], content: str, media_type: str
) -> None:
    app = create_app()

    with client_for(app) as client:
        response = client.post(
            PROBE_PATH,
            headers={**headers, "Content-Type": media_type},
            content=content,
        )

    assert_safe_error(response, status=422, code="invalid_request")
    assert "C2_EXTRA_CANARY" not in response.text
    assert content not in response.text


def test_replay_keeps_first_identity_receipt_and_time() -> None:
    app = create_app()

    first = send_probe(app, key="c2-b2-replay")
    replay = send_probe(app, key="c2-b2-replay")

    assert first.status_code == replay.status_code == 200
    first_payload = first.json()
    replay_payload = replay.json()
    assert first_payload["replayed"] is False
    assert replay_payload["replayed"] is True
    for field in ("request_id", "challenge", "receipt", "created_at"):
        assert replay_payload[field] == first_payload[field]


def test_same_key_with_different_input_conflicts_without_a_second_receipt() -> None:
    calls = 0

    def counted_receipt() -> str:
        nonlocal calls
        calls += 1
        return f"POC-count-{calls}"

    app = create_app(probe_service=ProbeService(receipt_factory=counted_receipt))

    first = send_probe(app, key="c2-b2-conflict", challenge="first")
    conflict = send_probe(app, key="c2-b2-conflict", challenge="second")

    assert first.status_code == 200
    conflict_payload = assert_safe_error(
        conflict, status=409, code="duplicate_request_conflict"
    )
    assert conflict_payload["request_id"] == first.json()["request_id"]
    assert calls == 1


def test_same_text_with_different_event_keys_is_not_deduplicated() -> None:
    app = create_app()

    first = send_probe(app, key="c2-b2-event-a", challenge="same text")
    second = send_probe(app, key="c2-b2-event-b", challenge="same text")

    assert first.status_code == second.status_code == 200
    assert first.json()["request_id"] != second.json()["request_id"]
    assert first.json()["receipt"] != second.json()["receipt"]


def test_concurrent_identical_requests_create_exactly_one_record() -> None:
    receipt_calls = 0
    receipt_lock = threading.Lock()

    def counted_receipt() -> str:
        nonlocal receipt_calls
        with receipt_lock:
            receipt_calls += 1
        return "POC-C2-CONCURRENT"

    app = create_app(probe_service=ProbeService(receipt_factory=counted_receipt))

    with ThreadPoolExecutor(max_workers=12) as pool:
        responses = list(
            pool.map(
                lambda _: send_probe(app, key="c2-b2-concurrent"),
                range(24),
            )
        )

    assert all(response.status_code == 200 for response in responses)
    payloads = [response.json() for response in responses]
    assert receipt_calls == 1
    assert len({payload["request_id"] for payload in payloads}) == 1
    assert {payload["receipt"] for payload in payloads} == {"POC-C2-CONCURRENT"}
    assert sum(payload["replayed"] is False for payload in payloads) == 1
    assert sum(payload["replayed"] is True for payload in payloads) == 23


def test_concurrent_conflicting_payloads_have_one_winner_and_no_overwrite() -> None:
    receipt_calls = 0
    receipt_lock = threading.Lock()

    def counted_receipt() -> str:
        nonlocal receipt_calls
        with receipt_lock:
            receipt_calls += 1
            number = receipt_calls
        return f"POC-C2-RACE-{number}"

    app = create_app(probe_service=ProbeService(receipt_factory=counted_receipt))
    challenges = ["alpha", "beta"] * 8

    with ThreadPoolExecutor(max_workers=12) as pool:
        responses = list(
            pool.map(
                lambda challenge: send_probe(
                    app, key="c2-b2-conflict-race", challenge=challenge
                ),
                challenges,
            )
        )

    successes = [response.json() for response in responses if response.status_code == 200]
    conflicts = [response for response in responses if response.status_code == 409]
    assert successes and conflicts
    assert receipt_calls == 1
    assert len({payload["challenge"] for payload in successes}) == 1
    assert len({payload["request_id"] for payload in successes}) == 1
    assert len({payload["receipt"] for payload in successes}) == 1
    for response in conflicts:
        payload = assert_safe_error(
            response, status=409, code="duplicate_request_conflict"
        )
        assert payload["request_id"] == successes[0]["request_id"]


def test_distinct_concurrent_keys_do_not_share_identity_or_receipt() -> None:
    app = create_app()
    keys = [f"c2-b2-distinct-concurrent-{index}" for index in range(16)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(lambda key: send_probe(app, key=key), keys))

    assert all(response.status_code == 200 for response in responses)
    payloads = [response.json() for response in responses]
    assert len({payload["request_id"] for payload in payloads}) == len(keys)
    assert len({payload["receipt"] for payload in payloads}) == len(keys)


def test_new_process_local_service_does_not_claim_persistent_replay() -> None:
    first = send_probe(create_app(), key="c2-b2-process-local")
    after_restart_equivalent = send_probe(
        create_app(), key="c2-b2-process-local"
    )

    assert first.status_code == after_restart_equivalent.status_code == 200
    assert after_restart_equivalent.json()["replayed"] is False
    assert first.json()["request_id"] != after_restart_equivalent.json()["request_id"]
    assert first.json()["receipt"] != after_restart_equivalent.json()["receipt"]


def test_success_and_replay_logs_are_valid_json_and_omit_private_inputs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="wife_system.api")
    private_key = "wx-user-C2-B2-private-key"
    private_challenge = "C2-B2 full private message canary"
    app = create_app()

    first = send_probe(app, key=private_key, challenge=private_challenge)
    replay = send_probe(app, key=private_key, challenge=private_challenge)

    assert first.status_code == replay.status_code == 200
    records = [json.loads(record.getMessage()) for record in caplog.records]
    serialized = json.dumps(records, ensure_ascii=False)
    assert private_key not in serialized
    assert private_challenge not in serialized
    assert any(
        record.get("event") == "probe_created"
        and record.get("request_id") == first.json()["request_id"]
        and record.get("receipt") == first.json()["receipt"]
        for record in records
    )
    assert any(
        record.get("event") == "probe_replayed"
        and record.get("request_id") == first.json()["request_id"]
        for record in records
    )


def test_validation_logs_and_response_omit_body_header_and_framework_details(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="wife_system.api")
    private_key = "C2-B2-VALIDATION-PRIVATE-KEY"
    private_value = "C2-B2-VALIDATION-PRIVATE-BODY"
    app = create_app()

    with client_for(app) as client:
        response = client.post(
            PROBE_PATH,
            headers={"Idempotency-Key": private_key},
            json={"challenge": private_value, "extra": private_value},
        )

    assert_safe_error(response, status=422, code="invalid_request")
    combined = response.text + "\n" + "\n".join(
        record.getMessage() for record in caplog.records
    )
    assert private_key not in combined
    assert private_value not in combined
    assert "RequestValidationError" not in combined


def test_internal_failure_returns_safe_500_and_service_can_handle_next_request(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level("INFO", logger="wife_system.api")
    calls = 0
    private_failure = "C2-B2-PRIVATE-STACK-CANARY"

    def fail_once() -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError(private_failure)
        return "POC-C2-RECOVERED"

    app = create_app(probe_service=ProbeService(receipt_factory=fail_once))

    failed = send_probe(app, key="c2-b2-failure")
    recovered = send_probe(app, key="c2-b2-recovered")

    failed_payload = assert_safe_error(failed, status=500, code="internal_error")
    assert private_failure not in failed.text
    assert private_failure not in "\n".join(
        record.getMessage() for record in caplog.records
    )
    assert recovered.status_code == 200
    assert recovered.json()["receipt"] == "POC-C2-RECOVERED"
    assert recovered.json()["request_id"] != failed_payload["request_id"]


def test_naive_clock_is_a_safe_internal_error_and_does_not_cache_a_record() -> None:
    private_key = "c2-b2-naive-clock"
    service = ProbeService(clock=lambda: datetime(2026, 9, 14, 16, 0, 0))
    app = create_app(probe_service=service)

    first = send_probe(app, key=private_key)
    second = send_probe(app, key=private_key)

    first_payload = assert_safe_error(first, status=500, code="internal_error")
    second_payload = assert_safe_error(second, status=500, code="internal_error")
    assert first_payload["request_id"] != second_payload["request_id"]
    assert "timezone" not in first.text.lower()
