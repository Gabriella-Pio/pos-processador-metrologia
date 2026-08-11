"""Resolução de overrides sobre o DTO parseado (RelatorioCalypsoDto)."""
from __future__ import annotations

import copy
from typing import Any

from src.core.parser.table_extractor import MedicaoItemDto


def medicao_item_to_dict(item: MedicaoItemDto) -> dict[str, str]:
    return {
        "caracteristica": item.caracteristica,
        "tipo": item.tipo,
        "valor_medido": item.valor_medido,
        "nominal": item.nominal,
        "tol_superior": item.tol_superior,
        "tol_inferior": item.tol_inferior,
        "desvio": item.desvio,
        "status": item.status,
    }


def medicao_dict_to_item(row: dict[str, str]) -> MedicaoItemDto:
    return MedicaoItemDto(
        caracteristica=row.get("caracteristica", ""),
        tipo=row.get("tipo", ""),
        valor_medido=row.get("valor_medido", ""),
        nominal=row.get("nominal", ""),
        tol_superior=row.get("tol_superior", ""),
        tol_inferior=row.get("tol_inferior", ""),
        desvio=row.get("desvio", ""),
        status=row.get("status", "Dentro"),
    )


def get_dto_scalar(dto: Any, key: str, default: str = "") -> str:
    if dto is None:
        return default
    value = getattr(dto, key, default)
    return str(value) if value is not None else default


def get_itens_medicao_as_dicts(dto: Any) -> list[dict[str, str]]:
    if dto is None:
        return []
    items = getattr(dto, "itens_medicao", []) or []
    return [medicao_item_to_dict(item) for item in items]


def build_prose_context(dto: Any, document: Any) -> dict[str, str]:
    """Contexto para templates de prosa com placeholders."""
    componente_default = "Não identificado"
    if document is not None:
        componente_default = getattr(document, "evaluated_component", "") or componente_default
    ctx = {
        "componente": get_dto_scalar(dto, "componente", componente_default) or componente_default,
        "operador": get_dto_scalar(dto, "operador", "Não informado"),
        "maquina_mmc": get_dto_scalar(dto, "maquina_mmc", "Não identificada"),
        "numero_medicoes": str(
            getattr(dto, "numero_medicoes_cabecalho", None)
            or len(getattr(dto, "itens_medicao", []) or [])
        ),
        "numero_medicoes_cabecalho": get_dto_scalar(dto, "numero_medicoes_cabecalho", "0"),
        "n_pecas": str(len(getattr(dto, "piece_labels", []) or []) or 1),
        "total_fora": str(
            sum(getattr(s, "fora_count", 0) for s in getattr(dto, "series", []) or [])
            if getattr(dto, "series", None) is not None
            else sum(
                1
                for item in (getattr(dto, "itens_medicao", []) or [])
                if str(getattr(item, "status", "")).lower() == "fora"
            )
        ),
    }
    if document is not None:
        ctx["client_project"] = getattr(document, "client_project", "")
        ctx["evaluated_component"] = getattr(document, "evaluated_component", "")
        template_id = getattr(document, "template_id", "")
        source_kind = getattr(document, "source_kind", "")
        if template_id in {"estatistico", "statistical"}:
            ctx["report_kind"] = "estatistico"
        elif template_id in {"mixed", "hibrido"}:
            ctx["report_kind"] = "mixed"
        elif template_id in {"tomografia", "tomo"} or source_kind == "insp_ect":
            ctx["report_kind"] = "tomografia"
        else:
            ctx["report_kind"] = "mmc"
    return ctx


def build_effective_dto(raw_dto: Any, parsed_overrides: dict[str, Any]) -> Any:
    """Retorna cópia do DTO com overrides aplicados."""
    if raw_dto is None:
        return None
    dto = copy.deepcopy(raw_dto)

    scalar = parsed_overrides.get("scalar", {})
    for key, value in scalar.items():
        if hasattr(dto, key):
            if key == "numero_medicoes_cabecalho":
                try:
                    setattr(dto, key, int(value))
                except (TypeError, ValueError):
                    setattr(dto, key, value)
            else:
                setattr(dto, key, value)

    if "itens_medicao" in parsed_overrides:
        rows = parsed_overrides["itens_medicao"]
        dto.itens_medicao = [medicao_dict_to_item(row) for row in rows]

    return dto


def extract_scalar_overrides(raw_dto: Any, parsed_overrides: dict[str, Any]) -> dict[str, str]:
    """Valores efetivos dos campos escalares para exibição na UI."""
    scalar_ov = parsed_overrides.get("scalar", {})
    keys = (
        "componente", "operador", "maquina_mmc", "numero_mmc", "data_hora",
        "software", "versao_software", "numero_medicoes_cabecalho",
    )
    result: dict[str, str] = {}
    for key in keys:
        if key in scalar_ov:
            result[key] = str(scalar_ov[key])
        else:
            result[key] = get_dto_scalar(raw_dto, key)
    return result


def is_scalar_overridden(key: str, parsed_overrides: dict[str, Any]) -> bool:
    return key in parsed_overrides.get("scalar", {})


def is_itens_overridden(parsed_overrides: dict[str, Any]) -> bool:
    return "itens_medicao" in parsed_overrides
