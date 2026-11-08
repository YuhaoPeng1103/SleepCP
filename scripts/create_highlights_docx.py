from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


HIGHLIGHTS = [
    "Marginal conformal coverage can hide patients below nominal.",
    "Subject-wise folds expose a 12.6-point worst-patient shortfall.",
    "Posterior smoothing cuts sets from 2.54 to 1.53 stages per epoch.",
    "Review workload falls from 76% to 16% of epochs on 30-s scoring.",
    "Per-patient adaptation lifts worst-patient coverage from 0.77 to 0.89.",
]


def set_font(run, name="Arial", size=None, bold=None, color=None):
    run.font.name = name
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), name)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), name)
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = RGBColor(*color)


def main():
    root = Path(__file__).resolve().parents[1]
    output = root / "paper" / "submission" / "highlights.docx"
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(18)
    run = title.add_run("Highlights")
    set_font(run, size=18, bold=True, color=(0, 0, 0))

    subtitle = doc.add_paragraph()
    subtitle.paragraph_format.space_after = Pt(14)
    run = subtitle.add_run(
        "Patient-adaptive conformal prediction sets for reliable "
        "single-channel EEG sleep staging"
    )
    set_font(run, size=11, color=(0, 0, 0))

    for text in HIGHLIGHTS:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.paragraph_format.left_indent = Inches(0.32)
        paragraph.paragraph_format.first_line_indent = Inches(-0.2)
        paragraph.paragraph_format.space_after = Pt(11)
        paragraph.paragraph_format.line_spacing = 1.15
        run = paragraph.add_run(text)
        set_font(run, size=11, color=(0, 0, 0))

    doc.save(output)
    print(output)


if __name__ == "__main__":
    main()
