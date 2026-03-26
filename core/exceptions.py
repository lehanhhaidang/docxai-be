from __future__ import annotations


class DocFlowError(Exception):
    """Base error for DocFlow."""


class DocxParseError(DocFlowError):
    """Invalid or unreadable .docx file."""


class SessionNotFoundError(DocFlowError):
    """Session does not exist or has expired."""


class SpecValidationError(DocFlowError):
    """Format Spec references unknown ids or styles."""


class AIError(DocFlowError):
    """Claude API or JSON parsing failure."""
