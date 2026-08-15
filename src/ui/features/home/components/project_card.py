"""Cards e linhas para projetos em andamento na Home."""
from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import QEvent, QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.cards import ElidingLabel
from src.ui.components.icons import icon_edit, icon_ellipsis, icon_layers, icon_trash
from src.ui.features.home.models.dashboard import ProjectSummary
from src.ui.styles import (
    PALETTE,
    SPACING,
    TYPOGRAPHY,
    action_card_hover_style,
    action_card_idle_style,
    badge_style,
    caption_style,
    configure_app_popup_menu,
    dashboard_card_media_style,
    recent_file_row_style,
    scaled_dashboard_card_size,
)


def _project_tooltip(summary: ProjectSummary) -> str:
    lines = [summary.display_name, f"Modo: {summary.report_mode_label()}"]
    if summary.components:
        lines.append("Componentes: " + ", ".join(summary.components[:5]))
    lines.append("Clique para abrir · menu ⋯ para renomear ou excluir")
    return "\n".join(lines)


def _meta_parts(summary: ProjectSummary) -> tuple[str, str, str]:
    """modo, cliente, data curta."""
    date_str = summary.updated_at.strftime("%d/%m/%Y")
    mode = summary.report_mode_label()
    client = summary.client_project or "—"
    return mode, client, date_str


def _meta_line(summary: ProjectSummary, *, short_date: bool = False) -> str:
    date_fmt = "%d/%m/%Y" if short_date else "%d/%m/%Y %H:%M"
    date_str = summary.updated_at.strftime(date_fmt)
    if summary.is_batch:
        return f"{summary.document_count} PDFs · {summary.client_project} · {date_str}"
    return f"{summary.client_project} · {summary.report_mode_label()} · {date_str}"


class ProjectRow(QFrame):
    """Linha de projeto — clique abre; ⋯ renomeia/exclui; checkbox para lote."""

    opened = pyqtSignal(str)
    renamed = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)
    selection_changed = pyqtSignal(str, bool)

    def __init__(
        self,
        summary: ProjectSummary,
        *,
        compact: bool = False,
        selected: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("HomeProjectRow")
        self._summary = summary
        self._compact = compact
        self._build_ui()
        self.set_selected(selected)

    def _build_ui(self) -> None:
        p = PALETTE
        scale = TYPOGRAPHY.size_body / 13
        row_height = max(40, round((44 if self._compact else 56) * scale))
        icon_size = max(28, round((32 if self._compact else 38) * scale))
        pad_v = SPACING.xs if self._compact else SPACING.sm
        self.setMinimumHeight(row_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(recent_file_row_style())
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.sm, pad_v, SPACING.sm, pad_v)
        layout.setSpacing(SPACING.sm if self._compact else SPACING.md)

        self._check = QCheckBox()
        self._check.setToolTip("Selecionar para exclusão em lote")
        self._check.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self._check.toggled.connect(self._on_check_toggled)
        layout.addWidget(self._check, 0, Qt.AlignmentFlag.AlignVCenter)

        icon_host = QLabel()
        icon_host.setFixedSize(icon_size, icon_size)
        icon_host.setPixmap(
            icon_layers().pixmap(max(16, icon_size - 8), max(16, icon_size - 8))
        )
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
        self._title_edit.setObjectName("HomeProjectTitle")
        self._title_edit.setReadOnly(True)
        self._title_edit.setFrame(False)
        self._title_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._title_edit.setToolTip("Clique para abrir o projeto")
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

        meta = ElidingLabel(_meta_line(self._summary))
        meta.setStyleSheet(caption_style())
        text_col.addWidget(meta)
        layout.addLayout(text_col, stretch=1)

        self._more_btn = QToolButton()
        self._more_btn.setObjectName("HomeProjectMoreBtn")
        self._more_btn.setIcon(icon_ellipsis())
        self._more_btn.setToolTip("Mais ações")
        self._more_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._more_btn.setFixedSize(28, 28)
        self._more_btn.setAutoRaise(True)
        self._more_btn.clicked.connect(self._show_menu)
        layout.addWidget(self._more_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        self.setToolTip(_project_tooltip(self._summary))

    def project_id(self) -> str:
        return self._summary.project_id

    def set_selected(self, selected: bool) -> None:
        self._check.blockSignals(True)
        self._check.setChecked(selected)
        self._check.blockSignals(False)

    def is_selected(self) -> bool:
        return self._check.isChecked()

    def _on_check_toggled(self, checked: bool) -> None:
        self.selection_changed.emit(self._summary.project_id, checked)

    def _show_menu(self) -> None:
        menu = QMenu(self)
        configure_app_popup_menu(menu)
        rename_action = QAction(icon_edit(), "Renomear", menu)
        rename_action.triggered.connect(self._begin_title_edit)
        menu.addAction(rename_action)
        menu.addSeparator()
        delete_action = QAction(icon_trash(), "Excluir", menu)
        delete_action.triggered.connect(
            lambda: self.delete_requested.emit(self._summary.project_id)
        )
        menu.addAction(delete_action)
        menu.exec(self._more_btn.mapToGlobal(QPoint(0, self._more_btn.height())))

    def _begin_title_edit(self) -> None:
        self._title_edit.setReadOnly(False)
        self._title_edit.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self._title_edit.setFrame(True)
        self._title_edit.selectAll()
        self._title_edit.setFocus()

    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self._title_edit:
            if event.type() == QEvent.Type.MouseButtonPress:
                if (
                    event.button() == Qt.MouseButton.LeftButton
                    and self._title_edit.isReadOnly()
                ):
                    self.opened.emit(self._summary.project_id)
                    return True
            if event.type() == QEvent.Type.MouseButtonDblClick:
                self._begin_title_edit()
                return True
        return super().eventFilter(obj, event)

    def _commit_title(self) -> None:
        if self._title_edit.isReadOnly():
            return
        new_name = self._title_edit.text().strip()
        self._title_edit.setReadOnly(True)
        self._title_edit.setFrame(False)
        self._title_edit.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        if not new_name:
            self._title_edit.setText(self._summary.display_name)
            return
        if new_name != self._summary.display_name:
            self.renamed.emit(self._summary.project_id, new_name)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return
        if (
            self._title_edit.isReadOnly()
            and not self._title_edit.underMouse()
            and not self._more_btn.underMouse()
            and not self._check.underMouse()
        ):
            self.opened.emit(self._summary.project_id)
        super().mousePressEvent(event)


class ProjectCard(QFrame):
    """Card de projeto — faixa de mídia + corpo com chip de modo."""

    opened = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    selection_changed = pyqtSignal(str, bool)
    rename_requested = pyqtSignal(str)

    def __init__(
        self,
        summary: ProjectSummary,
        *,
        selected: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("HomeProjectCard")
        self._summary = summary
        self._build_ui()
        self.set_selected(selected)

    def _build_ui(self) -> None:
        p = PALETTE
        width, height = scaled_dashboard_card_size()
        self.setMinimumWidth(width)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._idle_style = action_card_idle_style()
        self._hover_style = action_card_hover_style(p.senai_blue_light)
        self.setStyleSheet(self._idle_style)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        media = QFrame()
        media.setFixedHeight(max(72, round(78 * TYPOGRAPHY.size_body / 13)))
        media.setStyleSheet(dashboard_card_media_style())
        media_layout = QVBoxLayout(media)
        media_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        media_layout.setSpacing(0)

        chrome = QHBoxLayout()
        chrome.setContentsMargins(0, 0, 0, 0)
        chrome.setSpacing(0)
        self._check = QCheckBox()
        self._check.setToolTip("Selecionar para exclusão em lote")
        self._check.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self._check.toggled.connect(self._on_check_toggled)
        chrome.addWidget(self._check, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        chrome.addStretch(1)
        self._more_btn = QToolButton()
        self._more_btn.setIcon(icon_ellipsis())
        self._more_btn.setToolTip("Mais ações")
        self._more_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._more_btn.setFixedSize(26, 26)
        self._more_btn.setAutoRaise(True)
        self._more_btn.setStyleSheet(
            f"QToolButton {{ background: transparent; border: none; border-radius: 6px; }}"
            f"QToolButton:hover {{ background: rgba(255,255,255,0.08); }}"
        )
        self._more_btn.clicked.connect(self._show_menu)
        chrome.addWidget(
            self._more_btn, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        media_layout.addLayout(chrome)

        icon_size = max(36, round(40 * TYPOGRAPHY.size_body / 13))
        icon_label = QLabel()
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(
            icon_layers().pixmap(max(20, icon_size - 12), max(20, icon_size - 12))
        )
        icon_label.setStyleSheet(
            f"background: rgba(74, 111, 212, 0.22); "
            f"border-radius: {SPACING.radius_md}px; border: none;"
        )
        media_layout.addStretch(1)
        media_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
        media_layout.addStretch(1)
        root.addWidget(media)

        body = QVBoxLayout()
        body.setContentsMargins(SPACING.md, SPACING.sm + 2, SPACING.md, SPACING.md)
        body.setSpacing(6)

        title = QLabel(self._summary.display_name)
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        title.setMaximumHeight(max(40, TYPOGRAPHY.size_body * 3 + 2))
        title.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_body}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold}; "
            f"background: transparent; border: none;"
        )
        body.addWidget(title)

        mode, client, date_str = _meta_parts(self._summary)
        chips = QHBoxLayout()
        chips.setContentsMargins(0, 0, 0, 0)
        chips.setSpacing(6)

        mode_chip = QLabel(mode)
        mode_chip.setStyleSheet(
            f"color: {p.senai_blue_light}; background: rgba(74, 111, 212, 0.16); "
            f"border: none; border-radius: {SPACING.radius_pill}px; "
            f"padding: 2px 8px; font-size: {TYPOGRAPHY.size_micro}px; "
            f"font-weight: {TYPOGRAPHY.weight_semibold};"
        )
        chips.addWidget(mode_chip, 0, Qt.AlignmentFlag.AlignVCenter)

        if self._summary.is_batch:
            pdf_chip = QLabel(f"{self._summary.document_count} PDFs")
            pdf_chip.setStyleSheet(
                f"color: {p.text_secondary}; background: {p.bg_surface_alt}; "
                f"border: none; border-radius: {SPACING.radius_pill}px; "
                f"padding: 2px 8px; font-size: {TYPOGRAPHY.size_micro}px;"
            )
            chips.addWidget(pdf_chip, 0, Qt.AlignmentFlag.AlignVCenter)

        chips.addStretch(1)
        body.addLayout(chips)

        client_label = ElidingLabel(client)
        client_label.setStyleSheet(
            f"color: {p.text_secondary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"background: transparent; border: none;"
        )
        body.addWidget(client_label)

        date_label = QLabel(date_str)
        date_label.setStyleSheet(
            f"color: {p.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"background: transparent; border: none;"
        )
        body.addWidget(date_label)
        body.addStretch(1)
        root.addLayout(body)

        self.setToolTip(_project_tooltip(self._summary))

    def project_id(self) -> str:
        return self._summary.project_id

    def set_selected(self, selected: bool) -> None:
        self._check.blockSignals(True)
        self._check.setChecked(selected)
        self._check.blockSignals(False)

    def _on_check_toggled(self, checked: bool) -> None:
        self.selection_changed.emit(self._summary.project_id, checked)

    def _show_menu(self) -> None:
        menu = QMenu(self)
        configure_app_popup_menu(menu)
        rename_action = QAction(icon_edit(), "Renomear", menu)
        rename_action.triggered.connect(
            lambda: self.rename_requested.emit(self._summary.project_id)
        )
        menu.addAction(rename_action)
        menu.addSeparator()
        delete_action = QAction(icon_trash(), "Excluir", menu)
        delete_action.triggered.connect(
            lambda: self.delete_requested.emit(self._summary.project_id)
        )
        menu.addAction(delete_action)
        menu.exec(self._more_btn.mapToGlobal(QPoint(0, self._more_btn.height())))

    def enterEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._hover_style)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self.setStyleSheet(self._idle_style)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            for widget in (self._check, self._more_btn):
                local = widget.mapFrom(self, pos)
                if widget.rect().contains(local):
                    event.accept()
                    return
            self.opened.emit(self._summary.project_id)
        super().mousePressEvent(event)
