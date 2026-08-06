"""Testes de merge e resolução de linhas de tabela."""
from __future__ import annotations

from src.core.domain.table_row_merge import (
    apply_legacy_introducao_overrides,
    merge_table_rows,
    merge_with_defaults,
    resolve_introducao_table_rows,
)
from src.core.domain.table_row_specs import default_table_rows


def test_merge_with_defaults_preserves_stored_order() -> None:
    defaults = [
        {"id": "a", "label": "A", "value": "1"},
        {"id": "b", "label": "B", "value": "2"},
    ]
    stored = [{"id": "b", "label": "B custom", "value": "22"}]
    merged = merge_with_defaults(defaults, stored)
    assert [row["id"] for row in merged] == ["b", "a"]
    assert merged[0]["label"] == "B custom"
    assert merged[0]["value"] == "22"
    assert merged[1]["id"] == "a"
    assert merged[1]["value"] == "1"


def test_merge_with_defaults_append_missing_false() -> None:
    defaults = default_table_rows("introducao")
    stored = [{"id": "amostra", "label": "Amostra X", "value": "2 peças"}]
    merged = merge_with_defaults(defaults, stored, append_missing=False)
    assert len(merged) == 1
    assert merged[0]["label"] == "Amostra X"


def test_apply_legacy_introducao_overrides_updates_labels_and_values() -> None:
    rows = default_table_rows("introducao")
    overrides = {
        "title_amostra": "AMOSTRA TESTE",
        "valor_amostra": "3 peças",
    }
    result = apply_legacy_introducao_overrides(rows, overrides)
    amostra = next(row for row in result if row["id"] == "amostra")
    assert amostra["label"] == "AMOSTRA TESTE"
    assert amostra["value"] == "3 peças"


def test_resolve_introducao_table_rows_uses_legacy_when_no_stored() -> None:
    rows = resolve_introducao_table_rows({"valor_amostra": "5 peças"})
    amostra = next(row for row in rows if row["id"] == "amostra")
    assert amostra["value"] == "5 peças"


def test_resolve_introducao_table_rows_strips_prose_rows_from_stored() -> None:
    stored = [
        {"id": "objetivo", "label": "Objetivo", "value": "texto"},
        {"id": "amostra", "label": "Amostra", "value": "1"},
    ]
    rows = resolve_introducao_table_rows({"table_rows": stored})
    assert all(row["id"] != "objetivo" for row in rows)
    assert any(row["id"] == "amostra" for row in rows)


def test_merge_table_rows_returns_defaults_when_empty() -> None:
    defaults = merge_table_rows("identificacao", None)
    assert defaults == default_table_rows("identificacao")
    assert defaults[0]["id"] == "client_project"
