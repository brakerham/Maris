from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from wife_system.api.app import create_app
from wife_system.api.desktop_runtime import DesktopReadinessError, DesktopRuntimeGate


class ReadyRuntime:
    def readiness(self) -> tuple[bool, str | None]:
        return True, None

    def core_readiness(self) -> tuple[bool, str | None]:
        return True, None


def test_desktop_gate_is_disabled_for_general_deployments() -> None:
    client = TestClient(create_app(host_runtime=ReadyRuntime()))  # type: ignore[arg-type]
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").json() == {"status": "ready"}
    response = client.get("/api/v1/desktop/readyz")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "desktop_profile_required"


def test_managed_desktop_gate_requires_exact_nonce_without_echoing_it() -> None:
    nonce = b"n" * 43
    app = create_app(
        host_runtime=ReadyRuntime(),  # type: ignore[arg-type]
        desktop_runtime_gate=DesktopRuntimeGate(managed=True, startup_nonce=nonce),
    )
    client = TestClient(app, raise_server_exceptions=False)
    missing = client.get("/api/v1/desktop/readyz")
    wrong = client.get("/api/v1/desktop/readyz", headers={"X-Maris-Startup-Nonce": "wrong" * 9})
    accepted = client.get("/api/v1/desktop/readyz", headers={"X-Maris-Startup-Nonce": nonce.decode()})
    assert missing.status_code == wrong.status_code == 503
    assert missing.json()["error"]["code"] == "desktop_startup_nonce_required"
    assert wrong.json()["error"]["code"] == "desktop_startup_nonce_mismatch"
    assert nonce.decode() not in missing.text + wrong.text
    assert accepted.json() == {"status": "ready"}


def test_gate_configuration_and_direct_errors_are_fail_closed() -> None:
    with pytest.raises(ValueError, match="invalid_desktop_startup_nonce"):
        DesktopRuntimeGate(managed=True, startup_nonce=b"short")
    with pytest.raises(ValueError, match="unexpected_desktop_startup_nonce"):
        DesktopRuntimeGate(startup_nonce=b"n" * 32)
    with pytest.raises(DesktopReadinessError, match="desktop_startup_nonce_mismatch"):
        DesktopRuntimeGate(managed=True, startup_nonce=b"n" * 32).verify_desktop_ready("x" * 32)
