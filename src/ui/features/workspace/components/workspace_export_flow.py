"""Fluxo de exportação do workspace (diálogos e validação de banner)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog, QWidget

from src.ui.components.feedback import FeedbackLevel, InlineBanner, show_info
from src.ui.controllers.app_state import AppState
from src.ui.features.workspace.viewmodels.workspace_viewmodel import WorkspaceViewModel


def run_workspace_export(
    parent: QWidget,
    vm: WorkspaceViewModel,
    app_state: AppState,
    *,
    export_individual_cb,
    export_merged_cb,
) -> None:
    session = app_state.project_session
    multi = session is not None and len(session.documents) > 1

    if multi and export_merged_cb.isChecked() and not export_merged_cb.isEnabled():
        show_info(
            parent,
            "Exportação unificada",
            "Em breve — mescla seções institucionais em um único PDF.",
        )

    if multi and export_individual_cb.isChecked():
        output_dir = QFileDialog.getExistingDirectory(parent, "Pasta para exportação em lote")
        if output_dir:
            paths = vm.export_all_documents(Path(output_dir))
            if paths:
                show_info(parent, "Exportação em lote", f"{len(paths)} PDF(s) exportado(s).")
        return

    output_path, _ = QFileDialog.getSaveFileName(parent, "Exportar PDF", "", "PDF (*.pdf)")
    if output_path:
        vm.export_document(Path(output_path))


def apply_export_validation_banner(banner: InlineBanner, issues: list[dict]) -> None:
    errors = [i for i in issues if i.get("level") == "error"]
    warnings = [i for i in issues if i.get("level") == "warning"]
    if errors:
        banner.set_level(FeedbackLevel.DANGER)
        banner.set_message(errors[0]["message"])
    elif warnings:
        banner.set_level(FeedbackLevel.WARNING)
        banner.set_message(warnings[0]["message"])
    else:
        banner.set_level(FeedbackLevel.INFO)
        banner.set_message("")
        banner.sync_visibility()
