"""Painel de configuração de layout de seção no editor de template."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QFrame, QLabel, QVBoxLayout, QWidget

from src.ui.styles import SPACING, PALETTE, caption_style
from src.ui.components.widget_lifecycle import clear_layout


def _notice_style(*, padding: str = "8px") -> str:
    return (
        f"color: {PALETTE.senai_orange}; background: {PALETTE.senai_orange_glow}; "
        f"border: 1px solid {PALETTE.senai_orange}; border-radius: 8px; padding: {padding};"
    )


_LOCKED_NOTICE = (
    "Este bloco faz parte do layout padrão da seção e não pode ser desativado aqui. "
    "Para um relatório diferente, crie uma seção personalizada."
)


class TemplateLayoutPanel(QFrame):
    """Configuração de layout — fotos, gráficos e tabelas no template."""

    kinds_changed = pyqtSignal(list)
    blocked_action = pyqtSignal(str)

    _OPTIONS = (
        ("photos", "Fotografias", "Reserva espaço para imagens nesta seção do PDF."),
        ("graphics", "Gráficos", "Reserva espaço para gráficos analíticos."),
        ("tables", "Tabela", "Inclui bloco de tabela nesta seção."),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._option_cards: dict[str, QFrame] = {}
        self._locked_labels: dict[str, QLabel] = {}
        self._workspace_mode = False
        self._locked_kinds: set[str] = set()
        self._addable_kinds: set[str] = set()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        layout.setSpacing(SPACING.sm)

        self._hint = QLabel()
        self._hint.setWordWrap(True)
        self._hint.setObjectName("SidebarHint")
        self._hint.setStyleSheet(caption_style())
        self._apply_hint_text()
        layout.addWidget(self._hint)

        self._notice = QLabel()
        self._notice.setObjectName("LayoutBlockedNotice")
        self._notice.setWordWrap(True)
        self._notice.hide()
        layout.addWidget(self._notice)
        self._notice_timer = QTimer(self)
        self._notice_timer.setSingleShot(True)
        self._notice_timer.timeout.connect(self._notice.hide)

        for kind, label, tooltip in self._OPTIONS:
            card = QFrame()
            card.setObjectName("GlobalFieldCard")
            card.installEventFilter(self)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            card_layout.setSpacing(2)
            cb = QCheckBox(label)
            cb.setToolTip(tooltip)
            cb.installEventFilter(self)
            cb.stateChanged.connect(lambda _state, k=kind: self._on_kind_changed(k))
            card_layout.addWidget(cb)
            locked_meta = QLabel("Incluído no template")
            locked_meta.setObjectName("GlobalFieldMeta")
            locked_meta.setVisible(False)
            card_layout.addWidget(locked_meta)
            self._checkboxes[kind] = cb
            self._option_cards[kind] = card
            self._locked_labels[kind] = locked_meta
            layout.addWidget(card)

        self._tables_host = QWidget()
        self._tables_host_layout = QVBoxLayout(self._tables_host)
        self._tables_host_layout.setContentsMargins(0, 0, 0, 0)
        self._tables_host_layout.setSpacing(SPACING.sm)
        self._tables_host.setVisible(False)
        layout.addWidget(self._tables_host)
        layout.addStretch(1)

    def show_blocked_notice(self, message: str, duration_ms: int = 4500) -> None:
        self._notice.setText(f"⚠ {message}")
        self._notice.setStyleSheet(_notice_style())
        self._notice.show()
        self._notice_timer.start(duration_ms)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if event.type() != QEvent.Type.MouseButtonRelease or not self._workspace_mode:
            return super().eventFilter(obj, event)
        for kind, card in self._option_cards.items():
            if kind not in self._locked_kinds:
                continue
            if obj is card or obj is self._checkboxes[kind]:
                self.show_blocked_notice(_LOCKED_NOTICE)
                return True
        return super().eventFilter(obj, event)

    def set_workspace_mode(self, enabled: bool) -> None:
        self._workspace_mode = enabled
        self._apply_hint_text()
        self._apply_checkbox_locks()
        self._apply_option_visibility()

    def set_locked_kinds(self, kinds: list[str]) -> None:
        self._locked_kinds = set(kinds)
        self._apply_checkbox_locks()

    def set_addable_kinds(self, kinds: list[str]) -> None:
        self._addable_kinds = set(kinds)
        self._apply_option_visibility()

    def _apply_option_visibility(self) -> None:
        for kind, card in self._option_cards.items():
            if self._workspace_mode:
                visible = kind in self._addable_kinds or kind in self._locked_kinds
            else:
                visible = True
            card.setVisible(visible)

    def _apply_checkbox_locks(self) -> None:
        for kind, cb in self._checkboxes.items():
            locked = self._workspace_mode and kind in self._locked_kinds
            card = self._option_cards[kind]
            meta = self._locked_labels[kind]
            if locked:
                cb.blockSignals(True)
                cb.setChecked(True)
                cb.blockSignals(False)
            cb.setEnabled(not locked)
            meta.setVisible(locked)
            card.setProperty("locked", "true" if locked else "false")
            cb.setProperty("locked", "true" if locked else "false")
            card.style().unpolish(card)
            card.style().polish(card)
            cb.style().unpolish(cb)
            cb.style().polish(cb)
            card.setCursor(
                Qt.CursorShape.ForbiddenCursor if locked else Qt.CursorShape.ArrowCursor
            )

    def _apply_hint_text(self) -> None:
        if self._workspace_mode:
            self._hint.setText(
                "Blocos do template ficam fixos. Você pode acrescentar fotos ou gráficos. "
                "Tabela extra só em seções que já usam tabela ou em seções personalizadas — "
                "para outro layout, crie uma seção customizada."
            )
        else:
            self._hint.setText(
                "Marque os blocos que esta seção deve reservar no relatório. "
                "No workspace, o usuário preenche fotos, gráficos e dados reais."
            )

    def set_table_widget(self, widget: QWidget | None) -> None:
        clear_layout(self._tables_host_layout, discard=False)
        if widget is not None:
            self._tables_host_layout.addWidget(widget)
            self._tables_host.setVisible(True)
        else:
            self._tables_host.setVisible(False)

    def set_kinds(self, kinds: list[str]) -> None:
        active = set(kinds) | self._locked_kinds
        for kind, cb in self._checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(kind in active)
            cb.blockSignals(False)
        self._apply_checkbox_locks()

    def current_kinds(self) -> list[str]:
        selected = {kind for kind, cb in self._checkboxes.items() if cb.isChecked()}
        merged = selected | self._locked_kinds
        order = ("photos", "graphics", "tables")
        return sorted(merged, key=lambda k: order.index(k) if k in order else 99)

    def _on_kind_changed(self, kind: str) -> None:
        cb = self._checkboxes[kind]
        if self._workspace_mode and kind in self._locked_kinds:
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
            self.show_blocked_notice(_LOCKED_NOTICE)
            return
        if (
            self._workspace_mode
            and kind not in self._addable_kinds
            and kind not in self._locked_kinds
            and cb.isChecked()
        ):
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
            self.show_blocked_notice(
                "Tabela nesta seção não é suportada. Use uma seção com tabela nativa "
                "(ex.: Identificação) ou crie uma seção personalizada com linhas customizadas."
            )
            return
        self.kinds_changed.emit(self.current_kinds())
