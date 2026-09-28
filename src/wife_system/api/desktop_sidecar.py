"""Managed desktop entry point with a machine-readable parent handshake."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import socket
import sys
import uuid
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config

from wife_system.api.production import ProductionConfig, create_production_app


PROTOCOL = "maris-desktop-sidecar@1"
LOOPBACK = "127.0.0.1"


class SidecarConfigurationError(RuntimeError):
    pass


def _required(name: str) -> str:
    value = os.environ.get(name)
    if value is None or not value.strip():
        raise SidecarConfigurationError(f"missing_{name.casefold()}")
    return value


def _project_root() -> Path:
    configured = os.environ.get("MARIS_HOST_PROJECT_ROOT")
    root = Path(configured) if configured else Path(__file__).resolve().parents[3]
    ini = root / "alembic.ini"
    migrations = root / "migrations"
    if not ini.is_file() or not migrations.is_dir():
        raise SidecarConfigurationError("host_resources_unavailable")
    return root


def _upgrade_database(root: Path, database_url: str) -> None:
    previous = os.environ.get("FINANCE_DATABASE_URL")
    os.environ["FINANCE_DATABASE_URL"] = database_url
    try:
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        command.upgrade(config, "head")
    finally:
        if previous is None:
            os.environ.pop("FINANCE_DATABASE_URL", None)
        else:
            os.environ["FINANCE_DATABASE_URL"] = previous


async def _watch_parent(server: uvicorn.Server) -> None:
    line = await asyncio.to_thread(sys.stdin.readline)
    if line.strip() == "shutdown" or line == "":
        server.should_exit = True


async def _serve() -> int:
    instance_id = str(uuid.UUID(_required("MARIS_DESKTOP_INSTANCE_ID")))
    nonce = _required("WIFE_DESKTOP_STARTUP_NONCE")
    if len(nonce.encode("utf-8")) < 32:
        raise SidecarConfigurationError("invalid_desktop_startup_nonce")

    root = _project_root()
    database_url = _required("WIFE_DATABASE_URL")
    _upgrade_database(root, database_url)
    application = create_production_app(ProductionConfig.from_environment())

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    listener.bind((LOOPBACK, 0))
    listener.listen(128)
    listener.setblocking(False)
    port = int(listener.getsockname()[1])

    config = uvicorn.Config(
        application,
        host=LOOPBACK,
        port=port,
        loop="asyncio",
        workers=1,
        reload=False,
        access_log=False,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    handshake = {
        "protocol": PROTOCOL,
        "instance_id": instance_id,
        "host": LOOPBACK,
        "port": port,
        "nonce_digest": hashlib.sha256(nonce.encode("utf-8")).hexdigest(),
    }
    print(json.dumps(handshake, separators=(",", ":")), flush=True)
    parent_watch = asyncio.create_task(_watch_parent(server))
    try:
        await server.serve(sockets=[listener])
    finally:
        parent_watch.cancel()
        await asyncio.gather(parent_watch, return_exceptions=True)
        listener.close()
        engine = getattr(application.state, "engine", None)
        if engine is not None:
            engine.dispose()
    return 0


def main() -> int:
    try:
        return asyncio.run(_serve())
    except Exception as exc:
        error = {"event": "MARIS_SIDECAR_ERROR", "type": type(exc).__name__}
        print(json.dumps(error, separators=(",", ":")), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
