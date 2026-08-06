"""Textos de interpretação por item de medição (MMC / CALYPSO)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.domain.number_utils import to_float


@dataclass(frozen=True)
class MeasurementLimits:
    valor_medido: float
    limite_inferior: float
    limite_superior: float


def item_has_tolerance(item: Any) -> bool:
    return (
        getattr(item, "tol_superior", "N/A") != "N/A"
        and getattr(item, "tol_inferior", "N/A") != "N/A"
    )


def measurement_limits(item: Any) -> MeasurementLimits | None:
    if not item_has_tolerance(item):
        return None
    nominal = to_float(getattr(item, "nominal", "0"))
    sup = to_float(getattr(item, "tol_superior", "0"))
    inf = to_float(getattr(item, "tol_inferior", "0"))
    return MeasurementLimits(
        valor_medido=to_float(getattr(item, "valor_medido", "0")),
        limite_superior=nominal + sup,
        limite_inferior=nominal - abs(inf),
    )


def format_item_bullet_plain(item: Any) -> str:
    """Texto plano para o editor (sem marcação HTML)."""
    caracteristica = getattr(item, "caracteristica", "") or "característica"
    tipo = getattr(item, "tipo", "") or "—"
    valor = getattr(item, "valor_medido", "") or "—"
    status = getattr(item, "status", "") or ""
    limits = measurement_limits(item)
    if limits is None:
        return (
            f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
            f"{valor}, sem valores de tolerância cadastrados no relatório de origem."
        )
    if status == "Dentro":
        return (
            f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
            f"{valor}, permanecendo dentro dos limites cadastrados de "
            f"{limits.limite_inferior:.4f} a {limits.limite_superior:.4f}."
        )
    if limits.valor_medido > limits.limite_superior:
        excedente = limits.valor_medido - limits.limite_superior
        return (
            f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
            f"{valor}, ficando acima dos limites cadastrados de "
            f"{limits.limite_inferior:.4f} a {limits.limite_superior:.4f}, "
            f"resultando em um excedente de +{excedente:.4f}."
        )
    if limits.valor_medido < limits.limite_inferior:
        faltante = limits.limite_inferior - limits.valor_medido
        return (
            f"A característica {caracteristica}, do tipo {tipo}, apresentou valor medido de "
            f"{valor}, ficando abaixo dos limites cadastrados de "
            f"{limits.limite_inferior:.4f} a {limits.limite_superior:.4f}, "
            f"resultando em um déficit de -{faltante:.4f}."
        )
    return (
        f"A característica {caracteristica} ({tipo}) apresentou valor medido de "
        f"{valor} fora dos limites."
    )


def format_item_bullet_html(item: Any, *, alert_color: str) -> str:
    """Parágrafo HTML para o PDF (ReportLab)."""
    caracteristica = getattr(item, "caracteristica", "") or "característica"
    tipo = getattr(item, "tipo", "") or "—"
    valor = getattr(item, "valor_medido", "") or "—"
    status = getattr(item, "status", "") or ""
    limits = measurement_limits(item)
    if limits is None:
        return (
            f"• A característica <b>{caracteristica}</b>, do tipo {tipo}, apresentou valor medido de "
            f"<b>{valor}</b>, sem valores de tolerância cadastrados no relatório de origem."
        )
    if status == "Dentro":
        return (
            f"• A característica <b>{caracteristica}</b>, do tipo {tipo}, apresentou valor medido de "
            f"<b>{valor}</b>, permanecendo <b>dentro</b> dos limites cadastrados de "
            f"{limits.limite_inferior:.4f} a {limits.limite_superior:.4f}."
        )
    if limits.valor_medido > limits.limite_superior:
        excedente = limits.valor_medido - limits.limite_superior
        return (
            f"• A característica <b>{caracteristica}</b>, do tipo {tipo}, apresentou valor medido de "
            f"<b>{valor}</b>, ficando <b>acima</b> dos limites cadastrados de "
            f"{limits.limite_inferior:.4f} a {limits.limite_superior:.4f}, "
            f"resultando em um excedente de <font color='{alert_color}'><b>+{excedente:.4f}</b></font>."
        )
    if limits.valor_medido < limits.limite_inferior:
        faltante = limits.limite_inferior - limits.valor_medido
        return (
            f"• A característica <b>{caracteristica}</b>, do tipo {tipo}, apresentou valor medido de "
            f"<b>{valor}</b>, ficando <b>abaixo</b> dos limites cadastrados de "
            f"{limits.limite_inferior:.4f} a {limits.limite_superior:.4f}, "
            f"resultando em um déficit de <font color='{alert_color}'><b>-{faltante:.4f}</b></font>."
        )
    return (
        f"• A característica <b>{caracteristica}</b> ({tipo}) apresentou valor medido de "
        f"<b>{valor}</b> fora dos limites."
    )


def iter_mmc_bullet_htmls(items: list[Any], *, alert_color: str) -> list[str]:
    return [format_item_bullet_html(item, alert_color=alert_color) for item in items]
