"""Comandos de template no contexto do workspace."""
from __future__ import annotations

from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import ReportDocument, TemplateRepository
from src.ui.features.workspace.services.template_workspace_service import TemplateWorkspaceService


class TemplateCommands:
    @staticmethod
    def apply_template_change(
        session: ProjectSession,
        document: ReportDocument,
        template_id: str,
        template_service: TemplateWorkspaceService,
    ) -> None:
        slot = session.active_slot
        if session.report_mode == "mixed" and slot is not None:
            slot.template_id = template_id
            template_service.apply_template_change(document, template_id)
            return
        session.template_id = template_id
        for project_slot in session.documents:
            if project_slot.document is not None:
                project_slot.template_id = template_id
                template_service.apply_template_change(project_slot.document, template_id)

    @staticmethod
    def save_and_link_template(
        session: ProjectSession,
        document: ReportDocument,
        name: str,
        create_new: bool,
        template_service: TemplateWorkspaceService,
    ) -> str | None:
        template_id = template_service.save_as_template(document, name, create_new)
        if template_id is None:
            return None
        session.template_id = template_id
        for slot in session.documents:
            if slot.document is not None:
                slot.document.template_id = template_id
        return template_id
