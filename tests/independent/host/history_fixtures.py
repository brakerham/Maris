"""Low-level P0-P3 history fixtures independent from current P4 ORM models."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import text

from wife_system.finance.models import BOOTSTRAP_USER_ID


def _database_id(connection, value: uuid.UUID):
    return value if connection.dialect.name == "postgresql" else value.hex


def seed_p3_history(connection) -> dict[str, object]:
    """Insert representative P1/P2/P3 rows using only the P3 database contract."""

    values = {
        name: _database_id(connection, uuid.uuid4())
        for name in (
            "account",
            "category",
            "finance_receipt",
            "transaction",
            "account_entry",
            "expense_entry",
            "run",
            "pending",
            "conversation",
            "preview_receipt",
            "import_batch",
            "import_candidate",
        )
    }
    values["owner"] = _database_id(connection, BOOTSTRAP_USER_ID)
    now = datetime(2026, 9, 26, 8, 0, tzinfo=UTC)

    connection.execute(
        text(
            "INSERT INTO account (id,name,currency,archived_at,created_at,version_id) "
            "VALUES (:id,'virtual P3 history account','CNY',NULL,:now,1)"
        ),
        {"id": values["account"], "now": now},
    )
    connection.execute(
        text(
            "INSERT INTO category "
            "(id,kind,name,name_normalized,archived_at,created_at,version_id) "
            "VALUES (:id,'expense','virtual P3 history expense','virtual p3 history expense',NULL,:now,1)"
        ),
        {"id": values["category"], "now": now},
    )
    connection.execute(
        text(
            "INSERT INTO command_receipt "
            "(id,source_system,key_version,key_digest,request_fingerprint,command_name,"
            "result_type,result_id,result_json,completed_at,created_at) VALUES "
            "(:id,'p4-c11-r1',1,:digest,:fingerprint,'record_expense',"
            "'financial_transaction',:result_id,NULL,:now,:now)"
        ),
        {
            "id": values["finance_receipt"],
            "digest": "a" * 64,
            "fingerprint": "b" * 64,
            "result_id": values["transaction"],
            "now": now,
        },
    )
    connection.execute(
        text(
            "INSERT INTO financial_transaction "
            "(id,kind,status,occurred_at,currency,related_transaction_id,relation_kind,"
            "command_receipt_id,created_at) VALUES "
            "(:id,'expense','posted',:now,'CNY',NULL,NULL,:receipt,:now)"
        ),
        {"id": values["transaction"], "receipt": values["finance_receipt"], "now": now},
    )
    connection.execute(
        text(
            "INSERT INTO transaction_entry "
            "(id,transaction_id,line_no,entry_role,amount_minor,account_id,category_id) VALUES "
            "(:account_entry,:transaction,1,'account',-4321,:account,NULL),"
            "(:expense_entry,:transaction,2,'expense',4321,NULL,:category)"
        ),
        {
            "account_entry": values["account_entry"],
            "expense_entry": values["expense_entry"],
            "transaction": values["transaction"],
            "account": values["account"],
            "category": values["category"],
        },
    )

    connection.execute(
        text(
            "INSERT INTO agent_run "
            "(id,actor_id,conversation_id,source_system,source_event_digest,request_fingerprint,status,"
            "pause_reason,pending_action_id,answer,error_code,result_json,events_json,model_name,created_at,updated_at) "
            "VALUES (:id,:owner,:conversation,'api_test',:event_digest,:fingerprint,'paused',"
            "'needs_confirmation',NULL,NULL,NULL,NULL,NULL,'virtual-model',:now,:now)"
        ),
        {
            "id": values["run"],
            "owner": values["owner"],
            "conversation": values["conversation"],
            "event_digest": "c" * 64,
            "fingerprint": "d" * 64,
            "now": now,
        },
    )
    connection.execute(
        text(
            "INSERT INTO pending_action "
            "(id,run_id,actor_id,conversation_id,source_system,action_type,action_json,"
            "missing_fields_json,resource_versions_json,status,version_id,confirmation_code,"
            "approval_grant_id,final_result_json,created_at,expires_at,updated_at) VALUES "
            "(:id,:run,:owner,:conversation,'api_test','record_expense',:action_json,'[]','{}',"
            "'needs_confirmation',1,'R1HIST01',NULL,NULL,:now,:expires,:now)"
        ),
        {
            "id": values["pending"],
            "run": values["run"],
            "owner": values["owner"],
            "conversation": values["conversation"],
            "action_json": '{"amount":"43.21"}',
            "now": now,
            "expires": now + timedelta(days=1),
        },
    )
    connection.execute(
        text("UPDATE agent_run SET pending_action_id=:pending WHERE id=:run"),
        {"pending": values["pending"], "run": values["run"]},
    )

    connection.execute(
        text(
            "INSERT INTO command_receipt "
            "(id,source_system,key_version,key_digest,request_fingerprint,command_name,"
            "result_type,result_id,result_json,completed_at,created_at) VALUES "
            "(:id,'activity_import',1,:digest,:fingerprint,'preview_activity_import',"
            "'activity_import_batch',:result_id,NULL,:now,:now)"
        ),
        {
            "id": values["preview_receipt"],
            "digest": "e" * 64,
            "fingerprint": "f" * 64,
            "result_id": values["import_batch"],
            "now": now,
        },
    )
    connection.execute(
        text(
            "INSERT INTO activity_import_batch "
            "(id,owner_id,status,parser_version,source_label,content_key_version,content_digest,"
            "preview_receipt_id,commit_receipt_id,selection_fingerprint,version_id,created_at,committed_at) "
            "VALUES (:id,:owner,'previewed','activity-md-v1','virtual history',1,:digest,"
            ":receipt,NULL,NULL,1,:now,NULL)"
        ),
        {
            "id": values["import_batch"],
            "owner": values["owner"],
            "digest": "1" * 128,
            "receipt": values["preview_receipt"],
            "now": now,
        },
    )
    connection.execute(
        text(
            "INSERT INTO activity_import_candidate "
            "(id,batch_id,ordinal,source_heading,source_line_start,source_line_end,block_digest,"
            "name_normalized,currency,reference_minor,reference_min_minor,reference_max_minor,"
            "proposed_action,target_template_id,target_expected_version,issues_json,decision,"
            "result_template_id,result_template_version) VALUES "
            "(:id,:batch,1,'virtual history activity',1,2,:digest,'virtual history activity','CNY',"
            "2500,2500,2500,'create',NULL,NULL,'[]',NULL,NULL,NULL)"
        ),
        {
            "id": values["import_candidate"],
            "batch": values["import_batch"],
            "digest": "2" * 128,
        },
    )
    return values
