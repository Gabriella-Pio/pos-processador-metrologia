"""Lógica compartilhada das sidebars workspace e template."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame

from src.core.domain.ports import VersionEntry
from src.ui.shared.report_editor.section_edit_view import SectionEditView


class BaseSidebarPanel(QFrame):
    """Estado e fluxo comum: sumário → abrir editor de seção → patch em refresh."""

    edit_visibility_changed = pyqtSignal(bool)

    def __init__(self, edit_view: SectionEditView | None = None, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("WorkspaceSidebar")
        self._sections_map: dict[str, dict] = {}
        self._active_section_id: str | None = None
        self._edit_open = False
        self._vm = None
        self._version_entries: list[VersionEntry] = []
        self._edit_view = edit_view or SectionEditView()

    @property
    def edit_view(self) -> SectionEditView:
        return self._edit_view

    @property
    def is_editing(self) -> bool:
        return self._edit_open

    def bind_view_model(self, view_model) -> None:
        self._vm = view_model

    def render_sections(self, sections: list[dict]) -> None:
        self._sections_map = {s["id"]: s for s in sections}
        self._render_sections_list(sections)
        if self._edit_open and self._active_section_id:
            if self._active_section_id in self._sections_map:
                self._refresh_edit_if_open()
            else:
                self._close_edit()

    def _render_sections_list(self, sections: list[dict]) -> None:
        """Subclasses atualizam o widget de sumário."""
        raise NotImplementedError

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        self._set_sections_panel_active(section_id)

    def _set_sections_panel_active(self, section_id: str | None) -> None:
        raise NotImplementedError

    def _section_overrides_from_summary(self, section: dict) -> dict:
        overrides = dict(section.get("fields") or {})
        media_kinds = section.get("media_kinds")
        if isinstance(media_kinds, list):
            overrides["media_kinds"] = list(media_kinds)
        disabled_chart_ids = section.get("disabled_chart_ids")
        if isinstance(disabled_chart_ids, list):
            overrides["disabled_chart_ids"] = list(disabled_chart_ids)
        return overrides

    def open_edit_for_section(
        self,
        section_id: str,
        *,
        itens_medicao: list[dict[str, str]] | None = None,
    ) -> None:
        self._active_section_id = section_id
        self._set_sections_panel_active(section_id)
        section = self._sections_map.get(section_id, {"id": section_id, "title": section_id})
        overrides = self._section_overrides_from_summary(section)
        locked_media_kinds: list[str] = []
        if self._vm is not None and hasattr(self._vm, "locked_media_kinds"):
            locked_media_kinds = self._vm.locked_media_kinds(section_id)
        self._edit_view.set_locked_media_kinds(locked_media_kinds)
        self._edit_view.open_section(
            section_id,
            section,
            overrides,
            section.get("table_rows"),
            itens_medicao,
            self._version_entries,
            locked_media_kinds,
        )
        self._after_edit_opened(section_id)
        already_open = self._edit_open
        self._edit_open = True
        if not already_open:
            self.edit_visibility_changed.emit(True)

    def _after_edit_opened(self, section_id: str) -> None:
        """Hook pós-abertura (ex.: filtrar fotos no workspace)."""

    def _refresh_edit_if_open(self) -> None:
        if not self._edit_open or self._active_section_id is None:
            return
        force = self._edit_view.should_force_patch()
        if not force:
            if self._edit_view.has_pending_textarea():
                return
            if self._should_skip_refresh_while_focused() and self._edit_view.has_focused_editor():
                return
        section = self._sections_map.get(self._active_section_id, {})
        self._edit_view.patch_section(
            self._section_overrides_from_summary(section),
            section.get("table_rows"),
            self._itens_medicao_for_refresh(),
            section,
        )

    def _should_skip_refresh_while_focused(self) -> bool:
        """Workspace evita sobrescrever campos com foco; template não."""
        return False

    def _itens_medicao_for_refresh(self) -> list[dict[str, str]] | None:
        return None

    def _close_edit(self) -> None:
        if not self._edit_open:
            return
        self._edit_open = False
        self._on_edit_closed()
        self.edit_visibility_changed.emit(False)

    def _on_edit_closed(self) -> None:
        """Hook ao fechar editor (ex.: reset breadcrumb no workspace)."""

    def set_version_entries(self, entries: list[VersionEntry]) -> None:
        self._version_entries = list(entries)
        if self._edit_open and self._active_section_id == "historico_versoes":
            self._edit_view.set_version_entries(entries)

    def close_edit(self) -> None:
        self._close_edit()

    def editing_section_id(self) -> str | None:
        if not self._edit_open:
            return None
        return self._edit_view.current_section_id()
