"""Comandos de edição de campos parseados do PDF (globais e medições)."""
from __future__ import annotations

from src.core.application.document_editing import sync_operador
from src.core.domain.ports import ReportDocument


class ParsedFieldCommands:
    @staticmethod
    def update_parsed_field(document: ReportDocument, key: str, value: str) -> None:
        if key in ("client_project", "evaluated_component"):
            if key == "client_project":
                document.client_project = value
            else:
                document.evaluated_component = value
        elif key == "operador":
            sync_operador(document, value)
        else:
            document.parsed_overrides.setdefault("scalar", {})[key] = value

    @staticmethod
    def restore_parsed_field(document: ReportDocument, key: str) -> None:
        if key in ("client_project", "evaluated_component"):
            raw = document.raw_parsed_data
            if key == "client_project":
                document.client_project = getattr(raw, "cliente_projeto", "Projeto")
            else:
                document.evaluated_component = getattr(raw, "componente", "Componente")
        else:
            document.parsed_overrides.get("scalar", {}).pop(key, None)

    @staticmethod
    def update_itens_medicao(document: ReportDocument, rows: list[dict[str, str]]) -> None:
        document.parsed_overrides["itens_medicao"] = rows

    @staticmethod
    def restore_itens_medicao(document: ReportDocument) -> None:
        document.parsed_overrides.pop("itens_medicao", None)
