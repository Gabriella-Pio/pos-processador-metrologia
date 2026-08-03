"""Painel de templates — lista, grade, filtro e CTA."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.cards import ActionCard, TemplateCard
from src.ui.components.icons import icon_empty_results
from src.ui.models.dashboard import TemplateSummary, empty_results_messages, filter_templates
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, apply_elevation, caption_style
from src.ui.views.home.grid_utils import grid_columns_for_width
from src.ui.components.centered_layout import make_centered_column
from src.ui.components.home import EmptyState, TabSectionHeader, ViewToggle
from src.ui.views.home.layout_utils import (
    add_filter_empty_state,
    clear_layout,
    make_list_card_shell,
    set_grid_filter_empty_mode,
)


class _TemplateListRow(QFrame):
    """Linha compacta de template para a vista lista."""

    selected = pyqtSignal(str)

    def __init__(self, summary: TemplateSummary, parent=None) -> None:
        super().__init__(parent)
        self._template_id = summary.template_id
        p = PALETTE
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-bottom: 1px solid {p.border_subtle};
            }}
            QFrame:hover {{
                background: {p.bg_surface_alt};
                border-radius: {SPACING.radius_sm}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        icon = QLabel("PDF")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"background: rgba(74,111,212,0.15); color: {p.senai_blue_light}; "
            f"font-size: 9px; font-weight: {TYPOGRAPHY.weight_bold}; "
            f"border-radius: {SPACING.radius_sm}px; border: none;"
        )
        layout.addWidget(icon)

        name = QLabel(summary.name)
        name.setStyleSheet(
            f"font-weight: {TYPOGRAPHY.weight_semibold}; color: {p.text_primary}; "
            f"background: transparent; border: none;"
        )
        layout.addWidget(name, stretch=1)

        if summary.is_default:
            badge = QLabel("Padrão SENAI/ZEISS")
            badge.setStyleSheet(caption_style())
            badge.setSizePolicy(
                QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
            )
            layout.addWidget(badge)

    def mousePressEvent(self, event) -> None:
        self.selected.emit(self._template_id)
        super().mousePressEvent(event)


class _TemplateCreateRow(QFrame):
    """Linha de ação para criar template na vista lista."""

    clicked = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        p = PALETTE
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-top: 1px solid {p.border_subtle};
            }}
            QFrame:hover {{
                background: rgba(240, 67, 30, 0.08);
                border-radius: {SPACING.radius_sm}px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.md)

        icon = QLabel("+")
        icon.setFixedSize(36, 36)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(
            f"background: rgba(240, 67, 30, 0.12); color: {p.senai_orange}; "
            f"font-size: 18px; font-weight: {TYPOGRAPHY.weight_bold}; "
            f"border-radius: {SPACING.radius_sm}px; border: none;"
        )
        layout.addWidget(icon)

        text_block = QVBoxLayout()
        text_block.setSpacing(2)
        text_block.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Novo template")
        title.setStyleSheet(
            f"font-weight: {TYPOGRAPHY.weight_semibold}; color: {p.text_primary}; "
            f"background: transparent; border: none;"
        )
        subtitle = QLabel("Criar do zero")
        subtitle.setStyleSheet(caption_style())
        text_block.addWidget(title)
        text_block.addWidget(subtitle)
        layout.addLayout(text_block, stretch=1)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit()
        super().mousePressEvent(event)


class TemplatesPanel(QWidget):
    template_selected = pyqtSignal(str)
    create_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("HomeSurface")
        self._all_templates: list[TemplateSummary] = []
        self._filter_query = ""

        self._toggle = ViewToggle(default="grid")
        self._toggle.view_changed.connect(self._on_view_changed)

        self._list_card, self._list_layout = make_list_card_shell()

        list_page_layout = QVBoxLayout()
        list_page_layout.setContentsMargins(0, 0, 0, 0)
        list_page_layout.setSpacing(0)
        list_page_layout.addWidget(self._list_card, 0, Qt.AlignmentFlag.AlignTop)

        list_page = QWidget()
        list_page.setLayout(list_page_layout)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setSpacing(SPACING.md)
        self._grid.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        self._grid_cols = grid_columns_for_width(self._grid_widget.width())
        self._grid_widget.installEventFilter(self)

        self._stack = QStackedWidget()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._stack.addWidget(list_page)
        self._stack.addWidget(self._wrap_grid_page())
        self._stack.setCurrentIndex(1)

        centered_outer, column = make_centered_column()

        self._section_header = TabSectionHeader(
            "Meus templates",
            "Estruturas reutilizáveis para seus relatórios de metrologia",
            right=self._toggle,
        )
        column.addWidget(self._section_header)
        column.addWidget(self._stack)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(centered_outer)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def refresh_appearance(self) -> None:
        self._toggle.refresh_appearance()
        self._refresh_views()

    def _wrap_grid_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, SPACING.xl)
        layout.setSpacing(0)

        self._grid_empty_card, self._grid_empty_layout = make_list_card_shell()
        self._grid_empty_card.hide()
        layout.addWidget(self._grid_empty_card, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._grid_widget, stretch=1)
        return page

    def eventFilter(self, obj, event) -> bool:
        if obj is self._grid_widget and event.type() == QEvent.Type.Resize:
            self._update_grid_columns()
        return super().eventFilter(obj, event)

    def _update_grid_columns(self) -> None:
        cols = grid_columns_for_width(self._grid_widget.width())
        if cols != self._grid_cols:
            self._grid_cols = cols
            self._refresh_views()

    def render(self, templates: list[TemplateSummary]) -> None:
        self._all_templates = list(templates)
        self._refresh_views()

    def apply_filter(self, query: str) -> None:
        self._filter_query = query
        self._refresh_views()

    def visible_count(self) -> int:
        return len(filter_templates(self._all_templates, self._filter_query))

    def has_visible_items(self) -> bool:
        if not self._filter_query.strip():
            return bool(self._all_templates)
        return self.visible_count() > 0

    def _filtered_templates(self) -> list[TemplateSummary]:
        return filter_templates(self._all_templates, self._filter_query)

    def _refresh_views(self) -> None:
        templates = self._filtered_templates()
        self._rebuild_list(templates)
        self._rebuild_grid(templates)

    def _rebuild_list(self, templates: list[TemplateSummary]) -> None:
        clear_layout(self._list_layout)

        is_filtering = bool(self._filter_query.strip())
        if is_filtering and not templates:
            title, subtitle = empty_results_messages(self._filter_query)
            empty = add_filter_empty_state(
                self._list_layout,
                title,
                subtitle,
                "Novo template",
                icon_empty_results(),
            )
            empty.action_requested.connect(self.create_requested.emit)
            return

        for summary in templates:
            row = _TemplateListRow(summary)
            row.selected.connect(self.template_selected.emit)
            self._list_layout.addWidget(row)

        if not is_filtering:
            create_row = _TemplateCreateRow()
            create_row.clicked.connect(self.create_requested.emit)
            self._list_layout.addWidget(create_row)

    def _rebuild_grid(self, templates: list[TemplateSummary]) -> None:
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        templates = self._filtered_templates()
        is_filtering = bool(self._filter_query.strip())

        if is_filtering and not templates:
            set_grid_filter_empty_mode(
                self._grid_empty_card, self._grid_widget, show_empty=True
            )
            title, subtitle = empty_results_messages(self._filter_query)
            empty = add_filter_empty_state(
                self._grid_empty_layout,
                title,
                subtitle,
                "Novo template",
                icon_empty_results(),
            )
            empty.action_requested.connect(self.create_requested.emit)
            return

        set_grid_filter_empty_mode(
            self._grid_empty_card, self._grid_widget, show_empty=False
        )

        cols = max(1, self._grid_cols)
        for index, summary in enumerate(templates):
            card = TemplateCard(summary)
            apply_elevation(card, blur=20, y_offset=3, alpha=90)
            card.selected.connect(self.template_selected.emit)
            self._grid.addWidget(card, index // cols, index % cols)

        if not is_filtering:
            total = len(templates)
            create_card = ActionCard(
                icon="+",
                title="Novo template",
                subtitle="Criar do zero",
                accent_color=PALETTE.senai_orange,
                accent_bg="rgba(240, 67, 30, 0.10)",
            )
            create_card.clicked.connect(self.create_requested.emit)
            self._grid.addWidget(create_card, total // cols, total % cols)

    def _on_view_changed(self, mode: str) -> None:
        self._stack.setCurrentIndex(0 if mode == "list" else 1)
        if mode == "grid":
            self._update_grid_columns()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_grid_columns()
