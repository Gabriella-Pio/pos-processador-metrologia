"""Conversão de markdown leve (editor) para HTML inline do ReportLab."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from typing import Literal

from src.core.domain.pdf_plain_text import limit_combining_marks

_PLACEHOLDER_PATTERN = re.compile(r"\{[^{}]+\}")
_NUMBERED_LINE = re.compile(r"^(\d+)\. (.*)$")


@dataclass(frozen=True)
class ListEnterAction:
    kind: Literal["default", "continue", "exit"]
    insert_text: str = ""
    prefix_length: int = 0


def resolve_list_enter(line_text: str) -> ListEnterAction:
    """Define o comportamento do Enter em linhas de lista markdown."""
    if line_text.startswith("- "):
        if not line_text[2:].strip():
            return ListEnterAction("exit", prefix_length=2)
        return ListEnterAction("continue", insert_text="\n- ")

    numbered = _NUMBERED_LINE.match(line_text)
    if numbered is not None:
        prefix = f"{numbered.group(1)}. "
        if not numbered.group(2).strip():
            return ListEnterAction("exit", prefix_length=len(prefix))
        next_number = int(numbered.group(1)) + 1
        return ListEnterAction("continue", insert_text=f"\n{next_number}. ")

    return ListEnterAction("default")


def markdown_to_reportlab_html(text: str) -> str:
    """Converte subset de markdown para tags aceitas pelo ``Paragraph`` do ReportLab.

    Suporta ``**negrito**``, ``*itálico*``, linhas ``- item`` (bullet), ``1. item`` (numerada)
    e quebras de linha. Placeholders ``{chave}`` são preservados literalmente.
    Texto sem marcadores passa inalterado (apenas com escape de ``<>&``).
    """
    if not text:
        return ""

    normalized = limit_combining_marks(text).replace("\r\n", "\n").replace("\r", "\n")
    placeholders: list[str] = []

    def _stash_placeholder(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"\x00PH{len(placeholders) - 1}\x00"

    protected = _PLACEHOLDER_PATTERN.sub(_stash_placeholder, normalized)
    html_lines: list[str] = []
    for line in protected.split("\n"):
        numbered = _NUMBERED_LINE.match(line)
        if line.startswith("- "):
            converted = _inline_markdown(line[2:])
            html_lines.append(f"• {converted}")
        elif numbered:
            number, content = numbered.group(1), numbered.group(2)
            html_lines.append(f"{number}. {_inline_markdown(content)}")
        else:
            html_lines.append(_inline_markdown(line))

    result = "<br/>".join(html_lines)
    for index, placeholder in enumerate(placeholders):
        token = f"\x00PH{index}\x00"
        result = result.replace(token, html.escape(placeholder, quote=False))
    return result


def _inline_markdown(text: str) -> str:
    parts: list[str] = []
    position = 0
    while position < len(text):
        bold_start = text.find("**", position)
        if bold_start == -1:
            parts.append(_italic_markdown(text[position:]))
            break
        parts.append(_italic_markdown(text[position:bold_start]))
        bold_end = text.find("**", bold_start + 2)
        if bold_end == -1:
            parts.append(html.escape(text[bold_start:], quote=False))
            break
        inner = text[bold_start + 2:bold_end]
        parts.append(f"<b>{_inline_markdown(inner)}</b>")
        position = bold_end + 2
    return "".join(parts)


def _italic_markdown(text: str) -> str:
    parts: list[str] = []
    position = 0
    while position < len(text):
        italic_start = text.find("*", position)
        if italic_start == -1:
            parts.append(html.escape(text[position:], quote=False))
            break
        parts.append(html.escape(text[position:italic_start], quote=False))
        italic_end = text.find("*", italic_start + 1)
        if italic_end == -1:
            parts.append(html.escape(text[italic_start:], quote=False))
            break
        inner = text[italic_start + 1:italic_end]
        parts.append(f"<i>{html.escape(inner, quote=False)}</i>")
        position = italic_end + 1
    return "".join(parts)


def strip_markdown_formatting(text: str) -> str:
    """Remove marcadores markdown leves da seleção, preservando placeholders."""
    if not text:
        return ""

    placeholders: list[str] = []

    def _stash_placeholder(match: re.Match[str]) -> str:
        placeholders.append(match.group(0))
        return f"\x00PH{len(placeholders) - 1}\x00"

    protected = _PLACEHOLDER_PATTERN.sub(_stash_placeholder, text)
    lines: list[str] = []
    for line in protected.split("\n"):
        stripped_line = re.sub(r"^- ", "", line)
        stripped_line = re.sub(r"^\d+\. ", "", stripped_line)
        lines.append(_strip_inline_markdown(stripped_line))

    result = "\n".join(lines)
    for index, placeholder in enumerate(placeholders):
        result = result.replace(f"\x00PH{index}\x00", placeholder)
    return result


def _strip_inline_markdown(text: str) -> str:
    current = text
    while True:
        updated = re.sub(r"\*\*(.+?)\*\*", r"\1", current)
        updated = re.sub(r"\*(.+?)\*", r"\1", updated)
        if updated == current:
            return current
        current = updated
