from __future__ import annotations
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

_ALIGN_VAL = {
    "LEFT": "left",
    "RIGHT": "right",
    "CENTER": "center",
    "JUSTIFY": "both",
}


def iter_body_items(doc: Document) -> list[dict]:
    """
    Return ordered list of body items as dicts:
      { "kind": "paragraph"|"table", "element": lxml_element }
    """
    items = []
    for child in doc.element.body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if tag == "p":
            items.append({"kind": "paragraph", "element": child})
        elif tag == "tbl":
            items.append({"kind": "table", "element": child})
    return items


def apply_heading_level(doc: Document, para_el, level: int) -> None:
    """Restyle a paragraph element as Heading <level>."""
    style_name = f"Heading {level}"
    try:
        doc.styles[style_name]
    except KeyError:
        from docx.enum.style import WD_STYLE_TYPE
        doc.styles.add_style(style_name, WD_STYLE_TYPE.PARAGRAPH)

    pPr = para_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        para_el.insert(0, pPr)

    pStyle = pPr.find(qn("w:pStyle"))
    if pStyle is None:
        pStyle = OxmlElement("w:pStyle")
        pPr.insert(0, pStyle)
    pStyle.set(qn("w:val"), style_name)


def apply_alignment(para_el, alignment: str) -> None:
    """Set paragraph alignment via XML."""
    val = _ALIGN_VAL.get(alignment.upper())
    if not val:
        return
    pPr = para_el.find(qn("w:pPr"))
    if pPr is None:
        pPr = OxmlElement("w:pPr")
        para_el.insert(0, pPr)
    jc = pPr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        pPr.append(jc)
    jc.set(qn("w:val"), val)


def _make_paragraph(text: str, style_name: str) -> OxmlElement:
    para = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    pStyle = OxmlElement("w:pStyle")
    pStyle.set(qn("w:val"), style_name)
    pPr.append(pStyle)
    para.append(pPr)
    if text:
        r = OxmlElement("w:r")
        t = OxmlElement("w:t")
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        r.append(t)
        para.append(r)
    return para


def insert_paragraph_after(ref_el, text: str, style_name: str):
    """Insert a new paragraph immediately after ref_el."""
    new_para = _make_paragraph(text, style_name)
    ref_el.addnext(new_para)
    return new_para


def prepend_paragraph(doc: Document, text: str, style_name: str):
    """Insert a new paragraph at the very start of the document body."""
    new_para = _make_paragraph(text, style_name)
    doc.element.body.insert(0, new_para)
    return new_para


def remove_element(el) -> None:
    """Remove an XML element from its parent."""
    parent = el.getparent()
    if parent is not None:
        parent.remove(el)
