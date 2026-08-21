"""
Componentes de feedback ao usuário — dark edition.

InlineBanner → faixa estilo GitHub Alert (border-left colorida)
show_friendly_error / show_info / confirm_action / prompt_text → design system
"""
from __future__ import annotations

from enum import Enum, auto
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QWidget

from src.ui.components.app_dialog import AppDialog, AppMessageDialog, DialogKind, present_app_dialog
from src.ui.components.buttons import PrimaryButton, SecondaryButton
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY
from src.ui.styles.helpers import inline_banner_style


class FeedbackLevel(Enum):
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    DANGER = auto()


def _level_colors(level: FeedbackLevel) -> tuple[str, str]:
    p = PALETTE
    mapping = {
        FeedbackLevel.INFO: (p.info, p.info_bg),
        FeedbackLevel.SUCCESS: (p.success, p.success_bg),
        FeedbackLevel.WARNING: (p.warning, p.warning_bg),
        FeedbackLevel.DANGER: (p.danger, p.danger_bg),
    }
    return mapping[level]


_LEVEL_ICONS = {
    FeedbackLevel.INFO: "ℹ",
    FeedbackLevel.SUCCESS: "✓",
    FeedbackLevel.WARNING: "⚠",
    FeedbackLevel.DANGER: "✕",
}


class InlineBanner(QWidget):
    """Faixa de aviso inline estilo GitHub Alert — border-left colorida,
    ícone circular e texto semântico. Não bloqueante.
    """

    def __init__(
        self,
        message: str,
        level: FeedbackLevel = FeedbackLevel.INFO,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._level = level
        icon_char = _LEVEL_ICONS[level]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._icon_label = QLabel(icon_char)
        self._icon_label.setFixedSize(22, 22)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignTop)

        self._message_label = QLabel(message)
        self._message_label.setWordWrap(True)
        layout.addWidget(self._message_label, stretch=1)

        self.setMaximumHeight(56)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        color, bg = _level_colors(self._level)
        self.setStyleSheet(inline_banner_style(color=color, bg=bg))
        self._icon_label.setStyleSheet(f"""
            color: {color};
            background-color: transparent;
            font-size: {TYPOGRAPHY.size_body}px;
            font-weight: {TYPOGRAPHY.weight_bold};
        """)
        self._message_label.setStyleSheet(
            f"color: {color}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
        )

    def set_message(self, message: str) -> None:
        self._message_label.setText(message)

    def set_level(self, level: FeedbackLevel) -> None:
        self._level = level
        self._icon_label.setText(_LEVEL_ICONS[level])
        self.refresh_appearance()
        self.sync_visibility()

    @property
    def level(self) -> FeedbackLevel:
        return self._level

    def sync_visibility(self) -> None:
        """Visível apenas para avisos e erros — INFO/SUCCESS não ocupam espaço na preview."""
        self.setVisible(self._level in (FeedbackLevel.WARNING, FeedbackLevel.DANGER))


def show_friendly_error(
    parent: Optional[QWidget],
    title: str,
    message: str,
    details: Optional[str] = None,
) -> None:
    """Exibe um erro de forma amigável, sem expor stack traces ao operador."""
    AppMessageDialog.inform(
        parent,
        title,
        message,
        kind=DialogKind.WARNING,
        details=details,
    )


def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
    """Exibe uma confirmação neutra/positiva (ex.: exportação concluída)."""
    AppMessageDialog.inform(parent, title, message, kind=DialogKind.SUCCESS)


def confirm_action(parent: Optional[QWidget], title: str, message: str) -> bool:
    """Diálogo de confirmação padrão (ex.: excluir template, descartar edição)."""
    return AppMessageDialog.confirm(parent, title, message)


def confirm_dangerous_action(parent: Optional[QWidget], title: str, message: str) -> bool:
    """Confirmação para ações destrutivas."""
    return AppMessageDialog.confirm(
        parent,
        title,
        message,
        confirm_label="Excluir",
        cancel_label="Cancelar",
        danger=True,
    )


class _TextPromptDialog(AppDialog):
    """Prompt de texto alinhado ao tema (substitui QInputDialog no Windows)."""

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        label: str,
        *,
        default: str = "",
        placeholder: str = "",
        ok_label: str = "OK",
        cancel_label: str = "Cancelar",
    ) -> None:
        super().__init__(parent, window_title=title, minimum_width=420)
        self._value = ""

        self._field = LabeledLineEdit(label, placeholder=placeholder)
        self._field.set_text(default)
        self._field.field.returnPressed.connect(self.accept)

        layout = self.create_root_layout()
        self.add_dialog_header(layout, title)
        layout.addWidget(self._field)

        self.add_dialog_divider(layout)
        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        footer.addStretch(1)
        cancel_btn = SecondaryButton(cancel_label)
        cancel_btn.clicked.connect(self.reject)
        ok_btn = PrimaryButton(ok_label)
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.accept)
        footer.addWidget(cancel_btn)
        footer.addWidget(ok_btn)
        layout.addLayout(footer)

    def showEvent(self, event) -> None:  # noqa: ANN001, N802
        super().showEvent(event)
        self._field.field.setFocus()
        if self._field.field.text():
            self._field.field.selectAll()

    def accept(self) -> None:  # noqa: N802
        self._value = self._field.text()
        super().accept()

    @property
    def value(self) -> str:
        return self._value


def prompt_text(
    parent: Optional[QWidget],
    title: str,
    label: str,
    *,
    default: str = "",
    placeholder: str = "",
    allow_empty: bool = False,
) -> str | None:
    """Pede um texto ao usuário com o chrome do app (não o diálogo nativo do SO)."""
    dialog = _TextPromptDialog(
        parent,
        title,
        label,
        default=default,
        placeholder=placeholder,
    )
    if present_app_dialog(parent, dialog) != QDialog.DialogCode.Accepted:
        return None
    cleaned = dialog.value.strip()
    if not cleaned and not allow_empty:
        return None
    return cleaned
