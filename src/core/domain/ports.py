"""
Ports (interfaces) da camada de domínio.

Por Inversão de Dependência (o "D" do SOLID), a camada de UI/ViewModel
depende apenas destes contratos abstratos — nunca das implementações
concretas de parsing de PDF ou geração via ReportLab, que vivem em
``src/core/`` (fora do escopo desta entrega de UI) e serão injetadas
no ``main_window.py`` na montagem da aplicação.

Isso permite, por exemplo, substituir o parser real por um fake nos
testes de UI, sem tocar em nenhuma view.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol


@dataclass
class Annotation:
    """Uma marcação (seta, círculo, caixa de texto ou número) sobre uma imagem."""

    kind: str  # "arrow" | "circle" | "text_box" | "number"
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    text: str = ""


@dataclass
class ReportImage:
    """Uma fotografia da peça associada a uma seção do relatório."""

    image_path: Path
    section_id: str
    annotations: list[Annotation] = field(default_factory=list)


@dataclass
class VersionEntry:
    """Uma entrada do histórico de versões do relatório."""

    version_number: int
    timestamp: datetime
    responsible_name: str
    description: str


@dataclass
class TechnicalControlInfo:
    """Dados da Página de Controle Técnico."""

    measured_by: str
    reviewed_by: str
    approved_by: str = ""
    role: str = ""
    institutional_email: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ReportDocument:
    """Representação em memória do relatório em edição no Workspace."""

    source_pdf_path: Path
    client_project: str
    evaluated_component: str
    images: list[ReportImage] = field(default_factory=list)
    control_info: TechnicalControlInfo | None = None
    version_history: list[VersionEntry] = field(default_factory=list)
    template_id: str = "default"
    # Payload opaco devolvido pelo parser real (ex.: RelatorioCalypsoDto).
    # A UI nunca lê o conteúdo disto — apenas o carrega de volta para o
    # ReportExporter na hora de gerar o PDF final. Mantém a UI desacoplada
    # do formato interno usado pelo parser/gerador.
    raw_parsed_data: Any = None
    # Caminho do último PDF exportado com sucesso, usado para registrar
    # o arquivo no RecentFilesRepository após a exportação.
    last_export_path: Path | None = None


class ReportParser(Protocol):
    """Porta para leitura do PDF bruto gerado pelos equipamentos ZEISS."""

    def parse(self, pdf_path: Path) -> ReportDocument:
        ...


class ReportExporter(Protocol):
    """Porta para geração do PDF final enriquecido (implementada com ReportLab)."""

    def export(self, document: ReportDocument, output_path: Path) -> Path:
        ...

    def list_sections(self, document: ReportDocument) -> list[dict]:
        """Lista, na ordem real em que aparecerão no PDF final, as seções
        que este documento vai gerar — usado para montar o sumário
        (bookmarks) do Workspace de forma fiel ao que será exportado.
        Cada item: ``{"id": "resultados", "title": "Resultados dimensionais"}``.
        """
        ...


class RecentFilesRepository(ABC):
    """Porta de persistência do histórico de arquivos (implementada com SQLite)."""

    @abstractmethod
    def list_recent(self, limit: int = 20) -> list[dict]:
        ...

    @abstractmethod
    def save(self, document: ReportDocument, file_name: str) -> str:
        """Persiste o documento e retorna o ``file_id`` gerado."""


class TemplateRepository(ABC):
    """Porta de persistência de templates customizados (implementada com JSON)."""

    @abstractmethod
    def list_templates(self) -> list[dict]:
        ...

    @abstractmethod
    def save_template(self, template_id: str, sections_config: dict) -> None:
        ...