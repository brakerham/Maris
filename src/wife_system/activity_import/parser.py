"""A bounded text grammar, not a Markdown renderer or a tool interpreter."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace

from .errors import ActivityImportError
from .schemas import ImportIssue, unsafe_unicode

PARSER_VERSION = "activity-md-v1"
MAX_MINOR = 999_999_999_999
_DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]{1,2})?\Z")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_DEEP_HEADING = re.compile(r"^#{3,}(?: |$)")
_RANGE = re.compile(r"^([^ –至]+) *[-–至] *([^ –至]+)$")
_RISKY_TEXT = re.compile(r"<[^>]*>|!?(?:\[[^\]]*\]\([^)]*\)|\[[^\]]*\]\[[^\]]*\])|(?:[a-zA-Z][a-zA-Z0-9+.-]*://)|(?:[A-Za-z]:[\\/])|(?:\\\\)|(?:^|\s)(?:/|\.{1,2}/|~/)[^\s]*|(?:^|\s)[^\s/\\]+[/\\][^\s/\\]+\.[A-Za-z0-9]{1,12}(?:$|\s)")
_CURRENCY = re.compile(r"(?:[A-Za-z]{3,}|美元|欧元|日元|港元|英镑|人民币|[¥￥$€£])")
_COMBINATION = re.compile(r"^(?:[-*+] |[0-9]+[.)] )?(?:活动组合|组合|成员|组合成员|包含活动)\s*[:：]")
_FREE_FIELD = re.compile(r"^(?:频率|日期|交通|交通费|备注|说明|时间)\s*[:：]")


def clean_name(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())


def normalize_name(value: str) -> str:
    return clean_name(value).casefold()


def normalize_markdown(value: str) -> str:
    if not isinstance(value, str):
        raise ActivityImportError("invalid_request")
    text = value.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    if unsafe_unicode(text):
        raise ActivityImportError("invalid_request")
    if len(text.encode("utf-8")) > 64 * 1024:
        raise ActivityImportError("import_text_too_large")
    return text


@dataclass(frozen=True)
class ParsedCandidate:
    ordinal: int
    source_heading: str
    source_line_start: int
    source_line_end: int
    name_normalized: str
    reference_minor: int | None
    reference_min_minor: int | None
    reference_max_minor: int | None
    issues: tuple[ImportIssue, ...]
    block_text: str
    duplicate_name: bool = False

    @property
    def unresolved(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


@dataclass(frozen=True)
class ParsedDocument:
    normalized_markdown: str
    candidates: tuple[ParsedCandidate, ...]


def _issue(code: str, line: int, *, error: bool = False, field: str = "content") -> ImportIssue:
    return ImportIssue(code=code, severity="error" if error else "warning", field=field, line=line)


def _minor(value: str) -> int:
    if not _DECIMAL.fullmatch(value):
        raise ActivityImportError("invalid_amount_precision")
    whole, _, fraction = value.partition(".")
    # Bound before int conversion, including very long leading-zero inputs.
    significant = whole.lstrip("0") or "0"
    if len(significant) > 10:
        raise ActivityImportError("amount_out_of_range")
    result = int(significant) * 100 + int(fraction.ljust(2, "0") or "0")
    if result > MAX_MINOR:
        raise ActivityImportError("amount_out_of_range")
    return result


def _amount_intent(line: str) -> bool:
    text = line.strip().removeprefix("- ")
    return text.startswith(("参考金额", "通常每次"))


def _amount(line: str) -> tuple[int | None, int, int]:
    if _CURRENCY.search(line):
        raise ActivityImportError("unsupported_currency")
    exact = re.fullmatch(r"- 参考金额：(.+) 元", line)
    if exact:
        value = _minor(exact[1])
        return value, value, value
    ranged = re.fullmatch(r"- 参考金额范围：(.+) 元", line)
    natural = re.fullmatch(r"- 通常每次 (.+) 元，只用于预测。", line)
    matched = ranged or natural
    if not matched:
        raise ActivityImportError("invalid_amount_precision")
    endpoints = _RANGE.fullmatch(matched[1])
    if not endpoints:
        raise ActivityImportError("invalid_amount_precision")
    low, high = _minor(endpoints[1]), _minor(endpoints[2])
    if low > high:
        raise ActivityImportError("amount_out_of_range")
    return None, low, high


def _candidate(ordinal: int, lines: list[str], start: int, end: int, preamble: list[ImportIssue]) -> ParsedCandidate:
    heading = clean_name(lines[start][3:])
    issues = list(preamble)
    if len(heading) > 120:
        raise ActivityImportError("invalid_markdown_structure")
    if (
        not heading
        or _RISKY_TEXT.search(heading)
        or any(char in heading for char in "<>/\\")
    ):
        heading = f"未解析活动 {ordinal}"
        issues.append(_issue("invalid_activity_name", start + 1, error=True, field="name"))
    content_lines = lines[start + 1 : end]
    if sum(bool(line.strip()) for line in content_lines) > 20:
        raise ActivityImportError("import_candidate_limit_exceeded")
    reference = low = high = None
    count = 0
    fence: str | None = None
    for index in range(start + 1, end):
        raw = lines[index]
        line = raw.rstrip(" \t")
        number = index + 1
        if not line.strip():
            continue
        marker = _FENCE.match(line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            issues.append(_issue("unsupported_free_text", number, error=_amount_intent(line)))
            continue
        if marker:
            fence = marker[1]
            issues.append(_issue("unsupported_free_text", number))
            continue
        if _DEEP_HEADING.match(line):
            issues.append(_issue("unsupported_markdown_structure", number, error=True, field="structure"))
            continue
        if _COMBINATION.match(line.strip()):
            issues.append(_issue("unsupported_activity_combination", number, error=True, field="structure"))
            continue
        if re.match(r"^[ \t]+(?:[-*+] |[0-9]+[.)] )", line):
            issues.append(_issue("unsupported_free_text", number))
            continue
        if line.startswith(("    ", "\t")) or _RISKY_TEXT.search(line):
            issues.append(_issue("unsupported_free_text", number, error=_amount_intent(line)))
            continue
        if _amount_intent(line):
            count += 1
            if count > 1:
                reference = low = high = None
                issues.append(_issue("duplicate_amount_field", number, error=True, field="reference_amount"))
                continue
            try:
                reference, low, high = _amount(line)
            except ActivityImportError as exc:
                issues.append(_issue(exc.code, number, error=True, field="reference_amount"))
            continue
        if line.startswith("- ") and re.match(r"[^:：]+[:：]", line[2:]) and not _FREE_FIELD.match(line[2:]):
            issues.append(_issue("unknown_import_field", number))
        else:
            issues.append(_issue("unsupported_free_text", number))
    return ParsedCandidate(
        ordinal, heading, start + 1, end, normalize_name(heading),
        reference, low, high, tuple(issues), "\n".join(lines[start:end]),
    )


def parse_markdown(value: str) -> ParsedDocument:
    text = normalize_markdown(value)
    # Only LF is a document separator: Unicode whitespace remains text data.
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if len(lines) > 2000:
        raise ActivityImportError("import_text_too_large")
    starts: list[int] = []
    preamble: list[ImportIssue] = []
    h1_count = 0
    fence: str | None = None
    for index, line in enumerate(lines):
        marker = _FENCE.match(line)
        if fence:
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence) and not marker[2].strip():
                fence = None
            if not starts and line.strip():
                preamble.append(_issue("unsupported_free_text", index + 1))
            continue
        if marker:
            fence = marker[1]
            if not starts:
                preamble.append(_issue("unsupported_free_text", index + 1))
            continue
        if line.startswith("# "):
            h1_count += 1
            if h1_count > 1 or starts or len(clean_name(line[2:])) > 120:
                raise ActivityImportError("invalid_markdown_structure")
        elif line.startswith("## "):
            starts.append(index)
            if len(starts) > 50:
                raise ActivityImportError("import_candidate_limit_exceeded")
        elif not starts and line.strip():
            preamble.append(_issue("unsupported_free_text", index + 1))
    if not starts:
        raise ActivityImportError("invalid_markdown_structure")
    candidates = [
        _candidate(ordinal + 1, lines, start, starts[ordinal + 1] if ordinal + 1 < len(starts) else len(lines), preamble if ordinal == 0 else [])
        for ordinal, start in enumerate(starts)
    ]
    counts = Counter(candidate.name_normalized for candidate in candidates)
    return ParsedDocument(text, tuple(replace(candidate, duplicate_name=counts[candidate.name_normalized] > 1) for candidate in candidates))
