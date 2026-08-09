"""Importação de imagens de PDFs Bosello (INSP ECT) para a seção Tomografia."""
from __future__ import annotations

import shutil
from pathlib import Path

from src.core.domain.ports import ReportDocument, ReportImage
from src.core.parser.insp_ect_parser import InspEctParser, RelatorioInspEctDto

TOMOGRAPHY_SECTION_ID = "tomografia"


def bosello_images_storage_dir(source_pdf: Path) -> Path:
    """Diretório persistente ao lado do PDF de origem."""
    stem = source_pdf.stem or "bosello"
    return source_pdf.parent / ".pos-metrologia" / "bosello-images" / stem


def minimal_insp_ect_dto(source_pdf: Path) -> RelatorioInspEctDto:
    """DTO mínimo sem parse de texto — suficiente para export tomográfico com fotos."""
    component = source_pdf.stem.strip() or "Componente inspecionado"
    return RelatorioInspEctDto(componente=component, source_kind="insp_ect")


def import_bosello_images(
    source_pdf: Path,
    *,
    section_id: str = TOMOGRAPHY_SECTION_ID,
    replace_auto_imported: bool = False,
) -> list[ReportImage]:
    """Extrai imagens do PDF e copia para armazenamento persistente."""
    raw_paths = InspEctParser.extract_graphic_images_from_pdf(str(source_pdf))
    if not raw_paths:
        return []

    dest_dir = bosello_images_storage_dir(source_pdf)
    dest_dir.mkdir(parents=True, exist_ok=True)

    imported: list[ReportImage] = []
    for index, raw_path in enumerate(raw_paths, start=1):
        src = Path(raw_path)
        if not src.is_file():
            continue
        dest = dest_dir / f"img_{index:02d}{src.suffix or '.png'}"
        shutil.copy2(src, dest)
        imported.append(
            ReportImage(
                image_path=dest,
                section_id=section_id,
                bosello_import=True,
            )
        )
    return imported


def merge_bosello_images(
    document: ReportDocument,
    source_pdf: Path,
    *,
    replace_auto_imported: bool = False,
) -> int:
    """Anexa imagens Bosello ao documento sem remover fotos manuais."""
    if replace_auto_imported:
        document.images = [img for img in document.images if not img.bosello_import]

    existing_auto = {
        str(img.image_path)
        for img in document.images
        if img.bosello_import
    }
    if existing_auto and not replace_auto_imported:
        return 0

    imported = import_bosello_images(source_pdf)
    if not imported:
        return 0

    document.images.extend(imported)
    return len(imported)


def build_bosello_image_document(pdf_path: Path) -> ReportDocument:
    """Monta ``ReportDocument`` tomográfico a partir só das imagens do PDF Bosello."""
    from src.core.domain.ports import ReportDocument, TechnicalControlInfo

    dto = minimal_insp_ect_dto(pdf_path)
    document = ReportDocument(
        source_pdf_path=pdf_path,
        client_project="Cliente Padrão",
        evaluated_component=dto.componente,
        control_info=TechnicalControlInfo(
            measured_by="Operador Metrologista",
            reviewed_by="Supervisor SENAI",
            approved_by="",
            role="Técnico de Laboratório",
            institutional_email="metrologia@senaigo.com.br",
        ),
        raw_parsed_data=dto,
        source_kind="insp_ect",
        template_id="tomografia",
    )
    merge_bosello_images(document, pdf_path)
    return document


def build_manual_tomography_document(
    evaluated_component: str,
    *,
    client_project: str = "Cliente Padrão",
) -> ReportDocument:
    """Documento tomográfico sem PDF de origem — fotos só via aba Fotografias."""
    from src.core.domain.ports import ReportDocument, TechnicalControlInfo

    component = evaluated_component.strip() or "Componente avaliado"
    dto = RelatorioInspEctDto(componente=component, source_kind="insp_ect")
    return ReportDocument(
        source_pdf_path=Path(),
        client_project=client_project,
        evaluated_component=component,
        control_info=TechnicalControlInfo(
            measured_by="Operador Metrologista",
            reviewed_by="Supervisor SENAI",
            approved_by="",
            role="Técnico de Laboratório",
            institutional_email="metrologia@senaigo.com.br",
        ),
        raw_parsed_data=dto,
        source_kind="insp_ect",
        template_id="tomografia",
    )
