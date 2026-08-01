"""
Estado de sessão centralizado da aplicação.

Implementa o padrão Observer usando o mecanismo nativo de sinais/slots
do Qt: qualquer widget pode "assinar" (``.connect``) uma mudança de
estado sem que o ``AppState`` precise conhecer seus observadores. Isso
evita que o documento em edição fique espalhado em atributos de várias
views, prevenindo perda de dados ao navegar entre abas (Home →
Workspace → Templates).

Existe uma única instância (``AppState``) compartilhada, injetada nas
views a partir do ``MainWindow`` — não é um singleton global "mágico",
o que manteria os testes difíceis; é uma injeção de dependência simples.
"""
from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from src.core.ports import ReportDocument


class AppState(QObject):
    """Fonte única de verdade para o documento em edição e navegação.

    Sinais emitidos (Observer):
        document_changed: o ``ReportDocument`` ativo foi substituído ou alterado.
        images_changed: lista de imagens/anotações do documento ativo mudou.
        version_added: uma nova entrada de histórico de versão foi registrada.
    """

    document_changed = pyqtSignal(object)  # ReportDocument | None
    images_changed = pyqtSignal()
    version_added = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._active_document: ReportDocument | None = None

    @property
    def active_document(self) -> ReportDocument | None:
        return self._active_document

    def set_active_document(self, document: ReportDocument | None) -> None:
        """Define o documento em edição e notifica todos os observadores."""
        self._active_document = document
        self.document_changed.emit(document)

    def notify_images_changed(self) -> None:
        """Chamado pelo ViewModel do Workspace após drag-and-drop de imagens
        ou edição de anotações, para que a sidebar/preview se atualizem.
        """
        self.images_changed.emit()

    def register_version(self, entry) -> None:
        """Adiciona uma entrada ao histórico de versões do documento ativo."""
        if self._active_document is None:
            return
        self._active_document.version_history.append(entry)
        self.version_added.emit()

    def clear(self) -> None:
        """Limpa a sessão (ex.: ao voltar para o Dashboard sem salvar)."""
        self.set_active_document(None)
