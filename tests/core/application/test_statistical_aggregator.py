"""Testes do agregador estatístico multi-peça."""
from __future__ import annotations

from src.core.application.statistical_aggregator import (
    aggregate_measurement_series,
    build_statistical_batch_dto,
    classify_characteristic_tipo,
    display_characteristic_name,
    format_stat_number,
    normalize_characteristic_key,
    parse_measure_number,
)
from src.core.parser.table_extractor import MedicaoItemDto


def test_normalize_and_display_characteristic_names() -> None:
    assert normalize_characteristic_key("Diametro_ASSENTO ENTRADA") == "diametro assento entrada"
    assert normalize_characteristic_key("Cilindricidade ENCAIXE SUPERIOR") == (
        "cilindricidade encaixe superior"
    )
    assert display_characteristic_name("Diametro_ASSENTO ENTRADA").startswith("Diâmetro")
    assert classify_characteristic_tipo("Diametro_EMBOLO") == "diametro"
    assert classify_characteristic_tipo("Cilindricidade ASSENTO") == "cilindricidade"
    assert classify_characteristic_tipo("altura bico") == "altura"
    assert classify_characteristic_tipo("Altura_BICO", "GEOMETRIA GERAL") == "altura"


def test_parse_measure_number() -> None:
    assert parse_measure_number("81,9972 mm") == 81.9972
    assert parse_measure_number("0.0511") == 0.0511
    assert parse_measure_number("") is None


def test_aggregate_aligns_characteristics_across_pieces() -> None:
    piece_items = [
        (
            1,
            [
                MedicaoItemDto(
                    "Diametro_ASSENTO ENTRADA",
                    "Diâmetro",
                    "81,9972",
                    "81,9696",
                    "0,1500",
                    "0,1500",
                    "-0,0276",
                    "Dentro",
                ),
                MedicaoItemDto(
                    "Cilindricidade EMBOLO",
                    "Cilindricidade",
                    "0,0511",
                    "0,0000",
                    "0,0256",
                    "0,0000",
                    "0,0511",
                    "Fora",
                ),
            ],
        ),
        (
            2,
            [
                MedicaoItemDto(
                    "Diametro ASSENTO ENTRADA",
                    "Diâmetro",
                    "81,9800",
                    "81,9696",
                    "0,1500",
                    "0,1500",
                    "-0,0104",
                    "Dentro",
                ),
                MedicaoItemDto(
                    "Cilindricidade_EMBOLO",
                    "Cilindricidade",
                    "0,0400",
                    "0,0000",
                    "0,0256",
                    "0,0000",
                    "0,0400",
                    "Fora",
                ),
            ],
        ),
    ]
    series = aggregate_measurement_series(piece_items, piece_labels=["A", "B"])
    assert len(series) == 2
    diam = next(s for s in series if s.tipo == "diametro")
    cyl = next(s for s in series if s.tipo == "cilindricidade")
    assert diam.n == 2
    assert diam.fora_count == 0
    assert cyl.fora_count == 2
    assert diam.mean is not None
    assert format_stat_number(diam.mean).count(",") == 1


def test_build_statistical_batch_dto() -> None:
    items = [
        MedicaoItemDto("Diametro_X", "Diâmetro", "10,0", "10,0", "0,1", "0,1", "0", "Dentro"),
    ]
    batch = build_statistical_batch_dto(
        componente="Peça",
        cliente="Cliente",
        piece_labels=["1", "2"],
        piece_items=[(1, items), (2, items)],
    )
    assert batch.numero_medicoes_cabecalho == 2
    assert len(batch.series) == 1


def test_aggregate_altura_bico_series() -> None:
    piece_items = [
        (
            1,
            [
                MedicaoItemDto(
                    "altura bico",
                    "GEOMETRIA GERAL",
                    "89,8045 mm",
                    "90,0000",
                    "0,2000",
                    "0,2000",
                    "-0,1955",
                    "Dentro",
                ),
            ],
        ),
        (
            2,
            [
                MedicaoItemDto(
                    "altura bico",
                    "GEOMETRIA GERAL",
                    "89,8100 mm",
                    "90,0000",
                    "0,2000",
                    "0,2000",
                    "-0,1900",
                    "Dentro",
                ),
            ],
        ),
    ]
    series = aggregate_measurement_series(piece_items, piece_labels=["13", "14"])
    assert len(series) == 1
    assert series[0].tipo == "altura"
    assert series[0].n == 2
    assert series[0].unit == "mm"

    from src.core.application.statistical_aggregator import (
        build_estatistico_sections_config,
        present_measure_tipos,
        statistical_escopo_phrase,
    )

    tipos = present_measure_tipos(series)
    assert tipos == ["altura"]
    layout = build_estatistico_sections_config(tipos)
    assert layout["estat_resumo_alturas"]["enabled"] is True
    assert layout["estat_detalhe_alturas"]["enabled"] is True
    assert layout["estat_resumo_diametros"]["enabled"] is False
    assert layout["estat_resumo_cilindricidades"]["enabled"] is False
    assert "alturas" in statistical_escopo_phrase(tipos)

    from src.core.application.statistical_aggregator import (
        build_estatistico_introducao_metric_rows,
        build_statistical_batch_dto,
    )

    batch = build_statistical_batch_dto(
        componente="BICO",
        cliente="Cliente",
        piece_labels=["13", "14"],
        piece_items=piece_items,
    )
    metrics = build_estatistico_introducao_metric_rows(batch)
    ids = [row["id"] for row in metrics]
    assert ids == ["amostra", "valores", "fora", "pecas_ocorrencia", "fora_altura"]
    assert metrics[-1]["label"] == "ALTURAS FORA"
    assert metrics[-1]["value"] == "0/2"
    assert not any(row["id"] == "fora_diametro" for row in metrics)


def test_estatistico_type_footer_note_with_zero_tol() -> None:
    from src.core.application.statistical_aggregator import (
        StatisticalCharacteristicSeries,
        build_estatistico_section_notes,
        build_estatistico_type_footer_note,
        build_statistical_batch_dto,
    )

    series = StatisticalCharacteristicSeries(
        key="cilindricidade embolo",
        display_name="Cilindricidade EMBOLO",
        tipo="cilindricidade",
        nominal="0,0000",
        tol_superior="0,0000",
        tol_inferior="0,0000",
        unit="mm",
        values=[(1, 0.05, "Fora"), (2, 0.04, "Fora")],
    )
    note = build_estatistico_type_footer_note([series], "cilindricidade")
    assert "Resumo das cilindricidades (Embolo)" in note
    assert "2 ocorrências" in note
    assert "2 valores geométricos" in note
    assert "0,0000 mm" in note
    assert "próprio relatório da MMC" in note

    batch = build_statistical_batch_dto(
        componente="Peça",
        cliente="Cliente",
        piece_labels=["1", "2"],
        piece_items=[
            (
                1,
                [
                    MedicaoItemDto(
                        "Cilindricidade EMBOLO",
                        "Cilindricidade",
                        "0,05",
                        "0,0000",
                        "0,0000",
                        "0,0000",
                        "0,05",
                        "Fora",
                    )
                ],
            ),
            (
                2,
                [
                    MedicaoItemDto(
                        "Cilindricidade EMBOLO",
                        "Cilindricidade",
                        "0,04",
                        "0,0000",
                        "0,0000",
                        "0,0000",
                        "0,04",
                        "Fora",
                    )
                ],
            ),
        ],
    )
    notes = build_estatistico_section_notes(batch)
    assert "estat_resumo_cilindricidades" in notes
    assert "estat_detalhe_cilindricidades" in notes
    assert notes["estat_resumo_cilindricidades"] == notes["estat_detalhe_cilindricidades"]


def test_estatistico_type_footer_note_empty_when_no_fora() -> None:
    from src.core.application.statistical_aggregator import (
        StatisticalCharacteristicSeries,
        build_estatistico_type_footer_note,
    )

    series = StatisticalCharacteristicSeries(
        key="diametro x",
        display_name="Diâmetro X",
        tipo="diametro",
        nominal="10",
        tol_superior="0,1",
        tol_inferior="0,1",
        unit="mm",
        values=[(1, 10.0, "Dentro"), (2, 10.05, "Dentro")],
    )
    assert build_estatistico_type_footer_note([series], "diametro") == ""
