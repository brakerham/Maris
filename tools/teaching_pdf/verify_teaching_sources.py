"""Verify local code/document links and line anchors in the teaching Markdown."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = sorted((ROOT / "docs" / "teaching").glob("*.md"))
LINK = re.compile(r"\[[^]]+]\(([^)]+)\)")
LINE = re.compile(r"#L(\d+)(?:-L(\d+))?$")


def main() -> None:
    checked = 0
    for source in DOCS:
        text = source.read_text(encoding="utf-8")
        for raw in LINK.findall(text):
            target_text = raw
            match = LINE.search(target_text)
            if match:
                target_text = target_text[: match.start()]
            target = (source.parent / target_text).resolve()
            if not target.exists():
                raise AssertionError(f"{source.name}: missing {raw}")
            if match:
                count = len(target.read_text(encoding="utf-8").splitlines())
                start = int(match.group(1))
                end = int(match.group(2) or start)
                if not (1 <= start <= end <= count):
                    raise AssertionError(f"{source.name}: bad anchor {raw}; file has {count} lines")
            checked += 1
    print(f"checked {checked} local links across {len(DOCS)} Markdown files")


if __name__ == "__main__":
    main()
