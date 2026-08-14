"""Grade de fotos 2 colunas para o PDF (imagem + legenda por path)."""
from __future__ import annotations

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from src.core.domain.image_workspace import format_number_marker_legend, lookup_foto_edits
from src.core.generator.components.anchored_photo import AnchoredPhoto
from src.core.generator.components.image_handler import ReportImageHandler
from src.core.generator.constants import ReportTheme


def caption_for_path(captions: dict | None, path: str, *, fallback: str = "") -> str:
    """Resolve legenda por path da foto."""
    if not captions:
        return fallback
    for key in (path, str(path)):
        value = captions.get(key)
        if value:
            return str(value)
    name = path.rsplit("/", 1)[-1]
    for key, value in (captions or {}).items():
        if key.rsplit("/", 1)[-1] == name and value:
            return str(value)
    return fallback


def _combined_caption(
    captions: dict | None,
    path: str,
    edits: dict | None,
    *,
    default_caption: str = "",
) -> str:
    base = caption_for_path(captions, path, fallback=default_caption)
    marker_legend = format_number_marker_legend((edits or {}).get("annotations"))
    if base and marker_legend:
        return f"{base}<br/><i>{marker_legend}</i>"
    if marker_legend:
        return f"<i>{marker_legend}</i>"
    return base


def _photo_context(contexto_extra: dict | None, section_id: str) -> tuple[dict, list | None]:
    extra = contexto_extra or {}
    return extra.get("foto_edits") or {}, extra.get("photo_anchors")


def _caption_style(styles: dict, *, centered: bool):
    base = styles.get("legenda_foto") or styles.get("texto")
    if not centered or base is None:
        return base
    return ParagraphStyle(
        f"{getattr(base, 'name', 'legenda')}_centro",
        parent=base,
        alignment=TA_CENTER,
    )


def _build_photo_element(
    path: str,
    styles: dict,
    *,
    largura: int,
    altura: int,
    section_id: str = "",
    foto_edits: dict | None = None,
    photo_anchors: list | None = None,
):
    edits = lookup_foto_edits(foto_edits, path)
    elemento = ReportImageHandler.criar_elemento_foto(
        path,
        styles,
        largura=largura,
        altura=altura,
        preserve_original=True,
        edits=edits,
    )
    if section_id and photo_anchors is not None:
        return AnchoredPhoto(
            elemento,
            section_id=section_id,
            image_path=path,
            image_id=str(edits.get("image_id") or ""),
            anchor_list=photo_anchors,
        )
    return elemento


def _append_centered_photo_block(
    story,
    photo_element,
    caption_text: str,
    styles: dict,
    *,
    total_width: float,
) -> None:
    """Centraliza foto (+ legenda) na largura útil — 1 foto ou sobra ímpar da grade.

    Lista de flowables na célula (sem KeepTogether): KeepTogether+AnchoredPhoto
    dentro de Table estoura a altura no ReportLab (~2^24).
    """
    cells: list = [photo_element]
    if caption_text:
        cells.append(Paragraph(caption_text, _caption_style(styles, centered=True)))
    band = Table([[cells]], colWidths=[total_width])
    band.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    story.append(band)
    story.append(Spacer(1, 8))


def append_photo_grid(
    story,
    paths: list[str],
    captions: dict | None,
    styles: dict,
    *,
    section_id: str = "",
    foto_edits: dict | None = None,
    photo_anchors: list | None = None,
    total_width: float = 540,
    img_height: int = 150,
    default_caption: str = "",
) -> None:
    """Adiciona fotos ao story: 1 = centralizada; 2+ = grade 2 colunas (sobra centralizada)."""
    clean = [p for p in paths if p]
    if not clean:
        return

    if len(clean) == 1:
        path = clean[0]
        # Largura confortável para foto isolada (não estica até a margem).
        img_w = int(min(total_width * 0.72, 400))
        photo = _build_photo_element(
            path,
            styles,
            largura=img_w,
            altura=img_height,
            section_id=section_id,
            foto_edits=foto_edits,
            photo_anchors=photo_anchors,
        )
        legenda = _combined_caption(
            captions,
            path,
            lookup_foto_edits(foto_edits, path),
            default_caption=default_caption,
        )
        _append_centered_photo_block(
            story,
            photo,
            legenda,
            styles,
            total_width=total_width,
        )
        return

    col_w = total_width / 2
    img_w = int(col_w - 8)
    cells: list = []
    for path in clean:
        flowables = [
            _build_photo_element(
                path,
                styles,
                largura=img_w,
                altura=img_height,
                section_id=section_id,
                foto_edits=foto_edits,
                photo_anchors=photo_anchors,
            )
        ]
        edits = lookup_foto_edits(foto_edits, path)
        legenda = _combined_caption(captions, path, edits, default_caption=default_caption)
        if legenda:
            flowables.append(Paragraph(legenda, _caption_style(styles, centered=False)))
        cells.append(flowables)

    index = 0
    while index < len(cells):
        take = min(2, len(cells) - index)
        row = cells[index : index + take]
        index += take
        if take == 1:
            # Sobra ímpar (3ª, 5ª…): centraliza na largura total.
            path = clean[index - 1]
            photo = row[0][0]
            caption_text = _combined_caption(
                captions,
                path,
                lookup_foto_edits(foto_edits, path),
                default_caption=default_caption,
            )
            _append_centered_photo_block(
                story,
                photo,
                caption_text,
                styles,
                total_width=total_width,
            )
            continue
        band = Table([row], colWidths=[col_w, col_w])
        band.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("BOX", (0, 0), (-1, -1), 0.4, ReportTheme.COR_LINHA),
                ]
            )
        )
        story.append(band)
        story.append(Spacer(1, 6))


def append_section_photos_if_any(story, styles, section_id: str, contexto_extra: dict) -> None:
    """Fotos adicionadas no workspace em seções sem renderer nativo de imagem."""
    fotos = list((contexto_extra.get("fotos_secoes") or {}).get(section_id, []) or [])
    if not fotos:
        return
    captions = contexto_extra.get("foto_captions") or {}
    foto_edits, photo_anchors = _photo_context(contexto_extra, section_id)
    story.append(Spacer(1, 4))
    append_photo_grid(
        story,
        fotos,
        captions,
        styles,
        section_id=section_id,
        foto_edits=foto_edits,
        photo_anchors=photo_anchors,
    )
