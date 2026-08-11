"""Feature workspace — editor de relatório."""

__all__ = ["WorkspaceView", "WorkspaceViewModel"]


def __getattr__(name: str):
    if name == "WorkspaceView":
        from src.ui.features.workspace.components.workspace_view import WorkspaceView

        return WorkspaceView
    if name == "WorkspaceViewModel":
        from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel

        return WorkspaceViewModel
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
