"""Build the four P0-P3 Chinese teaching PDFs from their Markdown sources."""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output" / "pdf"
FONT_REGULAR = Path(r"C:\Windows\Fonts\Deng.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\Dengb.ttf")

BOOKS = (
    ("P0", "最小 Agent、HTTP 与微信桥接", ROOT / "docs/teaching/p0-agent-http-wechat.md", OUTPUT / "p0-agent-http-wechat-teaching.pdf"),
    ("P1", "财务数据底座", ROOT / "docs/teaching/p1-finance-data-foundation.md", OUTPUT / "p1-finance-data-foundation-teaching.pdf"),
    ("P2", "财务 Agent 工作流", ROOT / "docs/teaching/p2-finance-agent-workflow.md", OUTPUT / "p2-finance-agent-workflow-teaching.pdf"),
    ("P3", "Markdown 活动导入", ROOT / "docs/teaching/p3-activity-import.md", OUTPUT / "p3-activity-import-teaching.pdf"),
)

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#0B7A75")
PALE = colors.HexColor("#EAF5F4")
INK = colors.HexColor("#202A33")
MUTED = colors.HexColor("#60717F")
CODE_BG = colors.HexColor("#F3F5F7")
GRID = colors.HexColor("#CAD5DD")


def register_fonts() -> None:
    if not FONT_REGULAR.exists() or not FONT_BOLD.exists():
        raise FileNotFoundError("DengXian Chinese fonts are required")
    pdfmetrics.registerFont(TTFont("TeachingCN", str(FONT_REGULAR)))
    pdfmetrics.registerFont(TTFont("TeachingCN-Bold", str(FONT_BOLD)))
    pdfmetrics.registerFontFamily(
        "TeachingCN",
        normal="TeachingCN",
        bold="TeachingCN-Bold",
        italic="TeachingCN",
        boldItalic="TeachingCN-Bold",
    )


def inline(text: str) -> str:
    text = re.sub(r"\[([^]]+)]\([^)]+\)", r"\1", text)
    safe = html.escape(text, quote=False)
    safe = re.sub(r"`([^`]+)`", r'<font name="TeachingCN-Bold" color="#0B6B66">\1</font>', safe)
    safe = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", safe)
    return safe


def styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "body": ParagraphStyle(
            "BodyCN", parent=base["BodyText"], fontName="TeachingCN", fontSize=9.6,
            leading=15.5, textColor=INK, spaceAfter=5.5, wordWrap="CJK",
        ),
        "h1": ParagraphStyle(
            "Heading1CN", parent=base["Heading1"], fontName="TeachingCN-Bold", fontSize=20,
            leading=28, textColor=NAVY, spaceBefore=4, spaceAfter=12, wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "Heading2CN", parent=base["Heading2"], fontName="TeachingCN-Bold", fontSize=15,
            leading=21, textColor=NAVY, spaceBefore=2, spaceAfter=9, wordWrap="CJK",
        ),
        "h3": ParagraphStyle(
            "Heading3CN", parent=base["Heading3"], fontName="TeachingCN-Bold", fontSize=11.5,
            leading=17, textColor=TEAL, spaceBefore=7, spaceAfter=5, wordWrap="CJK",
        ),
        "bullet": ParagraphStyle(
            "BulletCN", parent=base["BodyText"], fontName="TeachingCN", fontSize=9.3,
            leading=14.5, leftIndent=15, firstLineIndent=-8, bulletIndent=5,
            textColor=INK, spaceAfter=3.5, wordWrap="CJK",
        ),
        "quote": ParagraphStyle(
            "QuoteCN", parent=base["BodyText"], fontName="TeachingCN", fontSize=9.2,
            leading=14.5, leftIndent=10, rightIndent=8, borderColor=TEAL, borderWidth=1.2,
            borderPadding=(6, 8, 6, 9), backColor=PALE, textColor=NAVY, spaceAfter=8,
            wordWrap="CJK",
        ),
        "code": ParagraphStyle(
            "CodeCN", parent=base["Code"], fontName="TeachingCN", fontSize=7.8,
            leading=11.3, leftIndent=7, rightIndent=7, borderColor=GRID, borderWidth=0.6,
            borderPadding=7, backColor=CODE_BG, textColor=colors.HexColor("#263746"),
            spaceBefore=3, spaceAfter=8, wordWrap="CJK",
        ),
        "caption": ParagraphStyle(
            "CaptionCN", parent=base["BodyText"], fontName="TeachingCN", fontSize=8,
            leading=11, textColor=MUTED, alignment=TA_CENTER, spaceAfter=6,
        ),
        "toc_title": ParagraphStyle(
            "TOCTitleCN", parent=base["Heading1"], fontName="TeachingCN-Bold", fontSize=20,
            leading=27, textColor=NAVY, spaceAfter=16,
        ),
        "cover_kicker": ParagraphStyle(
            "CoverKicker", parent=base["BodyText"], fontName="TeachingCN-Bold", fontSize=12,
            leading=16, textColor=TEAL, alignment=TA_CENTER, spaceAfter=12,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="TeachingCN-Bold", fontSize=26,
            leading=36, textColor=NAVY, alignment=TA_CENTER, wordWrap="CJK", spaceAfter=16,
        ),
        "cover_meta": ParagraphStyle(
            "CoverMeta", parent=base["BodyText"], fontName="TeachingCN", fontSize=10,
            leading=16, textColor=MUTED, alignment=TA_CENTER,
        ),
    }


class TeachingDocTemplate(BaseDocTemplate):
    def __init__(self, filename: str, *, book_code: str, book_title: str) -> None:
        self.book_code = book_code
        self.book_title = book_title
        self._bookmark_index = 0
        super().__init__(
            filename, pagesize=A4, leftMargin=20 * mm, rightMargin=20 * mm,
            topMargin=22 * mm, bottomMargin=18 * mm,
            title=f"{book_code} {book_title}", author="wife-system 技术顾问",
        )
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="content")
        self.addPageTemplates(PageTemplate(id="main", frames=[frame], onPage=self._decorate))

    def beforeDocument(self) -> None:
        # multiBuild runs more than one pass for the TOC; bookmark keys must be
        # identical on every pass or the index can never converge.
        self._bookmark_index = 0

    def _decorate(self, canvas, doc) -> None:
        page = canvas.getPageNumber()
        canvas.saveState()
        if page > 1:
            canvas.setStrokeColor(GRID)
            canvas.line(20 * mm, A4[1] - 15 * mm, A4[0] - 20 * mm, A4[1] - 15 * mm)
            canvas.setFont("TeachingCN", 7.5)
            canvas.setFillColor(MUTED)
            canvas.drawString(20 * mm, A4[1] - 11 * mm, f"{self.book_code} · {self.book_title}")
            canvas.drawRightString(A4[0] - 20 * mm, 10 * mm, f"{page}")
        canvas.restoreState()

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        name = flowable.style.name
        if name not in {"Heading1CN", "Heading2CN", "Heading3CN"}:
            return
        level = {"Heading1CN": 0, "Heading2CN": 0, "Heading3CN": 1}[name]
        title = flowable.getPlainText()
        key = f"h-{self._bookmark_index}"
        self._bookmark_index += 1
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(title, key, level=level, closed=False)
        self.notify("TOCEntry", (level, title, self.page, key))


def markdown_table(rows: list[list[str]], st: dict[str, ParagraphStyle], width: float):
    columns = max(len(row) for row in rows)
    normalized = [row + [""] * (columns - len(row)) for row in rows]
    if len(normalized) > 1 and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in normalized[1]):
        normalized.pop(1)
    head = ParagraphStyle(
        "TableHeadCN", parent=st["body"], fontName="TeachingCN-Bold",
        fontSize=7.4, leading=10.5, textColor=colors.white,
    )
    data = [
        [Paragraph(inline(cell.strip()), head if row_index == 0 else st["body"]) for cell in row]
        for row_index, row in enumerate(normalized)
    ]
    if columns == 2:
        col_widths = [width * 0.31, width * 0.69]
    elif columns == 3:
        col_widths = [width * 0.22, width * 0.28, width * 0.50]
    else:
        col_widths = [width / columns] * columns
    table = LongTable(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "TeachingCN-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "TeachingCN"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.4),
        ("LEADING", (0, 0), (-1, -1), 10.5),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F9FA")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def parse_markdown(path: Path, st: dict[str, ParagraphStyle], width: float):
    lines = path.read_text(encoding="utf-8").splitlines()
    story = []
    paragraph: list[str] = []
    code: list[str] = []
    in_code = False
    first_h1 = True
    first_h2 = True

    def flush_paragraph() -> None:
        if paragraph:
            story.append(Paragraph(inline(" ".join(part.strip() for part in paragraph)), st["body"]))
            paragraph.clear()

    index = 0
    while index < len(lines):
        line = lines[index]
        if line.startswith("```"):
            flush_paragraph()
            if in_code:
                story.append(Preformatted("\n".join(code), st["code"], maxLineLength=94))
                code.clear()
                in_code = False
            else:
                in_code = True
            index += 1
            continue
        if in_code:
            code.append(line)
            index += 1
            continue
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            rows = []
            while index < len(lines) and lines[index].startswith("|") and lines[index].endswith("|"):
                rows.append([cell.strip() for cell in lines[index].strip("|").split("|")])
                index += 1
            story.extend([markdown_table(rows, st, width), Spacer(1, 7)])
            continue
        if not line.strip():
            flush_paragraph()
            index += 1
            continue
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            title = heading.group(2)
            if level == 1:
                if first_h1:
                    first_h1 = False
                else:
                    story.append(PageBreak())
                story.append(Paragraph(inline(title), st["h1"]))
            elif level == 2:
                if first_h2:
                    first_h2 = False
                else:
                    story.append(PageBreak())
                story.append(Paragraph(inline(title), st["h2"]))
            else:
                story.append(Paragraph(inline(title), st["h3"]))
            index += 1
            continue
        if line.startswith("> "):
            flush_paragraph()
            story.append(Paragraph(inline(line[2:]), st["quote"]))
            index += 1
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        ordered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if bullet or ordered:
            flush_paragraph()
            if bullet:
                marker, value = "•", bullet.group(1)
            else:
                marker, value = f"{ordered.group(1)}.", ordered.group(2)
            story.append(Paragraph(inline(value), st["bullet"], bulletText=marker))
            index += 1
            continue
        paragraph.append(line)
        index += 1
    flush_paragraph()
    if code:
        story.append(Preformatted("\n".join(code), st["code"], maxLineLength=94))
    return story


def cover(book_code: str, book_title: str, st: dict[str, ParagraphStyle]):
    card = Table(
        [[Paragraph("wife-system · 阶段 0～3 实现后教材", st["cover_kicker"])],
         [Paragraph(f"{book_code}<br/>{html.escape(book_title)}", st["cover_title"])],
         [Paragraph("固定代码基线 6e89762<br/>中文学习版 · 虚拟数据示例", st["cover_meta"])]],
        colWidths=[150 * mm], rowHeights=[25 * mm, 72 * mm, 30 * mm], hAlign="CENTER",
    )
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("BOX", (0, 0), (-1, -1), 1.2, TEAL),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    return [Spacer(1, 34 * mm), card, Spacer(1, 18 * mm), Paragraph(
        "从实际代码、数据流和测试证据出发；每册可独立阅读。", st["cover_meta"]
    ), PageBreak()]


def build(book_code: str, book_title: str, source: Path, target: Path) -> None:
    st = styles()
    doc = TeachingDocTemplate(str(target), book_code=book_code, book_title=book_title)
    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC0", fontName="TeachingCN-Bold", fontSize=10, leading=16, leftIndent=0, textColor=NAVY),
        ParagraphStyle("TOC1", fontName="TeachingCN", fontSize=8.5, leading=13, leftIndent=12, textColor=INK),
    ]
    story = cover(book_code, book_title, st)
    story.extend([Paragraph("目录", st["toc_title"]), toc, PageBreak()])
    story.extend(parse_markdown(source, st, doc.width))
    doc.multiBuild(story)


def main() -> None:
    register_fonts()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for book_code, book_title, source, target in BOOKS:
        build(book_code, book_title, source, target)
        print(f"built {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
