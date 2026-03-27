from __future__ import annotations
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from lxml import etree

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


# ---------------------------------------------------------------------------
# Spacing helpers
# ---------------------------------------------------------------------------

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_W = "{%s}" % _W_NS


def _get_or_create(parent: etree._Element, tag: str) -> etree._Element:
    """Return first child with tag, or create+append it."""
    child = parent.find(tag)
    if child is None:
        child = etree.SubElement(parent, tag)
    return child


def _set_spacing_on_pPr(pPr: etree._Element, line_twips: int | None,
                         before_twips: int | None, after_twips: int | None) -> None:
    """Set w:spacing attributes on a w:pPr element."""
    spacing = _get_or_create(pPr, _W + "spacing")
    if line_twips is not None:
        spacing.set(_W + "line", str(line_twips))
        spacing.set(_W + "lineRule", "auto")
    if before_twips is not None:
        spacing.set(_W + "before", str(before_twips))
    if after_twips is not None:
        spacing.set(_W + "after", str(after_twips))


def apply_line_spacing(doc: Document, spacing_spec: dict) -> None:
    """
    Apply line and paragraph spacing to Normal + Heading 1/2/3 styles.

    spacing_spec format:
        { "line": 1.5, "before_pt": 6, "after_pt": 6 }
        line: 1.0 = single, 1.15, 1.5, 2.0
        before_pt / after_pt: spacing before/after paragraph in pt
    """
    line = spacing_spec.get("line")
    before_pt = spacing_spec.get("before_pt")
    after_pt = spacing_spec.get("after_pt")

    # Convert to twips (1 pt = 20 twips; lineRule="auto" base is 240 twips = single)
    line_twips = int(round(line * 240)) if line is not None else None
    before_twips = int(round(before_pt * 20)) if before_pt is not None else None
    after_twips = int(round(after_pt * 20)) if after_pt is not None else None

    target_styles = ["Normal", "Heading 1", "Heading 2", "Heading 3"]
    for style_name in target_styles:
        try:
            style = doc.styles[style_name]
        except KeyError:
            continue
        # Each style has an _element (CT_Style). We need w:pPr inside it.
        style_el = style.element
        pPr = _get_or_create(style_el, _W + "pPr")
        _set_spacing_on_pPr(pPr, line_twips, before_twips, after_twips)


def reset_direct_run_formatting(doc: Document) -> None:
    """
    Strip direct font name/size overrides from every run in the document body
    so that style-level font (applied via apply_body_font) takes effect.

    Removes w:rFonts and w:sz / w:szCs from each run's w:rPr.
    Preserves bold, italic, underline, color.
    """
    body = doc.element.body
    for r in body.iter(_W + "r"):
        rPr = r.find(_W + "rPr")
        if rPr is None:
            continue
        for tag in (_W + "rFonts", _W + "sz", _W + "szCs"):
            el = rPr.find(tag)
            if el is not None:
                rPr.remove(el)
    """
    Remove direct w:spacing overrides from every paragraph in the document body.

    Old .docx files may carry direct paragraph formatting that overrides style-level
    spacing. This function strips w:spacing from each paragraph's w:pPr so that
    style-level spacing (applied via apply_line_spacing) takes effect.
    """
    body = doc.element.body
    for p in body.iter(_W + "p"):
        pPr = p.find(_W + "pPr")
        if pPr is None:
            continue
        spacing = pPr.find(_W + "spacing")
        if spacing is not None:
            pPr.remove(spacing)
