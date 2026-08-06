"""Helpers compartilhados entre painéis da sidebar."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget

from src.ui.shared.report_editor.sidebar_chrome import sidebar_section_header


def section_header(title: str) -> QWidget:
    return sidebar_section_header(title)
