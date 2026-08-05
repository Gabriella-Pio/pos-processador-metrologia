"""Monta textos editáveis da seção Interpretação (MMC e tomografia)."""
from __future__ import annotations

from typing import Any

from src.core.parser.utils import ParserUtils


def build_interpretacao_editor_fields(
    effective_dto: Any,
    report_kind: str = "mmc",
    existing: dict[str, str] | None = None,
) -> dict[str, str]:
    """Preenche intro + bullets para o formulário do Workspace.

    - Tomografia: prosa qualitativa padrão (4 bullets).
    - MMC: intro + até 4 bullets a partir de itens fora de tolerância
      (ou resumo se não houver fora).
    """
    existing = dict(existing or {})
    result = dict(existing)

    if report_kind in {"tomografia", "insp_ect"}:
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS

        defaults = TOMO_PROSE_DEFAULTS.get("interpretacao", {})
        for key, value in defaults.items():
            if not str(result.get(key) or "").strip():
                result[key] = value
        return result

    items = list(getattr(effective_dto, "itens_medicao", []) or [])
    componente = str(getattr(effective_dto, "componente", "") or "componente")
    if not str(result.get("intro") or "").strip():
        result["intro"] = (
            f"Análise detalhada das {len(items)} características inspecionadas no "
            f"componente {componente}:"
        )

    # Já tem bullets preenchidos (override do usuário) — respeita
    if any(str(result.get(f"bullet_{i}") or "").strip() for i in range(1, 5)):
        return result

    fora = [item for item in items if getattr(item, "status", "") == "Fora"]
    bullets = [_format_item_bullet(item) for item in (fora or items)[:4]]
    if not bullets:
        bullets = [
            "Nenhuma característica dimensional foi extraída do relatório de origem.",
            "Revise o PDF importado ou edite a tabela de resultados.",
        ]
    elif not fora and items:
        bullets = [
            f"Todas as {len(items)} características avaliadas permanecem dentro dos limites cadastrados.",
            *bullets[:3],
        ]

    for index, text in enumerate(bullets[:4], start=1):
        result[f"bullet_{index}"] = text
    return result


def _format_item_bullet(item: Any) -> str:
    caracteristica = getattr(item, "caracteristica", "") or "característica"
    tipo = getattr(item, "tipo", "") or "—"
    valor = getattr(item, "valor_medido", "") or "—"
    status = getattr(item, "status", "") or ""
    tem_tol = (
        getattr(item, "tol_superior", "N/A") != "N/A"
        and getattr(item, "tol_inferior", "N/A") != "N/A"
    )
    if not tem_tol:
        return (
            f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
            f"{valor}, sem valores de tolerância cadastrados no relatório de origem."
        )
    nominal = ParserUtils.converter_para_float(getattr(item, "nominal", "0"))
    sup = ParserUtils.converter_para_float(getattr(item, "tol_superior", "0"))
    inf = ParserUtils.converter_para_float(getattr(item, "tol_inferior", "0"))
    limite_sup = nominal + (sup or 0)
    limite_inf = nominal - abs(inf or 0)
    if status == "Dentro":
        return (
            f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
            f"{valor}, permanecendo dentro dos limites cadastrados de "
            f"{limite_inf:.4f} a {limite_sup:.4f}."
        )
    return (
        f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
        f"{valor}, ficando fora dos limites cadastrados de "
        f"{limite_inf:.4f} a {limite_sup:.4f}."
    )
