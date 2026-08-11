"""Diálogo de ajuda (atalhos) e painel de acessibilidade."""
from __future__ import annotations

from enum import Enum
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.accessibility import FONT_SCALE_PRESETS, AppearanceManager, AppearanceSettings
from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.feedback import confirm_action, confirm_dangerous_action, show_info
from src.ui.components.inputs import ThemedComboBox
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, heading_style, caption_style
from src.core.application.storage_cleanup import (
    DEFAULT_DB_PATH,
    audit_storage,
    clear_bosello_rendered_cache,
    clear_orphan_section_photos,
    clear_preview_temp,
    delete_stale_projects,
    format_storage_size,
    list_stale_projects,
)


class HelpDialogMode(Enum):
    HELP = "help"
    PREFERENCES = "preferences"


ShortcutRow = tuple[str, str, str]


SHORTCUT_GROUPS: tuple[tuple[str, tuple[ShortcutRow, ...]], ...] = (
    (
        "Navegação",
        (
            ("Alt+←", "Voltar", "Retorna à tela anterior"),
            ("Alt+→", "Avançar", "Avança na navegação"),
            ("F11", "Tela cheia", "Alterna janela maximizada / tela cheia"),
        ),
    ),
    (
        "Início",
        (
            ("Ctrl+N", "Novo arquivo", "Abre a criação de novo projeto"),
            ("Ctrl+T", "Novo template", "Cria um template de relatório"),
            ("Ctrl+K", "Buscar", "Foca o campo de busca na Home"),
            ("Esc", "Limpar busca", "Limpa busca e filtros ativos"),
        ),
    ),
    (
        "Ajuda",
        (
            ("F1", "Ajuda", "Abre este painel de ajuda e acessibilidade"),
        ),
    ),
)

HELP_TIPS: tuple[str, ...] = (
    "Use os filtros da Home para refinar arquivos por período, projeto ou componente.",
    "Clique no logo SENAI ou em «Início» no breadcrumb para voltar à tela principal.",
    "Templates definem a estrutura reutilizável dos relatórios exportados.",
    "Preferências de tema, contraste e fonte são salvas automaticamente.",
)


def _scroll_page(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    return scroll


class HelpAccessibilityDialog(AppDialog):
    """Atalhos (modo Ajuda) ou Acessibilidade + Armazenamento (modo Preferências)."""

    def __init__(
        self,
        parent=None,
        *,
        mode: HelpDialogMode = HelpDialogMode.HELP,
        initial_tab: int = 0,
        db_path: str | Path = DEFAULT_DB_PATH,
    ) -> None:
        if mode is HelpDialogMode.HELP:
            super().__init__(parent, window_title="Ajuda", minimum_width=580)
            self.setMinimumSize(580, 460)
            self.resize(640, 520)
        else:
            super().__init__(parent, window_title="Preferências", minimum_width=580)
            self.setMinimumSize(580, 480)
            self.resize(640, 560)
        self._mode = mode
        self._db_path = Path(db_path)
        self._manager = AppearanceManager.instance()
        self._draft = self._manager.settings
        self._build_ui()
        if hasattr(self, "_tabs"):
            self._tabs.setCurrentIndex(initial_tab)
        self._sync_controls_from_settings()

    def _build_ui(self) -> None:
        layout = self.create_root_layout()

        if self._mode is HelpDialogMode.HELP:
            self.add_dialog_header(
                layout,
                "Ajuda",
                "Atalhos de teclado e dicas de uso do laboratório.",
            )
        else:
            self.add_dialog_header(
                layout,
                "Preferências",
                "Ajustes visuais, acessibilidade e limpeza de armazenamento local.",
            )

        if self._mode is HelpDialogMode.HELP:
            layout.addWidget(_scroll_page(self._build_shortcuts_tab()), stretch=1)
        else:
            self._tabs = QTabWidget()
            self._tabs.setDocumentMode(True)
            self._tabs.addTab(
                _scroll_page(self._build_accessibility_tab()),
                "Acessibilidade",
            )
            self._tabs.addTab(
                _scroll_page(self._build_storage_tab()),
                "Armazenamento",
            )
            layout.addWidget(self._tabs, stretch=1)

        self.add_dialog_divider(layout)

        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        if self._mode is HelpDialogMode.PREFERENCES:
            reset_btn = SecondaryButton("Restaurar padrão")
            reset_btn.clicked.connect(self._reset_defaults)
            footer.addWidget(reset_btn)
        footer.addStretch(1)
        close_btn = PrimaryButton("Fechar")
        close_btn.setMinimumWidth(120)
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)
        layout.addLayout(footer)

    def _build_shortcuts_tab(self) -> QWidget:
        p = PALETTE
        page = QWidget()
        page.setStyleSheet(f"background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        outer.setSpacing(SPACING.lg)

        for group_title, rows in SHORTCUT_GROUPS:
            outer.addWidget(self._group_title(group_title))
            outer.addWidget(self._shortcut_table(rows))

        outer.addWidget(self._group_title("Dicas"))
        tips_frame = QFrame()
        tips_frame.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        tips_layout = QVBoxLayout(tips_frame)
        tips_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        tips_layout.setSpacing(SPACING.sm)
        for tip in HELP_TIPS:
            row = QLabel(f"• {tip}")
            row.setWordWrap(True)
            row.setStyleSheet(
                f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
                f"background: transparent; border: none;"
            )
            tips_layout.addWidget(row)
        outer.addWidget(tips_frame)
        outer.addStretch(1)
        return page

    def _group_title(self, text: str) -> QLabel:
        label = QLabel(text.upper())
        label.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: 11px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; letter-spacing: 0.8px; "
            f"background: transparent; border: none; margin-bottom: 2px;"
        )
        return label

    def _shortcut_table(self, rows: tuple[ShortcutRow, ...]) -> QFrame:
        p = PALETTE
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.xs)

        for index, (keys, action, description) in enumerate(rows):
            row = QHBoxLayout()
            row.setSpacing(SPACING.md)

            key_label = QLabel(keys)
            key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            key_label.setMinimumWidth(76)
            key_label.setStyleSheet(
                f"color: {p.senai_orange}; font-family: monospace; font-size: 12px; "
                f"font-weight: {TYPOGRAPHY.weight_bold}; background: rgba(240,67,30,0.12); "
                f"border: 1px solid rgba(240,67,30,0.25); border-radius: {SPACING.radius_sm}px; "
                f"padding: 6px 8px;"
            )

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            action_label = QLabel(action)
            action_label.setStyleSheet(
                f"color: {p.text_primary}; font-weight: {TYPOGRAPHY.weight_semibold}; "
                f"background: transparent; border: none;"
            )
            desc_label = QLabel(description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet(
                f"color: {p.text_muted}; font-size: 12px; background: transparent; border: none;"
            )
            text_col.addWidget(action_label)
            text_col.addWidget(desc_label)

            row.addWidget(key_label, 0, Qt.AlignmentFlag.AlignTop)
            row.addLayout(text_col, stretch=1)
            layout.addLayout(row)

            if index < len(rows) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setFixedHeight(1)
                sep.setStyleSheet(f"background: {p.border_subtle}; border: none;")
                layout.addWidget(sep)

        return frame

    def _build_accessibility_tab(self) -> QWidget:
        p = PALETTE
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        outer.setSpacing(SPACING.lg)

        outer.addWidget(self._settings_section(
            "Tema",
            "Escolha entre aparência escura ou clara.",
        ))
        theme_row = QHBoxLayout()
        theme_row.setSpacing(SPACING.xl)
        self._theme_group = QButtonGroup(self)
        self._theme_dark = QRadioButton("Escuro")
        self._theme_light = QRadioButton("Claro")
        for index, btn in enumerate((self._theme_dark, self._theme_light)):
            self._theme_group.addButton(btn, index)
            theme_row.addWidget(btn)
        theme_row.addStretch(1)
        outer.addLayout(theme_row)

        outer.addWidget(self._settings_section(
            "Contraste",
            "Alto contraste melhora legibilidade de textos e bordas.",
        ))
        contrast_row = QHBoxLayout()
        contrast_row.setSpacing(SPACING.xl)
        self._contrast_group = QButtonGroup(self)
        self._contrast_normal = QRadioButton("Normal")
        self._contrast_high = QRadioButton("Alto contraste")
        for index, btn in enumerate((self._contrast_normal, self._contrast_high)):
            self._contrast_group.addButton(btn, index)
            contrast_row.addWidget(btn)
        contrast_row.addStretch(1)
        outer.addLayout(contrast_row)

        outer.addWidget(self._settings_section(
            "Tamanho da fonte",
            "Ajuste o zoom global da interface.",
        ))
        self._font_combo = ThemedComboBox()
        self._font_combo.setMinimumHeight(44)
        for label, scale in FONT_SCALE_PRESETS:
            self._font_combo.addItem(label, scale)
        outer.addWidget(self._font_combo)

        hint = QLabel(
            "Alterações aplicadas imediatamente e salvas para a próxima sessão."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color: {p.text_muted}; font-size: 12px; background: transparent; border: none;"
        )
        outer.addWidget(hint)

        preview = QFrame()
        preview.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        preview_layout.setSpacing(SPACING.xs)
        preview_caption = QLabel("PRÉ-VISUALIZAÇÃO")
        preview_caption.setStyleSheet(
            f"color: {p.text_muted}; font-size: 10px; font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"letter-spacing: 0.6px; background: transparent; border: none;"
        )
        self._preview_title = QLabel("Relatório de Metrologia")
        self._preview_body = QLabel(
            "Texto de exemplo — dimensões, tolerâncias e resultados de medição."
        )
        self._preview_body.setWordWrap(True)
        preview_layout.addWidget(preview_caption)
        preview_layout.addWidget(self._preview_title)
        preview_layout.addWidget(self._preview_body)
        outer.addWidget(preview)

        self._theme_group.idClicked.connect(lambda _id: self._apply_draft())
        self._contrast_group.idClicked.connect(lambda _id: self._apply_draft())
        self._font_combo.currentIndexChanged.connect(lambda _idx: self._apply_draft())

        return page

    def _build_storage_tab(self) -> QWidget:
        p = PALETTE
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(SPACING.lg, SPACING.lg, SPACING.lg, SPACING.lg)
        outer.setSpacing(SPACING.lg)

        intro = QLabel(
            "Libere espaço em disco removendo caches temporários e dados órfãos. "
            "PDFs ZEISS originais e exports salvos não são apagados."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet(caption_style())
        outer.addWidget(intro)

        self._storage_summary_host = QVBoxLayout()
        self._storage_summary_host.setSpacing(SPACING.sm)
        outer.addLayout(self._storage_summary_host)

        refresh_btn = SecondaryButton("Atualizar estimativas")
        refresh_btn.clicked.connect(self._refresh_storage_audit)
        outer.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        outer.addWidget(self._group_title("Limpeza"))
        outer.addWidget(self._storage_action_row(
            "Cache de preview",
            "Remove imagens temporárias de preview e exportação.",
            "Limpar cache de preview",
            self._on_clear_preview_temp,
        ))
        outer.addWidget(self._storage_action_row(
            "Capturas Bosello",
            "Apaga renderizações ao lado dos PDFs. Reimporte o Bosello para reconstruir.",
            "Limpar Bosello",
            self._on_clear_bosello_cache,
            dangerous=True,
        ))
        outer.addWidget(self._storage_action_row(
            "Fotos órfãs",
            "Remove cópias em .pos-metrologia/section-photos sem referência nas sessões.",
            "Limpar fotos órfãs",
            self._on_clear_orphan_photos,
            dangerous=True,
        ))

        outer.addWidget(self._settings_section(
            "Projetos em andamento",
            "Exclui registros antigos da Home — não apaga PDFs nem exports no disco.",
        ))
        stale_row = QHBoxLayout()
        stale_row.setSpacing(SPACING.sm)
        self._stale_months_combo = ThemedComboBox()
        for months in (3, 6, 12):
            self._stale_months_combo.addItem(f"Mais de {months} meses", months)
        self._stale_months_combo.setCurrentIndex(1)
        self._stale_months_combo.currentIndexChanged.connect(
            lambda _idx: self._refresh_storage_audit()
        )
        stale_row.addWidget(self._stale_months_combo)
        self._stale_projects_label = QLabel()
        self._stale_projects_label.setStyleSheet(caption_style())
        stale_row.addWidget(self._stale_projects_label, stretch=1)
        outer.addLayout(stale_row)

        delete_projects_btn = SecondaryButton("Excluir projetos antigos…")
        delete_projects_btn.clicked.connect(self._on_delete_stale_projects)
        outer.addWidget(delete_projects_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addStretch(1)

        self._refresh_storage_audit()
        return page

    def _storage_action_row(
        self,
        title: str,
        description: str,
        button_label: str,
        handler,
        *,
        dangerous: bool = False,
    ) -> QFrame:
        p = PALETTE
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: {p.bg_surface}; border: 1px solid {p.border}; "
            f"border-radius: {SPACING.radius_md}px; }}"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {p.text_primary}; font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"background: transparent; border: none;"
        )
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(caption_style())
        text_col.addWidget(title_label)
        text_col.addWidget(desc_label)
        layout.addLayout(text_col, stretch=1)

        btn = SecondaryButton(button_label)
        if dangerous:
            btn.setProperty("danger", True)
        btn.clicked.connect(handler)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignTop)
        return frame

    def _clear_storage_summary(self) -> None:
        while self._storage_summary_host.count():
            item = self._storage_summary_host.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _refresh_storage_audit(self) -> None:
        self._clear_storage_summary()
        for category in audit_storage(self._db_path):
            row = QLabel(
                f"{category.label}: {category.file_count} arquivo(s) · "
                f"{format_storage_size(category.total_bytes)}"
            )
            row.setWordWrap(True)
            row.setStyleSheet(caption_style())
            self._storage_summary_host.addWidget(row)
            detail = QLabel(category.description)
            detail.setWordWrap(True)
            detail.setStyleSheet(
                f"color: {PALETTE.text_muted}; font-size: 12px; "
                f"background: transparent; border: none; margin-bottom: 4px;"
            )
            self._storage_summary_host.addWidget(detail)

        months = int(self._stale_months_combo.currentData() or 6)
        stale = list_stale_projects(self._db_path, months=months)
        if stale:
            self._stale_projects_label.setText(
                f"{len(stale)} projeto(s) elegível(is) para exclusão."
            )
        else:
            self._stale_projects_label.setText(
                f"Nenhum projeto com mais de {months} meses sem atualização."
            )

    def _on_clear_preview_temp(self) -> None:
        categories = {item.key: item for item in audit_storage(self._db_path)}
        size_label = format_storage_size(categories["preview_temp"].total_bytes)
        if not confirm_action(
            self,
            "Limpar cache de preview?",
            f"Serão removidos aproximadamente {size_label} de arquivos temporários.",
        ):
            return
        freed = clear_preview_temp()
        show_info(self, "Cache limpo", f"Liberação estimada: {format_storage_size(freed)}.")
        self._refresh_storage_audit()

    def _on_clear_bosello_cache(self) -> None:
        categories = {item.key: item for item in audit_storage(self._db_path)}
        size_label = format_storage_size(categories["bosello_cache"].total_bytes)
        if not confirm_dangerous_action(
            self,
            "Limpar capturas Bosello?",
            f"Isso remove {size_label} de renderizações locais.\n\n"
            "Para recuperar, reimporte o PDF Bosello no projeto.",
        ):
            return
        freed = clear_bosello_rendered_cache(self._db_path)
        show_info(self, "Bosello limpo", f"Liberação estimada: {format_storage_size(freed)}.")
        self._refresh_storage_audit()

    def _on_clear_orphan_photos(self) -> None:
        if not confirm_dangerous_action(
            self,
            "Limpar fotos órfãs?",
            "Remove cópias em section-photos que não estão referenciadas nas sessões salvas.",
        ):
            return
        freed = clear_orphan_section_photos(self._db_path)
        show_info(self, "Fotos órfãs removidas", f"Liberação estimada: {format_storage_size(freed)}.")
        self._refresh_storage_audit()

    def _on_delete_stale_projects(self) -> None:
        months = int(self._stale_months_combo.currentData() or 6)
        stale = list_stale_projects(self._db_path, months=months)
        if not stale:
            show_info(
                self,
                "Nada para excluir",
                f"Não há projetos em andamento com mais de {months} meses sem atualização.",
            )
            return
        preview = "\n".join(f"• {row.display_name}" for row in stale[:8])
        if len(stale) > 8:
            preview += f"\n• … e mais {len(stale) - 8}"
        if not confirm_dangerous_action(
            self,
            "Excluir projetos antigos?",
            f"{len(stale)} projeto(s) serão removidos da Home:\n\n{preview}\n\n"
            "Exports e PDFs no disco não serão apagados.",
        ):
            return
        removed = delete_stale_projects(self._db_path, months=months)
        show_info(self, "Projetos excluídos", f"{removed} registro(s) removido(s) do histórico.")
        self._refresh_storage_audit()

    def _settings_section(self, title: str, description: str) -> QWidget:
        p = PALETTE
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        title_label = QLabel(title.upper())
        title_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: 11px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; letter-spacing: 0.8px; "
            f"background: transparent; border: none;"
        )
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet(
            f"color: {p.text_secondary}; font-size: 12px; background: transparent; border: none;"
        )
        layout.addWidget(title_label)
        layout.addWidget(desc_label)
        return box

    def _sync_controls_from_settings(self) -> None:
        if self._mode is HelpDialogMode.HELP:
            return
        settings = self._draft
        self._theme_group.blockSignals(True)
        self._contrast_group.blockSignals(True)
        self._font_combo.blockSignals(True)
        try:
            self._theme_dark.setChecked(settings.theme == "dark")
            self._theme_light.setChecked(settings.theme == "light")
            self._contrast_normal.setChecked(settings.contrast == "normal")
            self._contrast_high.setChecked(settings.contrast == "high")
            for index in range(self._font_combo.count()):
                if abs(float(self._font_combo.itemData(index)) - settings.font_scale) < 0.001:
                    self._font_combo.setCurrentIndex(index)
                    break
        finally:
            self._theme_group.blockSignals(False)
            self._contrast_group.blockSignals(False)
            self._font_combo.blockSignals(False)
        self._refresh_preview_styles()
        self._refresh_widget_styles()

    def _collect_draft(self) -> AppearanceSettings:
        theme = "light" if self._theme_light.isChecked() else "dark"
        contrast = "high" if self._contrast_high.isChecked() else "normal"
        font_scale = float(self._font_combo.currentData() or 1.0)
        return AppearanceSettings(theme=theme, contrast=contrast, font_scale=font_scale)

    def _apply_draft(self) -> None:
        self._draft = self._collect_draft()
        self._manager.apply(self._draft)
        self._refresh_preview_styles()
        self._refresh_widget_styles()

    def _reset_defaults(self) -> None:
        self._draft = AppearanceSettings()
        self._manager.apply(self._draft)
        self._sync_controls_from_settings()

    def _refresh_preview_styles(self) -> None:
        p = PALETTE
        self._preview_title.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_h3}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; background: transparent; border: none;"
        )
        self._preview_body.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )

    def _refresh_widget_styles(self) -> None:
        """Atualiza estilos do próprio diálogo após mudança de tema."""
        self._refresh_preview_styles()
