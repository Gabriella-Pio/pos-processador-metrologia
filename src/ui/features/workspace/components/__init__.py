"""Componentes da feature workspace."""

__all__ = ["SectionEditorPanel", "SectionsPanel", "WorkspaceView"]


def __getattr__(name: str):
    if name == "SectionEditorPanel":
        from src.ui.features.workspace.components.section_editor_panel import SectionEditorPanel

        return SectionEditorPanel
    if name == "SectionsPanel":
        from src.ui.features.workspace.components.sections_panel import SectionsPanel

        return SectionsPanel
    if name == "WorkspaceView":
        from src.ui.features.workspace.components.workspace_view import WorkspaceView

        return WorkspaceView
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
