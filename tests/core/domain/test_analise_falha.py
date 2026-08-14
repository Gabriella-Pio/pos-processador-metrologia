"""Testes do modo análise de falha (setup, validator, smoke de seções)."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.core.application.bosello_image_import import build_manual_falha_document
from src.core.application.export_context_builder import resolve_report_kind
from src.core.application.unified_export import (
    UnifiedExportKind,
    build_mixed_mmc_bosello_document,
    resolve_unified_export_kind,
)
from src.core.domain.export_validator import validate_for_export
from src.core.domain.falha_template_defaults import FALHA_TEMPLATE_ID, falha_blocks
from src.core.domain.ports import ReportDocument, ReportImage, TechnicalControlInfo
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.generator.engine import ReportGenerator
from src.core.infrastructure.template_repository import JSONTemplateRepository
from src.ui.features.workspace.services.document_session_service import DocumentSessionService


class _ParserStub:
    def parse(self, pdf_path: Path):
        raise AssertionError(f"parser não deveria ser chamado: {pdf_path}")


def test_builtin_analise_falha_template(tmp_path: Path) -> None:
    repo = JSONTemplateRepository(str(tmp_path / "templates.json"))
    assert any(t["id"] == "analise_falha" for t in repo.list_templates())
    assert repo.get_template_config("analise_falha")
    assert repo.get_content_defaults("analise_falha")


def test_build_project_session_falha_without_pdf() -> None:
    service = DocumentSessionService(_ParserStub())
    session = service.build_project_session(
        "Cliente Falha",
        [],
        template_id="default",
        report_mode="falha",
        default_component="Peça quebrada",
    )
    assert session.report_mode == "falha"
    assert session.template_id == "analise_falha"
    assert len(session.documents) == 1
    assert session.documents[0].template_id == "analise_falha"


def test_parse_slot_falha_without_pdf_uses_manual_document() -> None:
    service = DocumentSessionService(_ParserStub())
    session = ProjectSession(
        client_project="Cliente",
        template_id="analise_falha",
        report_mode="falha",
        documents=[
            ProjectDocumentSlot(
                source_pdf_path=Path(),
                evaluated_component="Peça UF",
                source_kind="insp_ect",
                template_id="analise_falha",
            )
        ],
    )
    ok, _notice = service.parse_slot(session, 0)
    assert ok is True
    document = session.documents[0].document
    assert document is not None
    assert document.template_id == "analise_falha"
    assert resolve_report_kind(document) == "falha"
    assert document.images == []


def test_validate_falha_requires_photo() -> None:
    document = build_manual_falha_document("Peça", client_project="Cliente")
    issues = validate_for_export(document)
    assert any(i.level == "error" and "foto" in i.message.lower() for i in issues)

    foto = Path("/tmp/optica.png")
    document.images = [
        ReportImage(image_path=foto, section_id="inspecao_optica", image_id="o1")
    ]
    issues = validate_for_export(document)
    assert not any(i.level == "error" for i in issues)


def test_validate_falha_accepts_tomo_photo_only() -> None:
    document = build_manual_falha_document("Peça", client_project="Cliente")
    document.images = [
        ReportImage(
            image_path=Path("/tmp/tomo.png"),
            section_id="tomografia",
            image_id="t1",
            bosello_import=True,
        )
    ]
    issues = validate_for_export(document)
    assert not any(i.level == "error" for i in issues)


def test_mixed_unified_without_bosello_slot_uses_unified_tomo(tmp_path: Path) -> None:
    img = tmp_path / "cap.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 32)
    doc1 = ReportDocument(
        source_pdf_path=tmp_path / "p1.pdf",
        client_project="Cargill",
        evaluated_component="p1",
        control_info=TechnicalControlInfo(measured_by="Master", reviewed_by="Supervisor"),
        raw_parsed_data=SimpleNamespace(
            componente="p1",
            operador="Master",
            maquina_mmc="PRISMO",
            itens_medicao=[],
            source_kind="calypso",
        ),
        source_kind="calypso",
        template_id="default",
    )
    doc2 = ReportDocument(
        source_pdf_path=tmp_path / "p2.pdf",
        client_project="Cargill",
        evaluated_component="p2",
        control_info=TechnicalControlInfo(measured_by="Master", reviewed_by="Supervisor"),
        raw_parsed_data=SimpleNamespace(
            componente="p2",
            operador="Master",
            maquina_mmc="PRISMO",
            itens_medicao=[],
            source_kind="calypso",
        ),
        source_kind="calypso",
        template_id="default",
    )
    session = ProjectSession(
        client_project="Cargill",
        template_id="default",
        report_mode="mixed",
        documents=[
            ProjectDocumentSlot(tmp_path / "p1.pdf", "p1", document=doc1, source_kind="calypso"),
            ProjectDocumentSlot(tmp_path / "p2.pdf", "p2", document=doc2, source_kind="calypso"),
        ],
        unified_images=[
            ReportImage(
                image_path=img,
                section_id="tomografia",
                image_id="u1",
                bosello_import=True,
            )
        ],
        unified_images_ready=True,
    )
    assert resolve_unified_export_kind(session) == UnifiedExportKind.MIXED_MMC_BOSSELLO
    mixed = build_mixed_mmc_bosello_document(session)
    assert mixed.template_id == "mixed"
    assert any(i.section_id == "tomografia" for i in mixed.images)


def test_smoke_falha_sections_render(tmp_path: Path) -> None:
    document = build_manual_falha_document("Peça", client_project="Cliente Teste")
    out = tmp_path / "falha_smoke.pdf"
    ReportGenerator.gerar_relatorio_enriquecido(
        dados_parseados=document.raw_parsed_data,
        caminho_saida=str(out),
        cliente_projeto=document.client_project,
        componente_avaliado=document.evaluated_component,
        template_config=list(falha_blocks()),
        opcoes_extras={"report_kind": "falha"},
        section_prose={},
    )
    assert out.exists() and out.stat().st_size > 500
    assert FALHA_TEMPLATE_ID == "analise_falha"
    for section_id in ("inspecao_optica", "resultados_superficies", "discussao_falha"):
        assert section_id in ReportGenerator.REGISTRY_SECOES
