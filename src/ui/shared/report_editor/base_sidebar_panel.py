"""Lógica compartilhada das sidebars workspace e template."""
from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame

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

    def open_edit_for_section(
        self,
        section_id: str,
        *,
        itens_medicao: list[dict[str, str]] | None = None,
    ) -> None:
        self._active_section_id = section_id
        self._set_sections_panel_active(section_id)
        section = self._sections_map.get(section_id, {"id": section_id, "title": section_id})
        overrides = dict(section.get("fields") or {})
        self._edit_view.open_section(
            section_id,
            section,
            overrides,
            section.get("table_rows"),
            itens_medicao,
        )
        self._after_edit_opened(section_id)
        self._edit_open = True
        self.edit_visibility_changed.emit(True)

    def _after_edit_opened(self, section_id: str) -> None:
        """Hook pós-abertura (ex.: filtrar fotos no workspace)."""

    def _refresh_edit_if_open(self) -> None:
        if not self._edit_open or self._active_section_id is None:
            return
        if self._edit_view.has_pending_textarea():
            return
        if self._should_skip_refresh_while_focused() and self._edit_view.has_focused_editor():
            return
        section = self._sections_map.get(self._active_section_id, {})
        self._edit_view.patch_section(
            dict(section.get("fields") or {}),
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

    def close_edit(self) -> None:
        self._close_edit()

    def editing_section_id(self) -> str | None:
        if not self._edit_open:
            return None
        return self._edit_view.current_section_id()
