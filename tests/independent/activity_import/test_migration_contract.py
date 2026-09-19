from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


P2_HEAD = "7f3e2d1c9a4b"
P3_HEAD = "c82d7a4f901e"


def config_for(url: str) -> Config:
    root = Path(__file__).resolve().parents[3]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def test_c9_empty_sqlite_upgrade_downgrade_and_rebuild(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'empty.sqlite3'}"
    cfg = config_for(url)
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
        assert {"activity_import_batch", "activity_import_candidate"}.issubset(inspect(connection).get_table_names())
    engine.dispose()
    command.downgrade(cfg, P2_HEAD)
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
    engine.dispose()


def test_c9_existing_p2_history_ids_amount_and_references_survive_upgrade(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'history.sqlite3'}"
    cfg = config_for(url)
    command.upgrade(cfg, P2_HEAD)
    template_id, revision_id, occurrence_id = uuid.uuid4().hex, uuid.uuid4().hex, uuid.uuid4().hex
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text(
            "INSERT INTO activity_template (id,current_revision_id,archived_at,created_at,version_id) "
            "VALUES (:id,NULL,NULL,CURRENT_TIMESTAMP,1)"
        ), {"id": template_id})
        connection.execute(text(
            "INSERT INTO activity_template_revision "
            "(id,template_id,revision_no,name,reference_minor,currency,created_at) "
            "VALUES (:id,:template,1,'虚拟 历史',456,'CNY',CURRENT_TIMESTAMP)"
        ), {"id": revision_id, "template": template_id})
        connection.execute(text(
            "UPDATE activity_template SET current_revision_id=:revision WHERE id=:template"
        ), {"revision": revision_id, "template": template_id})
        connection.execute(text(
            "INSERT INTO activity_occurrence "
            "(id,template_revision_id,occurred_at,status,created_at,version_id) "
            "VALUES (:id,:revision,CURRENT_TIMESTAMP,'active',CURRENT_TIMESTAMP,1)"
        ), {"id": occurrence_id, "revision": revision_id})
    engine.dispose()
    command.upgrade(cfg, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.execute(text(
            "SELECT reference_minor,reference_min_minor,reference_max_minor "
            "FROM activity_template_revision WHERE id=:id"
        ), {"id": revision_id}).one() == (456, 456, 456)
        assert connection.scalar(text(
            "SELECT name_normalized FROM activity_template WHERE id=:id"
        ), {"id": template_id}) == "虚拟 历史"
        assert connection.scalar(text(
            "SELECT template_revision_id FROM activity_occurrence WHERE id=:id"
        ), {"id": occurrence_id}) == revision_id
    engine.dispose()


def test_c9_normalized_duplicate_aborts_before_p3_schema_change(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'collision.sqlite3'}"
    cfg = config_for(url)
    command.upgrade(cfg, P2_HEAD)
    engine = create_engine(url)
    with engine.begin() as connection:
        for ordinal, name in enumerate(("CAFE\u0301", "CAFÉ"), start=1):
            template, revision = uuid.uuid4().hex, uuid.uuid4().hex
            connection.execute(text(
                "INSERT INTO activity_template (id,current_revision_id,archived_at,created_at,version_id) "
                "VALUES (:id,NULL,NULL,CURRENT_TIMESTAMP,1)"
            ), {"id": template})
            connection.execute(text(
                "INSERT INTO activity_template_revision "
                "(id,template_id,revision_no,name,reference_minor,currency,created_at) "
                "VALUES (:id,:template,1,:name,NULL,'CNY',CURRENT_TIMESTAMP)"
            ), {"id": revision, "template": template, "name": name})
            connection.execute(text(
                "UPDATE activity_template SET current_revision_id=:revision WHERE id=:template"
            ), {"revision": revision, "template": template})
    engine.dispose()
    with pytest.raises(Exception):
        command.upgrade(cfg, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == P2_HEAD
        assert "activity_import_batch" not in inspect(connection).get_table_names()
    engine.dispose()
