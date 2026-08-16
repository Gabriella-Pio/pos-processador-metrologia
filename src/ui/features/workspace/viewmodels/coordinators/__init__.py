"""Coordenadores (mixins) do WorkspaceViewModel."""
from src.ui.features.workspace.viewmodels.coordinators.project_coordinator import (
    WorkspaceProjectCoordinator,
)
from src.ui.features.workspace.viewmodels.coordinators.edit_coordinator import (
    WorkspaceEditCoordinator,
)
from src.ui.features.workspace.viewmodels.coordinators.media_coordinator import (
    WorkspaceMediaCoordinator,
)
from src.ui.features.workspace.viewmodels.coordinators.lifecycle_coordinator import (
    WorkspaceLifecycleCoordinator,
)

__all__ = [
    "WorkspaceProjectCoordinator",
    "WorkspaceEditCoordinator",
    "WorkspaceMediaCoordinator",
    "WorkspaceLifecycleCoordinator",
]
