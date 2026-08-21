"""Campos de entrada reutilizáveis — dark edition com label uppercase e ícone de busca."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QPoint, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QPalette
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
        self._sync_placeholder_palette()

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
                font-size: {TYPOGRAPHY.size_h3}px;
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
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
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
        self._field.setStyleSheet(search_field_inner_style())
        self._sync_placeholder_palette()
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                color: {p.text_muted};
                background: transparent;
                border: none;
                font-size: {TYPOGRAPHY.size_h3}px;
                font-weight: {TYPOGRAPHY.weight_bold};
                border-radius: {SPACING.radius_sm}px;
            }}
            QPushButton:hover {{
                color: {p.text_primary};
                background: {p.bg_surface_alt};
            }}
        """)
        self._hint_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
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

    def _sync_placeholder_palette(self) -> None:
        palette = self._field.palette()
        color = QColor(PALETTE.text_secondary)
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            palette.setColor(group, QPalette.ColorRole.PlaceholderText, color)
        self._field.setPalette(palette)

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
                f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
                f"background: transparent; border: none; padding-left: 4px;"
            )
            self._hint_label.setText(self._result_hint)
            self._hint_label.show()
        elif self._filter_summary:
            self._hint_label.setStyleSheet(
                f"color: {p.senai_orange}; font-size: {TYPOGRAPHY.size_caption}px; "
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

        self._combo = ThemedComboBox()
        self._combo.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self._combo.setMinimumWidth(200)
        self._combo.setMaximumWidth(280)
        self._combo.setToolTip("Layout aplicado ao relatório")

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


_POPUP_MAX_ROWS = 8
_POPUP_ITEM_HEIGHT = 36


def _filter_combo_popup_stylesheet() -> str:
    """Estilo aplicado direto no view/popup — o QSS global nem sempre pinta a janela flutuante."""
    from src.ui.styles import PALETTE, SPACING

    p, s = PALETTE, SPACING
    return f"""
        QListView#FilterComboPopup {{
            background-color: {p.bg_elevated};
            color: {p.text_primary};
            border: 1px solid {p.border_strong};
            border-radius: {s.radius_sm}px;
            padding: 4px;
            outline: none;
        }}
        QListView#FilterComboPopup::item {{
            padding: 8px 20px;
            border-radius: 4px;
            min-height: 24px;
            color: {p.text_primary};
        }}
        QListView#FilterComboPopup::item:hover {{
            background-color: rgba(240, 67, 30, 0.22);
        }}
        QListView#FilterComboPopup::item:selected {{
            background-color: rgba(240, 67, 30, 0.22);
            color: {p.text_primary};
        }}
        QFrame#FilterComboPopupWindow,
        QWidget#FilterComboPopupWindow {{
            background-color: {p.bg_elevated};
            border: 1px solid {p.border_strong};
            border-radius: {s.radius_sm}px;
        }}
    """


def configure_themed_combo(combo: QComboBox) -> None:
    """Aplica o mesmo visual dos filtros refinados e do menu ⋯."""
    combo.setObjectName("FilterCombo")
    view = combo.view()
    view.setObjectName("FilterComboPopup")
    view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    view.setStyleSheet(_filter_combo_popup_stylesheet())
    combo.setMaxVisibleItems(_POPUP_MAX_ROWS)
    view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setUniformItemSizes(True)
    view.setMouseTracking(True)


class ThemedComboBox(QComboBox):
    """Combo com popup limitado, scroll e hover igual ao menu ⋯."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        configure_themed_combo(self)

    def refresh_appearance(self) -> None:
        self.view().setStyleSheet(_filter_combo_popup_stylesheet())

    def showPopup(self) -> None:
        view = self.view()
        view.setMinimumWidth(self.width())
        # Tokens + altura ANTES do show — mutar depois deslocava o popup pro topo.
        view.setStyleSheet(_filter_combo_popup_stylesheet())
        rows = min(max(self.count(), 1), self.maxVisibleItems())
        row_height = (
            max(view.sizeHintForRow(0), _POPUP_ITEM_HEIGHT)
            if self.count() > 0
            else _POPUP_ITEM_HEIGHT
        )
        popup_height = rows * row_height + 14
        view.setMaximumHeight(popup_height)

        super().showPopup()

        popup = view.window()
        if popup is None or popup is self:
            return
        popup.setObjectName("FilterComboPopupWindow")
        popup.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        # Só estilo da janela; não mexer de novo na altura do view (já aplicada).
        from src.ui.styles import PALETTE, SPACING

        p, s = PALETTE, SPACING
        popup.setStyleSheet(
            f"QFrame#FilterComboPopupWindow, QWidget#FilterComboPopupWindow {{"
            f" background-color: {p.bg_elevated};"
            f" border: 1px solid {p.border_strong};"
            f" border-radius: {s.radius_sm}px;"
            f"}}"
        )
        self._anchor_popup(popup, popup_height)
        # Qt às vezes reaplica geometria no próximo tick — ancora de novo.
        QTimer.singleShot(0, lambda: self._anchor_popup(popup, popup_height))

    def _anchor_popup(self, popup: QWidget, popup_height: int) -> None:
        """Garante que a lista fique colada ao combo (abaixo ou acima se faltar espaço)."""
        if popup is None or not popup.isVisible():
            return
        width = max(self.width(), popup.width())
        below = self.mapToGlobal(QPoint(0, self.height()))
        above = self.mapToGlobal(QPoint(0, 0))
        x = below.x()
        y = below.y()

        screen = None
        window = self.window()
        if window is not None and window.windowHandle() is not None:
            screen = window.windowHandle().screen()
        if screen is None:
            screen = QGuiApplication.screenAt(below)
        if screen is not None:
            geo = screen.availableGeometry()
            if y + popup_height > geo.bottom() and above.y() - popup_height >= geo.top():
                y = above.y() - popup_height
            x = min(max(x, geo.left()), max(geo.left(), geo.right() - width + 1))
            y = min(max(y, geo.top()), max(geo.top(), geo.bottom() - popup_height + 1))

        popup.setFixedWidth(width)
        popup.setMaximumHeight(popup_height)
        popup.move(x, y)
