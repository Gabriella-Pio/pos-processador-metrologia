"""Conversão de linhas da tabela de medições para o editor em cards."""
from __future__ import annotations

from src.ui.features.workspace.components.medicoes_table_editor import (
    _from_editor_rows,
    _to_editor_rows,
)


def test_medicao_rows_roundtrip() -> None:
    rows = [
        {
            "caracteristica": "DIÂMETRO",
            "tipo": "Dimensão",
            "valor_medido": "10,01",
            "nominal": "10,00",
            "tol_superior": "0,05",
            "tol_inferior": "0,05",
            "desvio": "0,01",
            "status": "Dentro",
        }
    ]
    editor = _to_editor_rows(rows)
    assert editor[0]["label"] == "DIÂMETRO"
    assert editor[0]["valor_medido"] == "10,01"
    assert _from_editor_rows(editor) == rows
