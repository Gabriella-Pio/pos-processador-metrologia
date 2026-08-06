"""Pilha de undo para alterações de seção no documento."""
from __future__ import annotations

from src.core.domain.ports import ReportDocument


class DocumentUndoStack:
    """Guarda um snapshot por vez para desfazer a última alteração estrutural."""

    def __init__(self, max_depth: int = 1) -> None:
        self._stack: list[tuple[str, dict]] = []
        self._max_depth = max_depth

    def push(self, document: ReportDocument, label: str) -> None:
        snapshot = {
            "section_overrides": {
                k: dict(v) if isinstance(v, dict) else v
                for k, v in document.section_overrides.items()
            },
            "parsed_overrides": dict(document.parsed_overrides),
            "section_order": list(document.section_order) if document.section_order else None,
        }
        self._stack.append((label, snapshot))
        if len(self._stack) > self._max_depth:
            self._stack = self._stack[-self._max_depth :]

    def undo(self, document: ReportDocument) -> bool:
        if not self._stack:
            return False
        _, snapshot = self._stack.pop()
        document.section_overrides = snapshot["section_overrides"]
        document.parsed_overrides = snapshot["parsed_overrides"]
        document.section_order = snapshot["section_order"]
        return True

    def clear(self) -> None:
        self._stack.clear()
