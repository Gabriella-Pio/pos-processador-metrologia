"""Monta textos editáveis da seção Interpretação (MMC e tomografia)."""
from __future__ import annotations

from typing import Any

from src.core.domain.measurement_interpretation import format_item_bullet_plain
from src.core.domain.report_field_registry import SectionFieldDef

_MAX_MMC_BULLETS = 80


def build_interpretacao_editor_fields(
    effective_dto: Any,
    report_kind: str = "mmc",
    existing: dict[str, str] | None = None,
    *,
    user_overrides: dict[str, str] | None = None,
) -> dict[str, str]:
    """Preenche intro + bullets automaticamente conforme o PDF.

    - Tomografia: 4 bullets qualitativos padrão.
    - MMC: **exatamente um bullet por item de medição** (N itens → N campos).
      Só preserva texto se estiver em ``user_overrides`` (edição explícita).
    """
    existing = dict(existing or {})
    user_overrides = {
        k: v
        for k, v in dict(user_overrides or {}).items()
        if v is not None and str(v).strip() and not isinstance(v, list)
    }
    result = dict(existing)
    result.update(user_overrides)

    if report_kind in {"tomografia", "insp_ect"}:
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS

        defaults = TOMO_PROSE_DEFAULTS.get("interpretacao", {})
        for key, value in defaults.items():
            if key not in user_overrides:
                result[key] = value
        return result

    items = list(getattr(effective_dto, "itens_medicao", []) or [])
    componente = str(getattr(effective_dto, "componente", "") or "componente")
    if "intro" not in user_overrides:
        result["intro"] = (
            f"Análise detalhada das {len(items)} características inspecionadas no "
            f"componente {componente}:"
        )

    if not items:
        generated = [
            "Nenhuma característica dimensional foi extraída do relatório de origem.",
            "Revise o PDF importado ou edite a tabela de resultados.",
        ]
    else:
        generated = [format_item_bullet_plain(item) for item in items[:_MAX_MMC_BULLETS]]

    # Sincroniza 1..N com o PDF; remove órfãos além de N (exceto override do usuário)
    n = len(generated)
    for index, text in enumerate(generated, start=1):
        key = f"bullet_{index}"
        if key in user_overrides:
            result[key] = user_overrides[key]
        else:
            result[key] = text

    for key in list(result.keys()):
        if not key.startswith("bullet_"):
            continue
        suffix = key.split("_", 1)[1]
        if not suffix.isdigit():
            continue
        index = int(suffix)
        if index > n and key not in user_overrides:
            result.pop(key, None)

    return result


def interpretacao_field_defs(fields: dict[str, str] | None = None) -> tuple[SectionFieldDef, ...]:
    """Campos dinâmicos: intro + bullet_1..N + nota de rodapé."""
    fields = fields or {}
    defs: list[SectionFieldDef] = [
        SectionFieldDef("intro", "Texto introdutório", "textarea"),
    ]
    bullet_indexes = sorted(
        int(key.split("_", 1)[1])
        for key in fields
        if key.startswith("bullet_")
        and key.split("_", 1)[1].isdigit()
        and str(fields.get(key) or "").strip()
    )
    if not bullet_indexes:
        bullet_indexes = list(range(1, 5))
    for index in bullet_indexes:
        defs.append(
            SectionFieldDef(f"bullet_{index}", f"Interpretação {index}", "textarea")
        )
    defs.append(SectionFieldDef("nota", "Nota de rodapé", "textarea"))
    return tuple(defs)


def interpretacao_bullet_keys(fields: dict[str, str] | None = None) -> list[str]:
    return [f.key for f in interpretacao_field_defs(fields) if f.key.startswith("bullet_")]
