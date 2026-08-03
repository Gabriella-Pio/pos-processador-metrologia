"""Carrega arquivos QSS e substitui tokens do design system."""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from src.ui.styles.tokens import PALETTE, SPACING, TYPOGRAPHY

_STYLES_DIR = Path(__file__).resolve().parent
_TOKEN_PATTERN = re.compile(r"\{(\w+)\}")


def qss_tokens(**extra: str | int) -> dict[str, str | int]:
    """Mapa plano de tokens para interpolação em templates QSS."""
    tokens: dict[str, str | int] = {}
    for source in (PALETTE, TYPOGRAPHY, SPACING):
        tokens.update(source.__dict__)
    tokens.update(extra)
    return tokens


def render_qss(template: str, **extra: str | int) -> str:
    """Substitui ``{token}`` e converte ``{{``/``}}`` em chaves QSS literais."""
    tokens = qss_tokens(**extra)

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in tokens:
            return match.group(0)
        return str(tokens[key])

    rendered = _TOKEN_PATTERN.sub(_replace, template)
    return rendered.replace("{{", "{").replace("}}", "}")


@lru_cache(maxsize=8)
def load_qss_file(filename: str) -> str:
    path = _STYLES_DIR / filename
    return path.read_text(encoding="utf-8")


def clear_style_cache() -> None:
    """Invalida caches QSS após mudança de tema/contraste/fonte."""
    load_qss_file.cache_clear()
    _widget_fragments.cache_clear()


def load_qss(filename: str, **extra: str | int) -> str:
    return render_qss(load_qss_file(filename), **extra)


@lru_cache(maxsize=1)
def _widget_fragments() -> dict[str, str]:
    """Extrai blocos nomeados de widgets.qss (marcadores ``/* @fragment name */``)."""
    content = load_qss_file("widgets.qss")
    fragments: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("/* @fragment ") and stripped.endswith("*/"):
            if current_name is not None:
                fragments[current_name] = "\n".join(current_lines).strip()
            current_name = stripped[len("/* @fragment ") : -2].strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(line)

    if current_name is not None:
        fragments[current_name] = "\n".join(current_lines).strip()
    return fragments


def load_fragment(name: str, **extra: str | int) -> str:
    fragments = _widget_fragments()
    if name not in fragments:
        available = ", ".join(sorted(fragments))
        raise KeyError(f"Fragmento QSS '{name}' não encontrado. Disponíveis: {available}")
    return render_qss(fragments[name], **extra)
