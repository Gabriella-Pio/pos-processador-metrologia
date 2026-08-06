"""
HeroCommandBar — hub de entrada da Home.

Destaca claramente as jornadas principais (relatório vs template),
métricas legíveis e busca ampla — alinhado à coluna central de 1100px.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.centered_layout import make_centered_column
from src.ui.components.icons import icon_file_pdf, icon_file_upload, icon_plus
from src.ui.components.inputs import SearchBar
from src.ui.features.home.models.dashboard import RecentFileSummary
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY
from src.ui.accessibility.themes import _is_light_palette
from src.ui.features.home.components.files_filter_bar import FilesFilterBar

AccentKind = Literal["orange", "blue"]


def _hero_gradient() -> str:
    p = PALETTE
    if _is_light_palette(p):
        return (
            f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            f"stop:0 #C8D0DA, stop:0.55 {p.bg_surface}, stop:1 {p.bg_base})"
        )
    return (
        f"qlineargradient(x1:0, y1:0, x2:0, y2:1, "
        f"stop:0 #1a2030, stop:0.55 {p.bg_surface}, stop:1 {p.bg_base})"
    )


class _SpotlightCard(QFrame):
    """Cartão de ação principal — borda lateral colorida e área clicável ampla."""

    clicked = pyqtSignal()

    def __init__(
        self,
        icon: QIcon,
        title: str,
        subtitle: str,
        *,
        accent: AccentKind = "orange",
        shortcut_hint: str = "",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._accent = accent
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(80)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._icon_label = QLabel()
        self._icon_label.setFixedSize(44, 44)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setPixmap(icon.pixmap(26, 26))
        layout.addWidget(self._icon_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(3)
        self._title_label = QLabel(title)
        self._subtitle_label = QLabel(subtitle)
        self._subtitle_label.setWordWrap(True)
        text_col.addWidget(self._title_label)
        text_col.addWidget(self._subtitle_label)
        layout.addLayout(text_col, stretch=1)

        self._hint_label: QLabel | None = None
        if shortcut_hint:
            self._hint_label = QLabel(shortcut_hint)
            self._hint_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            layout.addWidget(self._hint_label)

        self._rebuild_styles()
        self.setStyleSheet(self._idle)

    def set_text(self, title: str, subtitle: str) -> None:
        self._title_label.setText(title)
        self._subtitle_label.setText(subtitle)

    def _rebuild_styles(self) -> None:
        p = PALETTE
        accent_color = p.senai_orange if self._accent == "orange" else p.senai_blue_light
        accent_bg = "rgba(240, 67, 30, 0.10)" if self._accent == "orange" else "rgba(74, 111, 212, 0.12)"
        self._idle = f"""
            QFrame {{
                background: {p.bg_surface};
                border: 1px solid {p.border};
                border-left: 4px solid {accent_color};
                border-radius: {SPACING.radius_lg}px;
            }}
        """
        self._hover = f"""
            QFrame {{
                background: {accent_bg};
                border: 1px solid {accent_color};
                border-left: 4px solid {accent_color};
                border-radius: {SPACING.radius_lg}px;
            }}
        """
        self._title_label.setStyleSheet(
            f"color: {p.text_primary}; font-size: 16px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; background: transparent; border: none;"
        )
        self._subtitle_label.setStyleSheet(
            f"color: {p.text_secondary}; font-size: 12px; "
            f"background: transparent; border: none;"
        )
        self._icon_label.setStyleSheet(
            f"background: {accent_bg}; border-radius: {SPACING.radius_md}px; border: none;"
        )
        if self._hint_label is not None:
            self._hint_label.setStyleSheet(
                f"color: {p.text_muted}; font-size: 11px; letter-spacing: 0.5px; "
                f"background: transparent; border: none;"
            )

    def refresh_appearance(self) -> None:
        self._rebuild_styles()
        self.setStyleSheet(self._idle)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._hover)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._idle)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit()
        super().mousePressEvent(event)


class _InlineMetrics(QLabel):
    """Linha compacta de métricas — ex: 11 arquivos · 2 templates · último: Cargill."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setText("—")
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        self.setStyleSheet(
            f"color: {p.text_muted}; font-size: 13px; "
            f"background: transparent; border: none; padding: 0;"
        )

    def set_right_aligned(self, aligned: bool = True) -> None:
        self.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if aligned
            else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

    def set_stats(
        self,
        file_count: int,
        template_count: int,
        last_project: str | None = None,
    ) -> None:
        parts = [
            f"{file_count} arquivo{'s' if file_count != 1 else ''}",
            f"{template_count} template{'s' if template_count != 1 else ''}",
        ]
        if last_project:
            parts.append(f"último: {last_project[:24]}")
        self.setText(" · ".join(parts))


def _greeting_and_date() -> tuple[str, str, str]:
    now = datetime.now()
    days = [
        "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira",
        "Sexta-feira", "Sábado", "Domingo",
    ]
    months = [
        "", "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
    ]
    hour = now.hour
    greeting = "Bom dia" if hour < 12 else "Boa tarde" if hour < 18 else "Boa noite"
    parts = greeting.rsplit(" ", 1)
    base = parts[0] + " " if len(parts) == 2 else greeting
    accent = parts[1] if len(parts) == 2 else ""
    date_str = f"{days[now.weekday()]}, {now.day} de {months[now.month]} de {now.year}"
    return base, accent, date_str


class HeroCommandBar(QWidget):
    """Hub da Home — jornadas principais, métricas e busca."""

    search_changed = pyqtSignal(str)
    filters_changed = pyqtSignal(object)  # RecentFilesFilterState
    new_report_requested = pyqtSignal()
    new_template_requested = pyqtSignal()
    continue_last_requested = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        p = PALETTE
        self._last_file: Optional[RecentFileSummary] = None

        self.setStyleSheet(f"background: {_hero_gradient()};")

        base, accent, date_str = _greeting_and_date()
        centered_outer, column_layout = make_centered_column(background="transparent")

        greeting_row = QHBoxLayout()
        greeting_row.setSpacing(0)
        for text, color in ((base, p.text_primary), (accent, p.senai_orange)):
            if not text:
                continue
            part = QLabel(text)
            part.setStyleSheet(
                f"color: {color}; font-size: 26px; font-weight: {TYPOGRAPHY.weight_bold}; "
                f"background: transparent; border: none; letter-spacing: -0.5px;"
            )
            greeting_row.addWidget(part)
        greeting_row.addStretch(1)
        date_label = QLabel(date_str)
        date_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        date_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: 13px; background: transparent; border: none;"
        )
        greeting_row.addWidget(date_label)

        prompt = QLabel("O que você quer fazer?")
        prompt.setStyleSheet(
            f"color: {p.text_secondary}; font-size: 14px; font-weight: {TYPOGRAPHY.weight_medium}; "
            f"background: transparent; border: none;"
        )

        actions_row = QHBoxLayout()
        actions_row.setSpacing(SPACING.md)

        self._new_file_card = _SpotlightCard(
            icon_file_upload(),
            "Novo arquivo",
            "Importe PDFs ZEISS, enriqueça e exporte o relatório final.",
            accent="orange",
            shortcut_hint="Ctrl+N",
        )
        self._new_file_card.clicked.connect(self.new_report_requested.emit)

        self._secondary_card = _SpotlightCard(
            icon_plus(),
            "Novo template",
            "Defina a estrutura reutilizável para seus relatórios de metrologia.",
            accent="blue",
            shortcut_hint="Ctrl+T",
        )
        self._secondary_card.clicked.connect(self.new_template_requested.emit)

        self._continue_card = _SpotlightCard(
            icon_file_pdf(),
            "Continuar",
            "Retome seu último trabalho.",
            accent="orange",
        )
        self._continue_card.hide()
        self._continue_card.clicked.connect(self._on_continue_clicked)

        actions_row.addWidget(self._new_file_card, stretch=1)
        actions_row.addWidget(self._secondary_card, stretch=1)
        actions_row.addWidget(self._continue_card, stretch=1)

        self.search_bar = SearchBar(
            "Buscar arquivos ou templates…  (Ctrl+K)",
            show_filter_toggle=True,
        )
        self.search_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.search_bar.textChanged.connect(self.search_changed.emit)

        self.filter_bar = FilesFilterBar()
        self.filter_bar.filters_changed.connect(self._on_filters_changed)
        self.search_bar.filter_toggled.connect(self._on_filter_toggle)
        self.filter_bar.set_expanded(False)

        discovery_panel = QFrame()
        discovery_panel.setObjectName("heroDiscoveryPanel")
        self._discovery_panel = discovery_panel
        self._apply_discovery_panel_style(discovery_panel)
        discovery_layout = QVBoxLayout(discovery_panel)
        discovery_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)
        discovery_layout.setSpacing(SPACING.md)
        discovery_layout.addWidget(self.search_bar)
        discovery_layout.addWidget(self.filter_bar)

        self._inline_metrics = _InlineMetrics()
        self._inline_metrics.set_right_aligned(True)

        subtitle_row = QHBoxLayout()
        subtitle_row.setSpacing(SPACING.md)
        subtitle_row.addWidget(prompt, stretch=0)
        subtitle_row.addStretch(1)
        subtitle_row.addWidget(self._inline_metrics, stretch=0)

        column_layout.setSpacing(0)
        column_layout.setContentsMargins(0, SPACING.xl, 0, 0)
        column_layout.addLayout(greeting_row)
        column_layout.addSpacing(SPACING.sm)
        column_layout.addLayout(subtitle_row)
        column_layout.addSpacing(SPACING.lg)
        column_layout.addLayout(actions_row)
        column_layout.addSpacing(SPACING.lg)
        column_layout.addWidget(discovery_panel)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(centered_outer)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

    def _on_continue_clicked(self) -> None:
        if self._last_file is not None:
            self.continue_last_requested.emit(self._last_file.file_id)

    def _on_filter_toggle(self, expanded: bool) -> None:
        self.filter_bar.set_expanded(expanded)
        self.search_bar.set_filter_toggle_checked(expanded)
        self._sync_filter_summary()
        self._sync_minimum_height()

    def _on_filters_changed(self, state) -> None:
        self.search_bar.set_filter_active(bool(state.active_labels()))
        self._sync_filter_summary(state)
        self.filters_changed.emit(state)
        self._sync_minimum_height()

    def _sync_filter_summary(self, state=None) -> None:
        if state is None:
            state = self.filter_bar.current_state()
        if self.filter_bar.is_expanded() or not self.filter_bar.isVisible():
            self.search_bar.set_filter_summary("")
            return
        labels = state.summary_chip_labels()
        self.search_bar.set_filter_summary(" · ".join(labels) if labels else "")

    @staticmethod
    def _apply_discovery_panel_style(panel: QFrame) -> None:
        p = PALETTE
        panel.setStyleSheet(f"""
            QFrame#heroDiscoveryPanel {{
                background: rgba(255, 255, 255, 0.02);
                border: 1px solid {p.border_subtle};
                border-radius: {SPACING.radius_lg}px;
            }}
        """)

    def refresh_appearance(self) -> None:
        self.setStyleSheet(f"background: {_hero_gradient()};")
        if hasattr(self, "_discovery_panel"):
            self._apply_discovery_panel_style(self._discovery_panel)
        self._continue_card.refresh_appearance()
        self._new_file_card.refresh_appearance()
        self._secondary_card.refresh_appearance()
        self._inline_metrics.refresh_appearance()
        self.search_bar.refresh_appearance()
        self.filter_bar.refresh_appearance()
        self._sync_minimum_height()

    def minimumSizeHint(self) -> QSize:
        hint = super().minimumSizeHint()
        content = self.layout().sizeHint() if self.layout() else hint
        return QSize(
            max(hint.width(), content.width()),
            max(hint.height(), content.height()),
        )

    def _sync_minimum_height(self) -> None:
        self.updateGeometry()
        parent = self.parentWidget()
        if parent is not None:
            parent.updateGeometry()

    def update_stats(
        self,
        file_count: int,
        template_count: int,
        last_file: Optional[RecentFileSummary] = None,
    ) -> None:
        self._last_file = last_file
        last_project = last_file.client_project if last_file is not None else None
        self._inline_metrics.set_stats(file_count, template_count, last_project)

        if last_file is not None:
            self._continue_card.set_text(
                f"Continuar · {last_file.file_name[:28]}",
                (
                    f"{last_file.client_project} · v{last_file.version} — "
                    f"retome de onde parou"
                ),
            )
            self._continue_card.show()
        else:
            self._continue_card.hide()

        self._sync_minimum_height()

    def set_search_result_hint(self, text: str) -> None:
        self.search_bar.set_result_hint(text)

    def focus_search(self) -> None:
        self.search_bar.focus_search()

    def set_filters_visible(self, visible: bool) -> None:
        """Oculta filtros estruturados fora da aba Arquivos."""
        self.filter_bar.setVisible(visible)
        self.search_bar.set_filter_toggle_visible(visible)
        if not visible:
            self.filter_bar.set_expanded(False)
            self.search_bar.set_filter_toggle_checked(False)
        self._sync_filter_summary()
        self._sync_minimum_height()


HeroSection = HeroCommandBar
