"""Testes das regras de ordenação do sumário."""
from __future__ import annotations

from src.ui.shared.report_editor.section_order_rules import (
    is_sidebar_section_draggable,
    validate_sidebar_order,
)


def test_fixed_sections_are_not_draggable() -> None:
    assert not is_sidebar_section_draggable("historico_versoes")
    assert not is_sidebar_section_draggable("anexos")
    assert is_sidebar_section_draggable("grafica")


def test_validate_sidebar_order_rejects_sections_after_anexos() -> None:
    valid, message = validate_sidebar_order(
        ["introducao", "anexos", "grafica"]
    )
    assert not valid
    assert "Anexos" in message
