"""Smoke tests da camada UI — imports e filtros do dashboard."""
from __future__ import annotations

from datetime import datetime

import pytest


def test_ui_module_imports() -> None:
    """Garante que todos os módulos de UI carregam sem NameError/import error."""
    modules = [
        "src.ui.styles",
        "src.ui.styles.tokens",
        "src.ui.styles.helpers",
        "src.ui.components.icons",
        "src.ui.features.workspace",
        "src.ui.features.workspace.components",
        "src.ui.features.workspace.components.workspace_view",
        "src.ui.features.workspace.components.section_editor_panel",
        "src.ui.features.workspace.components.section_edit_view",
        "src.ui.shared.report_editor.section_edit_view",
        "src.ui.shared.report_editor.preview_worker",
        "src.ui.shared.report_editor.editor_shell",
        "src.ui.shared.report_editor.base_sidebar_panel",
        "src.core.application",
        "src.core.application.document_editing",
        "src.ui.shared.report_editor",
        "src.ui.shared.report_editor.sections_list_panel",
        "src.ui.shared.report_editor.global_fields_panel",
        "src.ui.shared.report_editor.preview_panel",
        "src.ui.features.templates.viewmodels.template_editor_viewmodel",
        "src.ui.features.templates.components.template_sidebar_panel",
        "src.core.application.template_preview",
        "src.ui.features.workspace.components.medicoes_table_editor",
        "src.ui.features.workspace.dialogs.custom_section_dialog",
        "src.ui.features.workspace.dialogs.version_register_dialog",
        "src.ui.features.home.dialogs.project_setup_dialog",
        "src.ui.features.templates.components.template_editor_view",
        "src.core.domain.section_schema",
        "src.ui.components.inputs",
        "src.ui.components.centered_layout",
        "src.ui.features.home.components.hero",
        "src.ui.components.cards",
        "src.ui.components.header",
        "src.ui.components.tab_bar",
        "src.ui.features.home.components",
        "src.ui.features.home.components.files_filter_bar",
        "src.ui.features.home.components.layout_utils",
        "src.ui.features.home.components.recentes_panel",
        "src.ui.features.home.components.templates_panel",
        "src.ui.features.home.components.home_view",
        "src.ui.features.home.models.dashboard",
        "src.ui.features.home.viewmodels.home_viewmodel",
        "src.ui.features.home",
        "src.ui.controllers.navigation_controller",
        "src.ui.features.home.dialogs.import_dialog",
        "src.ui.dialogs.help_accessibility_dialog",
        "src.ui.accessibility",
        "src.ui.accessibility.appearance",
        "src.ui.main_window",
    ]
    for module_name in modules:
        __import__(module_name)


def test_filter_recent_files_matches_name_and_project() -> None:
    from src.ui.features.home.models.dashboard import RecentFileSummary, filter_recent_files

    files = [
        RecentFileSummary(
            file_id="1",
            file_name="pistao_trabalho.pdf",
            client_project="Cliente Alpha",
            version="1",
            updated_at=datetime(2026, 1, 1),
        ),
        RecentFileSummary(
            file_id="2",
            file_name="bomba.pdf",
            client_project="Projeto Beta",
            version="2",
            updated_at=datetime(2026, 1, 2),
        ),
    ]

    assert len(filter_recent_files(files, "")) == 2
    assert len(filter_recent_files(files, "pistao")) == 1
    assert filter_recent_files(files, "pistao")[0].file_id == "1"
    assert len(filter_recent_files(files, "beta")) == 1
    assert len(filter_recent_files(files, "inexistente")) == 0


def test_apply_recent_files_filters_by_period_and_project() -> None:
    from src.ui.features.home.models.dashboard import (
        PERIOD_7D,
        RecentFileSummary,
        RecentFilesFilterState,
        SORT_NAME,
        apply_recent_files_filters,
    )

    now = datetime(2026, 8, 3, 12, 0, 0)
    files = [
        RecentFileSummary(
            file_id="1",
            file_name="a.pdf",
            client_project="Cargill",
            version="v1",
            updated_at=datetime(2026, 8, 2, 10, 0, 0),
            evaluated_component="Pistão",
        ),
        RecentFileSummary(
            file_id="2",
            file_name="b.pdf",
            client_project="Global",
            version="v1",
            updated_at=datetime(2026, 7, 1, 10, 0, 0),
            evaluated_component="Bomba",
        ),
    ]

    state = RecentFilesFilterState(period=PERIOD_7D, project="Cargill")
    result = apply_recent_files_filters(files, state, now=now)
    assert len(result) == 1
    assert result[0].file_id == "1"

    sorted_by_name = apply_recent_files_filters(
        files,
        RecentFilesFilterState(sort=SORT_NAME),
        now=now,
    )
    assert [f.file_name for f in sorted_by_name] == ["a.pdf", "b.pdf"]


def test_filter_templates_matches_name() -> None:
    from src.ui.features.home.models.dashboard import TemplateSummary, filter_templates

    templates = [
        TemplateSummary(template_id="a", name="Relatório Padrão"),
        TemplateSummary(template_id="b", name="Tomografia"),
    ]

    assert len(filter_templates(templates, "")) == 2
    assert len(filter_templates(templates, "tomografia")) == 1
    assert filter_templates(templates, "tomografia")[0].template_id == "b"


def test_search_bar_emits_text_changed() -> None:
    """SearchBar propaga texto via pyqtSignal."""
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.components.inputs import SearchBar

    bar = SearchBar()
    received: list[str] = []
    bar.textChanged.connect(received.append)
    bar.field.setText("metrologia")
    app.processEvents()

    assert received == ["metrologia"]


def test_search_bar_clear() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.components.inputs import SearchBar

    bar = SearchBar()
    bar.field.setText("teste")
    app.processEvents()
    bar.clear()
    app.processEvents()

    assert bar.field.text() == ""


def test_tab_bar_uses_qtabbar() -> None:
    """TabBar da Home usa QTabBar nativo estilizado via QSS global."""
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication, QTabBar

    app = QApplication.instance() or QApplication([])
    from src.ui.components.tab_bar import TabBar

    bar = TabBar(["Arquivos", "Templates"])
    tab_widget = bar.tab_widget
    assert isinstance(tab_widget, QTabBar)
    assert tab_widget.objectName() == "HomeTabBar"
    assert tab_widget.count() == 2
    assert bar.height() == 44

    bar.update_count(0, 5)
    assert tab_widget.tabText(0) == "Arquivos (5)"
    bar.set_active(1)
    assert tab_widget.currentIndex() == 1


def test_search_bar_filter_button_uses_fragment_style() -> None:
    """Botão de filtro integrado na pill — sem borda standalone."""
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.components.inputs import SearchBar

    bar = SearchBar(show_filter_toggle=True)
    style = bar._filter_btn.styleSheet()
    assert "border: none" in style
    assert "border: 1px" not in style
    assert "FilterToggleButton" in style


def test_hero_command_bar_instantiates() -> None:
    pytest.importorskip("PyQt6")
    from datetime import datetime
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.components.hero import HeroCommandBar
    from src.ui.features.home.models.dashboard import RecentFileSummary

    hero = HeroCommandBar()
    assert not hero._new_file_card.isHidden()
    assert not hero._secondary_card.isHidden()
    assert hero._continue_card.isHidden()

    hero.update_stats(1, 3, 2)
    assert hero._continue_card.isHidden()

    last = RecentFileSummary(
        file_id="1",
        file_name="relatorio.pdf",
        client_project="Cargill",
        version="v1",
        updated_at=datetime(2026, 8, 3),
    )
    hero.update_stats(1, 3, 2, last_export=last)
    assert not hero._continue_card.isHidden()
    assert hero.filter_bar.is_expanded() is False


def test_files_filter_bar_expands() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.components import FilesFilterBar

    bar = FilesFilterBar()
    assert bar.is_expanded() is False
    bar.set_expanded(True)
    assert bar.is_expanded() is True


def test_home_view_has_page_scroll() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.viewmodels.home_viewmodel import HomeViewModel
    from src.ui.features.home.components.home_view import HomeView

    class _RepoStub:
        def list_recent(self, limit: int = 20):
            return []

        def list_templates(self):
            return []

    vm = HomeViewModel(_RepoStub(), _RepoStub())
    home = HomeView(vm)
    assert home._page_scroll.objectName() == "HomePageScroll"
    assert hasattr(home, "_scroll_host")


def test_hero_uses_inline_metrics() -> None:
    pytest.importorskip("PyQt6")
    from datetime import datetime
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.components.hero import HeroCommandBar
    from src.ui.features.home.models.dashboard import RecentFileSummary

    hero = HeroCommandBar()
    assert hasattr(hero, "_inline_metrics")
    hero.update_stats(2, 11, 3)
    assert "2 projetos" in hero._inline_metrics.text()
    assert "11 exports" in hero._inline_metrics.text()
    assert "3 templates" in hero._inline_metrics.text()

    last = RecentFileSummary(
        file_id="1",
        file_name="relatorio.pdf",
        client_project="Cargill",
        version="v1",
        updated_at=datetime(2026, 8, 3),
    )
    hero.update_stats(2, 11, 3, last_export=last)
    assert "último: Cargill" in hero._inline_metrics.text()


def test_filter_combo_uses_themed_popup() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.components import FilesFilterBar

    bar = FilesFilterBar()
    combo = bar._period
    assert combo.objectName() == "FilterCombo"
    assert combo.view().objectName() == "FilterComboPopup"


def test_recentes_panel_has_density_controls() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.components.recentes_panel import RecentesPanel

    panel = RecentesPanel()
    assert hasattr(panel, "_controls")
    assert panel._density == "comfortable"


def test_empty_results_messages() -> None:
    from src.ui.features.home.models.dashboard import empty_results_messages

    title, subtitle = empty_results_messages("hskgag")
    assert title == "Nenhum resultado encontrado"
    assert subtitle == 'Nenhum resultado corresponde a "hskgag".'

    title, subtitle = empty_results_messages(has_active_filters=True)
    assert subtitle == "Nenhum resultado corresponde aos filtros selecionados."


def test_app_header_breadcrumb() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.components.header import AppHeader

    header = AppHeader()
    header.set_breadcrumb([("Início", None), ("Workspace", None)])
    assert header is not None


def test_grid_columns_for_width() -> None:
    from src.ui.features.home.components.grid_utils import grid_columns_for_width

    # Margens padrão = 64px (xl * 2); card 168 + gap 16
    assert grid_columns_for_width(400) == 1
    assert grid_columns_for_width(800) == 4
    assert grid_columns_for_width(2000) == 6  # capped at MAX_GRID_COLUMNS


def test_base_stylesheet_loads_from_qss() -> None:
    from src.ui.styles import base_stylesheet

    sheet = base_stylesheet()
    assert "QMainWindow" in sheet
    assert "#0D1117" in sheet or "0D1117" in sheet
    assert "HomeSurface" in sheet
    assert "HomePageScroll" in sheet
    assert "HomeCenteredColumn" in sheet
    assert "HomeTabBar" in sheet
    assert "HomePanelScroll" in sheet
    assert "SectionHeaderTitle" in sheet
    assert "WorkspaceSurface" in sheet
    assert "WorkspaceSidebar" in sheet
    assert "WorkspaceProjectTabs" in sheet


def test_workspace_panels_refresh_appearance() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.accessibility.appearance import AppearanceManager, AppearanceSettings
    from src.ui.components.panels import (
        AnnotationToolbar,
        BookmarksPanel,
        ImageManagerPanel,
        VersionHistoryPanel,
    )
    from src.ui.features.workspace.components.section_editor_panel import SectionEditorPanel
    from src.ui.styles import PALETTE

    bookmarks = BookmarksPanel()
    images = ImageManagerPanel()
    toolbar = AnnotationToolbar()
    versions = VersionHistoryPanel()
    editor = SectionEditorPanel()

    AppearanceManager.instance().apply(AppearanceSettings(theme="light"), persist=False)
    light_bg = PALETTE.bg_sidebar
    bookmarks.refresh_appearance()
    editor.refresh_appearance()

    AppearanceManager.instance().apply(AppearanceSettings(theme="dark"), persist=False)
    dark_bg = PALETTE.bg_sidebar
    assert light_bg != dark_bg
    editor.refresh_appearance()
    assert editor.objectName() == "WorkspaceSidebar"


def test_home_surface_object_names() -> None:
    """Painéis Home usam objectNames — fundos vêm do QSS global, não inline."""
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication, QVBoxLayout

    app = QApplication.instance() or QApplication([])
    from src.ui.components.centered_layout import make_centered_column
    from src.ui.features.home.components.layout_utils import make_scroll

    outer, _ = make_centered_column()
    assert outer.objectName() == "HomeCenteredColumn"
    assert outer.styleSheet() == ""

    scroll = make_scroll(QVBoxLayout())
    assert scroll.objectName() == "HomePanelScroll"
    assert scroll.styleSheet() == ""
    wrapper = scroll.widget()
    assert wrapper is not None
    assert wrapper.objectName() == "HomeScrollContent"
    assert wrapper.styleSheet() == ""


def test_theme_switch_updates_home_surface_colors(tmp_path) -> None:
    """Troca de tema atualiza tokens nos seletores HomeSurface do QSS global."""
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.accessibility.appearance import AppearanceManager, AppearanceSettings
    from src.ui.styles import PALETTE, base_stylesheet

    storage = tmp_path / "prefs.json"
    manager = AppearanceManager(storage)
    manager.apply(AppearanceSettings(theme="dark"), persist=False)
    dark_bg = PALETTE.bg_base
    assert dark_bg in base_stylesheet()

    manager.apply(AppearanceSettings(theme="light"), persist=False)
    light_bg = PALETTE.bg_base
    assert light_bg != dark_bg
    assert light_bg in base_stylesheet()
    assert "HomeSurface" in base_stylesheet()


def test_tab_style_loads_fragments() -> None:
    from src.ui.styles import tab_style

    active = tab_style(active=True)
    inactive = tab_style(active=False)
    assert "senai_orange" in active or "#f0431e" in active
    assert "border-bottom" in inactive


def test_appearance_manager_persists_settings(tmp_path) -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.accessibility.appearance import AppearanceManager, AppearanceSettings

    storage = tmp_path / "prefs.json"
    manager = AppearanceManager(storage)
    manager.apply(
        AppearanceSettings(theme="light", contrast="high", font_scale=1.25),
        persist=True,
    )

    reloaded = AppearanceManager(storage)
    reloaded.load()
    settings = reloaded.settings
    assert settings.theme == "light"
    assert settings.contrast == "high"
    assert settings.font_scale == 1.25


def test_help_accessibility_dialog_instantiates() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.dialogs.help_accessibility_dialog import HelpAccessibilityDialog, HelpDialogMode

    dialog = HelpAccessibilityDialog()
    assert dialog.windowTitle() == "Ajuda"

    prefs = HelpAccessibilityDialog(mode=HelpDialogMode.PREFERENCES)
    assert prefs.windowTitle() == "Preferências"


def test_project_setup_dialog_single_screen() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication, QStackedWidget, QTableWidget

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.dialogs.project_setup_dialog import ProjectSetupDialog

    class _FakeParser:
        def parse(self, pdf_path):  # noqa: ANN001
            raise NotImplementedError

    class _FakeTemplateRepo:
        def list_templates(self) -> list[dict]:
            return [{"id": "default", "name": "Padrão"}]

    dialog = ProjectSetupDialog(_FakeParser(), _FakeTemplateRepo())
    assert dialog.findChild(QStackedWidget) is None
    assert dialog.findChild(QTableWidget) is None
    assert dialog._confirm_btn.text() == "Abrir workspace"
    assert dialog._component_field is not None
    assert dialog._files_error.isHidden()


def test_labeled_line_edit_shows_required_message() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.components.inputs import LabeledLineEdit

    field = LabeledLineEdit("Cliente / Projeto", required=True)
    field.show_validation_error()
    assert not field._error_label.isHidden()
    assert field._error_label.text() == "Campo obrigatório."

    field.set_text("Cargill")
    assert field._error_label.isHidden()


def test_drop_zone_accepts_drag_move() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtCore import QMimeData, Qt, QUrl
    from PyQt6.QtGui import QDragMoveEvent
    from PyQt6.QtWidgets import QApplication, QLabel

    app = QApplication.instance() or QApplication([])
    from src.ui.features.home.dialogs.import_dialog import DropZone

    counter = QLabel()
    zone = DropZone(counter)
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile("/tmp/sample.pdf")])
    event = QDragMoveEvent(
        zone.rect().center(),
        Qt.DropAction.CopyAction,
        mime,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    zone.dragMoveEvent(event)
    assert event.isAccepted()


def test_workspace_layout_editor_left_preview_right() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication, QSplitter

    app = QApplication.instance() or QApplication([])
    from src.core.infrastructure.adapters import RealReportExporterAdapter, RealReportParserAdapter
    from src.ui.controllers.app_state import AppState
    from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel
    from src.ui.features.workspace.components.workspace_view import WorkspaceView

    vm = WorkspaceViewModel(AppState(), RealReportParserAdapter(), RealReportExporterAdapter())
    view = WorkspaceView(AppState(), vm)
    splitter = view.findChild(QSplitter)
    assert splitter is not None
    assert splitter.widget(0).objectName() == "WorkspaceSidebar"
    assert splitter.widget(1).objectName() == "WorkspaceEditorPanel"
    assert splitter.widget(2).objectName() == "WorkspacePreviewPanel"
    assert not hasattr(view, "back_requested")


def test_inline_banner_hides_info_level() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.ui.components.feedback import FeedbackLevel, InlineBanner

    banner = InlineBanner("", FeedbackLevel.INFO)
    banner.sync_visibility()
    assert banner.isHidden()

    banner.set_level(FeedbackLevel.WARNING)
    assert banner.isVisible()

    banner.set_level(FeedbackLevel.DANGER)
    assert banner.isVisible()


def test_workspace_export_shortcut_and_hidden_banner() -> None:
    pytest.importorskip("PyQt6")
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    from src.core.infrastructure.adapters import RealReportExporterAdapter, RealReportParserAdapter
    from src.ui.controllers.app_state import AppState
    from src.ui.features.workspace.components.workspace_view import WorkspaceView
    from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel

    vm = WorkspaceViewModel(AppState(), RealReportParserAdapter(), RealReportExporterAdapter())
    view = WorkspaceView(AppState(), vm)

    assert view._banner.isHidden()
    assert view._export_btn.toolTip() == "Exportar PDF (Ctrl+E)"
    from PyQt6.QtGui import QKeySequence, QShortcut

    shortcuts = view.findChildren(QShortcut)
    sequences = {shortcut.key().toString() for shortcut in shortcuts}
    assert "Ctrl+S" in sequences
    assert "Ctrl+E" in sequences
    assert view._preview_menu is not None
    assert view._save_layout_action is not None
    assert view._template_selector is not None
    assert view._template_combo.objectName() == "FilterCombo"
    assert view._project_tabs_strip.objectName() == "WorkspaceProjectTabsStrip"
    from PyQt6.QtWidgets import QSplitter

    splitter = view.findChild(QSplitter)
    assert splitter is not None
    preview_panel = splitter.widget(2)
    assert preview_panel.objectName() == "WorkspacePreviewPanel"
    assert preview_panel.findChild(view._action_bar.__class__, "WorkspacePreviewContext") is not None
    assert view._project_tabs_strip.parentWidget() is view
