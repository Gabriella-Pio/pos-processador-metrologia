"""Aba Gráficos do editor de seção."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from src.core.domain.chart_figure_defs import chart_figure_defs
from src.ui.components.widget_lifecycle import clear_layout
from src.ui.styles import SPACING


class SectionGraphicsTab(QWidget):
    disabled_chart_ids_changed = pyqtSignal(str, list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._loading = False
        self._defaults_mode = False
        self._chart_checkboxes: dict[str, QCheckBox] = {}
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        self._graphics_hint = QLabel("Integração com gráficos Calypso em breve.", self)
        self._graphics_hint.setWordWrap(True)
        self._graphics_hint.setObjectName("SidebarHint")
        self._layout.addWidget(self._graphics_hint)
        self._layout.addStretch(1)

    def set_loading(self, loading: bool) -> None:
        self._loading = loading

    def set_defaults_mode(self, enabled: bool) -> None:
        self._defaults_mode = enabled

    def rebuild(self, section_id: str, overrides: dict) -> None:
        clear_layout(self._layout, discard=True)
        self._chart_checkboxes.clear()

        defs = chart_figure_defs(section_id)
        if not defs:
            if section_id == "grafica":
                self._graphics_hint = QLabel(
                    "Gráficos analíticos desta seção. Associe imagens exportadas do CALYPSO "
                    "ou use o layout para reservar espaço no PDF.",
                    self,
                )
            else:
                self._graphics_hint = QLabel("Integração com gráficos Calypso em breve.", self)
            self._graphics_hint.setWordWrap(True)
            self._graphics_hint.setObjectName("SidebarHint")
            self._layout.addWidget(self._graphics_hint)
            self._layout.addStretch(1)
            return

        intro = QLabel(
            "Marque os gráficos que devem aparecer no PDF. "
            "Para remover todos de uma vez, desmarque <b>Gráficos</b> na aba Layout.",
            self,
        )
        intro.setWordWrap(True)
        intro.setObjectName("SidebarHint")
        self._layout.addWidget(intro)

        disabled = {
            str(item)
            for item in (overrides.get("disabled_chart_ids") or [])
            if item
        }
        for figure in defs:
            cb = QCheckBox(figure.label, self)
            cb.setChecked(figure.id not in disabled)
            cb.stateChanged.connect(
                lambda _state, section=section_id: self._emit_disabled_chart_ids(section)
            )
            self._chart_checkboxes[figure.id] = cb
            self._layout.addWidget(cb)
        self._layout.addStretch(1)

    def _emit_disabled_chart_ids(self, section_id: str) -> None:
        if self._loading or self._defaults_mode:
            return
        disabled = [
            figure_id
            for figure_id, cb in self._chart_checkboxes.items()
            if not cb.isChecked()
        ]
        self.disabled_chart_ids_changed.emit(section_id, disabled)
