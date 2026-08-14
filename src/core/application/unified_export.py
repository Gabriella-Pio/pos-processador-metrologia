"""Consolidação de projeto multi-aba em um único ReportDocument para export/preview."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.application.lab_methods import (
    build_mixed_introducao_metric_rows,
    collect_lab_methods,
    format_methods_phrase,
)
from src.core.application.piece_ordering import (
    piece_label_for_slot,
    sort_session_documents,
)
from src.core.application.statistical_aggregator import (
    build_estatistico_introducao_metric_rows,
    build_estatistico_section_notes,
    build_estatistico_sections_config,
    build_statistical_batch_dto,
    present_measure_tipos,
    statistical_escopo_phrase,
)
from src.core.application.unified_media import (
    copy_report_image,
    resolve_unified_layout_images,
)
from src.core.domain.image_workspace import new_image_id
from src.core.domain.mixed_template_defaults import (
    ESTATISTICO_PROSE_DEFAULTS,
    ESTATISTICO_TEMPLATE_ID,
    MIXED_PROSE_DEFAULTS,
    MIXED_SECTIONS_CONFIG,
    MIXED_TEMPLATE_ID,
)
from src.core.domain.ports import ReportDocument, ReportImage
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession


class UnifiedExportKind(Enum):
    STATISTICAL_MMC = "statistical_mmc"
    MIXED_MMC_BOSSELLO = "mixed_mmc_bosello"
    UNSUPPORTED = "unsupported"


class UnifiedExportError(Exception):
    """Estratégia unificada indisponível ou dados insuficientes."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def _merge_session_unified_overrides(
    document: ReportDocument,
    session: ProjectSession,
) -> None:
    """Aplica preferências do workspace unificado (gráficos, media_kinds, etc.)."""
    for section_id, overrides in (session.unified_section_overrides or {}).items():
        if not isinstance(overrides, dict):
            continue
        current = dict(document.section_overrides.get(section_id) or {})
        for key in ("media_kinds", "disabled_chart_ids", "section_title"):
            if key in overrides:
                current[key] = overrides[key]
        document.section_overrides[section_id] = current


def _parsed_slots(session: ProjectSession) -> list[ProjectDocumentSlot]:
    return [slot for slot in session.documents if slot.document is not None]


def _slot_kind(slot: ProjectDocumentSlot) -> str:
    if slot.source_kind in {"calypso", "insp_ect"}:
        return slot.source_kind
    doc = slot.document
    if doc is not None and doc.source_kind in {"calypso", "insp_ect"}:
        return doc.source_kind
    return "calypso"


def _session_has_tomo_images(session: ProjectSession) -> bool:
    """True se há capturas Bosello/tomo no store unificado ou nas peças."""
    for img in session.unified_images or []:
        if img.section_id == "tomografia" or img.bosello_import:
            return True
    for slot in session.documents:
        doc = slot.document
        if doc is None:
            continue
        if any(
            img.section_id == "tomografia" or img.bosello_import
            for img in doc.images
        ):
            return True
        if doc.bosello_captured_paths:
            return True
    return False


def resolve_unified_export_kind(session: ProjectSession) -> UnifiedExportKind:
    slots = _parsed_slots(session)
    if len(slots) < 2:
        return UnifiedExportKind.UNSUPPORTED

    kinds = [_slot_kind(slot) for slot in slots]
    calypso_count = sum(1 for kind in kinds if kind == "calypso")
    bosello_count = sum(1 for kind in kinds if kind == "insp_ect")

    if calypso_count >= 1 and bosello_count >= 1 and calypso_count + bosello_count == len(slots):
        return UnifiedExportKind.MIXED_MMC_BOSSELLO

    # Híbrido sem slot Bosello quando já existem fotos tomográficas no projeto.
    if (
        calypso_count == len(slots)
        and calypso_count >= 2
        and _session_has_tomo_images(session)
    ):
        return UnifiedExportKind.MIXED_MMC_BOSSELLO

    if calypso_count == len(slots) and calypso_count >= 2:
        return UnifiedExportKind.STATISTICAL_MMC

    return UnifiedExportKind.UNSUPPORTED


def unsupported_unified_message(session: ProjectSession) -> str:
    kind = resolve_unified_export_kind(session)
    if kind != UnifiedExportKind.UNSUPPORTED:
        return ""
    slots = _parsed_slots(session)
    if len(slots) < 2:
        return "O modo unificado exige pelo menos dois relatórios parseados no projeto."
    kinds = {_slot_kind(slot) for slot in slots}
    if "calypso" in kinds and "insp_ect" in kinds and len(kinds) > 2:
        return (
            "Projeto heterogêneo demais para consolidação automática. "
            "Separe lotes estatísticos (só MMC) de projetos híbridos (MMC + Bosello)."
        )
    return (
        "Não foi possível determinar a estratégia de consolidação. "
        "Use N PDFs CALYPSO (relatório estatístico) ou 1+ CALYPSO com 1+ Bosello (híbrido)."
    )


def build_unified_export_document(session: ProjectSession) -> ReportDocument:
    """Monta documento virtual consolidado para preview/export unificado."""
    kind = resolve_unified_export_kind(session)
    if kind == UnifiedExportKind.MIXED_MMC_BOSSELLO:
        return build_mixed_mmc_bosello_document(session)
    if kind == UnifiedExportKind.STATISTICAL_MMC:
        return build_statistical_mmc_document(session)
    raise UnifiedExportError(unsupported_unified_message(session))


def _clone_document(document: ReportDocument) -> ReportDocument:
    return replace(
        document,
        attachment_pdf_paths=list(document.attachment_pdf_paths),
        images=[
            replace(
                img,
                annotations=list(img.annotations),
                crop=img.crop,
            )
            for img in document.images
        ],
        bosello_captured_paths=list(document.bosello_captured_paths),
        version_history=list(document.version_history),
        section_overrides=deepcopy(document.section_overrides),
        parsed_overrides=deepcopy(document.parsed_overrides),
        custom_sections=deepcopy(document.custom_sections),
        deleted_section_ids=list(document.deleted_section_ids),
        extra_section_ids=list(getattr(document, "extra_section_ids", None) or []),
        section_order=list(document.section_order) if document.section_order else None,
        template_layout_override=(
            deepcopy(document.template_layout_override)
            if document.template_layout_override
            else None
        ),
        control_info=document.control_info,
        raw_parsed_data=document.raw_parsed_data,
    )


def _apply_prose_defaults(document: ReportDocument, defaults: dict[str, dict[str, str]]) -> None:
    for section_id, values in defaults.items():
        current = dict(document.section_overrides.get(section_id, {}))
        for key, value in values.items():
            if not str(current.get(key) or "").strip():
                current[key] = value
        document.section_overrides[section_id] = current


def _copy_bosello_images(source: ReportDocument, *, section_id: str = "tomografia") -> list[ReportImage]:
    images: list[ReportImage] = []
    for img in source.images:
        if img.section_id != section_id and not img.bosello_import:
            continue
        if img.section_id != section_id and img.bosello_import:
            # Capturas Bosello fora da seção alvo ainda podem ir para tomografia.
            target_section = section_id
        else:
            target_section = img.section_id if img.section_id == section_id else section_id
        if not img.bosello_import and img.section_id != section_id:
            continue
        images.append(
            replace(
                img,
                image_id=img.image_id or new_image_id(),
                section_id=target_section if img.bosello_import else img.section_id,
                annotations=list(img.annotations),
            )
        )
    if images:
        return images
    # Fallback: biblioteca de capturas ainda não anexada à seção.
    for path in source.bosello_captured_paths:
        if not Path(path).is_file():
            continue
        images.append(
            ReportImage(
                image_path=Path(path),
                section_id=section_id,
                image_id=new_image_id(),
                bosello_import=True,
            )
        )
    return images


def build_mixed_mmc_bosello_document(session: ProjectSession) -> ReportDocument:
    """1+ CALYPSO + (1+ Bosello OU fotos tomo já no store) → relatório híbrido."""
    slots = _parsed_slots(session)
    calypso_slots = [slot for slot in slots if _slot_kind(slot) == "calypso"]
    bosello_slots = [slot for slot in slots if _slot_kind(slot) == "insp_ect"]
    has_tomo_images = _session_has_tomo_images(session)
    if not calypso_slots:
        raise UnifiedExportError(
            "Relatório híbrido exige pelo menos um PDF CALYPSO."
        )
    if not bosello_slots and not has_tomo_images:
        raise UnifiedExportError(
            "Relatório híbrido exige um PDF Bosello ou capturas tomográficas já importadas."
        )

    base_slot = calypso_slots[0]
    assert base_slot.document is not None
    document = _clone_document(base_slot.document)
    document.client_project = session.client_project or document.client_project
    document.evaluated_component = (
        base_slot.evaluated_component
        or document.evaluated_component
        or session.display_name
        or "Componente"
    )
    document.template_id = MIXED_TEMPLATE_ID
    document.template_layout_override = deepcopy(MIXED_SECTIONS_CONFIG)
    document.source_kind = "calypso"

    # Remove imagens tomográficas herdadas do slot MMC; reaplica a partir do store
    # unificado (se houver) ou das capturas Bosello das peças.
    layout_images = resolve_unified_layout_images(
        session,
        calypso_slots,
        layout=MIXED_SECTIONS_CONFIG,
    )
    document.images = [
        img
        for img in layout_images
        if img.section_id != "tomografia" and not img.bosello_import
    ]
    has_unified_tomo = any(
        img.section_id == "tomografia" or img.bosello_import
        for img in (session.unified_images or [])
    )
    if has_unified_tomo:
        document.images.extend(
            copy_report_image(img)
            for img in session.unified_images
            if img.section_id == "tomografia" or img.bosello_import
        )
        for img in session.unified_images:
            if (img.section_id == "tomografia" or img.bosello_import) and img.image_path not in document.bosello_captured_paths:
                document.bosello_captured_paths.append(img.image_path)
    elif bosello_slots:
        for bosello_slot in bosello_slots:
            assert bosello_slot.document is not None
            document.images.extend(_copy_bosello_images(bosello_slot.document))
            for path in bosello_slot.document.bosello_captured_paths:
                if path not in document.bosello_captured_paths:
                    document.bosello_captured_paths.append(path)
    else:
        for slot in calypso_slots:
            assert slot.document is not None
            document.images.extend(_copy_bosello_images(slot.document))
            for path in slot.document.bosello_captured_paths:
                if path not in document.bosello_captured_paths:
                    document.bosello_captured_paths.append(path)

    if not any(img.section_id == "tomografia" for img in document.images):
        raise UnifiedExportError(
            "Nenhuma captura Bosello disponível para a seção Tomografia. "
            "Importe o PDF Bosello e adicione fotos antes de exportar o PDF unificado."
        )

    calypso_paths = [
        slot.source_pdf_path
        for slot in calypso_slots
        if slot.source_pdf_path and str(slot.source_pdf_path).strip()
    ]
    # Unificado: todos os PDFs de origem do lote (peças MMC + Bosello).
    all_source_paths = [
        slot.source_pdf_path
        for slot in slots
        if slot.source_pdf_path and str(slot.source_pdf_path).strip()
    ]
    document.attachment_pdf_paths = list(dict.fromkeys(all_source_paths or calypso_paths))
    document.source_pdf_path = calypso_paths[0] if calypso_paths else document.source_pdf_path

    methods = collect_lab_methods(slots)
    metodos_frase = format_methods_phrase(methods, style="descriptive")
    prose = deepcopy(MIXED_PROSE_DEFAULTS)
    for section_values in prose.values():
        for key, value in list(section_values.items()):
            section_values[key] = (
                str(value)
                .replace("{componente}", document.evaluated_component or "Componente")
                .replace("{metodos}", metodos_frase)
            )
    document.section_overrides = {}
    _apply_prose_defaults(document, prose)

    intro = dict(document.section_overrides.get("introducao") or {})
    intro["table_rows"] = build_mixed_introducao_metric_rows(
        slots,
        n_pecas=max(1, len(calypso_slots)),
        dimensional_dto=document.raw_parsed_data,
    )
    document.section_overrides["introducao"] = intro

    grafica_overrides = dict(document.section_overrides.get("grafica", {}))
    kinds = list(grafica_overrides.get("media_kinds") or [])
    for kind in ("graphics", "photos"):
        if kind not in kinds:
            kinds.append(kind)
    grafica_overrides["media_kinds"] = kinds
    document.section_overrides["grafica"] = grafica_overrides

    # Garante mídia de fotos na tomografia.
    tomo_overrides = dict(document.section_overrides.get("tomografia", {}))
    kinds = list(tomo_overrides.get("media_kinds") or [])
    if "photos" not in kinds:
        kinds.append("photos")
    tomo_overrides["media_kinds"] = kinds
    document.section_overrides["tomografia"] = tomo_overrides
    document.deleted_section_ids = [
        sid
        for sid in session.unified_deleted_section_ids
        if sid not in {"cabecalho", "introducao"}
    ]
    _merge_session_unified_overrides(document, session)
    return document


def _copy_report_image(image: ReportImage) -> ReportImage:
    return copy_report_image(image)


def _collect_layout_images(
    slots: list[ProjectDocumentSlot],
    *,
    layout: dict[str, dict],
) -> list[ReportImage]:
    from src.core.application.unified_media import collect_layout_images_from_slots

    return collect_layout_images_from_slots(slots, layout=layout)


def _dto_attr(dto: Any, name: str, default: str = "") -> str:
    if dto is None:
        return default
    value = getattr(dto, name, None)
    return str(value).strip() if value is not None else default


def build_statistical_mmc_document(session: ProjectSession) -> ReportDocument:
    """N× CALYPSO → relatório estatístico consolidado."""
    sort_session_documents(session)
    slots = _parsed_slots(session)
    calypso_slots = [slot for slot in slots if _slot_kind(slot) == "calypso"]
    if len(calypso_slots) < 2:
        raise UnifiedExportError("Relatório estatístico exige pelo menos duas peças CALYPSO.")

    piece_labels: list[str] = []
    piece_items: list[tuple[int, list[Any]]] = []
    operador = ""
    maquina = ""
    for index, slot in enumerate(calypso_slots, start=1):
        assert slot.document is not None
        piece_labels.append(piece_label_for_slot(slot, index))
        dto = slot.document.raw_parsed_data
        items = list(getattr(dto, "itens_medicao", []) or [])
        if not items and slot.document.parsed_overrides.get("itens_medicao"):
            items = list(slot.document.parsed_overrides["itens_medicao"])
        piece_items.append((index, items))
        if not operador:
            operador = _dto_attr(dto, "operador")
        if not maquina:
            maquina = _dto_attr(dto, "maquina_mmc")

    first = calypso_slots[0]
    assert first.document is not None
    document = _clone_document(first.document)
    componente = (
        first.evaluated_component
        or document.evaluated_component
        or session.display_name
        or "Componente"
    )
    cliente = session.client_project or document.client_project
    batch = build_statistical_batch_dto(
        componente=componente,
        cliente=cliente,
        piece_labels=piece_labels,
        piece_items=piece_items,
        operador=operador,
        maquina_mmc=maquina,
    )
    if not batch.series:
        raise UnifiedExportError(
            "Não foi possível agregar características comuns entre as peças do lote."
        )

    document.client_project = cliente
    document.evaluated_component = componente
    document.template_id = ESTATISTICO_TEMPLATE_ID
    measure_tipos = present_measure_tipos(batch.series)
    layout = build_estatistico_sections_config(measure_tipos)
    document.template_layout_override = layout
    document.source_kind = "calypso"
    document.raw_parsed_data = batch
    document.images = resolve_unified_layout_images(
        session,
        calypso_slots,
        layout=layout,
    )
    document.bosello_captured_paths = []
    calypso_paths = [
        slot.source_pdf_path
        for slot in calypso_slots
        if slot.source_pdf_path and str(slot.source_pdf_path).strip()
    ]
    document.attachment_pdf_paths = list(dict.fromkeys(calypso_paths))
    document.source_pdf_path = calypso_paths[0] if calypso_paths else document.source_pdf_path
    document.custom_sections = []
    # Preferências do PDF unificado (ex.: desligar histórico/anexos).
    document.deleted_section_ids = [
        sid
        for sid in session.unified_deleted_section_ids
        if sid not in {"cabecalho", "introducao"}
    ]
    document.section_order = None

    n_pecas = str(len(piece_labels))
    escopo = statistical_escopo_phrase(measure_tipos)
    prose = deepcopy(ESTATISTICO_PROSE_DEFAULTS)
    for section_values in prose.values():
        for key, value in list(section_values.items()):
            section_values[key] = (
                value.replace("{n_pecas}", n_pecas)
                .replace("{componente}", componente)
                .replace("{escopo_medidas}", escopo)
            )
    document.section_overrides = {}
    _apply_prose_defaults(document, prose)

    # Métricas dinâmicas da capa (tipos presentes no lote).
    intro = dict(document.section_overrides.get("introducao") or {})
    intro["table_rows"] = build_estatistico_introducao_metric_rows(batch)
    document.section_overrides["introducao"] = intro

    # Interpretação no intro (a nota fica vazia para não duplicar no rodapé).
    interp = _build_statistical_interpretation(batch)
    document.section_overrides["interpretacao"] = {
        "intro": interp,
        "nota": "",
    }
    document.section_overrides["conclusao"] = {
        "texto": (
            f"Foi realizada a consolidação estatística das medições referentes a "
            f"{componente}, contemplando {n_pecas} peças e {batch.numero_medicoes_cabecalho} "
            f"valores medidos no lote."
        ),
        "nota": "",
    }
    document.section_overrides["identificacao"] = {
        "section_title": "IDENTIFICAÇÃO E CONDIÇÕES DE MEDIÇÃO",
        "intro": (
            "Dados consolidados do lote e condições de medição extraídas dos "
            "relatórios ZEISS CALYPSO (referência da primeira peça ordenada)."
        ),
        "table_rows": _statistical_identificacao_rows(
            componente=componente,
            cliente=cliente,
            n_pecas=len(piece_labels),
            batch=batch,
            first_document=first.document,
        ),
        "nota": "",
    }

    # Notas de rodapé automáticas por tipo (só quando há ocorrências fora).
    for section_id, note in build_estatistico_section_notes(batch).items():
        current = dict(document.section_overrides.get(section_id) or {})
        if not str(current.get("nota") or "").strip():
            current["nota"] = note
            document.section_overrides[section_id] = current

    for chart_section in ("estat_graficos", "estat_graficos_comp"):
        if layout.get(chart_section, {}).get("enabled"):
            chart_overrides = dict(document.section_overrides.get(chart_section) or {})
            chart_overrides.setdefault("media_kinds", ["graphics"])
            document.section_overrides[chart_section] = chart_overrides
    _merge_session_unified_overrides(document, session)
    return document


def _statistical_identificacao_rows(
    *,
    componente: str,
    cliente: str,
    n_pecas: int,
    batch,
    first_document: ReportDocument,
) -> list[dict[str, str]]:
    """Linhas da seção Identificação e condições de medição (DTO CALYPSO da 1ª peça)."""
    dto = getattr(first_document, "raw_parsed_data", None)
    software = _dto_attr(dto, "software") or batch.software or "ZEISS CALYPSO"
    versao = _dto_attr(dto, "versao_software")
    if versao and versao not in software:
        software = f"{software} {versao}".strip()
    return [
        {"id": "cliente", "label": "Cliente / Projeto", "value": cliente},
        {"id": "componente", "label": "Componente avaliado", "value": componente},
        {"id": "n_pecas", "label": "Quantidade de peças", "value": str(n_pecas)},
        {
            "id": "maquina",
            "label": "Máquina de medição",
            "value": batch.maquina_mmc or _dto_attr(dto, "maquina_mmc") or "Não identificada",
        },
        {
            "id": "numero_mmc",
            "label": "Número da MMC",
            "value": _dto_attr(dto, "numero_mmc") or "Não informado",
        },
        {"id": "software", "label": "Software", "value": software},
        {
            "id": "operador",
            "label": "Operador",
            "value": batch.operador or _dto_attr(dto, "operador") or "Não informado",
        },
        {
            "id": "data_hora",
            "label": "Data/Hora da medição (referência)",
            "value": _dto_attr(dto, "data_hora") or "Não informada",
        },
        {
            "id": "total_valores",
            "label": "Total de valores medidos",
            "value": str(batch.numero_medicoes_cabecalho),
        },
    ]


def _build_statistical_interpretation(batch) -> str:
    lines: list[str] = []
    total = batch.numero_medicoes_cabecalho
    n_pecas = len(batch.piece_labels)
    lines.append(
        f"A análise consolidou {total} valores medidos nas {n_pecas} peças avaliadas."
    )
    fora_series = [s for s in batch.series if s.fora_count > 0]
    if not fora_series:
        lines.append(
            "Todas as características permaneceram dentro dos limites informados nos "
            "relatórios de origem."
        )
    else:
        for series in fora_series:
            lines.append(
                f"“{series.display_name}” apresentou {series.fora_count} ocorrência(s) "
                f"fora dos limites informados no relatório de origem."
            )
    return "\n\n".join(lines)
