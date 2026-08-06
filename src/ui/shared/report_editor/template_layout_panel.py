"""Painel de configuração de layout de seção no editor de template."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QFrame, QLabel, QVBoxLayout, QWidget

from src.ui.styles import SPACING, caption_style


class TemplateLayoutPanel(QFrame):
    """Configuração de layout — fotos, gráficos e tabelas no template."""

    kinds_changed = pyqtSignal(list)

    _OPTIONS = (
        ("photos", "Fotografias", "Reserva espaço para imagens nesta seção do PDF."),
        ("graphics", "Gráficos", "Reserva espaço para gráficos analíticos."),
        ("tables", "Tabela", "Inclui bloco de tabela nesta seção."),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        hint = QLabel(
            "Marque os blocos que esta seção deve reservar no relatório. "
            "No workspace, o usuário preenche fotos, gráficos e dados reais."
        )
        hint.setWordWrap(True)
        hint.setObjectName("SidebarHint")
        hint.setStyleSheet(caption_style())
        layout.addWidget(hint)

        for kind, label, tooltip in self._OPTIONS:
            card = QFrame()
            card.setObjectName("GlobalFieldCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            card_layout.setSpacing(SPACING.xs)
            cb = QCheckBox(label)
            cb.setToolTip(tooltip)
            cb.stateChanged.connect(self._emit_kinds)
            card_layout.addWidget(cb)
            self._checkboxes[kind] = cb
            layout.addWidget(card)

        self._tables_host = QWidget()
        self._tables_host_layout = QVBoxLayout(self._tables_host)
        self._tables_host_layout.setContentsMargins(0, 0, 0, 0)
        self._tables_host_layout.setSpacing(SPACING.sm)
        self._tables_host.setVisible(False)
        layout.addWidget(self._tables_host)
        layout.addStretch(1)

    def set_table_widget(self, widget: QWidget | None) -> None:
        while self._tables_host_layout.count():
            item = self._tables_host_layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        if widget is not None:
            self._tables_host_layout.addWidget(widget)
            self._tables_host.setVisible(True)
        else:
            self._tables_host.setVisible(False)

    def set_kinds(self, kinds: list[str]) -> None:
        active = set(kinds)
        for kind, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(kind in active)
            cb.blockSignals(False)

    def current_kinds(self) -> list[str]:
        return [kind for kind, cb in self._checkboxes.items() if cb.isChecked()]

    def _emit_kinds(self, *_args) -> None:
        self.kinds_changed.emit(self.current_kinds())
