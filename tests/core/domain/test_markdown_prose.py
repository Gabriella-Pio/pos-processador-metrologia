"""Testes de conversão markdown → ReportLab HTML."""
from src.core.domain.markdown_prose import markdown_to_reportlab_html


def test_plain_text_escapes_html() -> None:
    assert markdown_to_reportlab_html("a < b & c") == "a &lt; b &amp; c"


def test_bold_and_italic() -> None:
    assert markdown_to_reportlab_html("**negrito** e *itálico*") == (
        "<b>negrito</b> e <i>itálico</i>"
    )


def test_mixed_bold_and_italic_segments() -> None:
    assert markdown_to_reportlab_html("**negrito** depois *itálico*") == (
        "<b>negrito</b> depois <i>itálico</i>"
    )

def test_bullet_lines_and_line_breaks() -> None:
    assert markdown_to_reportlab_html("- um\n- dois") == "• um<br/>• dois"


def test_preserves_placeholders() -> None:
    assert markdown_to_reportlab_html("**{componente}** medido") == (
        "<b>{componente}</b> medido"
    )


def test_numbered_lines_and_line_breaks() -> None:
    assert markdown_to_reportlab_html("1. primeiro\n2. segundo") == (
        "1. primeiro<br/>2. segundo"
    )


def test_strip_markdown_formatting() -> None:
    from src.core.domain.markdown_prose import strip_markdown_formatting

    assert strip_markdown_formatting("**negrito** e *itálico*") == "negrito e itálico"
    assert strip_markdown_formatting("- item\n2. outro") == "item\noutro"
    assert strip_markdown_formatting("**{componente}**") == "{componente}"


def test_resolve_list_enter_continues_bullet() -> None:
    from src.core.domain.markdown_prose import resolve_list_enter

    action = resolve_list_enter("- item")
    assert action.kind == "continue"
    assert action.insert_text == "\n- "


def test_resolve_list_enter_exits_empty_bullet() -> None:
    from src.core.domain.markdown_prose import resolve_list_enter

    action = resolve_list_enter("- ")
    assert action.kind == "exit"
    assert action.prefix_length == 2


def test_resolve_list_enter_continues_numbered() -> None:
    from src.core.domain.markdown_prose import resolve_list_enter

    action = resolve_list_enter("2. segundo")
    assert action.kind == "continue"
    assert action.insert_text == "\n3. "


def test_resolve_list_enter_exits_empty_numbered() -> None:
    from src.core.domain.markdown_prose import resolve_list_enter

    action = resolve_list_enter("3. ")
    assert action.kind == "exit"
    assert action.prefix_length == 3


def test_resolve_list_enter_default_for_plain_line() -> None:
    from src.core.domain.markdown_prose import resolve_list_enter

    assert resolve_list_enter("texto normal").kind == "default"


def test_empty_string() -> None:
    assert markdown_to_reportlab_html("") == ""


def test_zalgo_does_not_keep_stacked_marks() -> None:
    marks = "".join(chr(0x0300 + (index % 16)) for index in range(80))
    html = markdown_to_reportlab_html("a" + marks)
    combining = sum(1 for char in html if "\u0300" <= char <= "\u036f")
    assert combining <= 2
    assert html[:1].isalpha()

