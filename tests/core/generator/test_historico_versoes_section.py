"""Testes da seção Histórico de Versões no PDF."""
from __future__ import annotations

from datetime import datetime

from reportlab.platypus import Paragraph, Spacer, Table

from src.core.generator.sections.historico_versoes_section import HistoricoVersoesSection
from src.core.generator.styles import ReportStyles


def test_historico_section_renders_intro_and_version_table() -> None:
    section = HistoricoVersoesSection()
    story: list = []
    styles = ReportStyles.criar_estilos()
    section.render(
        story,
        styles,
        None,
        {
            "section_prose": {
                "historico_versoes": {
                    "intro": "Registro das versões emitidas deste relatório.",
                }
            },
            "section_anchor_map": {},
            "section_number_map": {"historico_versoes": "3"},
            "historico_versoes": [
                {
                    "version_number": 1,
                    "timestamp_str": "01/08/2026 14:30",
                    "responsible_name": "Ana Silva",
                    "description": "Versão inicial",
                }
            ],
        },
    )
    assert any(isinstance(item, Paragraph) for item in story)
    assert any(isinstance(item, Table) for item in story)
    assert any(isinstance(item, Spacer) for item in story)


def test_historico_section_renders_intro_when_no_versions() -> None:
    section = HistoricoVersoesSection()
    story: list = []
    styles = ReportStyles.criar_estilos()
    section.render(
        story,
        styles,
        None,
        {
            "section_prose": {
                "historico_versoes": {
                    "intro": "Texto introdutório do histórico.",
                }
            },
            "section_anchor_map": {},
            "section_number_map": {"historico_versoes": "3"},
            "historico_versoes": [],
        },
    )
    paragraphs = [item for item in story if isinstance(item, Paragraph)]
    assert len(paragraphs) >= 2
    intro_paragraphs = [p for p in paragraphs if "Texto introdutório do histórico." in p.text]
    assert intro_paragraphs
