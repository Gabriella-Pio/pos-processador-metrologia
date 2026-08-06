"""Cards e linhas para projetos em andamento na Home."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QVBoxLayout, QWidget

from src.ui.components.cards import ActionCard, ElidingLabel
from src.ui.components.icons import icon_layers
from src.ui.features.home.models.dashboard import ProjectSummary
from src.ui.styles import (
    PALETTE,
    SPACING,
    TYPOGRAPHY,
    action_card_hover_style,
    action_card_idle_style,
    badge_style,
    caption_style,
    recent_file_row_style,
)


class ProjectRow(QFrame):
    """Linha de projeto em andamento — duplo-clique no título para renomear."""

    opened = pyqtSignal(str)
    renamed = pyqtSignal(str, str)

    def __init__(
        self,
        summary: ProjectSummary,
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
        row_height = 44 if self._compact else 56
        icon_size = 32 if self._compact else 38
        pad_v = SPACING.xs if self._compact else SPACING.sm
        self.setMinimumHeight(row_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(recent_file_row_style())

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, pad_v, SPACING.md, pad_v)
        layout.setSpacing(SPACING.sm if self._compact else SPACING.md)

        icon_host = QLabel()
        icon_host.setFixedSize(icon_size, icon_size)
        icon_host.setPixmap(icon_layers().pixmap(icon_size - 8, icon_size - 8))
        icon_host.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_host.setStyleSheet(
            f"background: rgba(74, 111, 212, 0.15); border-radius: {icon_size // 2}px;"
        )
        layout.addWidget(icon_host)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(SPACING.xs)
        self._title_edit = QLineEdit(self._summary.display_name)
        self._title_edit.setReadOnly(True)
        self._title_edit.setFrame(False)
        self._title_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        self._title_edit.setToolTip("Duplo-clique para renomear")
        self._title_edit.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; background: transparent; "
            f"border: none; padding: 0;"
        )
        self._title_edit.installEventFilter(self)
        self._title_edit.editingFinished.connect(self._commit_title)
        title_row.addWidget(self._title_edit, stretch=1)
        if self._summary.is_batch:
            badge = QLabel(f"{self._summary.document_count} PDFs")
            badge.setStyleSheet(
                badge_style(p.senai_blue_light, "rgba(74, 111, 212, 0.15)")
            )
            title_row.addWidget(badge)
        text_col.addLayout(title_row)

        date_str = self._summary.updated_at.strftime("%d/%m/%Y %H:%M")
        meta = ElidingLabel(
            f"{self._summary.client_project} · {self._summary.report_mode_label()} · {date_str}"
        )
        meta.setStyleSheet(caption_style())
        text_col.addWidget(meta)
        layout.addLayout(text_col, stretch=1)

        self.setToolTip(self._tooltip_text())

    def _tooltip_text(self) -> str:
        lines = [self._summary.display_name, f"Modo: {self._summary.report_mode_label()}"]
        if self._summary.components:
            lines.append("Componentes: " + ", ".join(self._summary.components[:5]))
        lines.append("Duplo-clique no título para renomear")
        return "\n".join(lines)

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self._title_edit and event.type() == QEvent.Type.MouseButtonDblClick:
            self._title_edit.setReadOnly(False)
            self._title_edit.setCursor(Qt.CursorShape.IBeamCursor)
            self._title_edit.setFrame(True)
            self._title_edit.selectAll()
            self._title_edit.setFocus()
            return True
        return super().eventFilter(obj, event)

    def _commit_title(self) -> None:
        if self._title_edit.isReadOnly():
            return
        new_name = self._title_edit.text().strip()
        self._title_edit.setReadOnly(True)
        self._title_edit.setFrame(False)
        self._title_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        if not new_name:
            self._title_edit.setText(self._summary.display_name)
            return
        if new_name != self._summary.display_name:
            self.renamed.emit(self._summary.project_id, new_name)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self._title_edit.isReadOnly()
        ):
            self.opened.emit(self._summary.project_id)
        super().mousePressEvent(event)


class ProjectCard(ActionCard):
    """Card de projeto em andamento — modo grade."""

    opened = pyqtSignal(str)

    def __init__(self, summary: ProjectSummary, parent=None) -> None:
        p = PALETTE
        date_str = summary.updated_at.strftime("%d/%m/%Y")
        subtitle = f"{summary.client_project} · {date_str}"
        if summary.is_batch:
            subtitle = f"{summary.document_count} PDFs · {subtitle}"
        super().__init__(
            icon="",
            title=summary.display_name,
            subtitle=subtitle,
            accent_color=p.senai_blue_light,
            accent_bg="rgba(74, 111, 212, 0.15)",
            parent=parent,
        )
        self._project_id = summary.project_id
        self.setToolTip(ProjectRow(summary)._tooltip_text())
        self.clicked.connect(lambda: self.opened.emit(self._project_id))
        icon_label = QLabel()
        icon_label.setPixmap(icon_layers().pixmap(28, 28))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setFixedSize(52, 52)
        icon_label.setStyleSheet(
            action_card_idle_style()
            + " background: rgba(74, 111, 212, 0.15); border-radius: 26px;"
        )
        layout = self.layout()
        if layout is not None and layout.count() > 0:
            old = layout.itemAt(0).widget()
            if old is not None:
                layout.replaceWidget(old, icon_label)
                old.deleteLater()

    def enterEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(action_card_hover_style(PALETTE.senai_blue_light))
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(action_card_idle_style())
        super().leaveEvent(event)
