from __future__ import annotations
from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

_ALIGN = {"left": "LEFT", "right": "RIGHT", "center": "CENTER", "both": "JUSTIFY", "justify": "JUSTIFY"}


def _tag(el) -> str:
    return etree.QName(el.tag).localname


def _val(el, attr: str) -> str | None:
    return el.get(f"{{{W}}}{attr}")


def parse_styles(styles_xml: bytes) -> dict[str, dict]:
    """
    Parse styles.xml → {styleId: {font, size, bold, alignment}, ...}
    Also maps style names as aliases.
    """
    root = etree.fromstring(styles_xml)
    result: dict[str, dict] = {}

    for style_el in root.findall(f".//{{{W}}}style"):
        style_id = _val(style_el, "styleId")
        if not style_id:
            continue

        name_el = style_el.find(f"{{{W}}}name")
        style_name = _val(name_el, "val") if name_el is not None else None

        rpr = style_el.find(f".//{{{W}}}rPr")
        ppr = style_el.find(f".//{{{W}}}pPr")

        font = None
        size = None
        bold = False
        alignment = None

        if rpr is not None:
            fonts_el = rpr.find(f"{{{W}}}rFonts")
            if fonts_el is not None:
                font = _val(fonts_el, "ascii") or _val(fonts_el, "hAnsi")
            sz = rpr.find(f"{{{W}}}sz")
            if sz is not None and _val(sz, "val"):
                size = int(_val(sz, "val")) / 2
            bold_el = rpr.find(f"{{{W}}}b")
            if bold_el is not None:
                bold = _val(bold_el, "val") not in ("false", "0", None) or True

        if ppr is not None:
            jc = ppr.find(f"{{{W}}}jc")
            if jc is not None:
                alignment = _ALIGN.get((_val(jc, "val") or "").lower())

        entry = {"font": font, "size": size, "bold": bold, "alignment": alignment}
        result[style_id] = entry
        if style_name and style_name != style_id:
            result[style_name] = entry

    return result
