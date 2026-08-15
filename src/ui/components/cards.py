"""
Cards reutilizáveis para o Dashboard — dark edition.

ActionCard     → card base reutilizável (ícone pill + título + subtítulo)
TemplateCard   → especialização do ActionCard para templates
RecentFileRow  → linha da lista de recentes com hierarquia visual
"""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.buttons import IconButton
from src.ui.components.icons import icon_close

from src.ui.features.home.models.dashboard import RecentFileSummary, TemplateSummary
from src.ui.styles import (
    PALETTE,
    SPACING,
    TYPOGRAPHY,
    action_card_hover_style,
    action_card_icon_style,
    action_card_idle_style,
    action_card_subtitle_style,
    action_card_title_style,
    badge_style,
    caption_style,
    dashboard_card_media_style,
    default_template_badge_style,
    pdf_icon_pill_style,
    recent_file_row_style,
    scaled_dashboard_card_size,
)

__all__ = [
    "ActionCard",
    "ElidingLabel",
    "RecentFileCard",
    "RecentFileRow",
    "RecentFileSummary",
    "TemplateCard",
    "TemplateSummary",
]


class ElidingLabel(QLabel):
    """Rótulo que trunca texto longo com reticências conforme a largura."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._refresh()

    def set_full_text(self, text: str) -> None:
        self._full_text = text
        self._refresh()

    def resizeEvent(self, event) -> None:  # noqa: N802
        self._refresh()
        super().resizeEvent(event)

    def _refresh(self) -> None:
        width = self.width()
        if width <= 0:
            self.setText(self._full_text)
            return
        self.setText(
            self.fontMetrics().elidedText(
                self._full_text,
                Qt.TextElideMode.ElideRight,
                width,
            )
        )


class ActionCard(QFrame):
    """Card base da grade — faixa de mídia + corpo tipográfico."""

    clicked = pyqtSignal()

    def __init__(
        self,
        icon: str,
        title: str,
        subtitle: str = "",
        accent_color: str = "",
        accent_bg: str = "",
        card_width: int | None = None,
        card_height: int | None = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        p = PALETTE
        resolved_accent = accent_color or p.senai_blue_light
        resolved_bg = accent_bg or "rgba(74, 111, 212, 0.18)"
        scaled_w, scaled_h = scaled_dashboard_card_size()
        width = card_width if card_width is not None else scaled_w
        height = card_height if card_height is not None else scaled_h
        orange = resolved_accent.lower() in {p.senai_orange.lower(), "#f0431e"}

        if card_width is not None:
            self.setFixedWidth(width)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        else:
            self.setMinimumWidth(width)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._idle_style = action_card_idle_style()
        self._hover_style = action_card_hover_style(resolved_accent)
        self.setStyleSheet(self._idle_style)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        media = QFrame()
        media.setObjectName("DashboardCardMedia")
        media.setFixedHeight(max(72, round(78 * TYPOGRAPHY.size_body / 13)))
        media.setStyleSheet(dashboard_card_media_style(orange=orange))
        media_layout = QVBoxLayout(media)
        media_layout.setContentsMargins(SPACING.md, SPACING.md, SPACING.md, SPACING.sm)
        media_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_size = max(40, round(44 * TYPOGRAPHY.size_body / 13))
        icon_label = QLabel(icon)
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet(
            action_card_icon_style(
                accent_color=resolved_accent,
                accent_bg=resolved_bg,
                icon=icon,
            )
        )
        media_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignCenter)
        root.addWidget(media)

        body = QVBoxLayout()
        body.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        body.setSpacing(4)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title_label.setMaximumHeight(max(40, TYPOGRAPHY.size_body * 3 + 4))
        title_label.setStyleSheet(action_card_title_style())
        body.addWidget(title_label)

        if subtitle:
            sub_label = QLabel(subtitle)
            sub_label.setWordWrap(True)
            sub_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            sub_label.setMaximumHeight(max(30, TYPOGRAPHY.size_caption * 3))
            sub_label.setStyleSheet(action_card_subtitle_style())
            body.addWidget(sub_label)

        body.addStretch(1)
        root.addLayout(body)

    def enterEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._idle_style)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.clicked.emit()
        super().mousePressEvent(event)


class RecentFileCard(ActionCard):
    """Card de arquivo recente — modo grade, herda o visual do ActionCard."""

    opened = pyqtSignal(str)

    def __init__(self, summary: RecentFileSummary, parent=None) -> None:
        p = PALETTE
        date_str = summary.updated_at.strftime("%d/%m/%Y")
        super().__init__(
            icon="PDF",
            title=summary.file_name,
            subtitle=f"{summary.client_project} · {date_str}",
            accent_color=p.senai_orange,
            accent_bg="rgba(240, 67, 30, 0.15)",
            parent=parent,
        )
        self._file_id = summary.file_id
        self.clicked.connect(lambda: self.opened.emit(self._file_id))


class TemplateCard(ActionCard):
    """Card de template que emite ``selected(template_id)`` ao ser clicado."""

    selected = pyqtSignal(str)
    delete_requested = pyqtSignal(str)

    def __init__(self, summary: TemplateSummary, parent: Optional[QWidget] = None) -> None:
        p = PALETTE
        super().__init__(
            icon="PDF",
            title=summary.name,
            accent_color=p.senai_blue_light,
            accent_bg="rgba(74, 111, 212, 0.15)",
            parent=parent,
        )
        self._template_id = summary.template_id
        self._deletable = summary.deletable
        self.clicked.connect(lambda: self.selected.emit(self._template_id))

        if summary.is_default:
            layout = self.layout()
            layout.addSpacing(6)
            badge = QLabel("Padrão SENAI/ZEISS")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(default_template_badge_style())
            layout.addWidget(badge)

        if self._deletable:
            self._delete_btn = IconButton(icon_close(), "Excluir template")
            self._delete_btn.setParent(self)
            self._delete_btn.setFixedSize(24, 24)
            self._delete_btn.clicked.connect(
                lambda: self.delete_requested.emit(self._template_id)
            )
            self._reposition_delete_btn()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "_delete_btn"):
            self._reposition_delete_btn()

    def _reposition_delete_btn(self) -> None:
        margin = SPACING.xs
        btn = self._delete_btn
        btn.move(self.width() - btn.width() - margin, margin)
        btn.raise_()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if hasattr(self, "_delete_btn") and self._delete_btn.geometry().contains(
            event.position().toPoint()
        ):
            event.accept()
            return
        super().mousePressEvent(event)


class RecentFileRow(QFrame):
    """Linha de arquivo recente com hierarquia visual clara e hover suave."""

    opened = pyqtSignal(str)

    def __init__(
        self,
        summary: RecentFileSummary,
        *,
        compact: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._summary = summary
        self._compact = compact
        self._build_ui()

    def _build_ui(self) -> None:
        p = PALETTE
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        row_height = 40 if self._compact else 52
        icon_size = 30 if self._compact else 36
        pad_v = SPACING.xs if self._compact else SPACING.sm
        self.setMinimumHeight(row_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(recent_file_row_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, pad_v, SPACING.md, pad_v)
        layout.setSpacing(SPACING.sm if self._compact else SPACING.md)

        pdf_icon = QLabel("PDF")
        pdf_icon.setFixedSize(icon_size, icon_size)
        pdf_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pdf_icon.setStyleSheet(pdf_icon_pill_style())
        layout.addWidget(pdf_icon)

        info_block = QVBoxLayout()
        info_block.setSpacing(2)
        info_block.setContentsMargins(0, 0, 0, 0)

        self._name_label = ElidingLabel(self._summary.file_name)
        self._name_label.setStyleSheet(
            f"font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"font-size: {TYPOGRAPHY.size_body}px; "
            f"color: {p.text_primary}; background: transparent; border: none;"
        )

        project_label = QLabel(self._summary.client_project)
        project_label.setStyleSheet(caption_style())
        info_block.addWidget(self._name_label)
        info_block.addWidget(project_label)
        layout.addLayout(info_block, stretch=1)

        version_badge = QLabel(f"v{self._summary.version}")
        version_badge.setStyleSheet(
            badge_style(p.senai_blue_light, "rgba(74, 111, 212, 0.15)")
        )
        version_badge.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        layout.addWidget(version_badge)

        updated = QLabel(self._summary.updated_at.strftime("%d/%m/%Y  %H:%M"))
        updated.setStyleSheet(
            f"font-size: {TYPOGRAPHY.size_caption}px; "
            f"color: {p.text_muted}; background: transparent; border: none;"
        )
        updated.setMinimumWidth(110)
        updated.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )
        updated.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(updated)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.opened.emit(self._summary.file_id)
        super().mousePressEvent(event)
