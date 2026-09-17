from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from wife_system.api.app import create_app
from wife_system.probes import ProbeService


def build_client(*, probe_service: ProbeService | None = None) -> TestClient:
    return TestClient(create_app(probe_service=probe_service), raise_server_exceptions=False)


def test_health_check_has_frozen_response() -> None:
    response = build_client().get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "wife-system"}


def test_openapi_marks_idempotency_key_as_required() -> None:
    schema = build_client().get("/openapi.json").json()

    parameters = schema["paths"]["/api/v1/probes"]["post"]["parameters"]
    idempotency_key = next(item for item in parameters if item["name"] == "Idempotency-Key")
    assert idempotency_key["required"] is True


def test_creates_random_probe_with_request_id_and_aware_timestamp() -> None:
    client = build_client()

    first = client.post(
        "/api/v1/probes",
        headers={"Idempotency-Key": "event-1"},
        json={"challenge": "V001"},
    )
    second = client.post(
        "/api/v1/probes",
        headers={"Idempotency-Key": "event-2"},
        json={"challenge": "V001"},
    )

    assert first.status_code == second.status_code == 200
    first_body = first.json()
    second_body = second.json()
    assert first_body["challenge"] == second_body["challenge"] == "V001"
    assert first_body["request_id"] != second_body["request_id"]
    assert first_body["receipt"] != second_body["receipt"]
    assert first_body["receipt"].startswith("POC-")
    assert first_body["replayed"] is second_body["replayed"] is False
    assert datetime.fromisoformat(first_body["created_at"]).utcoffset() is not None


def test_same_key_and_payload_replays_first_probe() -> None:
    client = build_client()
    headers = {"Idempotency-Key": "same-event"}

    first = client.post("/api/v1/probes", headers=headers, json={"challenge": "V001"})
    replay = client.post("/api/v1/probes", headers=headers, json={"challenge": "V001"})

    assert first.status_code == replay.status_code == 200
    first_body = first.json()
    replay_body = replay.json()
    assert replay_body == {**first_body, "replayed": True}


def test_same_key_with_different_payload_returns_conflict() -> None:
    client = build_client()
    headers = {"Idempotency-Key": "conflicting-event"}
    first = client.post("/api/v1/probes", headers=headers, json={"challenge": "V001"})

    conflict = client.post("/api/v1/probes", headers=headers, json={"challenge": "V002"})

    assert conflict.status_code == 409
    assert conflict.json() == {
        "request_id": first.json()["request_id"],
        "error": {
            "code": "duplicate_request_conflict",
            "message": "The idempotency key was already used for different input.",
            "retryable": False,
        },
    }


@pytest.mark.parametrize(
    ("headers", "body"),
    [
        ({}, {"challenge": "V001"}),
        ({"Idempotency-Key": "event"}, {}),
        ({"Idempotency-Key": "event"}, {"challenge": ""}),
        ({"Idempotency-Key": "event"}, {"challenge": " "}),
        ({"Idempotency-Key": "event"}, {"challenge": "V001", "secret": "canary"}),
    ],
)
def test_invalid_requests_use_safe_stable_error(
    headers: dict[str, str], body: dict[str, str]
) -> None:
    response = build_client().post("/api/v1/probes", headers=headers, json=body)

    assert response.status_code == 422
    payload = response.json()
    assert payload["request_id"]
    assert payload["error"]["code"] == "invalid_request"
    assert "canary" not in response.text


def test_concurrent_replay_creates_exactly_one_receipt() -> None:
    calls = 0

    def receipt_factory() -> str:
        nonlocal calls
        calls += 1
        return "POC-concurrent"

    client = build_client(probe_service=ProbeService(receipt_factory=receipt_factory))

    def send() -> dict[str, object]:
        response = client.post(
            "/api/v1/probes",
            headers={"Idempotency-Key": "concurrent-event"},
            json={"challenge": "V001"},
        )
        assert response.status_code == 200
        return response.json()

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: send(), range(16)))

    assert calls == 1
    assert len({item["request_id"] for item in results}) == 1
    assert {item["receipt"] for item in results} == {"POC-concurrent"}
    assert sum(item["replayed"] is False for item in results) == 1


def test_logs_receipt_and_key_hash_without_private_inputs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level("INFO", logger="wife_system.api")
    private_key = "wx-user-private-canary"
    private_challenge = "private-message-canary"

    response = build_client().post(
        "/api/v1/probes",
        headers={"Idempotency-Key": private_key},
        json={"challenge": private_challenge},
    )

    assert response.status_code == 200
    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert response.json()["receipt"] in log_text
    assert private_key not in log_text
    assert private_challenge not in log_text
    for record in caplog.records:
        json.loads(record.getMessage())


def test_unhandled_service_failure_returns_safe_500(caplog: pytest.LogCaptureFixture) -> None:
    def fail_receipt() -> str:
        raise RuntimeError("private-failure-canary")

    caplog.set_level("INFO", logger="wife_system.api")
    client = build_client(probe_service=ProbeService(receipt_factory=fail_receipt))

    response = client.post(
        "/api/v1/probes",
        headers={"Idempotency-Key": "event"},
        json={"challenge": "V001"},
    )

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "private-failure-canary" not in response.text
    assert "private-failure-canary" not in "\n".join(
        record.getMessage() for record in caplog.records
    )
