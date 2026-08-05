"""
Painéis reutilizáveis das sidebars do Workspace — dark edition.

BookmarksPanel      → sumário interativo com árvore estilizada
ImageManagerPanel   → drop zone animada com lista de imagens
AnnotationToolbar   → ferramentas de marcação com botões toggle
VersionHistoryPanel → histórico com timeline visual (border-left colorida)
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPixmap
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.core.domain.ports import ReportImage, VersionEntry
from src.ui.components.buttons import IconButton, SecondaryButton
from src.ui.components.icons import app_icon, icon_close
from src.ui.components.placeholder_field import PlaceholderTextEdit
from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header
from src.ui.styles import PALETTE, SPACING, TYPOGRAPHY, sidebar_panel_style
from src.ui.styles.helpers import (
    caption_style,
    workspace_annotation_button_style,
    workspace_annotation_toolbar_style,
    workspace_bookmark_search_style,
    workspace_bookmark_tree_style,
    workspace_drop_hint_style,
    workspace_image_list_style,
    workspace_version_entry_style,
)


def _section_header(title: str) -> QWidget:
    return sidebar_section_header(title)


class BookmarksPanel(QFrame):
    """Sumário interativo do relatório (sidebar esquerda)."""

    section_selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebarPanel")

        self._sections: list[dict] = []
        self._active_section_id: str | None = None

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filtrar seção…")
        self._search.textChanged.connect(self._apply_filter)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(1)
        self._tree.setIndentation(16)
        self._tree.setUniformRowHeights(True)
        self._tree.itemClicked.connect(
            lambda item, _col: self.section_selected.emit(item.data(0, Qt.ItemDataRole.UserRole))
        )

        self._hint = QLabel("Clique em uma seção para navegar e associar fotografias.")
        self._hint.setObjectName("SidebarHint")
        self._hint.setWordWrap(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(_section_header("Sumário"))

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(SPACING.md, SPACING.xs, SPACING.md, SPACING.md)
        inner_layout.setSpacing(SPACING.sm)
        inner_layout.addWidget(self._hint)
        inner_layout.addWidget(self._search)
        inner_layout.addWidget(self._tree)
        layout.addWidget(inner, stretch=1)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._search.setStyleSheet(workspace_bookmark_search_style())
        self._tree.setStyleSheet(workspace_bookmark_tree_style())
        self._hint.setStyleSheet(caption_style())

    def render_sections(self, sections: list[dict]) -> None:
        self._sections = sections
        self._apply_filter(self._search.text())

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        if section_id is None:
            self._tree.clearSelection()
            return
        item = self._find_item_by_id(self._tree.invisibleRootItem(), section_id)
        if item is not None:
            self._tree.setCurrentItem(item)
            self._tree.scrollToItem(item)

    def _apply_filter(self, text: str) -> None:
        filtro = text.strip().lower()
        self._tree.clear()
        for section in self._sections:
            item = self._build_section_item(section, filtro)
            if item is not None:
                self._tree.invisibleRootItem().addChild(item)
        self._tree.expandAll()
        self.set_active_section(self._active_section_id)

    def _build_section_item(self, section: dict, filtro: str) -> QTreeWidgetItem | None:
        children = section.get("children", [])
        child_items: list[QTreeWidgetItem] = []
        for child in children:
            child_item = self._build_section_item(child, filtro)
            if child_item is not None:
                child_items.append(child_item)

        title = section["title"]
        image_count = int(section.get("image_count", 0) or 0)
        count_text = f"  {image_count} foto{'s' if image_count != 1 else ''}" if image_count > 0 else "  —"
        section_text = f"{title}{count_text}"

        matches_self = filtro in title.lower() or filtro in section.get("id", "").lower()
        if filtro and not matches_self and not child_items:
            return None

        item = QTreeWidgetItem([section_text])
        item.setData(0, Qt.ItemDataRole.UserRole, section["id"])
        item.setToolTip(0, title)

        if section.get("id") == self._active_section_id:
            font = item.font(0)
            font.setBold(True)
            item.setFont(0, font)

        for child_item in child_items:
            item.addChild(child_item)
        return item

    def _find_item_by_id(self, parent_item, section_id: str):
        for index in range(parent_item.childCount()):
            item = parent_item.child(index)
            if item.data(0, Qt.ItemDataRole.UserRole) == section_id:
                return item
            found = self._find_item_by_id(item, section_id)
            if found is not None:
                return found
        return None


class _ImageListRow(QFrame):
    remove_requested = pyqtSignal(object)
    _ROW_HEIGHT = 56
    _THUMB = 40

    def __init__(self, image: ReportImage, parent=None) -> None:
        super().__init__(parent)
        self.image = image
        self._selected = False
        self.setMinimumHeight(self._ROW_HEIGHT)
        self.setObjectName("ImageListRow")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._thumb = QLabel()
        self._thumb.setFixedSize(self._THUMB, self._THUMB)
        self._thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._thumb.setStyleSheet(
            f"background: {PALETTE.bg_surface_alt}; border-radius: 4px; border: 1px solid {PALETTE.border_subtle};"
        )
        pixmap = QPixmap(str(image.image_path))
        if not pixmap.isNull():
            self._thumb.setPixmap(
                pixmap.scaled(
                    self._THUMB,
                    self._THUMB,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )

        meta = QVBoxLayout()
        meta.setContentsMargins(0, 0, 0, 0)
        meta.setSpacing(2)
        name = QLabel(image.image_path.name)
        name.setToolTip(str(image.image_path))
        name.setWordWrap(False)
        name.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name.setStyleSheet(f"color: {PALETTE.text_primary}; background: transparent;")
        self._status = QLabel("")
        self._status.setStyleSheet(
            f"color: {PALETTE.text_muted}; font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )
        meta.addWidget(name)
        meta.addWidget(self._status)

        remove_btn = IconButton(icon_close(), "Remover foto")
        remove_btn.setFixedSize(22, 22)
        remove_btn.setIconSize(QSize(12, 12))
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.image))
        layout.addWidget(self._thumb)
        layout.addLayout(meta, stretch=1)
        layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        border = PALETTE.senai_blue_light if selected else PALETTE.border_subtle
        bg = "rgba(74, 111, 212, 0.16)" if selected else PALETTE.bg_surface
        self.setStyleSheet(
            f"QFrame#ImageListRow {{"
            f" background: {bg};"
            f" border: 1px solid {border};"
            f" border-radius: 8px;"
            f"}}"
        )
        self._status.setText("Selecionada — editar legenda abaixo" if selected else "Clique para selecionar")
        self._status.setStyleSheet(
            f"color: {PALETTE.senai_blue_light if selected else PALETTE.text_muted}; "
            f"font-size: {TYPOGRAPHY.size_caption}px; background: transparent;"
        )

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(super().sizeHint().width(), self._ROW_HEIGHT)


class ImageManagerPanel(QFrame):
    """Gerenciador de imagens por drag-and-drop (sidebar / aba Fotografias)."""

    image_dropped = pyqtSignal(Path)
    image_selected = pyqtSignal(object)
    image_remove_requested = pyqtSignal(object)
    image_caption_changed = pyqtSignal(object, str)
    choose_file_requested = pyqtSignal()

    def __init__(self, parent=None, *, show_header: bool = True) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._drop_active = False
        self._selected_image: ReportImage | None = None
        self._loading_caption = False
        self._row_widgets: list[_ImageListRow] = []
        self._caption_debounce = QTimer(self)
        self._caption_debounce.setSingleShot(True)
        self._caption_debounce.setInterval(450)
        self._caption_debounce.timeout.connect(self._flush_caption)

        self._list = QListWidget()
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._list.setSpacing(6)
        self._list.setFrameShape(QFrame.Shape.NoFrame)
        self._list.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self._list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.currentItemChanged.connect(self._on_current_changed)

        self._drop_hint = QLabel("Solte imagens PNG ou JPG aqui")
        self._drop_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._drop_hint.setWordWrap(True)
        self._drop_hint.setMinimumHeight(48)

        self._choose_btn = SecondaryButton("+ Escolher arquivo…")
        self._choose_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._choose_btn.clicked.connect(self.choose_file_requested.emit)

        self._hint = QLabel("Fotos desta seção")
        self._hint.setObjectName("GlobalFieldLabel")
        self._hint.setWordWrap(True)

        self._empty_list_hint = QLabel("Nenhuma foto ainda — adicione pela área acima.")
        self._empty_list_hint.setObjectName("SidebarHint")
        self._empty_list_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_list_hint.setWordWrap(True)

        # Bloco único: lista + legenda coladas (sem vão flutuante).
        self._selection_block = QFrame()
        self._selection_block.setObjectName("GlobalFieldCard")
        selection_layout = QVBoxLayout(self._selection_block)
        selection_layout.setContentsMargins(SPACING.sm, SPACING.sm, SPACING.sm, SPACING.sm)
        selection_layout.setSpacing(SPACING.xs)
        selection_layout.addWidget(self._hint)
        selection_layout.addWidget(self._empty_list_hint)
        selection_layout.addWidget(self._list)
        self._caption_label = QLabel("Legenda")
        self._caption_label.setObjectName("GlobalFieldLabel")
        self._caption_edit = PlaceholderTextEdit(multiline=False)
        self._caption_edit.set_text("")
        self._caption_edit.setEnabled(False)
        self._caption_edit.text_changed.connect(self._on_caption_changed)
        selection_layout.addWidget(self._caption_label)
        selection_layout.addWidget(self._caption_edit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._header = _section_header("Fotografias")
        self._header.setVisible(show_header)
        layout.addWidget(self._header)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        pad = SPACING.sm if show_header else 0
        inner_layout.setContentsMargins(pad, SPACING.xs if show_header else 0, pad, pad)
        inner_layout.setSpacing(SPACING.sm)
        if show_header:
            hint_legacy = QLabel("Arraste imagens aqui ou clique na lista para selecionar.")
            hint_legacy.setObjectName("SidebarHint")
            hint_legacy.setWordWrap(True)
            hint_legacy.setStyleSheet(caption_style())
            inner_layout.addWidget(hint_legacy)
        inner_layout.addWidget(self._drop_hint)
        inner_layout.addWidget(self._choose_btn)
        inner_layout.addWidget(self._selection_block)
        inner_layout.addStretch(1)
        layout.addWidget(inner, stretch=1)

        self.refresh_appearance()

    def selected_image(self) -> ReportImage | None:
        return self._selected_image

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._list.setStyleSheet(
            workspace_image_list_style()
            + "QListWidget::item { padding: 0px; margin: 0px; border: none; background: transparent; }"
        )
        self._empty_list_hint.setStyleSheet(caption_style())
        self._choose_btn.refresh_appearance()
        self._apply_drop_hint_style()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            self._drop_active = True
            self._apply_drop_hint_style()
            event.acceptProposedAction()

    def dragLeaveEvent(self, event) -> None:
        self._drop_active = False
        self._apply_drop_hint_style()

    def dropEvent(self, event: QDropEvent) -> None:
        self._drop_active = False
        self._apply_drop_hint_style()
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".png", ".jpg", ".jpeg"):
                self.image_dropped.emit(path)
        event.acceptProposedAction()

    def _apply_drop_hint_style(self) -> None:
        self._drop_hint.setStyleSheet(workspace_drop_hint_style(active=self._drop_active))

    def is_caption_editing(self) -> bool:
        return self._caption_edit.has_editor_focus()

    def render_images(self, images: list[ReportImage]) -> None:
        selected_path = (
            str(self._selected_image.image_path) if self._selected_image is not None else None
        )
        editing_caption = self.is_caption_editing()
        live_caption = self._caption_edit.get_text() if editing_caption else None

        self._list.clear()
        self._row_widgets.clear()
        has_images = len(images) > 0
        self._drop_hint.setVisible(True)
        self._list.setVisible(has_images)
        self._empty_list_hint.setVisible(not has_images)
        self._hint.setVisible(True)
        self._caption_label.setVisible(has_images)
        self._caption_edit.setVisible(has_images)
        restore_row = 0
        for index, image in enumerate(images):
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, image)
            row = _ImageListRow(image)
            row.remove_requested.connect(self.image_remove_requested.emit)
            self._row_widgets.append(row)
            self._list.addItem(item)
            self._list.setItemWidget(item, row)
            item.setSizeHint(QSize(max(80, self._list.viewport().width()), _ImageListRow._ROW_HEIGHT))
            if selected_path and str(image.image_path) == selected_path:
                restore_row = index
        if images:
            self._list.setCurrentRow(restore_row)
            self._select_image(
                images[restore_row],
                emit=True,
                preserve_caption=editing_caption,
                caption_override=live_caption,
            )
            if editing_caption:
                self._caption_edit.focus_editor()
        else:
            self._select_image(None, emit=True)
        self._sync_list_height()

    def _sync_list_height(self) -> None:
        """Altura da lista = conteúdo (evita vão vazio antes da legenda)."""
        count = self._list.count()
        if count == 0:
            self._list.setFixedHeight(0)
            return
        spacing = self._list.spacing()
        content_h = count * _ImageListRow._ROW_HEIGHT + max(0, count - 1) * spacing + 4
        max_h = 180
        self._list.setFixedHeight(min(content_h, max_h))
        if content_h > max_h:
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self._list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        image = item.data(Qt.ItemDataRole.UserRole)
        self._select_image(image, emit=True)

    def _on_current_changed(self, current: QListWidgetItem | None, _previous) -> None:
        if current is None:
            return
        image = current.data(Qt.ItemDataRole.UserRole)
        self._select_image(image, emit=True)

    def _select_image(
        self,
        image: ReportImage | None,
        *,
        emit: bool = False,
        preserve_caption: bool = False,
        caption_override: str | None = None,
    ) -> None:
        prev_path = (
            str(self._selected_image.image_path) if self._selected_image is not None else None
        )
        selected_path = str(image.image_path) if image is not None else None
        changed = prev_path != selected_path
        self._selected_image = image
        for row in self._row_widgets:
            row.set_selected(selected_path is not None and str(row.image.image_path) == selected_path)
        self._caption_edit.setEnabled(image is not None)
        if preserve_caption and not changed:
            # Mantém o que o usuário está digitando; não chama set_text.
            if caption_override is not None and image is not None:
                image.caption = caption_override
        else:
            self._loading_caption = True
            self._caption_edit.set_text(
                image.caption if image is not None else "",
                force=True,
            )
            self._loading_caption = False
        if emit and changed:
            self.image_selected.emit(image)

    def _on_caption_changed(self, _text: str) -> None:
        if self._loading_caption or self._selected_image is None:
            return
        self._caption_debounce.start()

    def _flush_caption(self) -> None:
        if self._selected_image is None:
            return
        self.image_caption_changed.emit(self._selected_image, self._caption_edit.get_text().strip())


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
        # Ferramentas ficam desabilitadas até existir canvas de anotação.
        # O card permanece visível (não cinza o frame inteiro).
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


class _VersionEntryWidget(QWidget):
    """Mini-card de versão com timeline visual (border-left colorida)."""

    def __init__(self, entry: VersionEntry, is_latest: bool = False, parent=None) -> None:
        super().__init__(parent)
        self._entry = entry
        self._is_latest = is_latest

        layout = QHBoxLayout(self)
        layout.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.sm)
        layout.setSpacing(SPACING.sm)

        self._line = QFrame()
        self._line.setFixedWidth(3)
        self._line.setMinimumHeight(32)
        layout.addWidget(self._line, 0, Qt.AlignmentFlag.AlignTop)

        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)

        header_row = QHBoxLayout()
        self._version_label = QLabel(f"v{entry.version_number}")
        self._responsible_label = QLabel(f"  {entry.responsible_name}")
        header_row.addWidget(self._version_label)
        header_row.addWidget(self._responsible_label)
        header_row.addStretch()
        content_layout.addLayout(header_row)

        self._meta = QLabel(
            f"{entry.timestamp.strftime('%d/%m/%Y %H:%M')}  ·  {entry.description}"
        )
        self._meta.setWordWrap(True)
        content_layout.addWidget(self._meta)

        layout.addLayout(content_layout, stretch=1)
        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        p = PALETTE
        accent_color = p.senai_orange if self._is_latest else p.senai_blue_light
        self._line.setStyleSheet(
            f"background-color: {accent_color}; border-radius: 2px;"
        )
        self._version_label.setStyleSheet(
            f"color: {accent_color}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_bold}; background: transparent;"
        )
        self._responsible_label.setStyleSheet(
            f"color: {p.text_primary}; font-size: {TYPOGRAPHY.size_caption}px; "
            f"font-weight: {TYPOGRAPHY.weight_medium}; background: transparent;"
        )
        self._meta.setStyleSheet(
            f"color: {p.text_muted}; font-size: 10px; background: transparent;"
        )
        self.setStyleSheet(workspace_version_entry_style(is_latest=self._is_latest))


class VersionHistoryPanel(QFrame):
    """Histórico de versões com timeline visual em tempo real."""

    new_version_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._entries: list[VersionEntry] = []

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)
        self._layout.addStretch()
        self._scroll.setWidget(self._content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(_section_header("Histórico de Versões"))
        outer.addWidget(self._scroll, stretch=1)

        from src.ui.components.buttons import PrimaryButton

        self._new_version_btn = PrimaryButton("Nova versão")
        self._new_version_btn.clicked.connect(self.new_version_requested.emit)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(SPACING.md, SPACING.sm, SPACING.md, SPACING.md)
        btn_row.addStretch(1)
        btn_row.addWidget(self._new_version_btn)
        outer.addLayout(btn_row)

        self.refresh_appearance()

    def refresh_appearance(self) -> None:
        self.setStyleSheet(sidebar_panel_style())
        self._scroll.setStyleSheet("background: transparent;")
        self._content.setStyleSheet("background: transparent;")
        if hasattr(self, "_new_version_btn"):
            self._new_version_btn.refresh_appearance()
        for index in range(self._layout.count() - 1):
            widget = self._layout.itemAt(index).widget()
            if widget is not None and hasattr(widget, "refresh_appearance"):
                widget.refresh_appearance()

    def render_history(self, entries: list[VersionEntry]) -> None:
        self._entries = list(entries)
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        for i, entry in enumerate(reversed(entries)):
            is_latest = i == 0
            widget = _VersionEntryWidget(entry, is_latest=is_latest)
            self._layout.insertWidget(self._layout.count() - 1, widget)
