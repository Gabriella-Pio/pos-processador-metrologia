"""Merge e resolução de linhas de tabela com overrides do usuário."""
from __future__ import annotations

from src.core.domain.table_row_specs import (
    INTRODUCAO_PROSE_ROW_IDS,
    default_table_rows,
    default_tomo_introducao_rows,
)


def apply_legacy_introducao_overrides(
    rows: list[dict[str, str]],
    overrides: dict | None,
) -> list[dict[str, str]]:
    """Aplica pares title_* / corpo legados sobre as linhas de métricas."""
    if not overrides:
        return [dict(row) for row in rows]

    label_keys = {
        "amostra": "title_amostra",
        "valores": "title_valores",
        "fora": "title_fora",
        "mmc": "title_mmc",
        "tipo_analise": "title_valores",
        "metodo": "title_fora",
        "equipamento": "title_mmc",
        "trincas": "title_trincas",
        "impurezas": "title_impurezas",
        "obstrucoes": "title_obstrucoes",
    }
    value_keys = {
        "amostra": "valor_amostra",
        "valores": "valor_valores",
        "fora": "valor_fora",
        "mmc": "valor_mmc",
        "tipo_analise": "valor_tipo_analise",
        "metodo": "valor_metodo",
        "equipamento": "valor_equipamento",
        "trincas": "valor_trincas",
        "impurezas": "valor_impurezas",
        "obstrucoes": "valor_obstrucoes",
    }
    filled: list[dict[str, str]] = []
    for row in rows:
        item = dict(row)
        row_id = item.get("id", "")
        title_key = label_keys.get(row_id)
        value_key = value_keys.get(row_id)
        if title_key and title_key in overrides:
            item["label"] = str(overrides[title_key])
        if value_key and value_key in overrides:
            item["value"] = str(overrides[value_key])
        filled.append(item)
    return filled


def _strip_introducao_prose_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [dict(row) for row in rows if row.get("id") not in INTRODUCAO_PROSE_ROW_IDS]


def merge_with_defaults(
    defaults: list[dict[str, str]],
    stored: list,
    *,
    append_missing: bool = True,
) -> list[dict[str, str]]:
    default_by_id = {row["id"]: row for row in defaults}
    merged: list[dict[str, str]] = []
    seen: set[str] = set()
    for row in stored:
        row_id = row.get("id", "")
        base = default_by_id.get(row_id, {"id": row_id, "label": row.get("label", ""), "value": ""})
        merged.append({
            "id": row_id or base["id"],
            "label": row.get("label", base["label"]),
            "value": row.get("value", base["value"]),
        })
        if row_id:
            seen.add(row_id)
    if append_missing:
        for row in defaults:
            if row["id"] not in seen:
                merged.append(dict(row))
    return merged


def resolve_introducao_table_rows(
    overrides: dict | None,
    *,
    report_kind: str = "mmc",
) -> list[dict[str, str]]:
    overrides = overrides or {}
    stored = overrides.get("table_rows")
    if stored:
        stored = _strip_introducao_prose_rows(stored)
    if report_kind == "tomografia":
        defaults = default_tomo_introducao_rows()
        if stored:
            return merge_with_defaults(defaults, stored, append_missing=False)
        return apply_legacy_introducao_overrides(defaults, overrides)
    if stored:
        return merge_with_defaults(
            default_table_rows("introducao"), stored, append_missing=False,
        )
    return apply_legacy_introducao_overrides(default_table_rows("introducao"), overrides)


def merge_table_rows(section_id: str, stored: list | None) -> list[dict[str, str]]:
    defaults = default_table_rows(section_id)
    if not stored:
        return defaults
    return merge_with_defaults(defaults, stored)
