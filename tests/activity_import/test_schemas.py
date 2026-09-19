from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from wife_system.activity_import.schemas import CommitRequest, Decision, ImportIssue, PreviewRequest


def valid_commit():
    return {
        "confirmed": True,
        "batch_version": 1,
        "content_digest": "hmac-sha256:v1:" + "a" * 64,
        "decisions": [{"candidate_id": str(uuid.uuid4()), "decision": "accept", "expected_action": "create", "expected_template_version": None, "acknowledged_warning_codes": []}],
    }


@pytest.mark.parametrize("value", [False, 1, 0, "true", "True", None])
def test_confirmation_requires_literal_boolean_true(value):
    data = valid_commit()
    data["confirmed"] = value
    with pytest.raises(ValidationError):
        CommitRequest.model_validate(data)


@pytest.mark.parametrize("value", [True, 1.0, "1", 0, -1])
def test_versions_are_strict_positive_integers(value):
    data = valid_commit()
    data["batch_version"] = value
    with pytest.raises(ValidationError):
        CommitRequest.model_validate(data)
    data = valid_commit()
    data["decisions"][0]["expected_template_version"] = value
    with pytest.raises(ValidationError):
        CommitRequest.model_validate(data)


@pytest.mark.parametrize("field", ["owner_id", "source_system", "name", "reference_minor", "target_template_id"])
def test_clients_cannot_self_declare_identity_or_business_fields(field):
    data = valid_commit()
    data["decisions"][0][field] = "virtual"
    with pytest.raises(ValidationError):
        CommitRequest.model_validate(data)
    with pytest.raises(ValidationError):
        PreviewRequest.model_validate({"markdown": "## 虚拟", field: "virtual"})


@pytest.mark.parametrize("missing", ["expected_template_version", "acknowledged_warning_codes", "decision", "expected_action", "candidate_id"])
def test_all_decision_fields_are_required(missing):
    data = valid_commit()
    del data["decisions"][0][missing]
    with pytest.raises(ValidationError):
        CommitRequest.model_validate(data)


def test_valid_schema_and_warning_duplicate_preserved_for_service_error():
    data = valid_commit()
    data["decisions"][0]["acknowledged_warning_codes"] = ["unsupported_free_text"] * 2
    result = CommitRequest.model_validate(data)
    assert result.decisions[0].acknowledged_warning_codes == ["unsupported_free_text"] * 2


@pytest.mark.parametrize(("label", "expected"), [(None, None), ("", ""), ("D:\\virtual\\activities.md", "activities.md"), ("/virtual/activities.md", "activities.md"), ("\\\\virtual\\share\\activities.md", "activities.md"), (" CAFE\u0301.md ", "CAFÉ.md")])
def test_source_label_is_basename_only(label, expected):
    assert PreviewRequest(markdown="## 虚拟", source_label=label).source_label == expected


@pytest.mark.parametrize("label", ["x" * 121, "https://example.invalid/fake.md", "<script>x</script>", "[x](fake)", "fake\u202e.md", "fake\x00.md", "fake\n.md", ".."])
def test_source_label_rejects_unsafe_content(label):
    with pytest.raises(ValidationError):
        PreviewRequest(markdown="## 虚拟", source_label=label)


@pytest.mark.parametrize("value", [1, True, 1.2, None, {"text": "virtual"}, ["virtual"]])
def test_markdown_is_strict_string(value):
    with pytest.raises(ValidationError):
        PreviewRequest(markdown=value)


def test_issues_allow_no_echo_payload_fields():
    with pytest.raises(ValidationError):
        ImportIssue(code="unsupported_free_text", severity="warning", field="content", line=1, input="virtual secret")
