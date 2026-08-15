"""Importação de imagens de PDFs Bosello (INSPECT) para a seção Tomografia."""
from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image

from src.core.domain.pdf_source import is_usable_source_pdf
from src.core.domain.image_workspace import new_image_id
from src.core.domain.ports import ReportDocument, ReportImage
from src.core.parser.insp_ect_parser import InspEctParser, RelatorioInspEctDto

TOMOGRAPHY_SECTION_ID = "tomografia"

# Limiar para descartar marcas quadradas do cabeçalho (ex.: Zeiss 295×295).
_MAX_LOGO_SIDE_PX = 400
_MIN_LOGO_ASPECT = 0.88
# Imagens com área < 12% da maior do mesmo PDF são tratadas como ícone decorativo.
_RELATIVE_AREA_RATIO = 0.12
_MIN_BATCH_AREA_FOR_RELATIVE = 400_000


def _image_metrics(path: Path) -> tuple[int, int, int] | None:
    try:
        with Image.open(path) as img:
            width, height = img.size
    except OSError:
        return None
    return width, height, width * height


def should_skip_bosello_image(
    width: int,
    height: int,
    *,
    max_area_in_batch: int | None = None,
) -> bool:
    """Descarta logos, faixas 1px e miniaturas irrelevantes do PDF Bosello."""
    area = width * height
    short_side = min(width, height)
    long_side = max(width, height)
    if short_side <= 2:
        return True
    if short_side < 120 or long_side < 120:
        return True
    if area < 40_000:
        return True
    aspect = short_side / long_side if long_side else 0.0
    if aspect >= _MIN_LOGO_ASPECT and long_side <= _MAX_LOGO_SIDE_PX:
        return True
    if (
        max_area_in_batch
        and max_area_in_batch >= _MIN_BATCH_AREA_FOR_RELATIVE
        and area < max_area_in_batch * _RELATIVE_AREA_RATIO
    ):
        return True
    return False


def is_likely_logo_or_icon(path: Path, *, max_area: int | None = None) -> bool:
    metrics = _image_metrics(path)
    if metrics is None:
        return False
    width, height, area = metrics
    return should_skip_bosello_image(width, height, max_area_in_batch=max_area or area)


def filter_importable_image_paths(paths: list[Path]) -> list[Path]:
    """Mantém só imagens úteis para Tomografia, ignorando logos repetidos do cabeçalho."""
    metrics: list[tuple[Path, int, int, int]] = []
    for path in paths:
        item = _image_metrics(path)
        if item is None:
            continue
        width, height, area = item
        metrics.append((path, width, height, area))
    if not metrics:
        return []
    max_area = max(item[3] for item in metrics)
    return [
        path
        for path, width, height, _area in metrics
        if not should_skip_bosello_image(width, height, max_area_in_batch=max_area)
    ]


_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def bosello_images_storage_dir(source_pdf: Path) -> Path:
    """Diretório persistente ao lado do PDF de origem."""
    stem = source_pdf.stem or "bosello"
    return source_pdf.parent / ".pos-metrologia" / "bosello-rendered" / stem


def list_cached_bosello_captures(source_pdf: Path) -> list[Path]:
    """Lista capturas já renderizadas em disco (sem reextrair do PDF)."""
    dest_dir = bosello_images_storage_dir(source_pdf)
    if not dest_dir.is_dir():
        return []
    return sorted(
        path
        for path in dest_dir.iterdir()
        if path.is_file() and path.suffix.lower() in _IMAGE_SUFFIXES
    )


def minimal_insp_ect_dto(source_pdf: Path) -> RelatorioInspEctDto:
    """DTO mínimo sem parse de texto — suficiente para export tomográfico com fotos."""
    component = source_pdf.stem.strip() or "Componente inspecionado"
    return RelatorioInspEctDto(componente=component, source_kind="insp_ect")


def render_bosello_capture_paths(
    source_pdf: Path,
    *,
    replace_library: bool = False,
) -> list[Path]:
    """Renderiza capturas do PDF e copia para armazenamento persistente.

    Com ``replace_library=False``, reutiliza o diretório em disco se já existir
    (reabertura de projeto sem reextrair imagens do PDF).
    """
    if not is_usable_source_pdf(source_pdf):
        return []

    if not replace_library:
        cached = list_cached_bosello_captures(source_pdf)
        if cached:
            return cached

    raw_paths = InspEctParser.extract_graphic_images_from_pdf(str(source_pdf))
    if not raw_paths:
        return []

    filtered_paths = filter_importable_image_paths([Path(raw_path) for raw_path in raw_paths])
    if not filtered_paths:
        return []

    dest_dir = bosello_images_storage_dir(source_pdf)
    if replace_library and dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    library: list[Path] = []
    next_index = 1
    for src in filtered_paths:
        if not src.is_file():
            continue
        dest = dest_dir / f"img_{next_index:02d}{src.suffix or '.png'}"
        next_index += 1
        shutil.copy2(src, dest)
        library.append(dest)
    return library


def ensure_bosello_capture_library(
    document: ReportDocument,
    source_pdf: Path,
    *,
    replace_library: bool = False,
) -> list[Path]:
    """Garante biblioteca de capturas no documento (sem alterar fotos em uso)."""
    if not replace_library and document.bosello_captured_paths:
        existing = [path for path in document.bosello_captured_paths if path.is_file()]
        if existing:
            document.bosello_captured_paths = existing
            return existing

    if not replace_library:
        cached = list_cached_bosello_captures(source_pdf)
        if cached:
            document.bosello_captured_paths = cached
            return cached

    library = render_bosello_capture_paths(source_pdf, replace_library=replace_library)
    document.bosello_captured_paths = library
    return library


def section_image_paths(document: ReportDocument, section_id: str) -> set[str]:
    return {
        str(img.image_path)
        for img in document.images
        if img.section_id == section_id
    }


def attach_bosello_captures(
    document: ReportDocument,
    paths: list[Path],
    section_id: str,
) -> int:
    """Adiciona capturas Bosello à seção, ignorando duplicatas."""
    in_section = section_image_paths(document, section_id)
    added = 0
    for path in paths:
        key = str(path)
        if key in in_section:
            continue
        document.images.append(
            ReportImage(
                image_path=path,
                section_id=section_id,
                image_id=new_image_id(),
                bosello_import=True,
            )
        )
        in_section.add(key)
        added += 1
    return added


def prune_bosello_logo_images(document: ReportDocument) -> int:
    """Remove logos já importados em sessões antigas."""
    bosello = [img for img in document.images if img.bosello_import]
    if not bosello:
        return 0
    keep_paths = {
        str(path)
        for path in filter_importable_image_paths([img.image_path for img in bosello])
    }
    before = len(document.images)
    document.images = [
        img
        for img in document.images
        if not img.bosello_import or str(img.image_path) in keep_paths
    ]
    if document.bosello_captured_paths:
        document.bosello_captured_paths = [
            path for path in document.bosello_captured_paths if str(path) in keep_paths
        ]
    return before - len(document.images)


def merge_bosello_images(
    document: ReportDocument,
    source_pdf: Path,
    *,
    replace_auto_imported: bool = False,
) -> int:
    """Popula biblioteca Bosello e anexa capturas à Tomografia na primeira importação."""
    if replace_auto_imported:
        document.images = [img for img in document.images if not img.bosello_import]

    library = ensure_bosello_capture_library(
        document,
        source_pdf,
        replace_library=replace_auto_imported,
    )
    if not library:
        return 0

    if any(img.bosello_import for img in document.images) and not replace_auto_imported:
        return 0

    attached = attach_bosello_captures(document, library, TOMOGRAPHY_SECTION_ID)
    prune_bosello_logo_images(document)
    return attached


def build_bosello_image_document(pdf_path: Path) -> ReportDocument:
    """Monta ``ReportDocument`` tomográfico a partir só das imagens do PDF Bosello."""
    from src.core.domain.ports import ReportDocument, TechnicalControlInfo

    if not is_usable_source_pdf(pdf_path):
        return build_manual_tomography_document(pdf_path.stem or "Componente avaliado")

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
    # Reutiliza cache em disco na reabertura; só reextrai se não houver capturas.
    merge_bosello_images(document, pdf_path, replace_auto_imported=False)
    return document


def refresh_bosello_auto_images_if_needed(document: ReportDocument) -> int:
    """Atualiza biblioteca legada e recupera capturas após migração de extração."""
    pdf = document.source_pdf_path
    if not is_usable_source_pdf(pdf):
        return 0
    path = Path(pdf)
    normalized_paths = [
        str(img.image_path).replace("\\", "/")
        for img in document.images
        if img.bosello_import or img.section_id == TOMOGRAPHY_SECTION_ID
    ]
    needs_refresh = any(img.bosello_import for img in document.images)
    needs_refresh = needs_refresh or any("/bosello-images/" in item for item in normalized_paths)
    if not needs_refresh:
        return 0

    library = ensure_bosello_capture_library(document, path, replace_library=True)
    library_keys = {str(item) for item in library}
    document.images = [
        img
        for img in document.images
        if not img.bosello_import or str(img.image_path) in library_keys
    ]
    if library and not any(
        img.section_id == TOMOGRAPHY_SECTION_ID and img.bosello_import
        for img in document.images
    ):
        return attach_bosello_captures(document, library, TOMOGRAPHY_SECTION_ID)
    return len(library)


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


def build_manual_falha_document(
    evaluated_component: str,
    *,
    client_project: str = "Cliente Padrão",
) -> ReportDocument:
    """Documento de análise de falha sem PDF — fotos ópticas/tomo via editor."""
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
        template_id="analise_falha",
    )


# Compatibilidade com testes e imports antigos.
def import_bosello_images(
    source_pdf: Path,
    *,
    section_id: str = TOMOGRAPHY_SECTION_ID,
    replace_auto_imported: bool = False,
) -> list[ReportImage]:
    library = render_bosello_capture_paths(source_pdf, replace_library=replace_auto_imported)
    return [
        ReportImage(
            image_path=path,
            section_id=section_id,
            image_id=new_image_id(),
            bosello_import=True,
        )
        for path in library
    ]
