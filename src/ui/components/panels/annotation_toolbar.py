"""Barra de ferramentas de anotação na foto selecionada."""
from __future__ import annotations

from PyQt6.QtCore import QSize, pyqtSignal
from PyQt6.QtWidgets import QButtonGroup, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.ui.components.icons import app_icon
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY
from src.ui.styles.helpers import workspace_annotation_button_style, workspace_annotation_toolbar_style


class AnnotationToolbar(QFrame):
    """Barra de ferramentas de anotação: seta, círculo, caixa de texto, numeração.

    Desenhar na imagem ainda não está implementado — a UI deixa isso explícito.
    """

    tool_selected = pyqtSignal(str)

    _TOOLS = (
        ("arrow", "arrow-right", "Seta"),
        ("circle", "circle", "Círculo"),
        ("text_box", "square", "Texto"),
        ("number", "list-ol", "Nº"),
    )

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("AnnotationToolbar")
        self._tools_active = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        outer.setSpacing(SPACING.xs)

        self._title = QLabel("Marcações na foto")
        self._title.setObjectName("GlobalFieldLabel")
        outer.addWidget(self._title)

        self._notice = QLabel(
            "Ainda não é possível desenhar setas/círculos na imagem — "
            "isso entra no próximo passo. Por ora, selecione a foto e edite a legenda."
        )
        self._notice.setWordWrap(True)
        self._notice.setObjectName("SidebarHint")
        outer.addWidget(self._notice)

        tools_row = QHBoxLayout()
        tools_row.setSpacing(SPACING.sm)
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)
        self._tool_buttons: list[QPushButton] = []
        self._build_tool_buttons(tools_row)
        tools_row.addStretch(1)
        outer.addLayout(tools_row)

        self.set_tools_enabled(False)
        self.refresh_appearance()

    def _build_tool_buttons(self, layout: QHBoxLayout) -> None:
        for tool_id, icon_name, label in self._TOOLS:
            button = QPushButton(label)
            button.setCheckable(True)
            button.setToolTip(label)
            button.setMinimumSize(64, 40)
            button.setProperty("tool_id", tool_id)
            button.setProperty("icon_name", icon_name)
            button.clicked.connect(lambda _checked, t=tool_id: self.tool_selected.emit(t))
            self._group.addButton(button)
            self._tool_buttons.append(button)
            layout.addWidget(button)

    def set_tools_enabled(self, enabled: bool) -> None:
        self._tools_active = False
        self._group.setExclusive(False)
        for button in self._tool_buttons:
            button.setChecked(False)
            button.setEnabled(False)
        self._group.setExclusive(True)
        if enabled:
            self._title.setText("Marcações na foto selecionada")
            self._notice.setText(
                "Em breve: desenhar seta, círculo, texto e numeração sobre a foto. "
                "Hoje isso ainda não está ligado ao preview."
            )
        else:
            self._title.setText("Marcações")
            self._notice.setText(
                "Selecione uma foto acima. Desenhar setas/círculos na imagem "
                "ainda não está disponível."
            )

    def refresh_appearance(self) -> None:
        p = PALETTE
        self.setStyleSheet(workspace_annotation_toolbar_style())
        self._title.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; background: transparent;"
        )
        self._notice.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        button_style = workspace_annotation_button_style()
        for button in self._tool_buttons:
            icon_name = button.property("icon_name")
            button.setIcon(app_icon(str(icon_name), color=p.text_secondary))
            button.setIconSize(QSize(16, 16))
            button.setStyleSheet(button_style)
