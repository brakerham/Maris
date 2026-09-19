from __future__ import annotations

import ast
import importlib.util
import uuid
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


P2_HEAD = "7f3e2d1c9a4b"
P3_HEAD = "c82d7a4f901e"
EXPECTED_IMPORT_CANDIDATE_FK_NAME = "fk_activity_template_revision_import_candidate"


def load_p3_migration():
    path = Path(__file__).resolve().parents[2] / "migrations" / "versions" / "c82d7a4f901e_add_activity_import.py"
    spec = importlib.util.spec_from_file_location("p3_activity_import_migration", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return path, module


def test_explicit_postgresql_identifier_names_are_bounded_and_fk_is_symmetric() -> None:
    path, migration = load_p3_migration()
    assert migration.POSTGRESQL_IDENTIFIER_MAX_LENGTH == 63
    assert migration.IMPORT_CANDIDATE_FK_NAME == EXPECTED_IMPORT_CANDIDATE_FK_NAME

    tree = ast.parse(path.read_text(encoding="utf-8"))
    string_constants = {
        target.id: node.value.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    def resolve_identifier(node: ast.expr) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.Name):
            return string_constants.get(node.id)
        return None

    identifier_first_arg_operations = {
        "create_check_constraint",
        "create_foreign_key",
        "create_index",
        "create_unique_constraint",
        "drop_constraint",
        "drop_index",
    }
    explicit_identifiers: list[str] = []
    fk_name_operations: list[tuple[str, str, str]] = []
    for function in (node for node in tree.body if isinstance(node, ast.FunctionDef)):
        for call in (node for node in ast.walk(function) if isinstance(node, ast.Call)):
            for keyword in call.keywords:
                if keyword.arg == "name":
                    identifier = resolve_identifier(keyword.value)
                    if identifier is not None:
                        explicit_identifiers.append(identifier)
            if not isinstance(call.func, ast.Attribute) or not call.args:
                continue
            if call.func.attr in identifier_first_arg_operations:
                identifier = resolve_identifier(call.args[0])
                if identifier is not None:
                    explicit_identifiers.append(identifier)
            if call.func.attr in {"create_foreign_key", "drop_constraint"}:
                identifier = resolve_identifier(call.args[0])
                if identifier == EXPECTED_IMPORT_CANDIDATE_FK_NAME:
                    fk_name_operations.append((function.name, call.func.attr, identifier))

    assert explicit_identifiers
    assert all(len(name) <= migration.POSTGRESQL_IDENTIFIER_MAX_LENGTH for name in explicit_identifiers)
    assert sorted(fk_name_operations) == [
        ("downgrade", "drop_constraint", EXPECTED_IMPORT_CANDIDATE_FK_NAME),
        ("upgrade", "create_foreign_key", EXPECTED_IMPORT_CANDIDATE_FK_NAME),
    ]


def migration_config(url: str) -> Config:
    root = Path(__file__).resolve().parents[2]
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def seed_template(connection, *, name: str, amount: int | None, archived: bool = False) -> tuple[str, str]:
    template_id = uuid.uuid4().hex
    revision_id = uuid.uuid4().hex
    connection.execute(text(
        "INSERT INTO activity_template (id,current_revision_id,archived_at,created_at,version_id) "
        "VALUES (:id,NULL,:archived,CURRENT_TIMESTAMP,1)"
    ), {"id": template_id, "archived": "2026-09-01 00:00:00" if archived else None})
    connection.execute(text(
        "INSERT INTO activity_template_revision "
        "(id,template_id,revision_no,name,reference_minor,currency,created_at) "
        "VALUES (:id,:template,1,:name,:amount,'CNY',CURRENT_TIMESTAMP)"
    ), {"id": revision_id, "template": template_id, "name": name, "amount": amount})
    connection.execute(text(
        "UPDATE activity_template SET current_revision_id=:revision WHERE id=:template"
    ), {"revision": revision_id, "template": template_id})
    return template_id, revision_id


def test_empty_sqlite_upgrade_repeat_downgrade_and_recover(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'empty.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, "head")
    command.upgrade(config, "head")
    engine = create_engine(url)
    assert engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == P3_HEAD
    assert {"activity_import_batch", "activity_import_candidate"}.issubset(inspect(engine).get_table_names())
    engine.dispose()
    command.downgrade(config, P2_HEAD)
    engine = create_engine(url)
    assert "activity_import_batch" not in inspect(engine).get_table_names()
    assert "name_normalized" not in {column["name"] for column in inspect(engine).get_columns("activity_template")}
    engine.dispose()
    command.upgrade(config, "head")


def test_existing_template_history_is_preserved_and_amount_is_backfilled(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'existing.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, P2_HEAD)
    engine = create_engine(url)
    with engine.begin() as connection:
        template_id, revision_id = seed_template(
            connection, name="  虚拟   跑步  ", amount=1234, archived=True
        )
        occurrence_id = uuid.uuid4().hex
        connection.execute(text(
            "INSERT INTO activity_occurrence "
            "(id,template_revision_id,occurred_at,status,created_at,version_id) "
            "VALUES (:id,:revision,CURRENT_TIMESTAMP,'active',CURRENT_TIMESTAMP,1)"
        ), {"id": occurrence_id, "revision": revision_id})
    engine.dispose()

    command.upgrade(config, "head")
    engine = create_engine(url)
    with engine.connect() as connection:
        template = connection.execute(text(
            "SELECT id,current_revision_id,name_normalized,archived_at,version_id "
            "FROM activity_template WHERE id=:id"
        ), {"id": template_id}).one()
        revision = connection.execute(text(
            "SELECT id,name,reference_minor,reference_min_minor,reference_max_minor,source_import_candidate_id "
            "FROM activity_template_revision WHERE id=:id"
        ), {"id": revision_id}).one()
        assert template.id == template_id
        assert template.current_revision_id == revision_id
        assert template.name_normalized == "虚拟 跑步"
        assert template.archived_at is not None
        assert template.version_id == 1
        assert revision == (revision_id, "  虚拟   跑步  ", 1234, 1234, 1234, None)
        assert connection.scalar(text(
            "SELECT template_revision_id FROM activity_occurrence WHERE id=:id"
        ), {"id": occurrence_id}) == revision_id
        assert connection.scalar(text("PRAGMA foreign_key_check")) is None
    engine.dispose()


def test_normalized_name_collision_fails_before_schema_changes(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'duplicate.sqlite3').as_posix()}"
    config = migration_config(url)
    command.upgrade(config, P2_HEAD)
    engine = create_engine(url)
    with engine.begin() as connection:
        seed_template(connection, name="虚拟 活动", amount=None)
        seed_template(connection, name="  虚拟   活动 ", amount=0, archived=True)
    engine.dispose()

    with pytest.raises(RuntimeError, match="duplicate or invalid normalized name"):
        command.upgrade(config, "head")
    engine = create_engine(url)
    assert engine.connect().scalar(text("SELECT version_num FROM alembic_version")) == P2_HEAD
    inspector = inspect(engine)
    assert "activity_import_batch" not in inspector.get_table_names()
    assert "name_normalized" not in {column["name"] for column in inspector.get_columns("activity_template")}
    engine.dispose()


def test_new_database_constraints_include_identity_amount_and_source_rules(tmp_path: Path) -> None:
    url = f"sqlite:///{(tmp_path / 'constraints.sqlite3').as_posix()}"
    command.upgrade(migration_config(url), "head")
    engine = create_engine(url)
    inspector = inspect(engine)
    template_constraints = {item["name"] for item in inspector.get_unique_constraints("activity_template")}
    revision_checks = {item["name"] for item in inspector.get_check_constraints("activity_template_revision")}
    candidate_checks = {item["name"] for item in inspector.get_check_constraints("activity_import_candidate")}
    revision_fks = {item["name"] for item in inspector.get_foreign_keys("activity_template_revision")}
    assert "uq_activity_template_name_normalized" in template_constraints
    assert "ck_activity_template_revision_reference_shape" in revision_checks
    assert {
        "ck_activity_import_candidate_reference_shape",
        "ck_activity_import_candidate_decision_shape",
        "ck_activity_import_candidate_target_shape",
    }.issubset(candidate_checks)
    assert EXPECTED_IMPORT_CANDIDATE_FK_NAME in revision_fks
    template_id = uuid.uuid4().hex
    revision_id = uuid.uuid4().hex
    with engine.begin() as connection:
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(text(
            "INSERT INTO activity_template "
            "(id,name_normalized,current_revision_id,archived_at,created_at,version_id) "
            "VALUES (:id,'虚拟约束',NULL,NULL,CURRENT_TIMESTAMP,1)"
        ), {"id": template_id})
        connection.execute(text(
            "INSERT INTO activity_template_revision "
            "(id,template_id,revision_no,name,reference_minor,reference_min_minor,reference_max_minor,"
            "source_import_candidate_id,currency,created_at) "
            "VALUES (:id,:template,1,'虚拟约束',100,100,100,NULL,'CNY',CURRENT_TIMESTAMP)"
        ), {"id": revision_id, "template": template_id})
        connection.execute(text(
            "UPDATE activity_template SET current_revision_id=:revision WHERE id=:template"
        ), {"revision": revision_id, "template": template_id})
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text(
                "UPDATE activity_template_revision SET reference_minor=NULL,"
                "reference_min_minor=200,reference_max_minor=100 WHERE id=:id"
            ), {"id": revision_id})
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO activity_template "
                "(id,name_normalized,current_revision_id,archived_at,created_at,version_id) "
                "VALUES (:id,'虚拟约束',NULL,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,1)"
            ), {"id": uuid.uuid4().hex})
    engine.dispose()
