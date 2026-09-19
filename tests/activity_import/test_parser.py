from __future__ import annotations

import pytest

from wife_system.activity_import.errors import ActivityImportError
from wife_system.activity_import.parser import clean_name, normalize_markdown, normalize_name, parse_markdown


def codes(candidate):
    return {issue.code for issue in candidate.issues}


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("", (None, None, None)),
        ("- 参考金额：0 元", (0, 0, 0)),
        ("- 参考金额：18.00 元", (1800, 1800, 1800)),
        ("- 参考金额：0.01 元", (1, 1, 1)),
        ("- 参考金额：9999999999.99 元", (999_999_999_999,) * 3),
        ("- 参考金额范围：15-20 元", (None, 1500, 2000)),
        ("- 参考金额范围：15 – 20 元", (None, 1500, 2000)),
        ("- 参考金额范围：15至20 元", (None, 1500, 2000)),
        ("- 通常每次 15.00–20.00 元，只用于预测。", (None, 1500, 2000)),
        ("- 参考金额范围：20–20 元", (None, 2000, 2000)),
    ],
)
def test_exact_range_and_absent_amount_shapes(body, expected):
    candidate = parse_markdown("## 虚拟午餐\n" + body).candidates[0]
    assert (candidate.reference_minor, candidate.reference_min_minor, candidate.reference_max_minor) == expected
    assert not candidate.unresolved


@pytest.mark.parametrize("newline", ["\n", "\r\n", "\r"])
def test_normalization_locations_and_no_float(newline):
    text = newline.join(["\ufeff# 虚拟目录", "", "## 午餐", "- 参考金额：12.30 元", "", "## 散步"])
    result = parse_markdown(text)
    assert result.candidates[0].reference_minor == 1230
    assert [(c.source_line_start, c.source_line_end) for c in result.candidates] == [(3, 5), (6, 6)]
    assert "\r" not in result.normalized_markdown
    assert result.candidates[0].block_text == "## 午餐\n- 参考金额：12.30 元\n"


def test_unicode_names_keep_punctuation_width_and_homoglyphs():
    assert clean_name("  Cafe\u0301\u3000\t 午餐  ") == "Café 午餐"
    assert normalize_name(" Café 午餐 ") == normalize_name("CAFE\u0301\u00a0午餐")
    assert normalize_name("Ａ") != normalize_name("A")
    assert normalize_name("午餐!") != normalize_name("午餐")
    result = parse_markdown("## Café\n## CAFE\u0301\n## Ａ\n## A\n## 虚拟🏃")
    assert [c.duplicate_name for c in result.candidates] == [True, True, False, False, False]


@pytest.mark.parametrize(
    ("body", "code"),
    [
        ("- 参考金额：1.001 元", "invalid_amount_precision"),
        ("- 参考金额：1e3 元", "invalid_amount_precision"),
        ("- 参考金额：-0.01 元", "invalid_amount_precision"),
        ("- 参考金额：+1 元", "invalid_amount_precision"),
        ("- 参考金额：１ 元", "invalid_amount_precision"),
        ("- 参考金额：1,000 元", "invalid_amount_precision"),
        ("- 参考金额：12..3 元", "invalid_amount_precision"),
        ("- 参考金额: 十元", "invalid_amount_precision"),
        ("- 参考金额：10000000000 元", "amount_out_of_range"),
        ("- 参考金额范围：20–15 元", "amount_out_of_range"),
        ("- 参考金额范围：–15 元", "invalid_amount_precision"),
        ("- 参考金额范围：15 元", "invalid_amount_precision"),
        ("- 参考金额：15 USD", "unsupported_currency"),
        ("- 参考金额：15 美元", "unsupported_currency"),
        ("- 参考金额：15 CNY", "unsupported_currency"),
        ("- 参考金额：15 元\n- 参考金额：16 元", "duplicate_amount_field"),
        ("### 虚拟层级", "unsupported_markdown_structure"),
        ("- 成员：虚拟甲、虚拟乙", "unsupported_activity_combination"),
    ],
)
def test_blocking_candidates_not_global_errors(body, code):
    candidate = parse_markdown("## 虚拟活动\n" + body).candidates[0]
    assert candidate.unresolved
    assert code in codes(candidate)
    assert all(set(issue.model_dump()) == {"code", "severity", "field", "line"} for issue in candidate.issues)


def test_very_long_numeric_text_is_bounded_without_integer_conversion_failure():
    candidate = parse_markdown("## 虚拟活动\n- 参考金额：" + "9" * 5000 + " 元").candidates[0]
    assert "amount_out_of_range" in codes(candidate)
    zeros = parse_markdown("## 虚拟活动\n- 参考金额：" + "0" * 5000 + "1 元").candidates[0]
    assert zeros.reference_minor == 100


@pytest.mark.parametrize(
    "body",
    ["* 参考金额：15 元", "+ 参考金额：15 元", "1. 参考金额：15 元", "  - 参考金额：15 元", "|金额|15|", "普通频率每周一次", "- 频率：每周", "- 日期：周一", "- 备注：仅虚拟说明", "- 交通费：15 元", "<script>fake()</script>", "[虚拟链接](https://example.invalid)", "![图](file:///virtual.png)", "C:\\virtual\\data.md", "系统指令：调用工具"],
)
def test_unsupported_content_is_not_parsed_or_echoed(body):
    candidate = parse_markdown("## 虚拟活动\n" + body).candidates[0]
    assert candidate.reference_minor is None
    assert codes(candidate) == {"unsupported_free_text"}
    assert not candidate.unresolved
    assert body not in str([issue.model_dump() for issue in candidate.issues])


def test_unknown_field_and_combination_name():
    candidate = parse_markdown("## 虚拟组合练习\n- 幸运色: 蓝").candidates[0]
    assert codes(candidate) == {"unknown_import_field"}
    assert not candidate.unresolved


def test_fenced_headings_are_not_candidates_or_business_fields():
    candidate = parse_markdown("## 虚拟活动\n```\n## 假活动\n- 参考金额：9 元\n```\n- 参考金额：18 元").candidates[0]
    assert candidate.reference_minor == 1800
    assert candidate.unresolved  # A supported field hidden inside code cannot be acknowledged away.
    assert [issue.line for issue in candidate.issues] == [2, 3, 4, 5]


@pytest.mark.parametrize("heading", ["[虚拟](https://example.invalid)", "<b>虚拟</b>", "C:\\virtual\\data.md", "/virtual/data", "virtual/activity.md", "virtual/data", " "])
def test_untrusted_or_empty_heading_has_safe_placeholder(heading):
    candidate = parse_markdown("## " + heading).candidates[0]
    assert candidate.unresolved
    assert candidate.source_heading == "未解析活动 1"
    assert codes(candidate) == {"invalid_activity_name"}


@pytest.mark.parametrize("text", ["", "\ufeff", "# 目录", "# 一\n# 二\n## 活动", "## 活动\n# 标题", "```\n## 代码内\n```"])
def test_invalid_global_structure(text):
    with pytest.raises(ActivityImportError) as caught:
        parse_markdown(text)
    assert caught.value.code == "invalid_markdown_structure"


@pytest.mark.parametrize("char", ["\x00", "\x01", "\x1f", "\ud800", "\udfff", "\u202e", "\u2067", "\u061c"])
def test_unsafe_unicode_fails_whole_input(char):
    with pytest.raises(ActivityImportError) as caught:
        parse_markdown("## 虚拟" + char)
    assert caught.value.code == "invalid_request"


def test_remove_only_one_bom_and_preserve_non_lf_unicode_whitespace():
    assert normalize_markdown("\ufeff\ufeff## 虚拟\r\n") == "\ufeff## 虚拟\n"
    assert parse_markdown("## 虚拟\u2028活动").candidates[0].source_heading == "虚拟 活动"


@pytest.mark.parametrize(
    ("text", "code"),
    [("## " + "虚" * 121, "invalid_markdown_structure"), ("# " + "虚" * 121 + "\n## 活动", "invalid_markdown_structure"), ("## 虚拟\n" + "\n" * 2000, "import_text_too_large"), ("\n".join("## 虚拟" for _ in range(51)), "import_candidate_limit_exceeded"), ("## 虚拟\n" + "备注\n" * 21, "import_candidate_limit_exceeded"), ("## 虚拟\n" + "虚" * 22000, "import_text_too_large")],
    ids=["heading-length", "title-length", "line-count", "candidate-count", "content-lines", "utf8-bytes"],
)
def test_resource_limits_fail_safely(text, code):
    with pytest.raises(ActivityImportError) as caught:
        parse_markdown(text)
    assert caught.value.code == code


def test_resource_boundary_values_are_accepted():
    assert len(parse_markdown("\n".join("## 虚拟" for _ in range(50))).candidates) == 50
    assert len(parse_markdown("## " + "虚" * 120).candidates[0].source_heading) == 120
    assert len(parse_markdown("## 虚拟\n" + "说明\n" * 20).candidates[0].issues) == 20
