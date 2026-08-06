"""Fakes in-memory para testes e demo da UI (sem parser/exportador reais)."""
from .adapters import FakeReportExporter, FakeReportParser
from .repositories import InMemoryRecentFilesRepository, InMemoryTemplateRepository

__all__ = [
    "FakeReportExporter",
    "FakeReportParser",
    "InMemoryRecentFilesRepository",
    "InMemoryTemplateRepository",
]
