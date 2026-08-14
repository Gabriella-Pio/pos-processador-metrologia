"""Formatação de células de medição com unidade (mm / inch / °)."""
from __future__ import annotations

import re
from typing import Any


def infer_measure_unit(raw: str | float | int | None) -> str:
    """Infere unidade a partir do texto bruto do CALYPSO (mm / inch / °)."""
    text = str(raw or "").strip().lower()
    if not text:
        return ""
    if "inch" in text or re.search(r"\bin\b", text):
        return "inch"
    if "mm" in text:
        return "mm"
    if "°" in text or "deg" in text:
        return "°"
    return ""


def resolve_item_unit(item: Any) -> str:
    """Unidade preferencial: coluna Medido; fallback nas demais colunas numéricas."""
    for attr in ("valor_medido", "nominal", "desvio", "tol_superior", "tol_inferior"):
        raw = item.get(attr, "") if isinstance(item, dict) else getattr(item, attr, "")
        unit = infer_measure_unit(raw)
        if unit:
            return unit
    return ""


def ensure_measure_unit(value: str | None, unit: str) -> str:
    """Garante que o texto exiba a unidade, sem duplicar se já houver."""
    text = str(value or "").strip()
    if not text or text.upper() in {"N/A", "-", "—"}:
        return text or "—"
    if not unit:
        return text
    if infer_measure_unit(text):
        return text
    bare = re.sub(r"\s*(mm|inch|in|°|deg)\s*$", "", text, flags=re.IGNORECASE).strip()
    return f"{bare} {unit}".strip() if bare else text


def format_item_measure_cells(item: Any) -> dict[str, str]:
    """Valores da linha com a mesma unidade do Medido (quando aplicável)."""
    unit = resolve_item_unit(item)

    def _get(attr: str) -> str:
        if isinstance(item, dict):
            return str(item.get(attr, "") or "")
        return str(getattr(item, attr, "") or "")

    return {
        "valor_medido": ensure_measure_unit(_get("valor_medido"), unit),
        "nominal": ensure_measure_unit(_get("nominal"), unit),
        "tol_superior": ensure_measure_unit(_get("tol_superior"), unit),
        "tol_inferior": ensure_measure_unit(_get("tol_inferior"), unit),
        "desvio": ensure_measure_unit(_get("desvio"), unit),
    }
