"""Repositórios in-memory para demo e testes de UI."""
from __future__ import annotations

from datetime import datetime

from src.core.domain.ports import ReportDocument


class InMemoryRecentFilesRepository:
    def __init__(self) -> None:
        self._files = [
            {
                "id": "1",
                "file_name": "Relatorio_Peca_A.pdf",
                "client_project": "Cliente Alfa",
                "version": "3",
                "updated_at": datetime.now(),
            },
        ]

    def list_recent(self, limit: int = 20):
        return self._files[:limit]

    def save(self, document: ReportDocument, file_name: str) -> str:
        new_id = str(len(self._files) + 1)
        self._files.insert(
            0,
            {
                "id": new_id,
                "file_name": file_name,
                "client_project": document.client_project,
                "version": "1",
                "updated_at": datetime.now(),
            },
        )
        return new_id

    def get_by_id(self, file_id: str):
        for item in self._files:
            if item["id"] == file_id:
                return {
                    "file_path": item["file_name"],
                    "client_project": item["client_project"],
                    "evaluated_component": item["file_name"],
                    "file_name": item["file_name"],
                }
        return None


class InMemoryTemplateRepository:
    def __init__(self) -> None:
        self._templates = [
            {"id": "default", "name": "Padrão SENAI/ZEISS", "is_default": True},
        ]

    def list_templates(self):
        return self._templates

    def save_template(self, template_id: str, sections_config: dict) -> None:
        pass

    def get_template_config(self, template_id: str) -> dict:
        return {}

    def get_content_defaults(self, template_id: str) -> dict:
        return {}

    def save_content_defaults(self, template_id: str, content: dict) -> None:
        pass

    def save_full_template(
        self, template_id: str, sections_config: dict, content_defaults: dict, name: str
    ) -> None:
        pass

    def update_template_name(self, template_id: str, name: str) -> None:
        pass

    def delete_template(self, template_id: str) -> bool:
        from src.core.infrastructure.template_repository import is_builtin_template_id

        if is_builtin_template_id(template_id):
            return False
        before = len(self._templates)
        self._templates = [t for t in self._templates if t.get("id") != template_id]
        return len(self._templates) < before
