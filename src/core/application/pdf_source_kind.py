"""Caso de uso: detectar o tipo de PDF de origem (CALYPSO vs Bosello/INSPECT)."""
from __future__ import annotations

from src.core.parser.source_kind import (
    SourceKind,
    clear_source_kind_cache,
    detect_source_kind,
    detect_source_kind_from_text,
)

__all__ = [
    "SourceKind",
    "clear_source_kind_cache",
    "detect_source_kind",
    "detect_source_kind_from_text",
]
