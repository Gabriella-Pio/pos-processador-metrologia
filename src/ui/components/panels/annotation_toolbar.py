"""Barra de ferramentas compacta para marcações na foto."""
from __future__ import annotations

from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QPushButton

from src.core.application.annotation_clipboard import has_clipboard
from src.ui.components.icons import app_icon
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY
from src.ui.styles.helpers import workspace_annotation_button_style, workspace_annotation_toolbar_style


class AnnotationToolbar(QFrame):
    tool_selected = pyqtSignal(str)
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_reset_requested = pyqtSignal()
    undo_requested = pyqtSignal()
    clear_crop_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    paste_requested = pyqtSignal()
    delete_selected_requested = pyqtSignal()
    select_mode_requested = pyqtSignal()

    _TOOLS = (
        ("", "hand-pointer", "Selecionar"),
        ("arrow", "arrow-right", "Seta"),
        ("circle", "circle", "Círculo"),
        ("text_box", "square", "Texto"),
        ("number", "list-ol", "Nº"),
        ("crop", "crop-alt", "Crop"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AnnotationToolbar")

        row = QHBoxLayout(self)
        row.setContentsMargins(SPACING.xs, SPACING.xs, SPACING.xs, SPACING.xs)
        row.setSpacing(SPACING.xs)

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._tool_buttons: list[QPushButton] = []
        for tool_id, icon_name, label in self._TOOLS:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setToolTip(label)
            button.setMinimumHeight(34)
            button.setProperty("tool_id", tool_id)
            button.setProperty("icon_name", icon_name)
            button.clicked.connect(lambda _checked, t=tool_id: self._on_tool_clicked(t))
            self._group.addButton(button)
            self._tool_buttons.append(button)
            row.addWidget(button)

        row.addSpacing(SPACING.sm)
        self._zoom_out_btn = self._mini_button("−", "Diminuir zoom")
        self._zoom_reset_btn = self._mini_button("100%", "Zoom original")
        self._zoom_in_btn = self._mini_button("+", "Aumentar zoom")
        self._copy_btn = self._mini_button("Copiar", "Copiar marcações (Ctrl+C)")
        self._paste_btn = self._mini_button("Colar", "Colar marcações (Ctrl+V)")
        self._delete_btn = self._mini_button("Apagar", "Apagar seleção (Del)")
        self._undo_btn = self._mini_button("Desfazer", "Desfazer última (Ctrl+Z)")
        self._clear_crop_btn = self._mini_button("Limpar crop", "Remover recorte")

        for button in (
            self._zoom_out_btn,
            self._zoom_reset_btn,
            self._zoom_in_btn,
            self._copy_btn,
            self._paste_btn,
            self._delete_btn,
            self._undo_btn,
            self._clear_crop_btn,
        ):
            row.addWidget(button)
        row.addStretch(1)

        self._zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        self._zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        self._zoom_reset_btn.clicked.connect(self.zoom_reset_requested.emit)
        self._undo_btn.clicked.connect(self.undo_requested.emit)
        self._clear_crop_btn.clicked.connect(self.clear_crop_requested.emit)
        self._copy_btn.clicked.connect(self.copy_requested.emit)
        self._paste_btn.clicked.connect(self.paste_requested.emit)
        self._delete_btn.clicked.connect(self.delete_selected_requested.emit)

        self.set_tools_enabled(False)
        self.refresh_appearance()

    def _mini_button(self, label: str, tooltip: str) -> QPushButton:
        button = QPushButton(label)
        button.setToolTip(tooltip)
        button.setMinimumHeight(34)
        return button

    def _on_tool_clicked(self, tool_id: str) -> None:
        if not tool_id:
            self.select_mode_requested.emit()
            self.tool_selected.emit("")
            return
        self.tool_selected.emit(tool_id)

    def set_zoom_percent(self, zoom: float) -> None:
        percent = int(round(zoom * 100))
        self._zoom_reset_btn.setText(f"{percent}%")

    def set_tools_enabled(self, enabled: bool) -> None:
        self._group.setExclusive(False)
        for button in self._tool_buttons:
            if not enabled:
                button.setChecked(False)
            button.setEnabled(enabled)
        self._group.setExclusive(True)
        if enabled and not any(button.isChecked() for button in self._tool_buttons):
            self._tool_buttons[0].setChecked(True)
        for button in (
            self._zoom_out_btn,
            self._zoom_reset_btn,
            self._zoom_in_btn,
            self._copy_btn,
            self._paste_btn,
            self._delete_btn,
            self._undo_btn,
            self._clear_crop_btn,
        ):
            button.setEnabled(enabled)
        self._update_paste_enabled()

    def _update_paste_enabled(self) -> None:
        self._paste_btn.setEnabled(self._paste_btn.isEnabled() and has_clipboard())

    def refresh_appearance(self) -> None:
        self.setStyleSheet(workspace_annotation_toolbar_style())
        button_style = workspace_annotation_button_style()
        for button in self._tool_buttons:
            icon_name = button.property("icon_name")
            button.setIcon(app_icon(str(icon_name), color=PALETTE.text_secondary))
            button.setIconSize(QSize(14, 14))
            button.setStyleSheet(button_style)
        for button in (
            self._zoom_out_btn,
            self._zoom_reset_btn,
            self._zoom_in_btn,
            self._copy_btn,
            self._paste_btn,
            self._delete_btn,
            self._undo_btn,
            self._clear_crop_btn,
        ):
            button.setStyleSheet(
                button_style
                + f"font-size: {TYPOGRAPHY.size_caption}px; padding: 4px 8px;"
            )
        self._update_paste_enabled()
