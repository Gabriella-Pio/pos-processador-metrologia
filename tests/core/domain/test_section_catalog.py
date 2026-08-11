"""Testes anti-drift do catálogo canônico de seções."""
from __future__ import annotations

from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.section_catalog import (
    SECTION_CATALOG,
    TEMPLATE_PROFILE_TOMOGRAFIA,
    catalog_by_id,
    default_enabled_blocks,
    section_heading_defaults,
    tomography_blocks,
)
from src.core.domain.section_schema import (
    SECTION_DEFINITIONS,
    SECTION_TITLES,
    TEMPLATE_PADRAO_OFICIAL,
    TEMPLATE_TOMOGRAFIA_OFICIAL,
    TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG,
)
from src.core.domain.table_row_registry import NUMBERED_SECTION_IDS, SECTION_HEADING_DEFAULTS
from src.core.generator.engine import ReportGenerator


def test_catalog_covers_all_section_definitions() -> None:
    catalog_ids = {meta.id for meta in SECTION_CATALOG}
    for section in SECTION_DEFINITIONS:
        assert section.id in catalog_ids


def test_section_titles_match_catalog() -> None:
    by_id = catalog_by_id()
    for section_id, title in SECTION_TITLES.items():
        assert by_id[section_id].label == title


def test_section_heading_defaults_match_catalog() -> None:
    assert SECTION_HEADING_DEFAULTS == section_heading_defaults()


def test_numbered_section_ids_match_catalog() -> None:
    expected = {meta.id for meta in SECTION_CATALOG if meta.numbered}
    assert NUMBERED_SECTION_IDS == frozenset(expected)


def test_registry_keys_exist_in_catalog() -> None:
    catalog_ids = {meta.registry_key for meta in SECTION_CATALOG}
    for section_id in ReportGenerator.REGISTRY_SECOES:
        assert section_id in catalog_ids


def test_prose_templates_keys_are_catalog_sections() -> None:
    catalog_ids = {meta.id for meta in SECTION_CATALOG}
    for section_id in PROSE_TEMPLATES:
        assert section_id in catalog_ids


def test_tomography_profile_only_references_catalog() -> None:
    catalog_ids = {meta.id for meta in SECTION_CATALOG}
    for section_id in TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG:
        assert section_id in catalog_ids
    assert TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG == TEMPLATE_PROFILE_TOMOGRAFIA


def test_mmc_default_blocks_snapshot() -> None:
    expected_types = [
        "cabecalho",
        "introducao",
        "identificacao",
        "controle_tecnico",
        "resultados",
        "grafica",
        "interpretacao",
        "conclusao",
        "historico_versoes",
        "anexos",
    ]
    blocks = default_enabled_blocks()
    assert [b["tipo"] for b in blocks] == expected_types
    assert TEMPLATE_PADRAO_OFICIAL == blocks


def test_tomography_blocks_snapshot() -> None:
    expected_types = [
        "cabecalho",
        "introducao",
        "identificacao",
        "metodo_escopo",
        "registro_componente",
        "tomografia",
        "resultados_inspecao",
        "interpretacao",
        "conclusao",
        "observacoes_limitacoes",
        "controle_tecnico",
        "historico_versoes",
        "anexos",
    ]
    blocks = tomography_blocks()
    assert [b["tipo"] for b in blocks] == expected_types
    assert TEMPLATE_TOMOGRAFIA_OFICIAL == blocks
    intro = next(b for b in blocks if b["tipo"] == "introducao")
    assert intro["config"].get("variant") == "tomografia"


def test_catalog_has_unique_ids() -> None:
    ids = [meta.id for meta in SECTION_CATALOG]
    assert len(ids) == len(set(ids))


def test_fixed_and_protected_section_ids() -> None:
    from src.core.domain.section_catalog import fixed_section_ids, protected_section_ids

    assert protected_section_ids() == frozenset({"cabecalho", "introducao"})
    assert fixed_section_ids() == frozenset({"cabecalho", "introducao", "anexos"})

    intro = catalog_by_id()["introducao"]
    historico = catalog_by_id()["historico_versoes"]
    anexos = catalog_by_id()["anexos"]
    assert intro.fixed_position == "start"
    assert historico.fixed_position == "none"
    assert anexos.fixed_position == "end"
