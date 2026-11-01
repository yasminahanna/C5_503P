"""Export the Markdown deliverables to PDF and Word.

Optional authoring dependencies: reportlab and python-docx. They are not needed
to run the submitted MCP project, whose deliverables are already exported.
"""

from html import escape
from pathlib import Path
import re
import textwrap

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables"
NAVY = "18334B"
TEAL = "087F8C"


def blocks(text):
    paragraph = []
    code = None
    for line in text.splitlines() + [""]:
        if line.startswith("```"):
            if paragraph:
                yield "p", " ".join(paragraph)
                paragraph = []
            if code is None:
                code = []
            else:
                yield "code", "\n".join(code)
                code = None
            continue
        if code is not None:
            code.append(line)
            continue
        if line.startswith("#") or not line.strip() or re.match(r"^(?:- |\d+\. )", line):
            if paragraph:
                yield "p", " ".join(paragraph)
                paragraph = []
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                yield f"h{level}", line[level:].strip()
            elif line.strip():
                yield "item", line.strip()
        else:
            paragraph.append(line.strip())


def pdf_markup(text):
    text = escape(text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2" color="#087F8C">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    return text


def plain(text):
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)
    return text.replace("**", "").replace("`", "")


def export_pdf(sources, destination, title):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCustom", fontName="Helvetica-Bold", fontSize=23,
                              leading=28, textColor=colors.HexColor("#" + NAVY), spaceAfter=16))
    styles.add(ParagraphStyle(name="HeadingCustom", fontName="Helvetica-Bold", fontSize=13,
                              leading=17, textColor=colors.HexColor("#" + TEAL), spaceBefore=15,
                              spaceAfter=8, keepWithNext=True))
    styles.add(ParagraphStyle(name="BodyCustom", fontName="Helvetica", fontSize=10.3,
                              leading=14.0 if len(sources) > 1 else 15.2,
                              spaceAfter=8 if len(sources) > 1 else 9, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name="ItemCustom", parent=styles["BodyCustom"], leftIndent=9,
                              firstLineIndent=-9, spaceAfter=6))
    styles.add(ParagraphStyle(name="CodeCustom", fontName="Courier", fontSize=8.2,
                              leading=11.4, backColor=colors.HexColor("#F0F4F6"),
                              borderPadding=8, spaceBefore=4, spaceAfter=12))
    story = []
    for index, source in enumerate(sources):
        if index:
            story.append(PageBreak())
        for kind, text in blocks(source.read_text(encoding="utf-8")):
            if kind == "h1":
                story.append(Paragraph(pdf_markup(text), styles["TitleCustom"]))
                story.append(HRFlowable(width="100%", color=colors.HexColor("#" + TEAL), thickness=2, spaceAfter=12))
            elif kind.startswith("h"):
                story.append(Paragraph(pdf_markup(text), styles["HeadingCustom"]))
            elif kind == "code":
                wrapped = "\n".join(textwrap.fill(line, width=86, subsequent_indent="  ") for line in text.splitlines())
                story.append(Preformatted(wrapped, styles["CodeCustom"]))
            else:
                story.append(Paragraph(pdf_markup(text), styles["ItemCustom" if kind == "item" else "BodyCustom"]))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D6E0E5"))
        canvas.line(48, 37, A4[0] - 48, 37)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#617382"))
        canvas.drawString(48, 24, "Yasmina Hanna | C5 - Agent Tools | " + title)
        canvas.drawRightString(A4[0] - 48, 24, str(doc.page))
        canvas.restoreState()

    # Keep each timed section together so narration does not continue onto a new page.
    protected = []
    group = []
    for item in story:
        if isinstance(item, PageBreak):
            if group:
                protected.append(KeepTogether(group))
                group = []
            protected.append(item)
        elif isinstance(item, Paragraph) and item.style.name == "HeadingCustom":
            if group:
                protected.append(KeepTogether(group))
            group = [item]
        else:
            group.append(item)
    if group:
        protected.append(KeepTogether(group))
    doc = SimpleDocTemplate(str(destination), pagesize=A4, rightMargin=48, leftMargin=48,
                            topMargin=44, bottomMargin=52, title=title, author="Yasmina Hanna")
    doc.build(protected, onFirstPage=footer, onLaterPages=footer)


def export_word(source, destination):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = section.bottom_margin = Inches(0.65)
    section.left_margin = section.right_margin = Inches(0.75)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.paragraph_format.space_after = Pt(7)
    for heading in ("Title", "Heading 1", "Heading 2"):
        doc.styles[heading].font.color.rgb = RGBColor.from_string(NAVY if heading == "Title" else TEAL)
    for kind, text in blocks(source.read_text(encoding="utf-8")):
        if kind.startswith("h"):
            doc.add_heading(plain(text), level=0 if kind == "h1" else min(int(kind[1:]) - 1, 3))
        elif kind == "code":
            p = doc.add_paragraph()
            run = p.add_run(text)
            run.font.name = "Consolas"
            run.font.size = Pt(9)
        else:
            doc.add_paragraph(plain(text))
    section.footer.paragraphs[0].text = "Yasmina Hanna | C5 - Agent Tools | Video speaker notes"
    doc.core_properties.author = "Yasmina Hanna"
    doc.core_properties.title = "Campus Library MCP Toolkit - Video Speaker Notes"
    doc.save(destination)


def main():
    OUTPUT.mkdir(exist_ok=True)
    export_pdf([ROOT / "docs/written_summary.md", ROOT / "docs/reflection.md"],
               OUTPUT / "C5_Written_Submission.pdf", "Reading summary and reflection")
    export_pdf([ROOT / "docs/speaker_notes.md"], OUTPUT / "C5_Speaker_Notes.pdf", "Video speaker notes")
    export_word(ROOT / "docs/speaker_notes.md", OUTPUT / "C5_Speaker_Notes.docx")
    for file in OUTPUT.iterdir():
        print(file.name, file.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
