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
    """Uma marcação (seta, círculo, caixa de texto ou número) sobre uma imagem.

    Coordenadas normalizadas (0–1) relativas à imagem original.
    """

    kind: str  # "arrow" | "circle" | "text_box" | "number" | "crop"
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    text: str = ""
    color: str = "#E85D04"
    legend: str = ""  # descrição do marcador numerado (legenda automática no PDF)


@dataclass
class ImageCrop:
    """Recorte manual normalizado (0–1) relativo à imagem original."""

    x: float
    y: float
    width: float
    height: float


@dataclass
class ReportImage:
    """Uma fotografia da peça associada a uma seção do relatório."""

    image_path: Path
    section_id: str
    image_id: str = ""
    annotations: list[Annotation] = field(default_factory=list)
    crop: ImageCrop | None = None
    caption: str = ""
    bosello_import: bool = False


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
    # PDFs de origem a anexar na seção Anexos (vazio = usa ``source_pdf_path``).
    attachment_pdf_paths: list[Path] = field(default_factory=list)
    images: list[ReportImage] = field(default_factory=list)
    # Biblioteca de capturas renderizadas do PDF Bosello (independente das fotos em uso).
    bosello_captured_paths: list[Path] = field(default_factory=list)
    control_info: TechnicalControlInfo | None = None
    version_history: list[VersionEntry] = field(default_factory=list)
    template_id: str = "default"
    section_overrides: dict[str, dict] = field(default_factory=dict)
    parsed_overrides: dict[str, Any] = field(default_factory=dict)
    custom_sections: list[dict] = field(default_factory=list)
    deleted_section_ids: list[str] = field(default_factory=list)
    # Seções do catálogo adicionadas ao relatório além do template atual.
    extra_section_ids: list[str] = field(default_factory=list)
    section_order: list[str] | None = None
    # Snapshot in-memory de sections_config (preview de template antes de salvar)
    template_layout_override: dict[str, dict] | None = None
    # Payload opaco devolvido pelo parser real
    # A UI nunca lê o conteúdo disto — apenas o carrega de volta para o
    # ReportExporter na hora de gerar o PDF final. Mantém a UI desacoplada
    # do formato interno usado pelo parser/gerador.
    raw_parsed_data: Any = None
    # Tipo de origem detectado pelo parser: "calypso" | "insp_ect"
    source_kind: str = "calypso"
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

    @abstractmethod
    def get_by_id(self, file_id: str) -> dict | None:
        """Retorna metadados de um registro recente ou ``None``."""


class VersionHistoryRepository(ABC):
    """Porta de persistência do histórico de versões por documento."""

    @abstractmethod
    def list_for_document(
        self,
        source_pdf_path: str,
        client_project: str,
        componente: str,
    ) -> list[VersionEntry]:
        ...

    @abstractmethod
    def append(
        self,
        source_pdf_path: str,
        client_project: str,
        componente: str,
        entry: VersionEntry,
    ) -> None:
        ...


class TemplateRepository(ABC):
    """Porta de persistência de templates customizados (implementada com JSON)."""

    @abstractmethod
    def list_templates(self) -> list[dict]:
        ...

    @abstractmethod
    def save_template(self, template_id: str, sections_config: dict) -> None:
        ...

    @abstractmethod
    def get_template_config(self, template_id: str) -> dict:
        """Retorna config {section_id: {enabled, order}} ou dict vazio."""

    @abstractmethod
    def update_template_name(self, template_id: str, name: str) -> None:
        """Atualiza o nome exibido de um template."""

    def delete_template(self, template_id: str) -> bool:
        """Remove template customizado. Retorna False se built-in ou inexistente."""
        return False

    def get_content_defaults(self, template_id: str) -> dict:
        """Defaults de conteúdo por seção — override em implementações JSON."""
        return {}

    def save_content_defaults(self, template_id: str, content: dict) -> None:
        """Persiste defaults de conteúdo (implementação opcional)."""
        pass

    def save_full_template(
        self,
        template_id: str,
        sections_config: dict,
        content_defaults: dict,
        name: str,
    ) -> None:
        """Salva estrutura + conteúdo + nome atomicamente."""
        self.save_template(template_id, sections_config)
        self.save_content_defaults(template_id, content_defaults)
        self.update_template_name(template_id, name)


class WorkspaceSessionPort(ABC):
    """Porta de persistência da sessão de edição do workspace."""

    @abstractmethod
    def save(self, document: ReportDocument) -> None:
        ...

    @abstractmethod
    def load(self, document: ReportDocument) -> bool:
        ...


class ProjectRepositoryPort(ABC):
    """Porta de persistência de projetos em edição (multi-PDF)."""

    @abstractmethod
    def save(self, workspace) -> None:
        ...

    @abstractmethod
    def get(self, project_id: str):
        ...

    @abstractmethod
    def list_recent(self, limit: int = 50) -> list:
        ...

    @abstractmethod
    def delete(self, project_id: str) -> bool:
        """Remove o projeto e versões associadas. True se algo foi apagado."""
        ...


class VersionSnapshotPort(ABC):
    """Porta de snapshots de versão por projeto (Fase 4)."""

    @abstractmethod
    def append(self, snapshot) -> int:
        ...

    @abstractmethod
    def list_for_project(self, project_id: str) -> list:
        ...