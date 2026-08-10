"""Grade de fotos 2 colunas para o PDF (imagem + legenda por path)."""
from __future__ import annotations

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
    """Adiciona fotos ao story: 1 = largura cheia; 2+ = grade 2 colunas."""
    clean = [p for p in paths if p]
    if not clean:
        return

    estilo_legenda = styles.get("legenda_foto") or styles.get("texto")

    if len(clean) == 1:
        path = clean[0]
        img_w = int(total_width)
        story.append(
            _build_photo_element(
                path,
                styles,
                largura=img_w,
                altura=img_height,
                section_id=section_id,
                foto_edits=foto_edits,
                photo_anchors=photo_anchors,
            )
        )
        legenda = _combined_caption(
            captions,
            path,
            lookup_foto_edits(foto_edits, path),
            default_caption=default_caption,
        )
        if legenda:
            story.append(Paragraph(legenda, estilo_legenda))
        story.append(Spacer(1, 8))
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
            flowables.append(Paragraph(legenda, estilo_legenda))
        cells.append(flowables)

    index = 0
    while index < len(cells):
        take = min(2, len(cells) - index)
        row = cells[index:index + take]
        index += take
        if take == 1:
            band = Table([row + [""]], colWidths=[col_w, col_w])
        else:
            band = Table([row], colWidths=[col_w, col_w])
        band.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("BOX", (0, 0), (-1, -1), 0.4, ReportTheme.COR_LINHA),
        ]))
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
