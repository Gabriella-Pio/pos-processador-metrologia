"""Parser de relatórios ZEISS INSPECT (equipamento Bosello / tomografia)."""
from __future__ import annotations

import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

import fitz

from src.core.parser.table_extractor import MedicaoItemDto

_VP_ELEMENT_RE = re.compile(
    r"Defeito do volume\s+\d+\.Vp\.(\d+)",
    re.IGNORECASE,
)
_NUMBER_RE = re.compile(r"[+-]?\d+(?:[.,]\d+)?")


@dataclass
class VolumeDefectItem:
    element: str
    property_name: str
    deviation: str
    pore_index: int | None = None


@dataclass
class RelatorioInspEctDto:
    """DTO tomográfico compatível com os consumidores do DTO CALYPSO (duck typing)."""

    componente: str = "Não identificado"
    servico_oferecido: str = "Inspeção tomográfica industrial"
    maquina_mmc: str = "ZEISS BOSELLO MAX 80-150"
    numero_mmc: str = "Não informado"
    operador: str = "Não informado"
    data_hora: str = "Não informada"
    run: str = "Não informado"
    numero_medicoes_cabecalho: int = 0
    fora_tolerancia_cabecalho: int = 0
    duracao_medicao: str = "00:00:00,0"
    software: str = "ZEISS INSPECT"
    versao_software: str = "Não informada"
    itens_medicao: List[MedicaoItemDto] = field(default_factory=list)
    avisos_auditoria: List[str] = field(default_factory=list)
    texto_bruto_integral: str = ""
    source_kind: str = "insp_ect"
    volume_label: str = "Defeito do volume 1"
    volume_total_mm3: str = ""
    pore_count: int = 0
    defect_items: List[VolumeDefectItem] = field(default_factory=list)
    graphic_image_paths: List[str] = field(default_factory=list)
    equipamento_default: str = "ZEISS BOSELLO MAX 80-150"
    tensao_kv: str = "225"
    corrente_ma: str = "6,2"


class InspEctParser:
    """Extrai resumo de volume e poros (Vp) de PDFs ZEISS INSPECT."""

    _RENDER_ZOOM = 2.0
    _MIN_VIEWPORT_PT = 80.0

    @staticmethod
    def extract_graphic_images_from_pdf(caminho_pdf: str, max_pages: int = 3) -> list[str]:
        """Renderiza vistas visíveis do PDF (inclui eixos e overlays vetoriais)."""
        from src.core.domain.pdf_source import is_usable_source_pdf

        if not is_usable_source_pdf(caminho_pdf):
            return []
        doc = fitz.open(caminho_pdf)
        try:
            return InspEctParser._extract_graphic_images(doc, max_pages=max_pages)
        finally:
            doc.close()

    @staticmethod
    def parse(caminho_pdf: str, extract_images: bool = False) -> RelatorioInspEctDto:
        doc = fitz.open(caminho_pdf)
        try:
            texto_completo = "\n".join((page.get_text("text") or "") for page in doc)
            dto = RelatorioInspEctDto(texto_bruto_integral=texto_completo)
            InspEctParser._fill_software_version(dto, texto_completo)
            InspEctParser._fill_volume_summary(dto, texto_completo)
            dto.defect_items = InspEctParser._extract_vp_items(texto_completo)
            dto.pore_count = len(dto.defect_items) or dto.pore_count
            dto.numero_medicoes_cabecalho = dto.pore_count
            dto.itens_medicao = [
                MedicaoItemDto(
                    caracteristica=item.element,
                    tipo=item.property_name or "Vp",
                    valor_medido=item.deviation,
                    nominal="",
                    tol_superior="",
                    tol_inferior="",
                    desvio=item.deviation,
                    status="Dentro",
                )
                for item in dto.defect_items
            ]
            if not dto.componente or dto.componente == "Não identificado":
                stem = Path(caminho_pdf).stem.strip()
                dto.componente = stem or "Componente inspecionado"
            if extract_images:
                dto.graphic_image_paths = InspEctParser._extract_graphic_images(doc)
            return dto
        finally:
            doc.close()

    @staticmethod
    def _fill_software_version(dto: RelatorioInspEctDto, text: str) -> None:
        match = re.search(r"Generated with ZEISS INSP EC T?\s*(\d{4})", text, re.IGNORECASE)
        if match:
            dto.versao_software = match.group(1)
            dto.software = f"ZEISS INSPECT {match.group(1)}"

    @staticmethod
    def _fill_volume_summary(dto: RelatorioInspEctDto, text: str) -> None:
        # Prefer table-style block near V_all / #
        v_all = re.search(
            r"V_all\s*\n?\s*([+-]?\d+(?:[.,]\d+)?)\s+([+-]?\d+(?:[.,]\d+)?)\s*\n?\s*([+-]?\d+(?:[.,]\d+)?)",
            text,
            re.IGNORECASE,
        )
        if v_all:
            dto.volume_total_mm3 = v_all.group(2).replace(",", ".")
        else:
            # Page-1 layout: V_all then three lines
            alt = re.search(
                r"V_all\s*\n\s*([+-]?\d+(?:[.,]\d+)?)\s*\n\s*([+-]?\d+(?:[.,]\d+)?)\s*\n\s*([+-]?\d+(?:[.,]\d+)?)",
                text,
                re.IGNORECASE,
            )
            if alt:
                dto.volume_total_mm3 = alt.group(2).replace(",", ".")

        pore_header = re.search(
            r"#\s*\n?\s*([+-]?\d+)\s*\n?\s*([+-]?\d+)\s*\n?\s*([+-]?\d+)",
            text,
        )
        if pore_header:
            try:
                dto.pore_count = abs(int(pore_header.group(2)))
            except ValueError:
                pass

        label = re.search(r"(Defeito do volume\s+\d+)", text, re.IGNORECASE)
        if label:
            dto.volume_label = label.group(1).strip()

    @staticmethod
    def _extract_vp_items(text: str) -> list[VolumeDefectItem]:
        items: list[VolumeDefectItem] = []
        lines = [ln.strip() for ln in text.splitlines()]
        for index, line in enumerate(lines):
            match = _VP_ELEMENT_RE.search(line)
            if not match:
                continue
            pore_index = int(match.group(1))
            element = match.group(0).strip()
            property_name = "Vp"
            deviation = ""
            # Following lines often: "Vp" then "+44.82"
            window = lines[index + 1 : index + 6]
            for wline in window:
                if wline.lower() == "vp":
                    property_name = "Vp"
                    continue
                nums = _NUMBER_RE.findall(wline.replace(" ", ""))
                if nums and not deviation:
                    # Prefer last number on the line (Dev)
                    deviation = nums[-1].replace(",", ".")
                    break
            items.append(
                VolumeDefectItem(
                    element=element,
                    property_name=property_name,
                    deviation=deviation,
                    pore_index=pore_index,
                )
            )
        # Deduplicate by pore index keeping first occurrence
        seen: set[int] = set()
        unique: list[VolumeDefectItem] = []
        for item in items:
            key = item.pore_index if item.pore_index is not None else -1
            if key in seen:
                continue
            seen.add(key)
            unique.append(item)
        return unique

    @staticmethod
    def _graphic_page_indices(doc: fitz.Document, max_pages: int) -> list[int]:
        """Páginas com vistas gráficas: resumos (p.1/3) e grade 2×2 (p.2)."""
        return list(range(min(max_pages, doc.page_count)))

    @staticmethod
    def _extract_graphic_images(doc: fitz.Document, max_pages: int = 3) -> list[str]:
        """Renderiza regiões visíveis do PDF (inclui eixos, grid e rótulos vetoriais)."""
        out_dir = Path(tempfile.mkdtemp(prefix="insp_ect_imgs_"))
        paths: list[str] = []
        matrix = fitz.Matrix(InspEctParser._RENDER_ZOOM, InspEctParser._RENDER_ZOOM)
        page_indices = InspEctParser._graphic_page_indices(doc, max_pages)

        for page_index in page_indices:
            page = doc[page_index]
            seen_xrefs: set[int] = set()
            for img_index, img in enumerate(page.get_images(full=True)):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                try:
                    info = doc.extract_image(xref)
                    embedded_w = int(info.get("width", 0))
                    embedded_h = int(info.get("height", 0))
                except Exception:
                    continue
                if min(embedded_w, embedded_h) <= 2:
                    continue

                for rect_index, rect in enumerate(page.get_image_rects(xref)):
                    if (
                        rect.width < InspEctParser._MIN_VIEWPORT_PT
                        or rect.height < InspEctParser._MIN_VIEWPORT_PT
                    ):
                        continue
                    clip = fitz.Rect(rect) & page.rect
                    pix = page.get_pixmap(matrix=matrix, clip=clip, alpha=False)
                    target = out_dir / f"p{page_index + 1}_{img_index + 1}_{rect_index + 1}.png"
                    pix.save(str(target))
                    paths.append(str(target))
        return paths
