"""Barra de filtros estruturados — aba Arquivos."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.inputs import ThemedComboBox, configure_themed_combo
from src.ui.features.home.models.dashboard import (
    PERIOD_7D,
    PERIOD_30D,
    PERIOD_90D,
    PERIOD_ALL,
    PERIOD_LABELS,
    PERIOD_TODAY,
    RecentFilesFilterState,
    SORT_LABELS,
    SORT_NAME,
    SORT_OLDEST,
    SORT_PROJECT,
    SORT_RECENT,
)
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY


class _FilterCombo(ThemedComboBox):
    def __init__(self, label: str, parent=None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(148)
        self._field_label = label

    def field_label(self) -> str:
        return self._field_label


class FilesFilterBar(QWidget):
    """Filtros por período, projeto, componente e ordenação."""

    filters_changed = pyqtSignal(object)  # RecentFilesFilterState

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        p = PALETTE
        self._state = RecentFilesFilterState()
        self._blocking = False
        self._expanded = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(SPACING.sm)

        self._filters_body = QWidget()
        body_layout = QVBoxLayout(self._filters_body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(SPACING.md)

        section_title = QLabel("Refinar resultados")
        self._section_title = section_title
        section_title.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"letter-spacing: 0.8px; background: transparent; border: none;"
        )

        row = QHBoxLayout()
        row.setSpacing(SPACING.md)

        self._period = _FilterCombo("Período")
        for key in (PERIOD_ALL, PERIOD_TODAY, PERIOD_7D, PERIOD_30D, PERIOD_90D):
            self._period.addItem(PERIOD_LABELS[key], key)
        self._period.currentIndexChanged.connect(self._emit_filters)
        row.addWidget(self._wrap_labeled("Período", self._period))

        self._project = _FilterCombo("Projeto")
        self._project.addItem("Todos os projetos", "")
        self._project.currentIndexChanged.connect(self._emit_filters)
        row.addWidget(self._wrap_labeled("Projeto", self._project))

        self._component = _FilterCombo("Componente")
        self._component.addItem("Todos os componentes", "")
        self._component.currentIndexChanged.connect(self._emit_filters)
        row.addWidget(self._wrap_labeled("Componente", self._component))

        self._sort = _FilterCombo("Ordenar")
        for key in (SORT_RECENT, SORT_OLDEST, SORT_NAME, SORT_PROJECT):
            self._sort.addItem(SORT_LABELS[key], key)
        self._sort.currentIndexChanged.connect(self._emit_filters)
        row.addWidget(self._wrap_labeled("Ordenar", self._sort))

        row.addStretch(1)

        body_layout.addWidget(section_title)
        body_layout.addLayout(row)

        self._clear_btn = QPushButton("Limpar filtros")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {p.text_muted};
                background: transparent;
                border: 1px solid {p.border};
                border-radius: {SPACING.radius_sm}px;
                padding: 6px 12px;
                font-size: {TYPOGRAPHY.size_caption}px;
            }}
            QPushButton:hover {{
                color: {p.senai_orange};
                border-color: {p.senai_orange};
                background: rgba(240, 67, 30, 0.08);
            }}
        """)
        self._clear_btn.clicked.connect(self.clear_filters)
        self._clear_btn.hide()

        self._chips = QLabel()
        self._chips.setWordWrap(True)
        self._chips.hide()
        self._chips.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"background: transparent; border: none; padding-top: 2px;"
        )

        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        footer.addWidget(self._chips, stretch=1)
        footer.addWidget(self._clear_btn)

        outer.addWidget(self._filters_body)
        outer.addLayout(footer)

        self.set_expanded(False)

    def is_expanded(self) -> bool:
        return self._expanded

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = expanded
        self._filters_body.setVisible(expanded)
        self.updateGeometry()

    def _wrap_labeled(self, text: str, combo: QComboBox) -> QWidget:
        p = PALETTE
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel(text.upper())
        label.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_micro}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"letter-spacing: 0.5px; background: transparent; border: none;"
        )
        layout.addWidget(label)
        layout.addWidget(combo)
        return box

    def set_query(self, query: str) -> None:
        self._state.query = query
        self._update_chips()

    def set_project_options(self, projects: list[str]) -> None:
        self._repopulate_combo(self._project, "Todos os projetos", projects, self._state.project)

    def set_component_options(self, components: list[str]) -> None:
        self._repopulate_combo(
            self._component, "Todos os componentes", components, self._state.component
        )

    def _repopulate_combo(
        self,
        combo: QComboBox,
        all_label: str,
        values: list[str],
        selected: str,
    ) -> None:
        self._blocking = True
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(all_label, "")
        select_index = 0
        for index, value in enumerate(values, start=1):
            combo.addItem(value, value)
            if value == selected:
                select_index = index
        combo.setCurrentIndex(select_index)
        combo.blockSignals(False)
        self._blocking = False

    def current_state(self) -> RecentFilesFilterState:
        return RecentFilesFilterState(
            query=self._state.query,
            period=self._period.currentData() or PERIOD_ALL,
            project=self._project.currentData() or "",
            component=self._component.currentData() or "",
            sort=self._sort.currentData() or SORT_RECENT,
        )

    def _emit_filters(self) -> None:
        if self._blocking:
            return
        self._state = RecentFilesFilterState(
            query=self._state.query,
            period=self._period.currentData() or PERIOD_ALL,
            project=self._project.currentData() or "",
            component=self._component.currentData() or "",
            sort=self._sort.currentData() or SORT_RECENT,
        )
        self._update_chips()
        self.filters_changed.emit(self.current_state())

    def _update_chips(self) -> None:
        labels = self.current_state().active_labels()
        if labels:
            self._chips.setText("Filtros ativos: " + " · ".join(labels))
            self._chips.show()
            self._clear_btn.show()
        else:
            self._chips.hide()
            self._clear_btn.hide()

    def clear_filters(self) -> None:
        self._blocking = True
        self._period.setCurrentIndex(0)
        self._project.setCurrentIndex(0)
        self._component.setCurrentIndex(0)
        self._sort.setCurrentIndex(0)
        self._blocking = False
        self._state = RecentFilesFilterState(query=self._state.query)
        self._update_chips()
        self.filters_changed.emit(self.current_state())

    def clear_all_including_query(self) -> None:
        self._state.query = ""
        self.clear_filters()

    def refresh_appearance(self) -> None:
        p = PALETTE
        self._section_title.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"letter-spacing: 0.8px; background: transparent; border: none;"
        )
        for combo in (self._period, self._project, self._component, self._sort):
            configure_themed_combo(combo)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {p.text_muted};
                background: transparent;
                border: 1px solid {p.border};
                border-radius: {SPACING.radius_sm}px;
                padding: 6px 12px;
                font-size: {TYPOGRAPHY.size_caption}px;
            }}
            QPushButton:hover {{
                color: {p.senai_orange};
                border-color: {p.senai_orange};
                background: rgba(240, 67, 30, 0.08);
            }}
        """)
        self._chips.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"background: transparent; border: none; padding-top: 2px;"
        )
        for label in self.findChildren(QLabel):
            if label is self._section_title or label is self._chips:
                continue
            if label.text().isupper() and len(label.text()) < 20:
                label.setStyleSheet(
                    f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_micro}px; "
                    f"font-weight: {TYPOGRAPHY.weight_semibold}; "
                    f"letter-spacing: 0.5px; background: transparent; border: none;"
                )
