"""Structural checks for the four generated teaching PDFs."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    "p0-agent-http-wechat-teaching.pdf": ("第一册：P0 最小 Agent、HTTP 与微信桥接", "AgentRunner"),
    "p1-finance-data-foundation-teaching.pdf": ("第二册：P1 财务数据底座", "FinanceService"),
    "p2-finance-agent-workflow-teaching.pdf": ("第三册：P2 财务 Agent 工作流", "pending_action"),
    "p3-activity-import-teaching.pdf": ("第四册：P3 Markdown 活动导入", "ActivityImportService"),
}


def main() -> None:
    for name, required in EXPECTED.items():
        path = ROOT / "output" / "pdf" / name
        reader = PdfReader(path)
        if len(reader.pages) < 6:
            raise AssertionError(f"{name}: implausibly short")
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        for token in required:
            if token not in text:
                raise AssertionError(f"{name}: missing {token!r}")
        if len(text.strip()) < 2500:
            raise AssertionError(f"{name}: extracted text too short")
        with pdfplumber.open(path) as pdf:
            if len(pdf.pages) != len(reader.pages):
                raise AssertionError(f"{name}: parser page count disagreement")
            empty = [index + 1 for index, page in enumerate(pdf.pages) if not (page.extract_text() or "").strip()]
            if empty:
                raise AssertionError(f"{name}: empty pages {empty}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        print(f"{name}\tpages={len(reader.pages)}\ttext={len(text)}\tsha256={digest}")


if __name__ == "__main__":
    main()
