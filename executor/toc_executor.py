from __future__ import annotations
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from executor.block_executor import _make_paragraph


def insert_toc(doc: Document, before_el=None) -> None:
    """
    Insert a TOC heading + TOC field paragraph.
    If before_el is given, inserts before that element; otherwise prepends to body.
    """
    toc_field = _build_toc_field_para()
    heading = _make_paragraph("Mục lục", "Heading1")

    if before_el is not None:
        before_el.addprevious(toc_field)
        toc_field.addprevious(heading)
    else:
        body = doc.element.body
        body.insert(0, toc_field)
        body.insert(0, heading)


def _build_toc_field_para() -> OxmlElement:
    para = OxmlElement("w:p")
    run = OxmlElement("w:r")

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instr.text = ' TOC \\o "1-3" \\h \\z \\u '

    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")

    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    run.extend([begin, instr, sep, end])
    para.append(run)
    return para
