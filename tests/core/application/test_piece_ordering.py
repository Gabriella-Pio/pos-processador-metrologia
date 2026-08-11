"""Testes de ordenação natural de peças em lote."""
from __future__ import annotations

from pathlib import Path

from src.core.application.piece_ordering import (
    extract_piece_number_from_name,
    natural_pdf_sort_key,
    sort_pdf_entries,
    sort_session_documents,
)
from src.core.application.statistical_aggregator import (
    aggregate_measurement_series,
    normalize_characteristic_key,
)
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.parser.table_extractor import MedicaoItemDto


def test_extract_piece_number_from_filename() -> None:
    assert extract_piece_number_from_name("CARCACA DE BOMBA 8.pdf") == 8
    assert extract_piece_number_from_name("peca_16.pdf") == 16
    assert extract_piece_number_from_name("relatorio.pdf") is None


def test_sort_pdf_entries_natural_order() -> None:
    entries = [
        (Path("/tmp/CARCACA DE BOMBA 16.pdf"), "X"),
        (Path("/tmp/CARCACA DE BOMBA 2.pdf"), "X"),
        (Path("/tmp/CARCACA DE BOMBA 10.pdf"), "X"),
        (Path("/tmp/CARCACA DE BOMBA 1.pdf"), "X"),
    ]
    sorted_entries = sort_pdf_entries(entries)
    assert [p.name for p, _ in sorted_entries] == [
        "CARCACA DE BOMBA 1.pdf",
        "CARCACA DE BOMBA 2.pdf",
        "CARCACA DE BOMBA 10.pdf",
        "CARCACA DE BOMBA 16.pdf",
    ]
    assert natural_pdf_sort_key(Path("a 10.pdf")) < natural_pdf_sort_key(Path("a 16.pdf"))


def test_sort_session_documents_preserves_active() -> None:
    session = ProjectSession(
        client_project="C",
        documents=[
            ProjectDocumentSlot(Path("/tmp/p3.pdf"), "c"),
            ProjectDocumentSlot(Path("/tmp/p1.pdf"), "c"),
            ProjectDocumentSlot(Path("/tmp/p2.pdf"), "c"),
        ],
        active_index=0,
    )
    assert sort_session_documents(session) is True
    assert [s.source_pdf_path.name for s in session.documents] == ["p1.pdf", "p2.pdf", "p3.pdf"]
    assert session.active_index == 2  # p3 was active


def test_normalize_merges_trab_abbreviation() -> None:
    assert normalize_characteristic_key("Diametro_AREA NAO TRAB") == normalize_characteristic_key(
        "Diametro AREA NAO TRABALHO"
    )


def test_area_trabalho_not_merged_with_nao_trabalho() -> None:
    """Regressão: merge agressivo sumia o diâmetro da área de trabalho (192→176)."""
    piece_items = [
        (
            1,
            [
                MedicaoItemDto(
                    "Diametro_AREA TRABALHO",
                    "Diâmetro",
                    "75,9838 mm",
                    "75,0",
                    "0,1",
                    "0,1",
                    "0",
                    "Dentro",
                ),
                MedicaoItemDto(
                    "Diametro_AREA NAO TRABALHO",
                    "Diâmetro",
                    "76,1000 mm",
                    "76,0",
                    "0,1",
                    "0,1",
                    "0",
                    "Dentro",
                ),
            ],
        ),
        (
            2,
            [
                MedicaoItemDto(
                    "Diametro AREA TRABALHO",
                    "Diâmetro",
                    "75,9874 mm",
                    "75,0",
                    "0,1",
                    "0,1",
                    "0",
                    "Dentro",
                ),
                MedicaoItemDto(
                    "Diametro AREA NAO TRAB",
                    "Diâmetro",
                    "76,1100 mm",
                    "76,0",
                    "0,1",
                    "0,1",
                    "0",
                    "Dentro",
                ),
            ],
        ),
    ]
    series = aggregate_measurement_series(piece_items, piece_labels=["1", "2"])
    assert len(series) == 2
    assert sum(s.n for s in series) == 4
    assert all(s.unit == "mm" for s in series)


def test_aggregate_aligns_trab_abbreviation_same_characteristic() -> None:
    piece_items = [
        (
            1,
            [
                MedicaoItemDto(
                    "Diametro_AREA NAO TRAB",
                    "Diâmetro",
                    "75,1 mm",
                    "75,0",
                    "0,1",
                    "0,1",
                    "0",
                    "Dentro",
                )
            ],
        ),
        (
            2,
            [
                MedicaoItemDto(
                    "Diametro AREA NAO TRABALHO",
                    "Diâmetro",
                    "75,2 mm",
                    "75,0",
                    "0,1",
                    "0,1",
                    "0",
                    "Dentro",
                )
            ],
        ),
    ]
    series = aggregate_measurement_series(piece_items, piece_labels=["1", "2"])
    assert len(series) == 1
    assert series[0].n == 2
    assert series[0].unit == "mm"


def test_short_characteristic_label_strips_measure_word() -> None:
    from src.core.application.statistical_aggregator import short_characteristic_label

    assert short_characteristic_label("Cilindricidade area de trabalho") == "area de trabalho"
    assert short_characteristic_label("Diâmetro embolo") == "embolo"


def test_infer_measure_unit_from_raw() -> None:
    from src.core.application.statistical_aggregator import infer_measure_unit

    assert infer_measure_unit("0,0215 mm") == "mm"
    assert infer_measure_unit("1.234 inch") == "inch"
    assert infer_measure_unit("0,0215") == ""


def test_format_series_limits_range_absolute() -> None:
    from src.core.application.statistical_aggregator import (
        StatisticalCharacteristicSeries,
        format_series_limits_range,
    )

    series = StatisticalCharacteristicSeries(
        key="diametro assento entrada",
        display_name="Diâmetro assento entrada",
        tipo="diametro",
        nominal="81,9972 mm",
        tol_superior="0,15",
        tol_inferior="0,15",
        unit="mm",
    )
    assert format_series_limits_range(series) == "81,8472 mm a 82,1472 mm"
