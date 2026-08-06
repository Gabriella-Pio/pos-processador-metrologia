"""Conversão numérica segura para strings de medição metrológica."""
from __future__ import annotations

import re


def to_float(valor_str: str) -> float:
    """Converte string de medida (ex.: ``0,0040 inch``, ``-0,0008``) para float."""
    if not valor_str or valor_str in {"N/A", "-"}:
        return 0.0
    limpo = re.sub(r"[^\d\.,\-]+", "", valor_str).replace(",", ".")
    try:
        return float(limpo)
    except ValueError:
        return 0.0
