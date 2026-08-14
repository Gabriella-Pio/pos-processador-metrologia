"""Helpers de processamento em lote (parse / export / modos de relatório)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from src.core.domain.ports import ReportDocument, ReportExporter, ReportParser
from src.core.parser.source_kind import SourceKind, detect_source_kind

ReportMode = Literal["mmc_only", "tomo_only", "mixed", "falha", "auto"]

TEMPLATE_ID_MMC = "default"
TEMPLATE_ID_TOMO = "tomografia"
TEMPLATE_ID_FALHA = "analise_falha"


@dataclass
class ParsedSlot:
    path: Path
    source_kind: SourceKind
    document: ReportDocument
    template_id: str


def template_id_for_kind(source_kind: SourceKind) -> str:
    return TEMPLATE_ID_TOMO if source_kind == "insp_ect" else TEMPLATE_ID_MMC


def infer_report_mode(kinds: list[SourceKind]) -> ReportMode:
    unique = set(kinds)
    if unique == {"calypso"}:
        return "mmc_only"
    if unique == {"insp_ect"}:
        return "tomo_only"
    return "mixed"


def filter_paths_for_mode(
    paths: list[Path],
    report_mode: ReportMode,
) -> tuple[list[Path], list[tuple[Path, str]]]:
    """Retorna (aceitos, rejeitados com motivo)."""
    accepted: list[Path] = []
    rejected: list[tuple[Path, str]] = []
    for path in paths:
        kind = detect_source_kind(path)
        if report_mode == "tomo_only":
            accepted.append(path)
            continue
        if report_mode == "falha":
            accepted.append(path)
            continue
        if report_mode == "mmc_only" and kind != "calypso":
            rejected.append((path, "modo MMC aceita apenas PDFs CALYPSO"))
            continue
        accepted.append(path)
    return accepted, rejected


def parse_batch(
    parser: ReportParser,
    paths: list[Path],
    *,
    report_mode: ReportMode = "auto",
    client_project: str = "",
    default_component: str = "",
) -> tuple[list[ParsedSlot], list[tuple[Path, str]]]:
    """Parseia N PDFs, tipando source_kind e template efetivo por slot."""
    if report_mode == "auto":
        kinds = [detect_source_kind(p) for p in paths]
        report_mode = infer_report_mode(kinds)

    accepted, rejected = filter_paths_for_mode(paths, report_mode)
    slots: list[ParsedSlot] = []
    for path in accepted:
        document = parser.parse(path)
        if client_project:
            document.client_project = client_project
        if default_component:
            document.evaluated_component = default_component
        kind: SourceKind = document.source_kind if document.source_kind in ("calypso", "insp_ect") else detect_source_kind(path)
        document.source_kind = kind
        if report_mode == "mixed":
            template_id = template_id_for_kind(kind)
        elif report_mode == "tomo_only":
            template_id = TEMPLATE_ID_TOMO
        elif report_mode == "falha":
            template_id = TEMPLATE_ID_FALHA
        else:
            template_id = TEMPLATE_ID_MMC
        document.template_id = template_id
        slots.append(ParsedSlot(path=path, source_kind=kind, document=document, template_id=template_id))
    return slots, rejected


def export_batch(
    exporter: ReportExporter,
    documents: list[ReportDocument],
    output_dir: Path,
) -> list[Path]:
    """Exporta um PDF enriquecido por documento."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index, document in enumerate(documents, start=1):
        stem = document.source_pdf_path.stem if document.source_pdf_path else f"relatorio_{index}"
        out = output_dir / f"{stem}_enriquecido.pdf"
        paths.append(exporter.export(document, out))
    return paths
