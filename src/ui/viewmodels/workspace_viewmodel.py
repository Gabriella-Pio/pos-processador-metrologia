"""ViewModel do Workspace de edição — ponte entre a UI e o core (parser/exportador)."""
from __future__ import annotations

import logging
import tempfile
import traceback
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF — usado só para RENDERIZAR o PDF de preview como
             # imagens; não é usado para nenhuma lógica de negócio aqui,
             # então não fere o desacoplamento da UI em relação ao parser.
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.ports import (
    Annotation,
    RecentFilesRepository,
    ReportDocument,
    ReportExporter,
    ReportImage,
    ReportParser,
    VersionEntry,
)
from src.ui.viewmodels.app_state import AppState

logger = logging.getLogger(__name__)


class WorkspaceViewModel(QObject):
    """Orquestra o carregamento, edição e exportação do documento ativo.

    A ``WorkspaceView`` nunca chama o parser ou o ReportLab diretamente
    — apenas este ViewModel o faz, através das interfaces (``ReportParser``,
    ``ReportExporter``) injetadas no construtor. Isso mantém a view livre
    de qualquer dependência de I/O ou de bibliotecas de PDF.
    """

    document_loaded = pyqtSignal(object)  # ReportDocument
    export_finished = pyqtSignal(Path)
    sections_summary_ready = pyqtSignal(list)  # [{"id", "title"}, ...]
    preview_ready = pyqtSignal(list)  # [bytes_png_pagina_1, bytes_png_pagina_2, ...]
    # title, message (amigável), details (traceback técnico completo — só
    # aparece se o usuário clicar em "Detalhes" na caixa de diálogo)
    error_occurred = pyqtSignal(str, str, str)

    def __init__(
        self,
        app_state: AppState,
        parser: ReportParser,
        exporter: ReportExporter,
        recent_files_repo: RecentFilesRepository | None = None,
    ) -> None:
        super().__init__()
        self._app_state = app_state
        self._parser = parser
        self._exporter = exporter
        self._recent_files_repo = recent_files_repo

    def load_from_pdf(self, pdf_path: Path, client_project: str, evaluated_component: str) -> None:
        """Importa um PDF bruto e inicializa o documento em edição."""
        try:
            document = self._parser.parse(pdf_path)
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao ler o PDF: %s", pdf_path)
            self.error_occurred.emit(
                "Não foi possível ler o PDF",
                "O arquivo pode estar corrompido ou em um formato não suportado "
                "pelos equipamentos ZEISS reconhecidos por esta aplicação.",
                traceback.format_exc(),
            )
            return
        # DIAGNÓSTICO TEMPORÁRIO — remover depois de confirmar a causa:
        logger.info(
            "Parser=%s | raw_parsed_data=%s | itens_medicao=%s",
            type(self._parser).__name__,
            document.raw_parsed_data,
            getattr(document.raw_parsed_data, "itens_medicao", "N/A"),
        )
        document.client_project = client_project
        document.evaluated_component = evaluated_component
        self._app_state.set_active_document(document)
        self.document_loaded.emit(document)
        self.refresh_sections_summary()
        self.generate_preview()

    def refresh_sections_summary(self) -> None:
        """Pede ao exportador a lista real de seções que vão compor o PDF
        final deste documento (na ordem certa) — usado pelo sumário
        (bookmarks) do Workspace, em vez de uma lista fixa/fake.
        """
        document = self._app_state.active_document
        if document is None:
            return
        try:
            secoes = self._exporter.list_sections(document)
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao montar o sumário de seções")
            return  # não vale a pena incomodar o operador por causa do sumário
        self.sections_summary_ready.emit(secoes)

    def generate_preview(self) -> None:
        """Gera um PDF de rascunho (mesma engine do PDF final, num arquivo
        temporário) e renderiza cada página como imagem — é a forma mais
        confiável de mostrar "como está ficando de verdade", incluindo
        onde as fotos caem, sem duplicar a lógica de layout na UI.
        """
        document = self._app_state.active_document
        if document is None:
            return
        try:
            with tempfile.TemporaryDirectory(prefix="metrologia_preview_") as tmp_dir:
                rascunho_path = Path(tmp_dir) / "preview.pdf"
                self._exporter.export(document, rascunho_path)
                paginas_png = self._renderizar_paginas(rascunho_path)
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao gerar o preview do relatório")
            self.error_occurred.emit(
                "Não foi possível atualizar o preview",
                "Alguns dados do relatório podem estar incompletos. O restante "
                "do Workspace continua funcionando normalmente.",
                traceback.format_exc(),
            )
            return
        self.preview_ready.emit(paginas_png)

    def _renderizar_paginas(self, pdf_path: Path, zoom: float = 1.6) -> list[bytes]:
        """Abre o PDF gerado com PyMuPDF e devolve cada página como PNG
        (em memória, sem salvar em disco) para a View exibir.
        """
        paginas = []
        matriz_zoom = fitz.Matrix(zoom, zoom)
        with fitz.open(pdf_path) as documento_pdf:
            for pagina in documento_pdf:
                pixmap = pagina.get_pixmap(matrix=matriz_zoom)
                paginas.append(pixmap.tobytes("png"))
        return paginas

    def add_image_to_section(self, image_path: Path, section_id: str) -> None:
        """Associa uma fotografia arrastada via drag-and-drop a uma seção."""
        document = self._app_state.active_document
        if document is None:
            return
        document.images.append(ReportImage(image_path=image_path, section_id=section_id))
        self._app_state.notify_images_changed()
        self.generate_preview()

    def add_annotation(self, image: ReportImage, annotation: Annotation) -> None:
        """Adiciona uma marcação (seta/círculo/caixa de texto/numeração) à imagem."""
        image.annotations.append(annotation)
        self._app_state.notify_images_changed()
        self.generate_preview()

    def build_preview_text(self, document: ReportDocument) -> str:
        """Monta um texto de pré-visualização a partir do payload opaco
        retornado pelo parser (``document.raw_parsed_data``).

        Usa ``getattr`` defensivo em vez de importar o DTO real do parser
        — assim o ViewModel continua sem depender de ``src.core.parser``
        diretamente (só o ``adapters.py`` conhece esse tipo concreto),
        e a função não quebra se algum campo não existir.
        """
        dto = document.raw_parsed_data
        if dto is None:
            return "Nenhum conteúdo extraído do PDF de origem."

        linhas = [
            f"Componente: {getattr(dto, 'componente', 'Não identificado')}",
            f"Máquina (MMC): {getattr(dto, 'maquina_mmc', 'Não identificada')}",
            f"Operador: {getattr(dto, 'operador', 'Não informado')}",
            f"Data/Hora da medição: {getattr(dto, 'data_hora', 'Não informada')}",
            f"Software: {getattr(dto, 'software', '')} {getattr(dto, 'versao_software', '')}".strip(),
            "",
        ]

        itens = getattr(dto, "itens_medicao", [])
        linhas.append(f"Características medidas: {len(itens)}")
        for item in itens:
            linhas.append(
                f"  • {item.caracteristica} ({item.tipo}): {item.valor_medido} "
                f"(nominal {item.nominal}) — {item.status}"
            )

        if not itens:
            linhas.append(
                "  (Nenhuma característica foi reconhecida pelo parser neste PDF — "
                "verifique se o layout do relatório de origem é compatível.)"
            )

        return "\n".join(linhas)

    def register_new_version(self, responsible_name: str, description: str) -> None:
        """Registra uma nova entrada no histórico de versões do documento ativo."""
        document = self._app_state.active_document
        if document is None:
            return
        next_number = len(document.version_history) + 1
        entry = VersionEntry(
            version_number=next_number,
            timestamp=datetime.now(),
            responsible_name=responsible_name,
            description=description,
        )
        self._app_state.register_version(entry)

    def export_document(self, output_path: Path) -> None:
        """Dispara a geração do PDF final enriquecido via ReportExporter."""
        document = self._app_state.active_document
        if document is None:
            self.error_occurred.emit(
                "Nenhum documento aberto",
                "Importe um relatório antes de exportar.",
                "",
            )
            return
        try:
            final_path = self._exporter.export(document, output_path)
        except Exception:  # noqa: BLE001
            logger.exception("Falha ao exportar o PDF para: %s", output_path)
            # Se o ReportLab já tiver escrito bytes parciais antes de falhar,
            # remove o arquivo corrompido para não deixar um PDF quebrado no
            # disco (evita o "não foi possível abrir o documento" do leitor
            # de PDF do sistema quando o usuário tentar abrir por engano).
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    logger.warning("Não foi possível remover o PDF parcial: %s", output_path)
            self.error_occurred.emit(
                "Falha ao exportar o PDF",
                "Ocorreu um erro ao gerar o documento final. Clique em "
                "\"Mostrar Detalhes\" para ver a causa técnica, ou verifique "
                "o arquivo de log em output_pdfs/logs/app.log.",
                traceback.format_exc(),
            )
            return

        if self._recent_files_repo is not None:
            try:
                self._recent_files_repo.save(document, str(final_path))
            except Exception:  # noqa: BLE001
                # Falha ao registrar no histórico não deve impedir o
                # operador de saber que o PDF já foi gerado com sucesso,
                # mas ainda registramos no log para investigação futura.
                logger.exception("Falha ao registrar %s no histórico", final_path)

        self.export_finished.emit(final_path)