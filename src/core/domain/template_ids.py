"""Identificadores de templates oficiais (builtins)."""
from __future__ import annotations

BUILTIN_TEMPLATE_IDS = frozenset({"default", "tomografia", "analise_falha"})


def is_builtin_template_id(template_id: str) -> bool:
    return template_id in BUILTIN_TEMPLATE_IDS
