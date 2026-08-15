"""Testes de serialização de snapshot de projeto."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.core.application.project_snapshot_serializer import (
    apply_workspace_to_document,
    deserialize_project_snapshot,
    serialize_project_snapshot,
)
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import ReportDocument, ReportImage, VersionEntry


def _sample_session() -> ProjectSession:
    document = ReportDocument(
        source_pdf_path=Path("/data/a.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
        template_id="default",
    )
    document.section_overrides = {"introducao": {"title": "Intro custom"}}
    document.images = [
        ReportImage(image_path=Path("/tmp/foto.png"), section_id="grafica", caption="Foto 1")
    ]
    document.version_history = [
        VersionEntry(
            version_number=1,
            timestamp=datetime(2026, 8, 6, 10, 0),
            responsible_name="Ana",
            description="Primeira versão",
        )
    ]
    session = ProjectSession(
        client_project="Cargill",
        template_id="default",
        report_mode="mixed",
        project_id="proj-1",
        display_name="relatorio_a",
        active_index=0,
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path("/data/a.pdf"),
                evaluated_component="Eixo",
                source_kind="calypso",
                template_id="default",
                document=document,
            )
        ],
    )
    return session


def test_serialize_project_snapshot_roundtrip() -> None:
    session = _sample_session()
    raw = serialize_project_snapshot(session)
    restored, workspaces, histories = deserialize_project_snapshot(raw)

    assert restored.project_id == "proj-1"
    assert restored.display_name == "relatorio_a"
    assert len(restored.documents) == 1
    assert str(restored.documents[0].source_pdf_path) == "/data/a.pdf"

    workspace = workspaces["/data/a.pdf"]
    assert workspace["section_overrides"]["introducao"]["title"] == "Intro custom"
    assert histories["/data/a.pdf"][0].responsible_name == "Ana"


def test_snapshot_preserves_unified_custom_and_extra_sections() -> None:
    session = _sample_session()
    session.unified_custom_sections = [{"id": "custom_1", "title": "Extra"}]
    session.unified_extra_section_ids = ["estat_resumo_diametros"]
    session.unified_deleted_section_ids = ["anexos"]
    restored, _workspaces, _histories = deserialize_project_snapshot(
        serialize_project_snapshot(session)
    )
    assert restored.unified_custom_sections == [{"id": "custom_1", "title": "Extra"}]
    assert restored.unified_extra_section_ids == ["estat_resumo_diametros"]
    assert restored.unified_deleted_section_ids == ["anexos"]


def test_apply_workspace_to_document() -> None:
    document = ReportDocument(
        source_pdf_path=Path("/data/a.pdf"),
        client_project="Cargill",
        evaluated_component="Eixo",
    )
    workspace = {
        "template_id": "tomografia",
        "section_overrides": {"x": {"y": 1}},
        "parsed_overrides": {},
        "section_order": ["introducao"],
        "images": [{"path": "/tmp/img.png", "section_id": "grafica", "caption": ""}],
        "custom_sections": [],
        "deleted_section_ids": [],
        "attachment_pdf_paths": ["/data/a.pdf"],
    }
    apply_workspace_to_document(document, workspace)
    assert document.template_id == "tomografia"
    assert document.section_order == ["introducao"]
    assert len(document.images) == 1
