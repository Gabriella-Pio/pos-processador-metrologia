from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..components.anchored_photo import AnchoredPhoto
from ..components.image_handler import ReportImageHandler
from ..components.photo_grid import _combined_caption, append_photo_grid, caption_for_path
from src.core.domain.image_workspace import lookup_foto_edits
from ..prose_helpers import format_prose_paragraph, get_section_prose, get_section_heading
from src.core.domain.placeholder_utils import resolve_placeholders
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import (
    INTRODUCAO_BLOCK_TITLES,
    SECTION_HEADING_DEFAULTS,
    default_falha_introducao_rows,
    default_table_rows,
    default_tomo_introducao_rows,
)

_CARD_BG = colors.HexColor("#EAF0FA")
_DEFAULT_PHOTO_CAPTION = "Peça avaliada em processo de medição na MMC"
_METRICS_TOTAL_WIDTH = 540


def _metrics_columns_for_count(n: int) -> int:
    """Escolhe colunas para evitar células vazias (ex.: 4 → 2×2)."""
    if n <= 1:
        return 1
    if n == 2 or n == 4:
        return 2
    return 3


class IntroducaoSection(BaseSection):
    """Capa no espírito do relatório CEM: prose (+ foto 50/50 se houver); métricas em grade."""

    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "introducao", SECTION_HEADING_DEFAULTS["introducao"],
        )
        story.append(anchored_section_title(
            heading, styles['subtitulo'], "introducao", contexto_extra.get("section_anchor_map"),
        ))
        ctx = contexto_extra.get("placeholder_context", {})
        componente_heading = resolve_placeholders("{componente}", ctx)
        story.append(Paragraph(componente_heading, styles['titulo']))
        story.append(Spacer(1, 8))

        prose = contexto_extra.get("section_prose", {}).get("introducao", {})
        tmpl = PROSE_TEMPLATES.get("introducao", {})

        estilo_bloco = ParagraphStyle(
            "IntroBlocoTitulo",
            parent=styles["texto"],
            fontName="Helvetica-Bold",
            spaceBefore=2,
            spaceAfter=2,
        )
        estilo_legenda = ParagraphStyle(
            "IntroFotoLegenda",
            parent=styles["texto"],
            fontSize=8,
            textColor=ReportTheme.COR_SECUNDARIA,
            alignment=1,
            spaceBefore=4,
        )
        estilo_card_label = ParagraphStyle(
            "IntroCardLabel",
            parent=styles["texto"],
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=ReportTheme.COR_SECUNDARIA,
            alignment=1,
            spaceAfter=2,
        )
        estilo_card_valor = ParagraphStyle(
            "IntroCardValor",
            parent=styles["texto"],
            fontName="Helvetica-Bold",
            fontSize=11,
            alignment=1,
        )

        blocos = (
            ("title_objetivo", "objetivo", "OBJETIVO"),
            ("title_escopo", "escopo", "ESCOPO DA ANÁLISE"),
            ("title_referencia", "referencia", "REFERÊNCIA DE MEDIÇÃO"),
        )
        left_flowables: list = []
        for title_key, body_key, default_title in blocos:
            title = str(prose.get(title_key) or INTRODUCAO_BLOCK_TITLES.get(title_key, default_title))
            body = get_section_prose(contexto_extra, "introducao", body_key, tmpl.get(body_key, ""))
            if not str(body or "").strip() and not str(title or "").strip():
                continue
            left_flowables.append(Paragraph(title, estilo_bloco))
            if body:
                left_flowables.append(Paragraph(format_prose_paragraph(body), styles["texto"]))
            left_flowables.append(Spacer(1, 8))

        # Só fotos associadas a esta seção — sem herdar de cabecalho/outras.
        fotos_secao = list(contexto_extra.get("fotos_secoes", {}).get("introducao", []) or [])
        if not fotos_secao:
            foto_legada = contexto_extra.get("opcoes_extras", {}).get("caminho_foto_peca")
            if foto_legada:
                fotos_secao = [foto_legada]

        foto_principal = fotos_secao[0] if fotos_secao else None
        has_photo = bool(foto_principal)

        captions = contexto_extra.get("foto_captions") or {}
        foto_edits = contexto_extra.get("foto_edits") or {}
        photo_anchors = contexto_extra.get("photo_anchors")

        if has_photo:
            edits = lookup_foto_edits(foto_edits, foto_principal)
            foto_element = ReportImageHandler.criar_elemento_foto(
                foto_principal,
                styles,
                largura=248,
                altura=168,
                preserve_original=True,
                edits=edits,
            )
            if photo_anchors is not None:
                foto = AnchoredPhoto(
                    foto_element,
                    section_id="introducao",
                    image_path=foto_principal,
                    image_id=str(edits.get("image_id") or ""),
                    anchor_list=photo_anchors,
                )
            else:
                foto = foto_element
            legenda = _combined_caption(
                captions,
                foto_principal,
                edits,
                default_caption=_DEFAULT_PHOTO_CAPTION,
            )
            photo_col_w = 254
            photo_table = Table([[foto]], colWidths=[photo_col_w])
            photo_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            right_flowables = [photo_table]
            if legenda:
                right_flowables.append(Paragraph(f"<i>{legenda}</i>", estilo_legenda))
            hero = Table(
                [[left_flowables or "", right_flowables]],
                colWidths=[270, 270],
            )
            hero.setStyle(TableStyle([
                ("VALIGN", (0, 0), (0, 0), "TOP"),
                ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("BOX", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#F7F9FC")),
            ]))
            story.append(hero)
            story.append(Spacer(1, 10))
        elif left_flowables:
            # Sem foto: conteúdo em largura total, sem moldura.
            for flowable in left_flowables:
                story.append(flowable)
            story.append(Spacer(1, 6))

        table_rows = (contexto_extra.get("table_rows") or {}).get("introducao", [])
        if not table_rows:
            kind = contexto_extra.get("report_kind")
            if kind == "tomografia":
                table_rows = default_tomo_introducao_rows()
            elif kind == "falha":
                table_rows = default_falha_introducao_rows()
            else:
                table_rows = default_table_rows("introducao")

        metric_cells = []
        for row in table_rows:
            label = resolve_placeholders(str(row.get("label", "")), ctx)
            value = resolve_placeholders(str(row.get("value", "")), ctx)
            metric_cells.append([
                Paragraph(label, estilo_card_label),
                Paragraph(value, estilo_card_valor),
            ])

        if metric_cells:
            self._append_responsive_metrics(story, metric_cells)
            story.append(Spacer(1, 8))

        extras = fotos_secao[1:]
        if extras:
            append_photo_grid(story, extras, captions, styles, img_height=140)

    @staticmethod
    def _append_responsive_metrics(story, metric_cells: list) -> None:
        """Grade sem células vazias: 4→2×2, 3/5/6/7…→até 3 colunas, última linha só com o que existe."""
        n = len(metric_cells)
        cols = _metrics_columns_for_count(n)
        index = 0
        while index < n:
            take = min(cols, n - index)
            chunk = metric_cells[index:index + take]
            index += take
            col_w = _METRICS_TOTAL_WIDTH / take
            band = Table([chunk], colWidths=[col_w] * take)
            band.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("BACKGROUND", (0, 0), (-1, -1), _CARD_BG),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
                ("BOX", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(band)
