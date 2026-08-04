"""Campos de entrada reutilizáveis — dark edition com label uppercase e ícone de busca."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.icons import app_icon, icon_filter, icon_search
from src.ui.styles import (
    PALETTE,
    SPACING,
    TYPOGRAPHY,
    filter_toggle_button_style,
    form_label_style,
    labeled_input_style,
    search_bar_container_style,
    search_field_inner_style,
)


class LabeledLineEdit(QWidget):
    """Campo de texto com rótulo uppercase acima.

    Usado em formulários: Cliente/Projeto, Componente Avaliado,
    campos de Controle Técnico, etc.
    """

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        required: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._required = required
        self._error_message: str | None = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        label_text = f"{label.upper()} *" if required else label.upper()
        self._label = QLabel(label_text)
        self._label.setStyleSheet(form_label_style())

        self._field = QLineEdit()
        self._field.setPlaceholderText(placeholder)
        self._field.setMinimumHeight(38)

        self._error_label = QLabel("")
        self._error_label.hide()
        self._error_label.setStyleSheet(
            f"color: {PALETTE.danger}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )

        self._update_validation_ui()
        self._field.textChanged.connect(self._update_validation_ui)

        layout.addWidget(self._label)
        layout.addWidget(self._field)
        layout.addWidget(self._error_label)

    def _update_validation_ui(self) -> None:
        is_invalid = self._required and not self._field.text().strip() and self._touched()
        self._field.setStyleSheet(labeled_input_style(invalid=is_invalid))
        if is_invalid:
            self._error_label.setText(self._error_message or "Campo obrigatório.")
            self._error_label.show()
        else:
            self._error_label.hide()

    def _touched(self) -> bool:
        return self._field.property("touched") is True

    def text(self) -> str:
        return self._field.text().strip()

    def set_text(self, value: str) -> None:
        self._field.setText(value)

    def is_valid(self) -> bool:
        return not self._required or bool(self.text())

    def mark_touched(self) -> None:
        self._field.setProperty("touched", True)
        self._update_validation_ui()

    def show_validation_error(self, message: str | None = None) -> None:
        if message is not None:
            self._error_message = message
        self.mark_touched()

    def clear_validation_error(self) -> None:
        self._field.setProperty("touched", False)
        self._error_message = None
        self._update_validation_ui()

    @property
    def field(self) -> QLineEdit:
        """Acesso ao QLineEdit interno para conexões de sinal específicas."""
        return self._field


class _FilterToggleWrap(QWidget):
    """Botão de filtro com badge sobreposto no canto superior direito."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(36, 36)

        self.button = QPushButton(self)
        self.button.setObjectName("FilterToggleButton")
        self.button.setIcon(icon_filter())
        self.button.setFixedSize(36, 36)
        self.button.setCheckable(True)
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.setToolTip("Refinar resultados")

        self.badge = QLabel(self.button)
        self.badge.setObjectName("FilterActiveBadge")
        self.badge.setFixedSize(6, 6)
        self.badge.move(26, 4)
        self.badge.hide()

    def set_badge_visible(self, visible: bool) -> None:
        self.badge.setVisible(visible)


class SearchBar(QWidget):
    """Campo de busca com ícone, botão limpar, filtro opcional e dica de resultados."""

    textChanged = pyqtSignal(str)
    filter_toggled = pyqtSignal(bool)

    def __init__(
        self,
        placeholder: str = "Buscar...",
        parent: Optional[QWidget] = None,
        *,
        show_filter_toggle: bool = False,
    ) -> None:
        super().__init__(parent)
        p = PALETTE
        self._filter_expanded = False
        self._filter_has_active = False
        self._result_hint = ""
        self._filter_summary = ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(4)

        self._container = QWidget()
        container_layout = QHBoxLayout(self._container)
        container_layout.setContentsMargins(14, 0, 8, 0)
        container_layout.setSpacing(8)

        icon_label = QLabel()
        icon_label.setFixedWidth(22)
        icon_label.setPixmap(icon_search().pixmap(20, 20))
        icon_label.setStyleSheet("background: transparent; border: none;")

        self._field = QLineEdit()
        self._field.setPlaceholderText(placeholder)
        self._field.setMinimumHeight(44)
        self._field.setStyleSheet(search_field_inner_style())

        self._filter_divider = QFrame()
        self._filter_divider.setObjectName("SearchBarDivider")
        self._filter_divider.setFrameShape(QFrame.Shape.VLine)
        self._filter_divider.setFixedWidth(1)
        self._filter_divider.setFixedHeight(24)
        self._filter_divider.hide()

        self._filter_wrap = _FilterToggleWrap()
        self._filter_btn = self._filter_wrap.button
        self._filter_btn.clicked.connect(self._on_filter_clicked)
        self._filter_wrap.hide()

        self._clear_btn = QPushButton("×")
        self._clear_btn.setFixedSize(24, 24)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setToolTip("Limpar busca (Esc)")
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {p.text_muted};
                background: transparent;
                border: none;
                font-size: 16px;
                font-weight: {TYPOGRAPHY.weight_bold};
                border-radius: {SPACING.radius_sm}px;
            }}
            QPushButton:hover {{
                color: {p.text_primary};
                background: {p.bg_surface_alt};
            }}
        """)
        self._clear_btn.clicked.connect(self.clear)
        self._clear_btn.hide()

        container_layout.addWidget(icon_label)
        container_layout.addWidget(self._field, stretch=1)
        if show_filter_toggle:
            self._filter_divider.show()
            self._filter_wrap.show()
            container_layout.addWidget(self._filter_divider)
            container_layout.addWidget(self._filter_wrap)
        container_layout.addWidget(self._clear_btn)

        self._hint_label = QLabel()
        self._hint_label.hide()
        self._hint_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: 12px; "
            f"background: transparent; border: none; padding-left: 4px;"
        )

        outer.addWidget(self._container)
        outer.addWidget(self._hint_label)

        self._apply_idle_style()
        self._apply_filter_button_style()
        self._field.focusInEvent = self._on_focus_in    # type: ignore[method-assign]
        self._field.focusOutEvent = self._on_focus_out  # type: ignore[method-assign]
        self._field.textChanged.connect(self._on_text_changed)

    def _on_filter_clicked(self, checked: bool) -> None:
        self._filter_expanded = checked
        self.filter_toggled.emit(checked)

    def set_filter_toggle_visible(self, visible: bool) -> None:
        self._filter_wrap.setVisible(visible)
        self._filter_divider.setVisible(visible)
        if not visible:
            self._filter_wrap.set_badge_visible(False)

    def set_filter_toggle_checked(self, checked: bool) -> None:
        self._filter_btn.blockSignals(True)
        self._filter_btn.setChecked(checked)
        self._filter_btn.blockSignals(False)
        self._filter_expanded = checked
        self._apply_filter_button_style()

    def set_filter_active(self, active: bool) -> None:
        self._filter_has_active = active
        self._filter_wrap.set_badge_visible(active and self._filter_wrap.isVisible())

    def _apply_filter_button_style(self) -> None:
        p = PALETTE
        self._filter_btn.setStyleSheet(filter_toggle_button_style())
        color = p.senai_orange if self._filter_btn.isChecked() else p.text_muted
        self._filter_btn.setIcon(app_icon("sliders-h", color=color))

    def refresh_appearance(self) -> None:
        p = PALETTE
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {p.text_muted};
                background: transparent;
                border: none;
                font-size: 16px;
                font-weight: {TYPOGRAPHY.weight_bold};
                border-radius: {SPACING.radius_sm}px;
            }}
            QPushButton:hover {{
                color: {p.text_primary};
                background: {p.bg_surface_alt};
            }}
        """)
        self._hint_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: 12px; "
            f"background: transparent; border: none; padding-left: 4px;"
        )
        if self._field.hasFocus():
            self._apply_focus_style()
        else:
            self._apply_idle_style()
        self._apply_filter_button_style()
        self._filter_wrap.set_badge_visible(
            self._filter_has_active and self._filter_wrap.isVisible()
        )
        self._update_hint_display()

    def _on_text_changed(self, text: str) -> None:
        self._clear_btn.setVisible(bool(text))
        self.textChanged.emit(text)

    def _apply_idle_style(self) -> None:
        self._container.setStyleSheet(search_bar_container_style(focused=False))

    def _apply_focus_style(self) -> None:
        self._container.setStyleSheet(search_bar_container_style(focused=True))

    def _on_focus_in(self, event) -> None:
        self._apply_focus_style()
        QLineEdit.focusInEvent(self._field, event)

    def _on_focus_out(self, event) -> None:
        self._apply_idle_style()
        QLineEdit.focusOutEvent(self._field, event)

    def clear(self) -> None:
        self._field.clear()
        self.set_result_hint("")

    def focus_search(self) -> None:
        self._field.setFocus()
        self._field.selectAll()

    def set_result_hint(self, text: str) -> None:
        self._result_hint = text
        self._update_hint_display()

    def set_filter_summary(self, text: str) -> None:
        self._filter_summary = text
        self._update_hint_display()

    def _update_hint_display(self) -> None:
        p = PALETTE
        if self._result_hint:
            self._hint_label.setStyleSheet(
                f"color: {p.text_muted}; font-size: 12px; "
                f"background: transparent; border: none; padding-left: 4px;"
            )
            self._hint_label.setText(self._result_hint)
            self._hint_label.show()
        elif self._filter_summary:
            self._hint_label.setStyleSheet(
                f"color: {p.senai_orange}; font-size: 12px; "
                f"font-weight: {TYPOGRAPHY.weight_medium}; "
                f"background: transparent; border: none; padding-left: 4px;"
            )
            self._hint_label.setText(self._filter_summary)
            self._hint_label.show()
        else:
            self._hint_label.hide()

    @property
    def field(self) -> QLineEdit:
        return self._field


class LayoutTemplateSelector(QWidget):
    """Seletor compacto de layout/template — meta row do header da preview."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("LayoutTemplateSelector")

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACING.xs)
        row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._label = QLabel("Layout")
        self._label.setObjectName("WorkspaceMetaLabel")

        self._dirty_dot = QLabel("●")
        self._dirty_dot.setObjectName("WorkspaceLayoutDirty")
        self._dirty_dot.setToolTip("Layout alterado — salve pelo menu ⋯")
        self._dirty_dot.hide()

        self._combo = QComboBox()
        self._combo.setObjectName("FilterCombo")
        self._combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._combo.setMinimumWidth(200)
        self._combo.setMaximumWidth(280)
        self._combo.setToolTip("Layout aplicado ao relatório")
        popup = self._combo.view()
        popup.setObjectName("FilterComboPopup")

        row.addWidget(self._label)
        row.addWidget(self._dirty_dot)
        row.addWidget(self._combo)

    @property
    def combo(self) -> QComboBox:
        return self._combo

    def set_layout_dirty(self, dirty: bool) -> None:
        self._dirty_dot.setVisible(dirty)
        tip = "Layout alterado — use ⋯ → Salvar layout…" if dirty else "Layout aplicado ao relatório"
        self._combo.setToolTip(tip)
