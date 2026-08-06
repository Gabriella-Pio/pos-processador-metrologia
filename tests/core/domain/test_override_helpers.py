"""Testes de merge e detecção de overrides de prosa."""
from __future__ import annotations

from src.core.domain.override_helpers import (
    default_prose_values,
    is_field_overridden,
    merge_section_prose,
    section_has_overrides,
)
from src.core.domain.prose_templates import PROSE_TEMPLATES


def test_default_prose_values_returns_section_templates() -> None:
    values = default_prose_values("introducao")
    assert values["objetivo"] == PROSE_TEMPLATES["introducao"]["objetivo"]
    assert "{componente}" in values["objetivo"]


def test_merge_section_prose_ignores_metadata_keys() -> None:
    overrides = {
        "objetivo": "Texto customizado",
        "title_objetivo": "OBJETIVO",
        "section_title": "Intro",
        "table_rows": [],
        "media_kinds": ["photo"],
    }
    merged = merge_section_prose("introducao", overrides)
    assert merged["objetivo"] == "Texto customizado"
    assert "title_objetivo" not in merged
    assert "section_title" not in merged


def test_is_field_overridden_detects_changed_value() -> None:
    overrides = {"introducao": {"objetivo": "Alterado"}}
    assert is_field_overridden("introducao", "objetivo", overrides) is True
    assert is_field_overridden("introducao", "escopo", overrides) is False


def test_section_has_overrides_with_table_rows() -> None:
    overrides = {"introducao": {"table_rows": [{"id": "a", "label": "A", "value": ""}]}}
    assert section_has_overrides("introducao", overrides) is True


def test_section_has_overrides_with_intro_title_key() -> None:
    overrides = {"introducao": {"title_objetivo": "OBJETIVO CUSTOM"}}
    assert section_has_overrides("introducao", overrides) is True
