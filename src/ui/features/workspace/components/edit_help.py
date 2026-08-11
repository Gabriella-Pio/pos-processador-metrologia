"""Textos de ajuda contextual para o editor de seções."""
from __future__ import annotations

import html
import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY

_GENERAL = """\
**Edição de seção**
• O preview à direita atualiza automaticamente após cada alteração.
• Use **Restaurar** para voltar ao valor padrão do template.
"""

_PLACEHOLDERS = """\
**Dados globais ({chave})**
• Digite `{` para ver a lista de dados globais e escolher um.
• Chips como `{componente}` aparecem abaixo do campo — clique no ✕ para remover.
• Edite valores globais em **Dados do relatório** no Sumário.
"""

_TABLE_ROWS = """\
**Linhas da tabela**
• Cada linha espelha o preview: **[rótulo] [valor]**.
• Arraste ⠿ para reordenar linhas.
• Valores podem usar placeholders `{client_project}`, `{componente}`, etc.
"""

_MEDIA = """\
**Fotografias, gráficos e tabelas**
• Use a barra superior para inserir ou localizar mídia.
• Arraste PNG/JPG para Fotografias ou clique no botão para escolher arquivo.
• Ferramentas de anotação ficam disponíveis quando há fotos na seção.
"""

_SECTION_HINTS: dict[str, str] = {
    "introducao": (
        "Edite Objetivo, Escopo, Referência e a nota de rodapé no Conteúdo. "
        "Na aba Fotografias, defina a legenda e remova fotos se necessário. "
        "Na Tabela, edite as métricas (Amostra, Valores, Fora…)."
    ),
    "identificacao": (
        "Edite o texto introdutório, o título e as linhas da tabela de identificação."
    ),
    "resultados": "Edite o texto introdutório e a grade de medições extraída do CALYPSO.",
    "grafica": "Texto introdutório e fotografias/gráficos do componente.",
    "tomografia": "Texto introdutório e fotografias da inspeção tomográfica.",
    "interpretacao": (
        "Texto introdutório, itens de interpretação e nota de rodapé. "
        "No template, edite o parágrafo inicial; os itens por medição são gerados "
        "automaticamente no workspace."
    ),
    "conclusao": (
        "Texto da conclusão e o rótulo centrado de Aprovação / Coordenação CEM "
        "(espaço para assinatura gov.br posterior)."
    ),
    "anexos": (
        "Lista e anexa ao final do relatório o(s) PDF(s) importado(s) pelo usuário."
    ),
    "controle_tecnico": "Edite o título, o subtítulo e as linhas da tabela de responsáveis (arraste para reordenar).",
}


def build_help_text(section_id: str, *, has_table: bool = False, has_media: bool = False) -> str:
    parts = [_GENERAL.strip()]
    section_hint = _SECTION_HINTS.get(section_id)
    if section_hint:
        parts.append(section_hint)
    parts.append(_PLACEHOLDERS.strip())
    if has_table or section_id in ("introducao", "identificacao", "controle_tecnico", "resultados"):
        parts.append(_TABLE_ROWS.strip())
    if has_media or section_id in ("introducao", "grafica", "tomografia"):
        parts.append(_MEDIA.strip())
    return "\n\n".join(parts)


def _inline_rich(text: str) -> str:
    """Converte **negrito** e `{chaves}` para rich text do QLabel."""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(
        r"\{([^}]+)\}",
        rf'<span style="color:{PALETTE.senai_orange}; font-family:monospace;">'
        r"{\1}</span>",
        escaped,
    )
    return escaped


def _section_title_label(title: str) -> QLabel:
    label = QLabel(title)
    label.setStyleSheet(
        f"color: {PALETTE.text_primary}; font-size: {TYPOGRAPHY.size_body}px; "
        f"font-weight: {TYPOGRAPHY.weight_semibold}; background: transparent; border: none;"
    )
    return label


def _bullet_label(text: str) -> QLabel:
    label = QLabel(f"• {_inline_rich(text)}")
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setStyleSheet(
        f"color: {PALETTE.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
        f"background: transparent; border: none; padding-left: 2px;"
    )
    return label


def _hint_label(text: str) -> QLabel:
    label = QLabel(_inline_rich(text))
    label.setWordWrap(True)
    label.setTextFormat(Qt.TextFormat.RichText)
    label.setStyleSheet(
        f"color: {PALETTE.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
        f"background: transparent; border: none; line-height: 1.45;"
    )
    return label


def _section_card(title: str, bullets: list[str], prose: list[str]) -> QFrame:
    frame = QFrame()
    frame.setObjectName("AppDialogInfoSection")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
    layout.setSpacing(SPACING.sm)
    layout.addWidget(_section_title_label(title))
    for bullet in bullets:
        layout.addWidget(_bullet_label(bullet))
    for paragraph in prose:
        layout.addWidget(_hint_label(paragraph))
    return frame


def build_help_content_widget(text: str, parent: QWidget | None = None) -> QWidget:
    """Monta o corpo da ajuda com seções e bullets (sem QTextEdit)."""
    page = QWidget(parent)
    page.setObjectName("AppDialogInfoContent")
    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(SPACING.md)

    for raw_block in text.strip().split("\n\n"):
        block = raw_block.strip()
        if not block:
            continue

        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        first = lines[0]
        if first.startswith("**") and first.endswith("**"):
            title = first.strip("*").strip()
            bullets: list[str] = []
            prose: list[str] = []
            for line in lines[1:]:
                if line.startswith("•"):
                    bullets.append(line.lstrip("•").strip())
                else:
                    prose.append(line)
            outer.addWidget(_section_card(title, bullets, prose))
        else:
            outer.addWidget(_hint_label(" ".join(lines)))

    outer.addStretch(1)
    return page
