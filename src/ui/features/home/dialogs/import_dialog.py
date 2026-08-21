"""Modal de importação em lote de PDFs — dark edition com drop zone animada."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QAbstractItemModel, QEvent, QObject, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeyEvent,
    QPainter,
    QPaintEvent,
    QPen,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from src.ui.components.app_dialog import AppDialog
from src.ui.components.buttons import IconButton, PrimaryButton, SecondaryButton
from src.ui.components.icons import icon_close, icon_file_pdf
from src.ui.components.inputs import LabeledLineEdit
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, fit_to_screen


class _PdfListRow(QFrame):
    remove_requested = pyqtSignal(str)
    _ROW_HEIGHT = 36

    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.path_str = str(path.resolve())
        self.setMinimumHeight(self._ROW_HEIGHT)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        icon = QLabel()
        icon.setPixmap(icon_file_pdf().pixmap(16, 16))
        icon.setFixedSize(16, 16)
        name = QLabel(path.name)
        name.setToolTip(self.path_str)
        name.setWordWrap(False)
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        name.setStyleSheet(f"color: {PALETTE.text_primary}; background: transparent;")
        remove_btn = IconButton(icon_close(), "Remover arquivo")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setIconSize(QSize(12, 12))
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.path_str))
        layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(name, stretch=1, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(super().sizeHint().width(), self._ROW_HEIGHT)


class DropZone(QFrame):
    """Área de drop com borda tracejada desenhada no paint (QSS dashed+radius corta a base)."""

    _HEIGHT = 168
    _BORDER = 2.0
    _INSET = 2.0

    def __init__(
        self,
        counter_label: QLabel,
        warning_label: QLabel | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._counter_label = counter_label
        self._warning_label = warning_label
        self._drag_active = False
        self.setObjectName("PdfDropZone")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAcceptDrops(True)
        self.setFixedHeight(self._HEIGHT)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        # Sem border no QSS — o tracejado completo é pintado em paintEvent.
        self.setStyleSheet("QFrame#PdfDropZone { background: transparent; border: none; }")

        self._empty_hint = QLabel("Arraste PDFs aqui\nou use o botão acima")
        self._empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_hint.setWordWrap(True)
        self._empty_hint.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._empty_hint.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_body}px; "
            f"background: transparent; border: none;"
        )

        self._list = QListWidget()
        self._list.setAcceptDrops(False)
        self._list.setDragEnabled(False)
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self._list.setStyleSheet(f"""
            QListWidget {{
                border: none;
                background: transparent;
                color: {PALETTE.text_primary};
                font-size: {TYPOGRAPHY.size_body}px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 0px;
                margin: 2px 0px;
                border-radius: 4px;
                border-bottom: 1px solid {PALETTE.border_subtle};
                min-height: {_PdfListRow._ROW_HEIGHT}px;
            }}
            QListWidget::item:selected {{
                background-color: rgba(74, 111, 212, 0.20);
                color: {PALETTE.senai_blue_light};
            }}
        """)
        self._list.installEventFilter(self)

        pages = QWidget(self)
        pages.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._pages = QStackedLayout(pages)
        self._pages.setContentsMargins(0, 0, 0, 0)
        self._pages.addWidget(self._empty_hint)
        self._pages.addWidget(self._list)

        pad = int(self._INSET + self._BORDER + 6)
        root = QVBoxLayout(self)
        root.setContentsMargins(pad, pad, pad, pad)
        root.setSpacing(0)
        root.addWidget(pages)

        self._update_counter()

    def count(self) -> int:
        return self._list.count()

    def model(self) -> QAbstractItemModel | None:
        return self._list.model()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:  # noqa: N802
        if watched is self._list and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if isinstance(key_event, QKeyEvent) and key_event.key() in (
                Qt.Key.Key_Delete,
                Qt.Key.Key_Backspace,
            ):
                self.remove_selected()
                return True
        return super().eventFilter(watched, event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect()).adjusted(self._INSET, self._INSET, -self._INSET, -self._INSET)
        radius = float(SPACING.radius_md)

        if self._drag_active:
            fill = QColor(74, 111, 212, 28)
            stroke = QColor(PALETTE.senai_blue_light)
        else:
            fill = QColor(PALETTE.bg_surface_alt)
            stroke = QColor(PALETTE.border_strong)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, radius, radius)

        pen = QPen(stroke, self._BORDER)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([5.0, 4.0])
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # Meia espessura para dentro: a linha inferior não é clipada na borda do widget.
        stroke_rect = rect.adjusted(1.0, 1.0, -1.0, -1.0)
        painter.drawRoundedRect(stroke_rect, radius - 1.0, radius - 1.0)
        painter.end()

    def _set_drag_active(self, active: bool) -> None:
        if self._drag_active == active:
            return
        self._drag_active = active
        self.update()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            self._set_drag_active(True)
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:  # noqa: N802
        self._set_drag_active(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        self._set_drag_active(False)
        pdf_paths = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".pdf")
        ]
        duplicates: list[str] = []
        for path in pdf_paths:
            if not self._add_path(path):
                duplicates.append(path.name)
        if duplicates:
            self.warn_duplicates(duplicates)
        event.acceptProposedAction()

    def _add_path(self, path: Path) -> bool:
        """Adiciona o PDF. Retorna False se já estava na lista."""
        path_str = str(path.resolve())
        for index in range(self._list.count()):
            existing = self._list.item(index)
            if existing is not None and existing.data(Qt.ItemDataRole.UserRole) == path_str:
                return False
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, path_str)
        item.setToolTip(path_str)
        row = _PdfListRow(path)
        row.remove_requested.connect(self._remove_path)
        self._list.addItem(item)
        self._list.setItemWidget(item, row)
        item.setSizeHint(QSize(max(self._list.viewport().width(), 120), _PdfListRow._ROW_HEIGHT))
        self._update_counter()
        if self._warning_label is not None:
            self._warning_label.clear()
            self._warning_label.hide()
        return True

    def add_path_string(self, path_str: str) -> bool:
        return self._add_path(Path(path_str))

    def _remove_path(self, path_str: str) -> None:
        for index in range(self._list.count()):
            item = self._list.item(index)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == path_str:
                self._list.takeItem(index)
                break
        self._update_counter()
        if self._warning_label is not None:
            self._warning_label.clear()
            self._warning_label.hide()

    def remove_selected(self) -> None:
        for item in list(self._list.selectedItems()):
            self._list.takeItem(self._list.row(item))
        self._update_counter()
        if self._warning_label is not None:
            self._warning_label.clear()
            self._warning_label.hide()

    def warn_duplicates(self, names: list[str]) -> None:
        if len(names) == 1:
            msg = f"Arquivo já importado na lista: {names[0]}"
        else:
            msg = f"{len(names)} arquivos já estavam na lista e foram ignorados."
        if self._warning_label is not None:
            self._warning_label.setText(msg)
            self._warning_label.show()
        else:
            from src.ui.components.feedback import show_info

            show_info(self.window(), "Arquivo já importado", msg)

    def _update_counter(self) -> None:
        count = self._list.count()
        self._pages.setCurrentIndex(0 if count == 0 else 1)
        if count == 0:
            self._counter_label.setText("Nenhum arquivo selecionado")
            self._counter_label.setStyleSheet(
                f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
            )
        else:
            self._counter_label.setText(
                f"{count} arquivo{'s' if count != 1 else ''} selecionado{'s' if count != 1 else ''}"
            )
            self._counter_label.setStyleSheet(
                f"color: {PALETTE.success}; font-size: {TYPOGRAPHY.size_caption}px; "
                f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
            )

    def selected_paths(self) -> list[Path]:
        return [
            Path(self._list.item(i).data(Qt.ItemDataRole.UserRole))
            for i in range(self._list.count())
        ]


class ImportDialog(AppDialog):
    """Fluxo de importação em lote ('Novo PDF / Processar Lote')."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent, window_title="Importar Relatórios PDF", minimum_width=540)
        _, dialog_height = fit_to_screen(560, 560, reference=parent)
        self.setMinimumHeight(dialog_height)
        self._surface.setMinimumHeight(dialog_height - 40)

        self._client_field = LabeledLineEdit("Cliente / Projeto", required=True)
        self._component_field = LabeledLineEdit("Componente Avaliado", required=True)
        self._counter_label = QLabel("Nenhum arquivo selecionado")
        self._counter_label.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        self._warning_label = QLabel("")
        self._warning_label.setWordWrap(True)
        self._warning_label.setStyleSheet(
            f"color: {PALETTE.warning}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        self._drop_zone = DropZone(self._counter_label, self._warning_label)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = self.create_root_layout()
        self.add_dialog_header(
            layout,
            "Importar relatórios PDF",
            "Arraste um ou mais PDFs brutos gerados pelos equipamentos ZEISS, ou clique em 'Selecionar'.",
        )

        browse_row = QHBoxLayout()
        browse_row.setSpacing(SPACING.sm)
        browse_btn = SecondaryButton("Selecionar arquivos…")
        browse_btn.clicked.connect(self._browse_files)
        remove_btn = SecondaryButton("Remover selecionados")
        remove_btn.setToolTip("Remove os PDFs marcados na lista (também Delete/Backspace)")
        remove_btn.clicked.connect(self._drop_zone.remove_selected)
        browse_row.addWidget(browse_btn)
        browse_row.addWidget(remove_btn)
        browse_row.addWidget(self._counter_label, stretch=1)

        layout.addLayout(browse_row)
        layout.addWidget(self._drop_zone)
        layout.addSpacing(SPACING.sm)
        layout.addWidget(self._warning_label)
        layout.addWidget(self._client_field)
        layout.addWidget(self._component_field)

        self.add_dialog_divider(layout)
        layout.addLayout(self._build_footer())

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        cancel_btn = SecondaryButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        confirm_btn = PrimaryButton("Importar e continuar →")
        confirm_btn.clicked.connect(self._on_confirm)

        row.addStretch(1)
        row.addWidget(cancel_btn)
        row.addWidget(confirm_btn)
        return row

    def _browse_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Selecionar PDFs", "", "PDF (*.pdf)")
        duplicates: list[str] = []
        for path in paths:
            if not self._drop_zone.add_path_string(path):
                duplicates.append(Path(path).name)
        if duplicates:
            self._drop_zone.warn_duplicates(duplicates)

    def _on_confirm(self) -> None:
        self._client_field.mark_touched()
        self._component_field.mark_touched()
        if not self._client_field.is_valid() or not self._component_field.is_valid():
            return
        if self._drop_zone.count() == 0:
            return
        self.accept()

    def get_result(self) -> dict:
        return {
            "pdf_paths": self._drop_zone.selected_paths(),
            "client_project": self._client_field.text(),
            "evaluated_component": self._component_field.text(),
        }
