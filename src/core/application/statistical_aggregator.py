"""Agregação estatística de medições CALYPSO em lote (várias peças)."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any

from src.core.domain.measure_display import infer_measure_unit


@dataclass
class StatisticalCharacteristicSeries:
    """Série de valores de uma característica ao longo das peças."""

    key: str
    display_name: str
    tipo: str  # "diametro" | "cilindricidade" | "outro"
    nominal: str = ""
    tol_superior: str = ""
    tol_inferior: str = ""
    unit: str = ""  # mm | inch | °
    values: list[tuple[int, float | None, str]] = field(default_factory=list)

    @property
    def n(self) -> int:
        return sum(1 for _, value, _ in self.values if value is not None)

    @property
    def measured_values(self) -> list[float]:
        return [value for _, value, _ in self.values if value is not None]

    @property
    def mean(self) -> float | None:
        values = self.measured_values
        if not values:
            return None
        return sum(values) / len(values)

    @property
    def stdev(self) -> float | None:
        values = self.measured_values
        if len(values) < 2:
            return 0.0 if values else None
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
        return math.sqrt(variance)

    @property
    def minimum(self) -> float | None:
        values = self.measured_values
        return min(values) if values else None

    @property
    def maximum(self) -> float | None:
        values = self.measured_values
        return max(values) if values else None

    @property
    def fora_count(self) -> int:
        return sum(1 for _, value, status in self.values if value is not None and _is_fora(status))


@dataclass
class StatisticalBatchDto:
    """DTO virtual para relatório estatístico consolidado."""

    componente: str
    cliente: str
    piece_labels: list[str]
    series: list[StatisticalCharacteristicSeries]
    source_kind: str = "calypso"
    operador: str = ""
    maquina_mmc: str = ""
    software: str = "ZEISS CALYPSO"
    numero_medicoes_cabecalho: int = 0
    itens_medicao: list = field(default_factory=list)


_DIAMETER_RE = re.compile(r"di[aá]metro|diametro", re.IGNORECASE)
_CYL_RE = re.compile(r"cilindricidade", re.IGNORECASE)
_ALTURA_RE = re.compile(r"\baltura\b", re.IGNORECASE)
_COMPRIMENTO_RE = re.compile(r"comprimento|largura|profundidade|espessura|dist[aâ]ncia|\braio\b|\bdim\b", re.IGNORECASE)
_ANGULO_RE = re.compile(r"[aâ]ngulo", re.IGNORECASE)
_PARALELISMO_RE = re.compile(r"paralelismo", re.IGNORECASE)
_PERP_RE = re.compile(r"perpendicularidade", re.IGNORECASE)
_COAX_RE = re.compile(r"coaxialidade|concentricidade|cocentricidade", re.IGNORECASE)

# Ordem de exibição no relatório unificado.
MEASURE_TYPE_ORDER: tuple[str, ...] = (
    "diametro",
    "altura",
    "comprimento",
    "cilindricidade",
    "paralelismo",
    "perpendicularidade",
    "coaxialidade",
    "angulo",
    "outro",
)

# (rótulo curto, heading resumo, heading detalhe, plural para prosa,
#  id seção resumo, id seção detalhe)
MEASURE_TYPE_META: dict[str, tuple[str, str, str, str, str, str]] = {
    "diametro": (
        "Diâmetros",
        "RESULTADOS ESTATÍSTICOS — DIÂMETROS",
        "TABELA DETALHADA DAS MEDIÇÕES — DIÂMETROS",
        "diâmetros",
        "estat_resumo_diametros",
        "estat_detalhe_diametros",
    ),
    "altura": (
        "Alturas",
        "RESULTADOS ESTATÍSTICOS — ALTURAS",
        "TABELA DETALHADA DAS MEDIÇÕES — ALTURAS",
        "alturas",
        "estat_resumo_alturas",
        "estat_detalhe_alturas",
    ),
    "comprimento": (
        "Dimensões lineares",
        "RESULTADOS ESTATÍSTICOS — DIMENSÕES LINEARES",
        "TABELA DETALHADA DAS MEDIÇÕES — DIMENSÕES LINEARES",
        "dimensões lineares",
        "estat_resumo_dimensoes",
        "estat_detalhe_dimensoes",
    ),
    "cilindricidade": (
        "Cilindricidades",
        "RESULTADOS ESTATÍSTICOS — CILINDRICIDADES",
        "TABELA DETALHADA DAS MEDIÇÕES — CILINDRICIDADES",
        "cilindricidades",
        "estat_resumo_cilindricidades",
        "estat_detalhe_cilindricidades",
    ),
    "paralelismo": (
        "Paralelismos",
        "RESULTADOS ESTATÍSTICOS — PARALELISMOS",
        "TABELA DETALHADA DAS MEDIÇÕES — PARALELISMOS",
        "paralelismos",
        "estat_resumo_paralelismos",
        "estat_detalhe_paralelismos",
    ),
    "perpendicularidade": (
        "Perpendicularidades",
        "RESULTADOS ESTATÍSTICOS — PERPENDICULARIDADES",
        "TABELA DETALHADA DAS MEDIÇÕES — PERPENDICULARIDADES",
        "perpendicularidades",
        "estat_resumo_perpendicularidades",
        "estat_detalhe_perpendicularidades",
    ),
    "coaxialidade": (
        "Coaxialidades",
        "RESULTADOS ESTATÍSTICOS — COAXIALIDADES",
        "TABELA DETALHADA DAS MEDIÇÕES — COAXIALIDADES",
        "coaxialidades",
        "estat_resumo_coaxialidades",
        "estat_detalhe_coaxialidades",
    ),
    "angulo": (
        "Ângulos",
        "RESULTADOS ESTATÍSTICOS — ÂNGULOS",
        "TABELA DETALHADA DAS MEDIÇÕES — ÂNGULOS",
        "ângulos",
        "estat_resumo_angulos",
        "estat_detalhe_angulos",
    ),
    "outro": (
        "Outras características",
        "RESULTADOS ESTATÍSTICOS — OUTRAS CARACTERÍSTICAS",
        "TABELA DETALHADA DAS MEDIÇÕES — OUTRAS CARACTERÍSTICAS",
        "outras características",
        "estat_resumo_outros",
        "estat_detalhe_outros",
    ),
}

_LINEAR_TIPOS = frozenset({"diametro", "altura", "comprimento"})
_GEOMETRIC_TIPOS = frozenset(
    {"cilindricidade", "paralelismo", "perpendicularidade", "coaxialidade", "angulo"}
)


def parse_measure_number(raw: str | float | int | None) -> float | None:
    """Converte valor medido textual (ex.: ``81,9972 mm``) em float."""
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    text = str(raw).strip()
    if not text:
        return None
    text = re.sub(r"[^\d,.\-]", "", text.replace(" ", ""))
    if not text or text in {"-", ".", ","}:
        return None
    text = text.replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def normalize_characteristic_key(name: str) -> str:
    """Chave estável para alinhar a mesma característica entre peças."""
    text = str(name or "").strip().lower()
    text = text.replace("á", "a").replace("ã", "a").replace("â", "a")
    text = text.replace("é", "e").replace("ê", "e")
    text = text.replace("í", "i").replace("ó", "o").replace("ô", "o").replace("ú", "u")
    text = text.replace("ç", "c")
    text = re.sub(r"^diametro[_\s\-]*", "diametro ", text)
    text = re.sub(r"^cilindricidade[_\s\-]*", "cilindricidade ", text)
    text = re.sub(r"[_\-/]+", " ", text)
    # Abreviações comuns (sem merge entre características distintas).
    text = re.sub(r"\btrab\b", "trabalho", text)
    text = re.sub(r"\bentr\b", "entrada", text)
    text = re.sub(r"\bsup\b", "superior", text)
    text = re.sub(r"\binf\b", "inferior", text)
    text = re.sub(r"\b(de|da|do|das|dos)\b", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def display_characteristic_name(name: str) -> str:
    """Rótulo amigável a partir do nome bruto do CALYPSO."""
    text = str(name or "").strip()
    text = re.sub(r"^Diametro[_\s\-]*", "Diâmetro ", text, flags=re.IGNORECASE)
    text = re.sub(r"^Cilindricidade[_\s\-]*", "Cilindricidade ", text, flags=re.IGNORECASE)
    text = re.sub(r"^Altura[_\s\-]*", "Altura ", text, flags=re.IGNORECASE)
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    lower = text.lower()
    for prefix, label in (
        ("diâmetro ", "Diâmetro"),
        ("cilindricidade ", "Cilindricidade"),
        ("altura ", "Altura"),
    ):
        if lower.startswith(prefix):
            rest = text[len(prefix) :].strip().lower()
            return f"{label} {rest}" if rest else label
    return text[:1].upper() + text[1:] if text else text


def short_characteristic_label(name: str) -> str:
    """Rótulo curto para cabeçalhos de tabela (sem palavra do tipo de medida)."""
    full = display_characteristic_name(name)
    shortened = re.sub(
        r"^(Diâmetro|Cilindricidade|Altura|Comprimento|Distância|Raio|Largura)\s+",
        "",
        full,
        flags=re.IGNORECASE,
    ).strip()
    return shortened or full


def classify_characteristic_tipo(name: str, tipo_hint: str = "") -> str:
    """Classifica o grupo metrológico a partir do nome (e, se útil, do tipo do parser)."""
    key = normalize_characteristic_key(name)

    def _from_blob(blob: str) -> str | None:
        if not blob.strip():
            return None
        if _CYL_RE.search(blob):
            return "cilindricidade"
        if _DIAMETER_RE.search(blob):
            return "diametro"
        if _ALTURA_RE.search(blob):
            return "altura"
        if _PARALELISMO_RE.search(blob):
            return "paralelismo"
        if _PERP_RE.search(blob):
            return "perpendicularidade"
        if _COAX_RE.search(blob):
            return "coaxialidade"
        if _ANGULO_RE.search(blob):
            return "angulo"
        if _COMPRIMENTO_RE.search(blob):
            return "comprimento"
        return None

    # Nome da característica tem prioridade sobre o tipo genérico do parser
    # (ex.: "altura bico" com hint "GEOMETRIA GERAL" / "DIÂMETRO").
    from_name = _from_blob(key)
    if from_name:
        return from_name
    hint = normalize_characteristic_key(tipo_hint)
    return _from_blob(hint) or "outro"


def measure_tipo_meta(tipo: str) -> tuple[str, str, str, str, str, str]:
    return MEASURE_TYPE_META.get(tipo, MEASURE_TYPE_META["outro"])


def present_measure_tipos(series: list[StatisticalCharacteristicSeries]) -> list[str]:
    """Tipos presentes no lote, na ordem canônica de exibição."""
    found = {item.tipo for item in series if item.tipo}
    ordered = [tipo for tipo in MEASURE_TYPE_ORDER if tipo in found]
    extras = sorted(found - set(MEASURE_TYPE_ORDER))
    return ordered + extras


def resumo_section_id(tipo: str) -> str:
    return measure_tipo_meta(tipo)[4]


def detalhe_section_id(tipo: str) -> str:
    return measure_tipo_meta(tipo)[5]


def tipo_from_estat_section_id(section_id: str) -> str | None:
    """Resolve o tipo metrológico a partir do id da seção estatística."""
    for tipo, meta in MEASURE_TYPE_META.items():
        if section_id in {meta[4], meta[5]}:
            return tipo
    return None


def is_linear_measure_tipo(tipo: str) -> bool:
    return tipo in _LINEAR_TIPOS


def is_geometric_measure_tipo(tipo: str) -> bool:
    return tipo in _GEOMETRIC_TIPOS


def statistical_escopo_phrase(tipos: list[str]) -> str:
    """Frase de escopo a partir dos tipos realmente presentes no lote."""
    labels = [measure_tipo_meta(t)[3] for t in tipos if t in MEASURE_TYPE_META]
    if not labels:
        return "as características dimensionais e geométricas informadas nos relatórios de medição da MMC"
    if len(labels) == 1:
        medidas = labels[0]
    elif len(labels) == 2:
        medidas = f"{labels[0]} e {labels[1]}"
    else:
        medidas = ", ".join(labels[:-1]) + f" e {labels[-1]}"
    return (
        "as características dimensionais e geométricas informadas "
        f"nos relatórios de medição da MMC, incluindo {medidas}"
    )


def _is_fora(status: str) -> bool:
    return str(status or "").strip().lower() in {"fora", "nok", "out"}


def _item_attr(item: Any, *names: str) -> str:
    for name in names:
        if isinstance(item, dict):
            value = item.get(name)
        else:
            value = getattr(item, name, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def aggregate_measurement_series(
    piece_items: list[tuple[int, list[Any]]],
    *,
    piece_labels: list[str] | None = None,
) -> list[StatisticalCharacteristicSeries]:
    """Agrega ``itens_medicao`` de várias peças em séries por característica."""
    series_map: dict[str, StatisticalCharacteristicSeries] = {}
    for piece_idx, items in piece_items:
        for item in items or []:
            raw_name = _item_attr(item, "caracteristica", "name")
            if not raw_name:
                continue
            key = normalize_characteristic_key(raw_name)
            if not key:
                continue
            tipo_hint = _item_attr(item, "tipo")
            series = series_map.get(key)
            if series is None:
                series = StatisticalCharacteristicSeries(
                    key=key,
                    display_name=display_characteristic_name(raw_name),
                    tipo=classify_characteristic_tipo(raw_name, tipo_hint),
                    nominal=_item_attr(item, "nominal"),
                    tol_superior=_item_attr(item, "tol_superior"),
                    tol_inferior=_item_attr(item, "tol_inferior"),
                )
                series_map[key] = series
            elif not series.nominal:
                series.nominal = _item_attr(item, "nominal")
                series.tol_superior = _item_attr(item, "tol_superior")
                series.tol_inferior = _item_attr(item, "tol_inferior")
            raw_measured = _item_attr(item, "valor_medido", "measured")
            if not series.unit:
                series.unit = (
                    infer_measure_unit(raw_measured)
                    or infer_measure_unit(series.nominal)
                    or infer_measure_unit(_item_attr(item, "nominal"))
                )
            value = parse_measure_number(raw_measured)
            status = _item_attr(item, "status")
            series.values.append((piece_idx, value, status))

    ordered = sorted(
        series_map.values(),
        key=lambda s: (
            MEASURE_TYPE_ORDER.index(s.tipo) if s.tipo in MEASURE_TYPE_ORDER else 99,
            s.display_name,
        ),
    )
    if piece_labels:
        for series in ordered:
            by_piece: dict[int, tuple[int, float | None, str]] = {}
            for row in series.values:
                idx = row[0]
                previous = by_piece.get(idx)
                if previous is None or (previous[1] is None and row[1] is not None):
                    by_piece[idx] = row
            series.values = list(by_piece.values())
            present = set(by_piece)
            for idx in range(1, len(piece_labels) + 1):
                if idx not in present:
                    series.values.append((idx, None, ""))
            series.values.sort(key=lambda row: row[0])
    return ordered


def build_statistical_batch_dto(
    *,
    componente: str,
    cliente: str,
    piece_labels: list[str],
    piece_items: list[tuple[int, list[Any]]],
    operador: str = "",
    maquina_mmc: str = "",
) -> StatisticalBatchDto:
    series = aggregate_measurement_series(piece_items, piece_labels=piece_labels)
    total_values = sum(s.n for s in series)
    return StatisticalBatchDto(
        componente=componente,
        cliente=cliente,
        piece_labels=list(piece_labels),
        series=series,
        operador=operador,
        maquina_mmc=maquina_mmc,
        numero_medicoes_cabecalho=total_values,
    )


def format_stat_number(value: float | None, *, digits: int = 4, unit: str = "") -> str:
    if value is None:
        return "—"
    formatted = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    text = formatted.replace(".", ",")
    if unit:
        return f"{text} {unit}"
    return text


def format_series_limits_range(series: StatisticalCharacteristicSeries) -> str:
    """Faixa absoluta: (nominal − tol−) a (nominal + tol+), ex.: ``81,8472 mm a 82,1472 mm``."""
    nominal = parse_measure_number(series.nominal)
    tol_sup = parse_measure_number(series.tol_superior)
    tol_inf = parse_measure_number(series.tol_inferior)
    if nominal is None or (tol_sup is None and tol_inf is None):
        return "—"
    lower = nominal - abs(tol_inf if tol_inf is not None else 0.0)
    upper = nominal + abs(tol_sup if tol_sup is not None else 0.0)
    unit = series.unit or ""
    return (
        f"{format_stat_number(lower, unit=unit)} a "
        f"{format_stat_number(upper, unit=unit)}"
    )


def series_by_tipo(
    series: list[StatisticalCharacteristicSeries],
    tipo: str,
) -> list[StatisticalCharacteristicSeries]:
    return [item for item in series if item.tipo == tipo]


def build_estatistico_sections_config(measure_tipos: list[str]) -> dict[str, dict]:
    """Liga resumo/detalhe apenas para os tipos de medida presentes no lote."""
    from copy import deepcopy

    from src.core.domain.mixed_template_defaults import ESTATISTICO_SECTIONS_CONFIG

    layout = deepcopy(ESTATISTICO_SECTIONS_CONFIG)
    present = [t for t in measure_tipos if t]
    for tipo in present:
        rid = resumo_section_id(tipo)
        did = detalhe_section_id(tipo)
        if rid in layout:
            layout[rid]["enabled"] = True
        if did in layout:
            layout[did]["enabled"] = True

    has_any = bool(present)
    layout["estat_graficos"]["enabled"] = has_any
    layout["estat_graficos_comp"]["enabled"] = has_any
    return layout


def _pieces_with_fora(batch: StatisticalBatchDto) -> int:
    n_pecas = len(batch.piece_labels or [])
    if n_pecas <= 0:
        return 0
    flagged: set[int] = set()
    for series in batch.series or []:
        for piece_idx, _value, status in series.values:
            if _is_fora(status):
                flagged.add(int(piece_idx))
    return len(flagged)


def build_estatistico_introducao_metric_rows(
    batch: StatisticalBatchDto,
) -> list[dict[str, str]]:
    """Cards da introdução: amostra/valores/fora + fora por tipo presente no lote."""
    n_pecas = len(batch.piece_labels or [])
    total_valores = int(batch.numero_medicoes_cabecalho or 0)
    if total_valores <= 0:
        total_valores = sum(s.n for s in batch.series or [])
    total_fora = sum(s.fora_count for s in batch.series or [])
    pecas_fora = _pieces_with_fora(batch)

    rows: list[dict[str, str]] = [
        {
            "id": "amostra",
            "label": "AMOSTRA",
            "value": f"{n_pecas} peça{'s' if n_pecas != 1 else ''}",
        },
        {
            "id": "valores",
            "label": "VALORES AVALIADOS",
            "value": str(total_valores),
        },
        {
            "id": "fora",
            "label": "FORA DOS LIMITES",
            "value": f"{total_fora} valor{'es' if total_fora != 1 else ''}",
        },
        {
            "id": "pecas_ocorrencia",
            "label": "PEÇAS COM OCORRÊNCIA",
            "value": f"{pecas_fora}/{n_pecas}" if n_pecas else "0/0",
        },
    ]

    for tipo in present_measure_tipos(list(batch.series or [])):
        group = series_by_tipo(list(batch.series or []), tipo)
        if not group:
            continue
        measured = sum(s.n for s in group)
        fora = sum(s.fora_count for s in group)
        short_label = measure_tipo_meta(tipo)[0].upper()
        rows.append(
            {
                "id": f"fora_{tipo}",
                "label": f"{short_label} FORA",
                "value": f"{fora}/{measured}",
            }
        )
    return rows


def _join_pt(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item or "").strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} e {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f" e {cleaned[-1]}"


def _series_has_zero_upper_tol(series: StatisticalCharacteristicSeries) -> bool:
    tol = parse_measure_number(series.tol_superior)
    return tol is not None and abs(tol) < 1e-12


def build_estatistico_type_footer_note(
    series_list: list[StatisticalCharacteristicSeries],
    tipo: str,
) -> str:
    """Nota de rodapé automática do resumo estatístico de um tipo de medida."""
    group = [s for s in series_list if s.tipo == tipo]
    if not group:
        return ""
    total = sum(s.n for s in group)
    fora = sum(s.fora_count for s in group)
    if fora <= 0 or total <= 0:
        return ""

    plural = measure_tipo_meta(tipo)[3]
    fora_names = []
    for s in group:
        if s.fora_count <= 0:
            continue
        raw = short_characteristic_label(s.display_name)
        fora_names.append(" ".join(part.capitalize() for part in raw.split()) if raw else raw)
    names_bit = _join_pt(fora_names)
    subject = f"{plural} ({names_bit})" if names_bit else plural

    if is_geometric_measure_tipo(tipo):
        valores_label = "valores geométricos avaliados"
    elif is_linear_measure_tipo(tipo):
        valores_label = "valores dimensionais avaliados"
    else:
        valores_label = "valores avaliados"

    ocorrencia = "ocorrência" if fora == 1 else "ocorrências"
    note = (
        f"Resumo das {subject}: foram registradas {fora} {ocorrencia} fora dos "
        f"limites informados em {total} {valores_label}."
    )

    zero_tol = [s for s in group if s.fora_count > 0 and _series_has_zero_upper_tol(s)]
    if zero_tol:
        unit = next((s.unit for s in zero_tol if s.unit), "mm")
        note += (
            f" Algumas características possuem limite superior registrado como "
            f"0,0000 {unit} nos relatórios de origem; nesses casos, a ocorrência "
            f"foi tratada conforme o próprio relatório da MMC."
        )
    return note


def build_estatistico_section_notes(
    batch: StatisticalBatchDto,
) -> dict[str, str]:
    """Notas de rodapé por seção de resumo/detalhe estatístico (só quando há fora)."""
    notes: dict[str, str] = {}
    series = list(batch.series or [])
    for tipo in present_measure_tipos(series):
        note = build_estatistico_type_footer_note(series, tipo)
        if not note:
            continue
        notes[resumo_section_id(tipo)] = note
        notes[detalhe_section_id(tipo)] = note
    return notes
