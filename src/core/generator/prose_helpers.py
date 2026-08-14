"""Helpers para leitura de prosa editável no generator."""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether, Paragraph, Spacer, Table, TableStyle

from src.core.domain.markdown_prose import markdown_to_reportlab_html
from src.core.domain.placeholder_utils import resolve_placeholders
from src.core.domain.section_numbering import format_numbered_heading, strip_number_prefix
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS
from .constants import ReportTheme


def format_prose_paragraph(text: str) -> str:
    """Converte markdown leve do editor para HTML do ReportLab."""
    return markdown_to_reportlab_html(str(text or ""))


def get_section_prose(contexto_extra: dict, section_id: str, key: str, default: str = "") -> str:
    prose = contexto_extra.get("section_prose", {}).get(section_id, {})
    value = prose.get(key)
    if value is not None and str(value).strip():
        raw = str(value)
    else:
        raw = default
    ctx = contexto_extra.get("placeholder_context", {})
    return resolve_placeholders(raw, ctx)


def get_section_heading(contexto_extra: dict, section_id: str, default: str) -> str:
    prose = contexto_extra.get("section_prose", {}).get(section_id, {})
    default_base = strip_number_prefix(default)
    stored = prose.get("section_title")
    if stored is not None and str(stored).strip():
        raw = str(stored)
    else:
        raw = default_base
    ctx = contexto_extra.get("placeholder_context", {})
    resolved = resolve_placeholders(raw, ctx)
    number_map = contexto_extra.get("section_number_map", {})
    return format_numbered_heading(section_id, resolved, number_map)


def append_anchored_section_title(story, styles, contexto_extra: dict, section_id: str) -> None:
    from .sections.base import append_section_title

    heading = get_section_heading(
        contexto_extra,
        section_id,
        SECTION_HEADING_DEFAULTS[section_id],
    )
    append_section_title(
        story,
        heading,
        styles["secao"],
        section_id,
        contexto_extra.get("section_anchor_map"),
    )


def append_section_prose_paragraph(
    story,
    styles,
    contexto_extra: dict,
    section_id: str,
    key: str,
    default: str = "",
    *,
    spacer_after: float = 0,
) -> bool:
    text = get_section_prose(contexto_extra, section_id, key, default)
    if not str(text or "").strip():
        return False
    story.append(Paragraph(format_prose_paragraph(text), styles["texto"]))
    if spacer_after:
        story.append(Spacer(1, spacer_after))
    return True


def render_section_header(
    story,
    styles,
    contexto_extra: dict,
    section_id: str,
    *,
    prose_key: str = "intro",
    prose_default: str = "",
    spacer_after_intro: float = 4,
) -> None:
    """Título numerado da seção + parágrafo introdutório opcional."""
    append_anchored_section_title(story, styles, contexto_extra, section_id)
    if prose_key:
        append_section_prose_paragraph(
            story,
            styles,
            contexto_extra,
            section_id,
            prose_key,
            prose_default,
            spacer_after=spacer_after_intro,
        )


def render_kv_table(
    story,
    styles,
    table_rows: list[dict],
    ctx: dict,
    *,
    col_widths: tuple[int, int] = (200, 340),
    bold_value_row_ids: frozenset[str] | None = None,
    value_for_empty: dict[str, str] | None = None,
    default_empty_value: str = "",
    fallback_row: tuple[str, str] | None = None,
    spacer_after: float = 10,
) -> None:
    """Tabela chave–valor com estilo padrão (identificação / controle técnico)."""
    bold_value_row_ids = bold_value_row_ids or frozenset()
    value_for_empty = value_for_empty or {}
    linhas = []
    for row in table_rows:
        label = resolve_placeholders(str(row.get("label", "")), ctx)
        value = resolve_placeholders(str(row.get("value", "")), ctx)
        row_id = str(row.get("id", ""))
        if not value:
            if value_for_empty and row_id in value_for_empty:
                value = value_for_empty[row_id]
            elif default_empty_value:
                value = default_empty_value
        if row_id in bold_value_row_ids and value:
            value = f"<b>{value}</b>"
        linhas.append([
            Paragraph(f"<b>{label}</b>", styles["texto"]),
            Paragraph(value or "", styles["texto"]),
        ])

    if not linhas and fallback_row:
        linhas = [[
            Paragraph(f"<b>{fallback_row[0]}</b>", styles["texto"]),
            Paragraph(fallback_row[1], styles["texto"]),
        ]]

    if not linhas:
        return

    tabela = Table(linhas, colWidths=list(col_widths))
    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F2F4F7")]),
            ("BOX", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, ReportTheme.COR_LINHA),
            ("PADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(KeepTogether([tabela]))
    if spacer_after:
        story.append(Spacer(1, spacer_after))


def append_section_footer_note(story, styles, section_id: str, contexto_extra: dict) -> None:
    """Nota de rodapé editável — comum a todas as seções."""
    # Estatístico: interpretação já sai completa no intro (evita itálico duplicado).
    if section_id == "interpretacao" and contexto_extra.get("report_kind") == "estatistico":
        return
    prose = contexto_extra.get("section_prose", {}).get(section_id, {}) or {}
    if section_id == "introducao":
        fallback = str(
            prose.get("nota")
            or prose.get("nota_deteccao")
            or prose.get("intro")
            or ""
        )
    else:
        fallback = str(prose.get("nota") or "")
    note = get_section_prose(contexto_extra, section_id, "nota", fallback)
    if not str(note or "").strip() and section_id == "introducao":
        note = get_section_prose(
            contexto_extra,
            section_id,
            "nota_deteccao",
            str(prose.get("nota_deteccao") or prose.get("intro") or ""),
        )
    if not str(note or "").strip():
        return
    # Em outras seções, intro pode ser o corpo — evita imprimir a mesma frase 2×.
    # Na introdução o corpo é objetivo/escopo/referencia; `intro` não é desenhado,
    # então NÃO comparar nota==intro (senão a nota tomográfica some).
    if section_id != "introducao":
        intro = str(prose.get("intro") or "").strip()
        if intro and str(note).strip() == intro:
            return
    estilo = ParagraphStyle(
        f"SectionNota_{section_id}",
        parent=styles["texto"],
        fontSize=8,
        textColor=ReportTheme.COR_SECUNDARIA,
        leading=11,
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph(f"<i>{format_prose_paragraph(note)}</i>", estilo))
    story.append(Spacer(1, 6))


def append_approval_signature(story, styles, contexto_extra: dict) -> bool:
    """Linha de assinatura + rótulo, sempre após o corpo do relatório (antes dos anexos).

    O texto continua editável em ``conclusao.aprovacao``; a posição no PDF é fixa
    no engine (abaixo de todas as seções de conteúdo, acima de anexos).
    """
    from reportlab.platypus import HRFlowable

    from src.core.domain.report_field_registry import PROSE_TEMPLATES

    default_label = PROSE_TEMPLATES.get("conclusao", {}).get(
        "aprovacao", "Aprovação / Coordenação CEM"
    )
    aprovacao = get_section_prose(
        contexto_extra,
        "conclusao",
        "aprovacao",
        default_label,
    )
    if not aprovacao.strip():
        return False
    story.append(Spacer(1, 48))
    story.append(
        HRFlowable(
            width="42%",
            thickness=0.7,
            color=colors.HexColor("#555555"),
            spaceBefore=0,
            spaceAfter=6,
            hAlign="CENTER",
        )
    )
    estilo = ParagraphStyle(
        "AprovacaoCemLabel",
        parent=styles["texto"],
        alignment=1,
        fontSize=9,
        textColor=colors.HexColor("#333333"),
        spaceBefore=0,
        spaceAfter=4,
    )
    story.append(Paragraph(aprovacao, estilo))
    return True
