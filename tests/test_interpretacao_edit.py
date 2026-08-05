"""Testes dos textos editáveis de Interpretação."""
from __future__ import annotations

from types import SimpleNamespace

from src.core.application.interpretacao_edit import build_interpretacao_editor_fields
from src.core.parser.table_extractor import MedicaoItemDto


def test_tomo_fills_qualitative_bullets() -> None:
    fields = build_interpretacao_editor_fields(None, report_kind="tomografia")
    assert "intro" in fields
    assert fields["bullet_1"]
    assert fields["bullet_2"]
    assert "trincas" in fields["bullet_1"].lower()


def test_mmc_fills_bullets_from_fora_items() -> None:
    dto = SimpleNamespace(
        componente="Peça X",
        itens_medicao=[
            MedicaoItemDto("DIM A", "X", "10.5", "10", "0.1", "0.1", "0.5", "Fora"),
            MedicaoItemDto("DIM B", "Y", "5.0", "5", "0.1", "0.1", "0.0", "Dentro"),
        ],
    )
    fields = build_interpretacao_editor_fields(dto, report_kind="mmc")
    assert "2 características" in fields["intro"]
    assert "DIM A" in fields["bullet_1"]
    assert "fora" in fields["bullet_1"].lower()


def test_respects_existing_bullet_overrides() -> None:
    dto = SimpleNamespace(componente="P", itens_medicao=[])
    fields = build_interpretacao_editor_fields(
        dto,
        report_kind="mmc",
        existing={"bullet_1": "Texto customizado do usuário"},
    )
    assert fields["bullet_1"] == "Texto customizado do usuário"
