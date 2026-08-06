"""Painel de PDFs exportados — histórico de exportações."""
from __future__ import annotations

from src.ui.features.home.components.recentes_panel import RecentesPanel


class ExportsPanel(RecentesPanel):
    """Lista de exportações registradas em ``documentos``."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._section_header.set_title("PDFs exportados")
        self._section_header.set_subtitle("Relatórios finais gerados pelo workspace")
