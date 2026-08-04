"""Operações de template no workspace."""
from __future__ import annotations

from src.core.application.template_apply import apply_template_content_defaults, apply_template_layout
from src.core.application.template_layout import (
    document_has_layout_changes,
    layout_snapshot,
)
from src.core.domain.ports import ReportDocument, ReportExporter, TemplateRepository


class TemplateWorkspaceService:
    def __init__(
        self,
        template_repo: TemplateRepository | None,
        exporter: ReportExporter,
    ) -> None:
        self._template_repo = template_repo
        self._exporter = exporter

    def is_layout_dirty(self, document: ReportDocument) -> bool:
        return document_has_layout_changes(document, self._template_repo)

    def list_templates(self) -> list[dict]:
        if self._template_repo is None:
            return [{"id": "default", "name": "Template Padrão SENAI/ZEISS", "is_default": True}]
        return self._template_repo.list_templates()

    def apply_template_change(self, document: ReportDocument, template_id: str) -> None:
        document.template_id = template_id
        document.section_overrides.clear()
        document.section_order = None
        document.deleted_section_ids = []
        document.custom_sections = []
        if self._template_repo is not None:
            apply_template_layout(document, self._template_repo)
            apply_template_content_defaults(document, self._template_repo)

    def save_as_template(
        self,
        document: ReportDocument,
        name: str,
        create_new: bool,
    ) -> str | None:
        if self._template_repo is None or not name.strip():
            return None
        template_id = document.template_id
        if create_new or template_id == "default":
            template_id = self._new_template_id()
        sections_config = self._build_sections_config(document)
        content_defaults = layout_snapshot(document)["section_overrides"]
        self._template_repo.save_full_template(
            template_id, sections_config, content_defaults, name.strip()
        )
        document.template_id = template_id
        return template_id

    def _new_template_id(self) -> str:
        existing = {t["id"] for t in self.list_templates()}
        index = 1
        while f"custom_{index}" in existing:
            index += 1
        return f"custom_{index}"

    def _build_sections_config(self, document: ReportDocument) -> dict:
        if hasattr(self._exporter, "get_export_blocks"):
            blocos = self._exporter.get_export_blocks(document)
        else:
            blocos = []
        return {
            bloco["tipo"]: {"enabled": True, "order": index}
            for index, bloco in enumerate(blocos)
        }
