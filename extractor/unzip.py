from __future__ import annotations
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from core.exceptions import DocxParseError


def unzip_docx(docx_bytes: bytes) -> dict[str, bytes]:
    """Unzip a .docx archive and return its contents keyed by internal path."""
    try:
        with ZipFile(BytesIO(docx_bytes), "r") as zf:
            return {name: zf.read(name) for name in zf.namelist()}
    except Exception as exc:
        raise DocxParseError("Not a valid .docx file (ZIP error)") from exc


def rezip_docx(files: dict[str, bytes]) -> bytes:
    """Re-assemble a .docx archive from a dict of file contents."""
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
        for path, data in files.items():
            zf.writestr(path, data)
    return buf.getvalue()
