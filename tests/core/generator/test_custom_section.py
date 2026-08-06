"""Testes do renderer de seção personalizada."""
from __future__ import annotations

from src.core.generator.sections.custom_section import CustomSection
from src.core.generator.styles import ReportStyles


def test_custom_section_renders_body_and_footer_note() -> None:
    section = CustomSection({"section_id": "custom_1"})
    story: list = []
    styles = ReportStyles.criar_estilos()
    section.render(
        story,
        styles,
        None,
        {
            "section_prose": {
                "custom_1": {
                    "title": "Teste",
                    "body": "Conteúdo da seção",
                    "nota": "Nota de rodapé",
                }
            },
            "section_anchor_map": {},
            "table_rows": {},
            "placeholder_context": {},
        },
    )
    assert len(story) >= 3
