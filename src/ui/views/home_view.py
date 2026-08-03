"""
HomeView — orquestrador da tela inicial (Arquivos | Templates).
"""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QScrollArea, QStackedWidget, QSizePolicy, QVBoxLayout, QWidget

from src.ui.styles import SPACING


class _HomeStack(QStackedWidget):
    """Stack que só considera a aba visível no minimumSizeHint — evita comprimir o hero."""

    def minimumSizeHint(self):
        current = self.currentWidget()
        if current is not None:
            return current.minimumSizeHint()
        return super().minimumSizeHint()


class _StickyTabScrollHost(QWidget):
    """Scroll da Home com tab bar que gruda abaixo do AppHeader ao rolar."""

    TAB_BAR_HEIGHT = 44
    TAB_HERO_GAP = SPACING.lg

    def __init__(self, hero: QWidget, tab_bar: QWidget, stack: QWidget, parent=None) -> None:
        super().__init__(parent)
        self._hero = hero
        self._tab_bar = tab_bar
        self._tab_bar.setParent(self)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(0)
        scroll_layout.addWidget(hero)

        self._tab_anchor = QWidget()
        self._tab_anchor.setFixedHeight(self.TAB_BAR_HEIGHT + self.TAB_HERO_GAP)
        scroll_layout.addWidget(self._tab_anchor)
        scroll_layout.addWidget(stack)

        self._page_scroll = QScrollArea()
        self._page_scroll.setObjectName("HomePageScroll")
        self._page_scroll.setWidgetResizable(True)
        self._page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._page_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._page_scroll.setWidget(scroll_content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._page_scroll, stretch=1)

        self._hero.installEventFilter(self)
        self._page_scroll.verticalScrollBar().valueChanged.connect(self._position_tab_bar)
        self._position_tab_bar(0)

    @property
    def page_scroll(self) -> QScrollArea:
        return self._page_scroll

    def eventFilter(self, obj, event) -> bool:
        if obj is self._hero and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.LayoutRequest,
        ):
            self._position_tab_bar(self._page_scroll.verticalScrollBar().value())
        return super().eventFilter(obj, event)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._position_tab_bar(self._page_scroll.verticalScrollBar().value())

    def _position_tab_bar(self, scroll_y: int) -> None:
        anchor_y = self._hero.height() + self.TAB_HERO_GAP
        y = max(0, anchor_y - scroll_y)
        stuck = y == 0 and scroll_y > 0
        self._tab_bar.setGeometry(0, y, self.width(), self.TAB_BAR_HEIGHT)
        self._tab_bar.raise_()
        if hasattr(self._tab_bar, "set_stuck"):
            self._tab_bar.set_stuck(stuck)


from src.ui.components.feedback import show_friendly_error
from src.ui.components.hero import HeroCommandBar
from src.ui.components.tab_bar import TabBar
from src.ui.models.dashboard import (
    RecentFileSummary,
    RecentFilesFilterState,
    TemplateSummary,
    distinct_components,
    distinct_projects,
)
from src.ui.viewmodels.home_viewmodel import HomeViewModel
from src.ui.views.home import RecentesPanel, TemplatesPanel


class HomeView(QWidget):
    new_document_requested = pyqtSignal()
    template_manager_requested = pyqtSignal()
    template_editor_requested = pyqtSignal(str)
    recent_file_opened = pyqtSignal(str)

    TAB_ARQUIVOS = 0
    TAB_TEMPLATES = 1

    def __init__(self, view_model: HomeViewModel, parent=None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._search_query = ""
        self._recent_files: list[RecentFileSummary] = []
        self._templates: list[TemplateSummary] = []
        self._build_ui()
        self._connect_view_model()
        self._vm.load_dashboard()

    def focus_search(self) -> None:
        self._hero.focus_search()

    def clear_search_and_filters(self) -> None:
        self._clear_search_and_filters()

    def _build_ui(self) -> None:
        self.setObjectName("HomeSurface")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._hero = HeroCommandBar()
        self._hero.search_changed.connect(self._on_search_changed)
        self._hero.filters_changed.connect(self._on_structured_filters_changed)
        self._hero.new_report_requested.connect(self.new_document_requested.emit)
        self._hero.new_template_requested.connect(self._on_create_template)
        self._hero.continue_last_requested.connect(self.recent_file_opened.emit)

        self._tab_bar = TabBar(["Arquivos", "Templates"])
        self._tab_bar.tab_changed.connect(self._on_tab_changed)

        self._arquivos = RecentesPanel()
        self._arquivos.opened.connect(self.recent_file_opened.emit)
        self._arquivos.import_requested.connect(self.new_document_requested.emit)

        self._templates_panel = TemplatesPanel()
        self._templates_panel.template_selected.connect(self._on_template_selected)
        self._templates_panel.create_requested.connect(self._on_create_template)

        self._stack = _HomeStack()
        self._stack.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self._stack.addWidget(self._arquivos)
        self._stack.addWidget(self._templates_panel)
        self._stack.setCurrentIndex(self.TAB_ARQUIVOS)

        self._scroll_host = _StickyTabScrollHost(self._hero, self._tab_bar, self._stack)
        self._page_scroll = self._scroll_host.page_scroll

        outer.addWidget(self._scroll_host, stretch=1)

    def _connect_view_model(self) -> None:
        self._vm.templates_loaded.connect(self._on_templates_loaded)
        self._vm.recent_files_loaded.connect(self._on_arquivos_loaded)
        self._vm.error_occurred.connect(
            lambda title, msg, details: show_friendly_error(self, title, msg, details)
        )

    def _on_template_selected(self, template_id: str) -> None:
        self.template_editor_requested.emit(template_id)

    def _on_create_template(self) -> None:
        self.template_editor_requested.emit("new")

    def _on_templates_loaded(self, templates: list[TemplateSummary]) -> None:
        self._templates = list(templates)
        self._templates_panel.render(templates)
        self._tab_bar.update_count(self.TAB_TEMPLATES, len(templates))
        self._refresh_hero_stats()
        if self._search_query:
            self._templates_panel.apply_filter(self._search_query)
            self._update_search_hint()

    def _on_arquivos_loaded(self, files: list[RecentFileSummary]) -> None:
        self._recent_files = list(files)
        self._arquivos.render(files)
        self._hero.filter_bar.set_project_options(distinct_projects(files))
        self._hero.filter_bar.set_component_options(distinct_components(files))
        self._tab_bar.update_count(self.TAB_ARQUIVOS, len(files))
        self._refresh_hero_stats()
        self._apply_arquivos_filters()

    def _merged_arquivos_filter_state(self) -> RecentFilesFilterState:
        bar = self._hero.filter_bar.current_state()
        return RecentFilesFilterState(
            query=self._search_query,
            period=bar.period,
            project=bar.project,
            component=bar.component,
            sort=bar.sort,
        )

    def _apply_arquivos_filters(self) -> None:
        self._arquivos.update_filters(self._merged_arquivos_filter_state())
        self._update_search_hint()

    def _clear_search_and_filters(self) -> None:
        self._search_query = ""
        self._hero.search_bar.clear()
        self._hero.filter_bar.clear_all_including_query()
        self._templates_panel.apply_filter("")
        self._apply_arquivos_filters()

    def _refresh_hero_stats(self) -> None:
        last = self._recent_files[0] if self._recent_files else None
        self._hero.update_stats(len(self._recent_files), len(self._templates), last)

    def _on_search_changed(self, query: str) -> None:
        self._search_query = query
        self._hero.filter_bar.set_query(query)
        self._apply_arquivos_filters()
        self._templates_panel.apply_filter(query)

        if not query.strip():
            return

        current_index = self._stack.currentIndex()
        current_has_results = (
            self._arquivos.has_visible_items()
            if current_index == self.TAB_ARQUIVOS
            else self._templates_panel.has_visible_items()
        )
        if current_has_results:
            return

        if self._arquivos.has_visible_items():
            self.switch_to_tab(self.TAB_ARQUIVOS)
        elif self._templates_panel.has_visible_items():
            self.switch_to_tab(self.TAB_TEMPLATES)

    def _on_structured_filters_changed(self, _state: RecentFilesFilterState) -> None:
        self._apply_arquivos_filters()

    def _update_search_hint(self) -> None:
        query = self._search_query.strip()
        if not query:
            self._hero.set_search_result_hint("")
            return
        file_count = self._arquivos.visible_count()
        template_count = self._templates_panel.visible_count()
        total = file_count + template_count
        if total == 0:
            self._hero.set_search_result_hint(f'Nenhum resultado para "{query}"')
        else:
            self._hero.set_search_result_hint(
                f"{total} resultado(s) — {file_count} arquivo(s), {template_count} template(s)"
            )

    def _on_tab_changed(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        self._hero.set_filters_visible(index == self.TAB_ARQUIVOS)

    def switch_to_tab(self, index: int) -> None:
        self._tab_bar.set_active(index)
        self._stack.setCurrentIndex(index)
        self._hero.set_filters_visible(index == self.TAB_ARQUIVOS)

    def refresh_appearance(self) -> None:
        """Reaplica estilos dinâmicos após mudança de tema/contraste/fonte."""
        self._tab_bar.refresh_appearance()
        self._hero.refresh_appearance()
        self._arquivos.refresh_appearance()
        self._templates_panel.refresh_appearance()
