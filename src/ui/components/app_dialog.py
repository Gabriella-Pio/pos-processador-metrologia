"""Diálogos modais alinhados ao design system dark da aplicação."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.buttons import DangerButton, IconButton, PrimaryButton, SecondaryButton
from src.ui.components.icons import icon_close
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, caption_style, heading_style


class DialogKind(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


_KIND_META = {
    DialogKind.INFO: ("ℹ", PALETTE.info, PALETTE.info_bg),
    DialogKind.SUCCESS: ("✓", PALETTE.success, PALETTE.success_bg),
    DialogKind.WARNING: ("⚠", PALETTE.warning, PALETTE.warning_bg),
    DialogKind.DANGER: ("✕", PALETTE.danger, PALETTE.danger_bg),
}


def present_app_dialog(parent: QWidget | None, dialog: QDialog) -> int:
    """Exibe diálogo com overlay quando há pai; senão usa ``exec()``."""
    if parent is not None:
        from src.ui.components.modal_presentation import present_modal_dialog

        return present_modal_dialog(parent, dialog)
    return dialog.exec()


_SHADOW_MARGIN = 20


class AppDialog(QDialog):
    """Base para diálogos — chrome padronizado, Esc fecha, overlay opcional."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        window_title: str = "",
        minimum_width: int = 440,
    ) -> None:
        super().__init__(parent)
        self._overlay: QWidget | None = None
        self.setObjectName("AppDialog")
        self.setWindowTitle(window_title)
        self.setMinimumWidth(minimum_width + _SHADOW_MARGIN * 2)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.FramelessWindowHint
        )

        shell = QVBoxLayout(self)
        shell.setContentsMargins(
            _SHADOW_MARGIN,
            _SHADOW_MARGIN,
            _SHADOW_MARGIN,
            _SHADOW_MARGIN,
        )

        self._surface = QFrame()
        self._surface.setObjectName("AppDialogSurface")
        self._surface.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        shell.addWidget(self._surface)

        self._content_layout = QVBoxLayout(self._surface)
        self._content_layout.setContentsMargins(SPACING.xl, SPACING.xl, SPACING.xl, SPACING.lg)
        self._content_layout.setSpacing(SPACING.md)
        self._surface.setMinimumWidth(minimum_width)

        esc = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        esc.setContext(Qt.ShortcutContext.WindowShortcut)
        esc.activated.connect(self.reject)

        self.hide()

    def done(self, result: int) -> None:  # noqa: N802
        super().done(result)
        self.hide()

    def keyPressEvent(self, event) -> None:  # noqa: ANN001, N802
        if event.key() == Qt.Key.Key_Escape:
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)

    def set_overlay(self, overlay: QWidget | None) -> None:
        self._overlay = overlay

    def set_overlay_visible(self, visible: bool) -> None:
        if self._overlay is not None:
            self._overlay.setVisible(visible)

    def create_root_layout(self) -> QVBoxLayout:
        return self._content_layout

    def add_dialog_header(
        self,
        layout: QVBoxLayout,
        title: str,
        subtitle: str | None = None,
    ) -> None:
        header_row = QHBoxLayout()
        header_row.setSpacing(SPACING.md)

        text_col = QVBoxLayout()
        text_col.setSpacing(SPACING.xs)
        title_label = QLabel(title)
        title_label.setObjectName("AppDialogTitle")
        title_label.setStyleSheet(heading_style(1))
        text_col.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("AppDialogSubtitle")
            subtitle_label.setWordWrap(True)
            subtitle_label.setStyleSheet(caption_style())
            text_col.addWidget(subtitle_label)

        close_btn = IconButton(icon_close(), "Fechar (Esc)")
        close_btn.setFixedSize(34, 34)
        close_btn.clicked.connect(self.reject)

        header_row.addLayout(text_col, stretch=1)
        header_row.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_row)

    def add_dialog_scroll_content(self, layout: QVBoxLayout, content: QWidget) -> QScrollArea:
        """Painel informativo com scroll — para conteúdo estruturado (não campo editável)."""
        panel = QFrame()
        panel.setObjectName("AppDialogInfoPanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.md)

        scroll = QScrollArea()
        scroll.setObjectName("AppDialogInfoScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)

        panel_layout.addWidget(scroll)
        layout.addWidget(panel, stretch=1)
        return scroll

    def add_dialog_divider(self, layout: QVBoxLayout) -> None:
        divider = QFrame()
        divider.setObjectName("AppDialogDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        layout.addWidget(divider)

    def add_dialog_footer(
        self,
        layout: QVBoxLayout,
        *,
        primary_label: str = "Fechar",
        secondary_buttons: list[QWidget] | None = None,
    ) -> PrimaryButton:
        self.add_dialog_divider(layout)
        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        for widget in secondary_buttons or []:
            footer.addWidget(widget)
        footer.addStretch(1)
        primary = PrimaryButton(primary_label)
        primary.setMinimumWidth(120)
        primary.clicked.connect(self.accept)
        footer.addWidget(primary)
        layout.addLayout(footer)
        return primary

    def add_dialog_action_footer(
        self,
        layout: QVBoxLayout,
        *,
        primary_label: str,
        secondary_label: str | None = None,
        danger_primary: bool = False,
        on_primary=None,
    ) -> PrimaryButton | DangerButton:
        """Rodapé com ação primária e cancelamento opcional."""
        self.add_dialog_divider(layout)
        footer = QHBoxLayout()
        footer.setSpacing(SPACING.sm)
        footer.addStretch(1)
        if secondary_label:
            cancel = SecondaryButton(secondary_label)
            cancel.clicked.connect(self.reject)
            footer.addWidget(cancel)
        primary_cls = DangerButton if danger_primary else PrimaryButton
        primary = primary_cls(primary_label)
        primary.setMinimumWidth(120)
        if on_primary is not None:
            primary.clicked.connect(on_primary)
        footer.addWidget(primary)
        layout.addLayout(footer)
        return primary


class AppMessageDialog(AppDialog):
    """Confirmação ou aviso — mesmo chrome dos modais (sem barra nativa, X interno)."""

    def __init__(
        self,
        parent: Optional[QWidget],
        title: str,
        message: str,
        *,
        kind: DialogKind = DialogKind.INFO,
        details: str | None = None,
        primary_label: str = "Entendi",
        secondary_label: str | None = None,
        danger_primary: bool = False,
    ) -> None:
        super().__init__(parent, window_title=title, minimum_width=440)
        self._confirmed = False
        self._surface.setMaximumWidth(520)
        self.setModal(True)

        layout = self.create_root_layout()
        self._add_kind_header(layout, kind, title, message)

        if details:
            details_box = QFrame()
            details_box.setObjectName("GlobalFieldCard")
            details_layout = QVBoxLayout(details_box)
            details_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
            details_view = QTextEdit()
            details_view.setObjectName("AppDialogDetails")
            details_view.setReadOnly(True)
            details_view.setPlainText(details)
            details_view.setMinimumHeight(100)
            details_layout.addWidget(details_view)
            layout.addWidget(details_box)

        self.add_dialog_action_footer(
            layout,
            primary_label=primary_label,
            secondary_label=secondary_label,
            danger_primary=danger_primary,
            on_primary=self._accept,
        )

    def _add_kind_header(
        self,
        layout: QVBoxLayout,
        kind: DialogKind,
        title: str,
        message: str,
    ) -> None:
        icon_char, accent, accent_bg = _KIND_META[kind]
        header_row = QHBoxLayout()
        header_row.setSpacing(SPACING.md)

        icon = QLabel(icon_char)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setFixedSize(40, 40)
        icon.setStyleSheet(
            f"color: {accent}; background-color: {accent_bg}; "
            f"border-radius: 20px; font-size: {TYPOGRAPHY.size_h2}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold};"
        )

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet(heading_style(3))

        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setObjectName("SidebarHint")
        message_label.setStyleSheet(caption_style())

        text_col = QVBoxLayout()
        text_col.setSpacing(SPACING.xs)
        text_col.addWidget(title_label)
        text_col.addWidget(message_label)

        close_btn = IconButton(icon_close(), "Fechar (Esc)")
        close_btn.setFixedSize(34, 34)
        close_btn.clicked.connect(self.reject)

        header_row.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        header_row.addLayout(text_col, stretch=1)
        header_row.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header_row)

    def _accept(self) -> None:
        self._confirmed = True
        self.accept()

    @property
    def confirmed(self) -> bool:
        return self._confirmed

    @classmethod
    def inform(
        cls,
        parent: Optional[QWidget],
        title: str,
        message: str,
        *,
        kind: DialogKind = DialogKind.INFO,
        details: str | None = None,
    ) -> None:
        dialog = cls(parent, title, message, kind=kind, details=details)
        present_app_dialog(parent, dialog)

    @classmethod
    def confirm(
        cls,
        parent: Optional[QWidget],
        title: str,
        message: str,
        *,
        confirm_label: str = "Confirmar",
        cancel_label: str = "Cancelar",
        danger: bool = False,
    ) -> bool:
        dialog = cls(
            parent,
            title,
            message,
            kind=DialogKind.DANGER if danger else DialogKind.WARNING,
            primary_label=confirm_label,
            secondary_label=cancel_label,
            danger_primary=danger,
        )
        present_app_dialog(parent, dialog)
        return dialog.confirmed
