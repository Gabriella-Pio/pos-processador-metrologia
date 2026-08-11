"""Classificação dos métodos de ensaio usados no laboratório (CMM, O-inspect, Bosello)."""
from __future__ import annotations

import re
from typing import Any, Iterable

# Chaves estáveis na ordem de exibição no relatório.
LAB_METHOD_ORDER: tuple[str, ...] = ("cmm", "o_inspect", "bosello")

# (rótulo curto, frase descritiva no estilo do PDF de referência)
LAB_METHOD_META: dict[str, tuple[str, str]] = {
    "cmm": ("CMM", "dimensional (CMM)"),
    "o_inspect": ("O-inspect", "óptico (O-inspect)"),
    "bosello": ("Bosello", "tomográfico (Bosello)"),
}

_O_INSPECT_RE = re.compile(
    r"o[\s\-]?inspect|optiv|óptic[oa]|optic[ao]",
    re.IGNORECASE,
)
_BOSELLO_RE = re.compile(r"bosello|\binsp[\s\-]?ect\b|tomograf", re.IGNORECASE)
_CMM_HINT_RE = re.compile(
    r"\b(prismo|contura|duramax|accura|mmz|centermax|micura|cmm|mmc)\b",
    re.IGNORECASE,
)


def join_portuguese(items: list[str]) -> str:
    cleaned = [str(item).strip() for item in items if str(item or "").strip()]
    if not cleaned:
        return ""
    if len(cleaned) == 1:
        return cleaned[0]
    if len(cleaned) == 2:
        return f"{cleaned[0]} e {cleaned[1]}"
    return ", ".join(cleaned[:-1]) + f" e {cleaned[-1]}"


def is_o_inspect_machine(machine_name: str) -> bool:
    return bool(_O_INSPECT_RE.search(str(machine_name or "")))


def classify_calypso_method(machine_name: str = "", *, path_hint: str = "") -> str:
    """Classifica PDF CALYPSO como CMM tátil ou O-inspect (óptico)."""
    blob = f"{machine_name} {path_hint}".strip()
    if is_o_inspect_machine(blob):
        return "o_inspect"
    if _CMM_HINT_RE.search(blob) or blob:
        return "cmm"
    return "cmm"


def classify_slot_method(slot: Any) -> str | None:
    """Retorna ``cmm`` / ``o_inspect`` / ``bosello`` a partir do slot do projeto."""
    kind = getattr(slot, "source_kind", "") or ""
    document = getattr(slot, "document", None)
    if not kind and document is not None:
        kind = getattr(document, "source_kind", "") or ""
    path = str(getattr(slot, "source_pdf_path", "") or "")

    if kind == "insp_ect":
        return "bosello"
    # Sem kind explícito, só trata como Bosello se o caminho/nome for inequívoco.
    if not kind and _BOSELLO_RE.search(path) and not _O_INSPECT_RE.search(path):
        return "bosello"

    machine = ""
    if document is not None:
        dto = getattr(document, "raw_parsed_data", None)
        if isinstance(dto, dict):
            machine = str(dto.get("maquina_mmc") or "")
        elif dto is not None:
            machine = str(getattr(dto, "maquina_mmc", "") or "")
        if not machine:
            overrides = getattr(document, "parsed_overrides", None) or {}
            if isinstance(overrides, dict):
                machine = str(overrides.get("maquina_mmc") or "")
    return classify_calypso_method(machine, path_hint=path)


def collect_lab_methods(slots: Iterable[Any]) -> list[str]:
    """Métodos presentes no lote, na ordem canônica do laboratório."""
    found: set[str] = set()
    for slot in slots:
        method = classify_slot_method(slot)
        if method:
            found.add(method)
    return [key for key in LAB_METHOD_ORDER if key in found]


def method_short_labels(methods: list[str]) -> list[str]:
    return [LAB_METHOD_META[m][0] for m in methods if m in LAB_METHOD_META]


def method_descriptive_labels(methods: list[str]) -> list[str]:
    return [LAB_METHOD_META[m][1] for m in methods if m in LAB_METHOD_META]


def format_methods_phrase(methods: list[str], *, style: str = "descriptive") -> str:
    """Frase para o card MÉTODOS.

    ``style="descriptive"`` → ``óptico (O-inspect) e tomográfico (Bosello)``
    ``style="names"`` → ``O-inspect e Bosello``
    """
    labels = (
        method_descriptive_labels(methods)
        if style == "descriptive"
        else method_short_labels(methods)
    )
    return join_portuguese(labels) or "Não informado"


def format_analysis_type(methods: list[str]) -> str:
    has_dim = any(m in {"cmm", "o_inspect"} for m in methods)
    has_tomo = "bosello" in methods
    if has_dim and has_tomo:
        if "o_inspect" in methods and "cmm" not in methods:
            return "Óptica e tomográfica"
        return "Dimensional e tomográfica"
    if has_tomo:
        return "Tomográfica"
    if "o_inspect" in methods and "cmm" not in methods:
        return "Óptica"
    return "Dimensional"


def collect_equipment_labels(slots: Iterable[Any]) -> list[str]:
    """Nomes de equipamentos únicos (máquina MMC / Bosello)."""
    labels: list[str] = []
    seen: set[str] = set()
    for slot in slots:
        method = classify_slot_method(slot)
        label = ""
        if method == "bosello":
            label = "ZEISS BOSELLO MAX 80-150"
            document = getattr(slot, "document", None)
            if document is not None:
                dto = getattr(document, "raw_parsed_data", None)
                machine = ""
                if isinstance(dto, dict):
                    machine = str(dto.get("maquina_mmc") or "")
                elif dto is not None:
                    machine = str(getattr(dto, "maquina_mmc", "") or "")
                if machine.strip():
                    label = machine.strip()
        else:
            document = getattr(slot, "document", None)
            if document is not None:
                dto = getattr(document, "raw_parsed_data", None)
                if isinstance(dto, dict):
                    label = str(dto.get("maquina_mmc") or "").strip()
                elif dto is not None:
                    label = str(getattr(dto, "maquina_mmc", "") or "").strip()
            if not label:
                label = LAB_METHOD_META.get(method or "", ("", ""))[0]
        key = label.casefold()
        if not label or key in seen:
            continue
        seen.add(key)
        labels.append(label)
    return labels


def _dto_fora_summary(dto: Any) -> tuple[int, int]:
    """Retorna (fora, total) a partir do DTO dimensional."""
    if dto is None:
        return 0, 0
    series = getattr(dto, "series", None)
    if series is not None:
        total = int(getattr(dto, "numero_medicoes_cabecalho", 0) or 0)
        if total <= 0:
            total = sum(getattr(s, "n", 0) for s in series)
        fora = sum(getattr(s, "fora_count", 0) for s in series)
        return int(fora), int(total)
    items = list(getattr(dto, "itens_medicao", []) or [])
    total = int(getattr(dto, "numero_medicoes_cabecalho", 0) or len(items))
    fora = 0
    for item in items:
        status = ""
        if isinstance(item, dict):
            status = str(item.get("status") or "")
        else:
            status = str(getattr(item, "status", "") or "")
        if status.strip().lower() in {"fora", "nok", "out"}:
            fora += 1
    return fora, total


def build_mixed_introducao_metric_rows(
    slots: Iterable[Any],
    *,
    n_pecas: int | None = None,
    tomografia_status: str = "Sem indicações internas detectáveis",
    dimensional_dto: Any = None,
) -> list[dict[str, str]]:
    """Cards da introdução do relatório misto (estilo CEMSZ / análise híbrida)."""
    slot_list = list(slots)
    methods = collect_lab_methods(slot_list)
    if n_pecas is None:
        calypso = [
            s
            for s in slot_list
            if classify_slot_method(s) in {"cmm", "o_inspect"}
        ]
        n_pecas = max(1, len(calypso) or 1)

    fora, total = _dto_fora_summary(dimensional_dto)
    if total <= 0 and dimensional_dto is None:
        for slot in slot_list:
            if classify_slot_method(slot) in {"cmm", "o_inspect"}:
                document = getattr(slot, "document", None)
                if document is not None:
                    fora, total = _dto_fora_summary(getattr(document, "raw_parsed_data", None))
                    if total:
                        break

    if total > 0:
        dimensional_value = f"{fora} fora / {total} valores"
    else:
        dimensional_value = "Conforme relatório dimensional"

    amostra = f"{n_pecas} peça{'s' if n_pecas != 1 else ''}"
    equipamentos = join_portuguese(collect_equipment_labels(slot_list)) or "Não informado"

    return [
        {"id": "amostra", "label": "AMOSTRA", "value": amostra},
        {
            "id": "tipo_analise",
            "label": "TIPO DE ANÁLISE",
            "value": format_analysis_type(methods),
        },
        {
            "id": "metodos",
            "label": "MÉTODOS",
            "value": format_methods_phrase(methods, style="descriptive"),
        },
        {
            "id": "equipamentos",
            "label": "EQUIPAMENTOS",
            "value": equipamentos,
        },
        {
            "id": "dimensional",
            "label": "RESULTADOS DIMENSIONAIS",
            "value": dimensional_value,
        },
        {
            "id": "tomografia",
            "label": "TOMOGRAFIA",
            "value": tomografia_status,
        },
    ]
