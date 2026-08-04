"""Resolução de placeholders `{chave}` em textos de prosa."""
from __future__ import annotations

import re

from src.core.domain.report_field_registry import GLOBAL_FIELDS

_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z0-9_]+)\}")

PLACEHOLDER_CATALOG: list[tuple[str, str]] = [(f.key, f.label) for f in GLOBAL_FIELDS] + [
    ("numero_medicoes", "Quantidade de medições"),
    ("total_fora", "Total fora dos limites"),
]


def placeholder_keys() -> list[str]:
    return [key for key, _ in PLACEHOLDER_CATALOG]


def placeholder_label(key: str) -> str:
    for pk, label in PLACEHOLDER_CATALOG:
        if pk == key:
            return label
    return key


def extract_placeholders(text: str) -> list[str]:
    return _PLACEHOLDER_RE.findall(text or "")


def remove_placeholder(text: str, key: str) -> str:
    return (text or "").replace(f"{{{key}}}", "")


def resolve_placeholders(text: str, context: dict[str, str]) -> str:
    if not text:
        return ""

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return str(context.get(key, match.group(0)))

    return _PLACEHOLDER_RE.sub(_replace, text)


def build_placeholder_context(dto, document) -> dict[str, str]:
    from src.core.domain.parsed_overrides import get_dto_scalar

    ctx: dict[str, str] = {
        "componente": get_dto_scalar(dto, "componente", "Não identificado"),
        "operador": get_dto_scalar(dto, "operador", "Não informado"),
        "maquina_mmc": get_dto_scalar(dto, "maquina_mmc", "Não identificada"),
        "numero_mmc": get_dto_scalar(dto, "numero_mmc", "Não informado"),
        "data_hora": get_dto_scalar(dto, "data_hora", "Não informada"),
        "software": get_dto_scalar(dto, "software", "ZEISS CALYPSO"),
        "versao_software": get_dto_scalar(dto, "versao_software", ""),
        "numero_medicoes_cabecalho": get_dto_scalar(dto, "numero_medicoes_cabecalho", "0"),
    }
    items = getattr(dto, "itens_medicao", []) or []
    ctx["numero_medicoes"] = str(len(items))
    ctx["total_fora"] = str(sum(1 for i in items if i.status == "Fora"))
    if document is not None:
        ctx["client_project"] = getattr(document, "client_project", "")
        ctx["evaluated_component"] = getattr(document, "evaluated_component", "")
    return ctx
