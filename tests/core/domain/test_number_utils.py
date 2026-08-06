"""Testes de conversão numérica."""
from src.core.domain.number_utils import to_float
from src.core.parser.utils import ParserUtils


def test_to_float_handles_comma_and_units() -> None:
    assert to_float("0,0040 inch") == 0.004
    assert to_float("-0,0008") == -0.0008


def test_to_float_handles_na_and_empty() -> None:
    assert to_float("N/A") == 0.0
    assert to_float("") == 0.0
    assert to_float("-") == 0.0


def test_parser_utils_delegates_to_number_utils() -> None:
    assert ParserUtils.converter_para_float("1,25 mm") == 1.25
