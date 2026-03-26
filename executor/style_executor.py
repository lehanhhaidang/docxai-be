from __future__ import annotations
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

_ALIGN = {
    "LEFT": WD_ALIGN_PARAGRAPH.LEFT,
    "RIGHT": WD_ALIGN_PARAGRAPH.RIGHT,
    "CENTER": WD_ALIGN_PARAGRAPH.CENTER,
    "JUSTIFY": WD_ALIGN_PARAGRAPH.JUSTIFY,
}


def ensure_paragraph_style(doc: Document, name: str):
    """Get or create a paragraph style by name."""
    try:
        return doc.styles[name]
    except KeyError:
        return doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)


def apply_remap_styles(doc: Document, remap: dict[str, dict]) -> None:
    """Apply font/size/bold/alignment overrides to named styles."""
    for style_name, props in remap.items():
        style = ensure_paragraph_style(doc, style_name)
        if props.get("font"):
            style.font.name = props["font"]
        if props.get("size") is not None:
            style.font.size = Pt(props["size"])
        if props.get("bold") is not None:
            style.font.bold = bool(props["bold"])
        align = (props.get("alignment") or "").upper()
        if align in _ALIGN:
            style.paragraph_format.alignment = _ALIGN[align]


def apply_body_font(doc: Document, font_spec: dict) -> None:
    """Apply default body font and size to the Normal style."""
    try:
        normal = doc.styles["Normal"]
    except KeyError:
        return
    if font_spec.get("body"):
        normal.font.name = font_spec["body"]
    if font_spec.get("size") is not None:
        normal.font.size = Pt(font_spec["size"])


def apply_margins(doc: Document, margins: dict) -> None:
    """Apply page margins (cm) to all sections."""
    for section in doc.sections:
        if margins.get("top") is not None:
            section.top_margin = Cm(margins["top"])
        if margins.get("bottom") is not None:
            section.bottom_margin = Cm(margins["bottom"])
        if margins.get("left") is not None:
            section.left_margin = Cm(margins["left"])
        if margins.get("right") is not None:
            section.right_margin = Cm(margins["right"])
