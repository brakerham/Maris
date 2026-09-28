from __future__ import annotations

import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: dict[str, object] | None = None,
) -> tuple[int, dict[str, object]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read())


def _wait_request(base_url: str, path: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, object]]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            return _request(base_url, path, headers=headers)
        except (OSError, urllib.error.URLError):
            time.sleep(0.05)
    raise AssertionError("sidecar did not accept loopback requests")


def test_managed_sidecar_handshake_owner_modules_and_bounded_stop(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    nonce = secrets.token_urlsafe(32)
    instance_id = str(uuid.uuid4())
    secret_names = (
        "WIFE_BOOTSTRAP_TOKEN",
        "WIFE_BINDING_HMAC_KEY",
        "WIFE_ADAPTER_TOKEN",
        "WIFE_HOST_STATE_KEY",
        "WIFE_CURSOR_KEY",
        "WIFE_AGENT_DIGEST_KEY",
        "WIFE_FINANCE_RECEIPT_KEY",
    )
    database = (tmp_path / "sidecar.db").as_posix()
    environment = {
        **os.environ,
        "PYTHONPATH": str(root / "src"),
        "PYTHONUNBUFFERED": "1",
        "MARIS_HOST_PROJECT_ROOT": str(root),
        "MARIS_DESKTOP_INSTANCE_ID": instance_id,
        "WIFE_DESKTOP_PROFILE": "managed",
        "WIFE_DESKTOP_STARTUP_NONCE": nonce,
        "WIFE_DATABASE_URL": f"sqlite+pysqlite:///{database}",
        **{name: secrets.token_urlsafe(32) for name in secret_names},
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "wife_system.api.desktop_sidecar"],
        cwd=root,
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    try:
        assert process.stdout is not None
        handshake_line = process.stdout.readline()
        handshake = json.loads(handshake_line)
        assert handshake == {
            "protocol": "maris-desktop-sidecar@1",
            "instance_id": instance_id,
            "host": "127.0.0.1",
            "port": handshake["port"],
            "nonce_digest": hashlib.sha256(nonce.encode()).hexdigest(),
        }
        assert nonce not in handshake_line
        base_url = f"http://127.0.0.1:{handshake['port']}"
        assert _wait_request(base_url, "/healthz")[0] == 200
        desktop = _wait_request(
            base_url,
            "/api/v1/desktop/readyz",
            {"X-Maris-Startup-Nonce": nonce},
        )
        assert desktop == (200, {"status": "ready"})
        general = _request(base_url, "/readyz")
        assert general[0] == 503
        assert general[1]["error"]["code"] == "agent_provider_unconfigured"  # type: ignore[index]

        assert _request(base_url, "/api/v1/auth/bootstrap-status") == (
            200,
            {"needs_initialization": True},
        )
        password = secrets.token_urlsafe(32)
        initialize = _request(
            base_url,
            "/api/v1/auth/initialize",
            method="POST",
            headers={
                "X-Bootstrap-Token": environment["WIFE_BOOTSTRAP_TOKEN"],
                "Idempotency-Key": str(uuid.uuid4()),
            },
            body={"handle": "local_owner", "password": password},
        )
        assert initialize[0] == 200
        login = _request(
            base_url,
            "/api/v1/auth/login",
            method="POST",
            body={
                "handle": "local_owner",
                "password": password,
                "client_fingerprint": "sidecar-smoke",
                "device_name": "Maris sidecar smoke",
                "platform": "windows_desktop",
            },
        )
        assert login[0] == 200
        access_token = str(login[1]["access_token"])
        modules = _request(
            base_url,
            "/api/v1/modules",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert modules[0] == 200
        assert [item["module_id"] for item in modules[1]] == ["daily_finance"]  # type: ignore[index]
    finally:
        if process.stdin is not None and process.poll() is None:
            process.stdin.write("shutdown\n")
            process.stdin.flush()
        process.wait(timeout=10)
        if process.poll() is None:
            process.kill()
        assert process.returncode == 0

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.2)
        assert probe.connect_ex(("127.0.0.1", int(handshake["port"]))) != 0
