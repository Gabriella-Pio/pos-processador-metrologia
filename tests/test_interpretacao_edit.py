"""Testes dos textos editáveis de Interpretação."""
from __future__ import annotations

from types import SimpleNamespace

from src.core.application.interpretacao_edit import (
    build_interpretacao_editor_fields,
    interpretacao_field_defs,
)
from src.core.parser.table_extractor import MedicaoItemDto


def _dto(*statuses: tuple[str, str]) -> SimpleNamespace:
    items = [
        MedicaoItemDto(name, "TIPO", "1", "0", "0.1", "0.1", "1", status)
        for name, status in statuses
    ]
    return SimpleNamespace(componente="Peça", itens_medicao=items)


def test_tomo_fills_qualitative_bullets() -> None:
    fields = build_interpretacao_editor_fields(None, report_kind="tomografia")
    assert fields["bullet_1"] and fields["bullet_4"]


def test_mmc_bullet_count_matches_items_automatically() -> None:
    dto = _dto(("A", "Fora"), ("B", "Dentro"), ("C", "Dentro"), ("D", "Fora"), ("E", "Dentro"))
    fields = build_interpretacao_editor_fields(dto, report_kind="mmc")
    assert "5 características" in fields["intro"]
    keys = [d.key for d in interpretacao_field_defs(fields)]
    assert keys == ["intro", "bullet_1", "bullet_2", "bullet_3", "bullet_4", "bullet_5"]
    assert "A" in fields["bullet_1"]
    assert "E" in fields["bullet_5"]


def test_scales_from_3_to_5_when_pdf_changes() -> None:
    """Troca de PDF com mais itens deve aumentar os campos automaticamente."""
    small = build_interpretacao_editor_fields(
        _dto(("A", "Fora"), ("B", "Dentro"), ("C", "Dentro")),
        report_kind="mmc",
    )
    assert len(interpretacao_field_defs(small)) == 4  # intro + 3

    larger = build_interpretacao_editor_fields(
        _dto(("A", "Fora"), ("B", "Dentro"), ("C", "Dentro"), ("D", "Fora"), ("E", "Dentro")),
        report_kind="mmc",
        existing=small,  # simula campos antigos ainda no formulário
        user_overrides={},  # documento novo sem overrides
    )
    assert len(interpretacao_field_defs(larger)) == 6  # intro + 5
    assert "D" in larger["bullet_4"]
    assert "E" in larger["bullet_5"]


def test_preserves_only_explicit_user_overrides() -> None:
    dto = _dto(("A", "Fora"), ("B", "Dentro"), ("C", "Dentro"))
    fields = build_interpretacao_editor_fields(
        dto,
        report_kind="mmc",
        user_overrides={"bullet_2": "Texto editado pelo usuário"},
    )
    assert "A" in fields["bullet_1"]
    assert fields["bullet_2"] == "Texto editado pelo usuário"
    assert "C" in fields["bullet_3"]
