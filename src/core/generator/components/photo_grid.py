"""Grade de fotos 2 colunas para o PDF (imagem + legenda por path)."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from src.core.generator.components.image_handler import ReportImageHandler
from src.core.generator.constants import ReportTheme


def caption_for_path(captions: dict | None, path: str, *, fallback: str = "") -> str:
    """Resolve legenda por path da foto."""
    if not captions:
        return fallback
    value = captions.get(path)
    if value:
        return str(value)
    # Fallback legado: mapa antigo section_id → caption (só se path não bater)
    return fallback


def append_photo_grid(
    story,
    paths: list[str],
    captions: dict | None,
    styles: dict,
    *,
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
            ReportImageHandler.criar_elemento_foto(
                path, styles, largura=img_w, altura=img_height,
            )
        )
        legenda = caption_for_path(captions, path, fallback=default_caption)
        if legenda:
            story.append(Paragraph(f"<i>{legenda}</i>", estilo_legenda))
        story.append(Spacer(1, 8))
        return

    col_w = total_width / 2
    img_w = int(col_w - 8)
    cells: list = []
    for path in clean:
        flowables = [
            ReportImageHandler.criar_elemento_foto(
                path, styles, largura=img_w, altura=img_height,
            )
        ]
        legenda = caption_for_path(captions, path, fallback=default_caption)
        if legenda:
            flowables.append(Paragraph(f"<i>{legenda}</i>", estilo_legenda))
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
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
        ]))
        story.append(band)
        story.append(Spacer(1, 6))
