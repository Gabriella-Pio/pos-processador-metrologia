"""
ViewModel do Workspace de edição — ponte entre a UI e o core (parser/exportador).
"""
from __future__ import annotations

import logging
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal, pyqtSlot

from src.core.application.session import load_workspace_session, save_workspace_session
from src.core.application.export_report import validate_export
from src.core.application.document_editing import (
    build_effective_document_dto,
    extract_global_field_values,
    get_measurement_rows,
    sync_measured_by,
    sync_operador,
)
from src.core.application.template_layout import (
    document_has_data_changes,
    document_has_layout_changes,
)
from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession
from src.core.domain.ports import (
    Annotation,
    RecentFilesRepository,
    ReportDocument,
    ReportExporter,
    ReportImage,
    ReportParser,
    TechnicalControlInfo,
    TemplateRepository,
    VersionEntry,
    VersionHistoryRepository,
    WorkspaceSessionPort,
)
from src.core.infrastructure.workspace_session_repository import SQLiteWorkspaceSessionRepository
from src.ui.features.workspace.presenters.section_summary_presenter import SectionSummaryPresenter
from src.ui.features.workspace.services.document_session_service import DocumentSessionService
from src.ui.features.workspace.services.preview_service import PreviewService
from src.ui.features.workspace.services.template_workspace_service import TemplateWorkspaceService
from src.ui.controllers.app_state import AppState

logger = logging.getLogger(__name__)

_PREVIEW_DEBOUNCE_MS = 600
_SESSION_SAVE_DEBOUNCE_MS = 2000


class _PreviewWorkerSignals(QObject):
    finished = pyqtSignal(int, list, dict)
    failed = pyqtSignal(int, str)


class _PreviewWorker(QRunnable):
    def __init__(
        self,
        generation: int,
        document: ReportDocument,
        preview_service: PreviewService,
    ) -> None:
        super().__init__()
        self._generation = generation
        self._document = document
        self._preview_service = preview_service
        self.signals = _PreviewWorkerSignals()

    @pyqtSlot()
    def run(self) -> None:
        try:
            pages = self._preview_service.render_pages(self._document)
            anchor_map = {}
            exporter = self._preview_service._exporter
            if hasattr(exporter, "_last_section_anchor_map"):
                anchor_map = dict(getattr(exporter, "_last_section_anchor_map", {}))
            self.signals.finished.emit(self._generation, pages, anchor_map)
        except Exception:
            logger.exception("Falha ao gerar preview em background")
            self.signals.failed.emit(self._generation, traceback.format_exc())


class WorkspaceViewModel(QObject):
    document_loaded = pyqtSignal(object)
    project_loaded = pyqtSignal(object)
    export_finished = pyqtSignal(Path)
    sections_summary_ready = pyqtSignal(list)
    preview_ready = pyqtSignal(list)
    preview_metadata_ready = pyqtSignal(dict)
    preview_generating = pyqtSignal(bool)
    global_fields_ready = pyqtSignal(dict, object)
    layout_dirty_changed = pyqtSignal(bool)
    data_dirty_changed = pyqtSignal(bool)
    template_dirty_changed = pyqtSignal(bool)
    templates_list_ready = pyqtSignal(list)
    export_validation_ready = pyqtSignal(list)
    error_occurred = pyqtSignal(str, str, str)

    def __init__(
        self,
        app_state: AppState,
        parser: ReportParser,
        exporter: ReportExporter,
        recent_files_repo: RecentFilesRepository | None = None,
        version_history_repo: VersionHistoryRepository | None = None,
        template_repo: TemplateRepository | None = None,
        session_repo: WorkspaceSessionPort | None = None,
    ) -> None:
        super().__init__()
        self._app_state = app_state
        self._parser = parser
        self._exporter = exporter
        self._recent_files_repo = recent_files_repo
        self._version_history_repo = version_history_repo
        self._template_repo = template_repo
        self._session_repo = session_repo or SQLiteWorkspaceSessionRepository()
        self._doc_service = DocumentSessionService(parser, template_repo, version_history_repo)
        self._template_service = TemplateWorkspaceService(template_repo, exporter)
        self._presenter = SectionSummaryPresenter(exporter)
        self._preview_service = PreviewService(exporter)
        self._preview_generation = 0
        self._thread_pool = QThreadPool.globalInstance()
        self._undo_stack: list[tuple[str, dict]] = []

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(_PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._run_preview)

        self._session_timer = QTimer(self)
        self._session_timer.setSingleShot(True)
        self._session_timer.setInterval(_SESSION_SAVE_DEBOUNCE_MS)
        self._session_timer.timeout.connect(self._persist_session)

    # ------------------------------------------------------------------ commit

    def _commit_document_change(
        self,
        *,
        preview: bool = True,
        summary: bool = True,
        layout_dirty: bool = False,
        data_dirty_flag: bool = False,
        globals_refresh: bool = False,
        persist: bool = True,
    ) -> None:
        if globals_refresh:
            self.refresh_global_fields()
        if summary:
            self.refresh_sections_summary()
        if preview:
            self.schedule_preview()
        if layout_dirty or data_dirty_flag:
            self._emit_dirty_state()
        if persist:
            self._schedule_session_save()
        self._refresh_export_validation()

    def _emit_dirty_state(self) -> None:
        layout = self.is_layout_dirty()
        data = self.is_data_dirty()
        self.layout_dirty_changed.emit(layout)
        self.data_dirty_changed.emit(data)
        self.template_dirty_changed.emit(layout)

    def _schedule_session_save(self) -> None:
        self._session_timer.start()

    def _persist_session(self) -> None:
        document = self._active_document()
        if document is None:
            return
        try:
            save_workspace_session(self._session_repo, document)
        except Exception:
            logger.exception("Falha ao persistir sessão do workspace")

    def _refresh_export_validation(self) -> None:
        document = self._active_document()
        if document is None:
            return
        issues = validate_export(document)
        self.export_validation_ready.emit([
            {"level": i.level, "message": i.message} for i in issues
        ])

    def _active_document(self) -> ReportDocument | None:
        return self._app_state.active_document

    def push_undo_snapshot(self, label: str) -> None:
        document = self._active_document()
        if document is None:
            return
        snapshot = {
            "section_overrides": {
                k: dict(v) if isinstance(v, dict) else v
                for k, v in document.section_overrides.items()
            },
            "parsed_overrides": dict(document.parsed_overrides),
            "section_order": list(document.section_order) if document.section_order else None,
        }
        self._undo_stack.append((label, snapshot))
        if len(self._undo_stack) > 1:
            self._undo_stack = self._undo_stack[-1:]

    def undo_last_change(self) -> bool:
        document = self._active_document()
        if document is None or not self._undo_stack:
            return False
        _, snapshot = self._undo_stack.pop()
        document.section_overrides = snapshot["section_overrides"]
        document.parsed_overrides = snapshot["parsed_overrides"]
        document.section_order = snapshot["section_order"]
        self._commit_document_change(
            preview=True, summary=True, layout_dirty=True, data_dirty_flag=True, globals_refresh=True
        )
        return True

    # ------------------------------------------------------------------ dirty

    def is_layout_dirty(self) -> bool:
        document = self._active_document()
        if document is None:
            return False
        return self._template_service.is_layout_dirty(document)

    def is_data_dirty(self) -> bool:
        document = self._active_document()
        if document is None:
            return False
        return document_has_data_changes(document)

    def is_template_dirty(self) -> bool:
        return self.is_layout_dirty()

    # ------------------------------------------------------------------ load

    def load_project(
        self,
        client_project: str,
        pdf_entries: list[tuple[Path, str]],
        template_id: str = "default",
        report_mode: str = "auto",
    ) -> None:
        session = self._doc_service.build_project_session(
            client_project, pdf_entries, template_id, report_mode=report_mode
        )
        self._app_state.set_project_session(session)
        self.project_loaded.emit(session)

        for index in range(len(session.documents)):
            if not self._parse_slot(session, index):
                return
        self.switch_document(0)

    def load_from_pdf(self, pdf_path: Path, client_project: str, evaluated_component: str) -> None:
        self.load_project(
            client_project,
            [(pdf_path, evaluated_component)],
            template_id="default",
        )

    def append_pdfs_to_project(self, paths: list[Path], default_component: str) -> None:
        session = self._app_state.project_session
        if session is None or not paths:
            return
        start_index = len(session.documents)
        for pdf_path in paths:
            session.documents.append(
                ProjectDocumentSlot(
                    source_pdf_path=pdf_path,
                    evaluated_component=default_component,
                )
            )
        for index in range(start_index, len(session.documents)):
            if not self._parse_slot(session, index):
                return
        self.project_loaded.emit(session)

    def switch_document(self, index: int) -> None:
        session = self._app_state.project_session
        if session is None:
            return
        session.set_active_index(index)
        document = session.active_document
        if document is None:
            return
        self._doc_service.load_versions_for_document(document)
        load_workspace_session(self._session_repo, document)
        self._app_state.set_active_document(document)
        self.document_loaded.emit(document)
        self._commit_document_change(
            preview=True, summary=True, layout_dirty=True, data_dirty_flag=True, globals_refresh=True, persist=False
        )
        self._emit_templates_list()

    def _emit_templates_list(self) -> None:
        self.templates_list_ready.emit(self.list_templates())

    def list_templates(self) -> list[dict]:
        return self._template_service.list_templates()

    def change_template(self, template_id: str) -> None:
        session = self._app_state.project_session
        document = self._active_document()
        if session is None or document is None or self._template_repo is None:
            return
        slot = session.active_slot
        if session.report_mode == "mixed" and slot is not None:
            slot.template_id = template_id
            self._template_service.apply_template_change(document, template_id)
        else:
            session.template_id = template_id
            for project_slot in session.documents:
                if project_slot.document is not None:
                    project_slot.template_id = template_id
                    self._template_service.apply_template_change(project_slot.document, template_id)
        self._commit_document_change(
            preview=True, summary=True, layout_dirty=True, data_dirty_flag=False, globals_refresh=True
        )

    def save_current_as_template(self, name: str, create_new: bool) -> str | None:
        document = self._active_document()
        session = self._app_state.project_session
        if document is None or session is None or not name.strip():
            return None
        template_id = self._template_service.save_as_template(document, name, create_new)
        if template_id is None:
            return None
        session.template_id = template_id
        for slot in session.documents:
            if slot.document is not None:
                slot.document.template_id = template_id
        self._emit_templates_list()
        self._emit_dirty_state()
        return template_id

    def reorder_sections(self, ordered_ids: list[str]) -> None:
        document = self._active_document()
        if document is None:
            return
        self.push_undo_snapshot("reorder")
        document.section_order = list(ordered_ids)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def load_from_recent(self, file_id: str) -> None:
        if self._recent_files_repo is None:
            self.error_occurred.emit(
                "Histórico indisponível",
                "O repositório de arquivos recentes não está configurado.",
                "",
            )
            return
        record = self._recent_files_repo.get_by_id(file_id)
        if record is None:
            self.error_occurred.emit(
                "Arquivo não encontrado",
                "Este registro não existe mais no histórico local.",
                "",
            )
            return
        pdf_path = Path(record["file_path"])
        if not pdf_path.exists():
            self.error_occurred.emit(
                "Arquivo ausente",
                f"O PDF não foi encontrado em:\n{pdf_path}",
                "",
            )
            return
        self.load_from_pdf(
            pdf_path,
            record.get("client_project", "Projeto"),
            record.get("evaluated_component", record.get("file_name", "Componente")),
        )

    def _parse_slot(self, session: ProjectSession, index: int) -> bool:
        ok, details = self._doc_service.parse_slot(session, index)
        if not ok:
            self.error_occurred.emit(
                "Não foi possível ler o PDF",
                f"Erro ao processar {session.documents[index].source_pdf_path.name}.",
                details,
            )
            return False
        slot_doc = session.documents[index].document
        if slot_doc is not None:
            load_workspace_session(self._session_repo, slot_doc)
        return True

    # ------------------------------------------------------------------ fields

    def refresh_global_fields(self) -> None:
        document = self._active_document()
        if document is None:
            return
        values, overridden = extract_global_field_values(document)
        self.global_fields_ready.emit(values, overridden)

    def get_effective_itens_medicao(self) -> list[dict[str, str]]:
        document = self._active_document()
        if document is None:
            return []
        return get_measurement_rows(document)

    def update_parsed_field(self, key: str, value: str) -> None:
        document = self._active_document()
        if document is None:
            return
        if key in ("client_project", "evaluated_component"):
            if key == "client_project":
                document.client_project = value
            else:
                document.evaluated_component = value
        elif key == "operador":
            sync_operador(document, value)
        else:
            document.parsed_overrides.setdefault("scalar", {})[key] = value
        self._commit_document_change(
            preview=True, summary=True, data_dirty_flag=True, globals_refresh=True
        )

    def restore_parsed_field(self, key: str) -> None:
        document = self._active_document()
        if document is None:
            return
        if key in ("client_project", "evaluated_component"):
            raw = document.raw_parsed_data
            if key == "client_project":
                document.client_project = getattr(raw, "cliente_projeto", "Projeto")
            else:
                document.evaluated_component = getattr(raw, "componente", "Componente")
        else:
            document.parsed_overrides.get("scalar", {}).pop(key, None)
        self._commit_document_change(
            preview=True, summary=True, data_dirty_flag=True, globals_refresh=True
        )

    def update_itens_medicao(self, rows: list[dict[str, str]]) -> None:
        document = self._active_document()
        if document is None:
            return
        document.parsed_overrides["itens_medicao"] = rows
        self._commit_document_change(preview=True, summary=True, data_dirty_flag=True)

    def restore_itens_medicao(self) -> None:
        document = self._active_document()
        if document is None:
            return
        document.parsed_overrides.pop("itens_medicao", None)
        self._commit_document_change(preview=True, summary=True, data_dirty_flag=True)

    def refresh_sections_summary(self) -> None:
        document = self._active_document()
        if document is None:
            return
        try:
            items = self._presenter.build(document)
            self.sections_summary_ready.emit([item.to_dict() for item in items])
        except Exception:
            logger.exception("Falha ao montar o sumário de seções")

    def update_section_field(self, section_id: str, field: str, value: str) -> None:
        document = self._active_document()
        if document is None:
            return
        control_fields = {
            "measured_by", "reviewed_by", "approved_by", "role", "institutional_email"
        }
        if section_id == "controle_tecnico" and field in control_fields:
            if document.control_info is None:
                document.control_info = TechnicalControlInfo(measured_by="", reviewed_by="")
            setattr(document.control_info, field, value)
            if field == "measured_by":
                sync_measured_by(document, value)
        else:
            document.section_overrides.setdefault(section_id, {})[field] = value
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def restore_section_block(self, section_id: str, title_key: str, body_key: str) -> None:
        document = self._active_document()
        if document is None:
            return
        section_ov = document.section_overrides.get(section_id, {})
        section_ov.pop(title_key, None)
        if body_key:
            section_ov.pop(body_key, None)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def restore_section(self, section_id: str) -> None:
        document = self._active_document()
        if document is None:
            return
        document.section_overrides.pop(section_id, None)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def restore_section_field(self, section_id: str, field: str) -> None:
        document = self._active_document()
        if document is None:
            return
        from src.core.domain.report_field_registry import INTRODUCAO_BODY_TITLE_KEYS

        section_ov = document.section_overrides.get(section_id, {})
        section_ov.pop(field, None)
        # Restaurar bloco inteiro: texto + título (Objetivo / Escopo / …)
        title_key = INTRODUCAO_BODY_TITLE_KEYS.get(field)
        if title_key:
            section_ov.pop(title_key, None)
        else:
            for body_key, paired_title in INTRODUCAO_BODY_TITLE_KEYS.items():
                if field == paired_title:
                    section_ov.pop(body_key, None)
                    break
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def update_section_table_rows(self, section_id: str, rows: list[dict[str, str]]) -> None:
        document = self._active_document()
        if document is None:
            return
        document.section_overrides.setdefault(section_id, {})["table_rows"] = rows
        if section_id == "controle_tecnico":
            self._sync_control_info_from_table_rows(document, rows)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def restore_section_table_rows(self, section_id: str) -> None:
        document = self._active_document()
        if document is None:
            return
        document.section_overrides.get(section_id, {}).pop("table_rows", None)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)

    def _sync_control_info_from_table_rows(self, document, rows: list[dict[str, str]]) -> None:
        from src.core.domain.table_row_registry import control_info_updates_from_rows

        updates = control_info_updates_from_rows(rows)
        if not updates:
            return
        if document.control_info is None:
            document.control_info = TechnicalControlInfo(
                measured_by=updates.get("measured_by", ""),
                reviewed_by=updates.get("reviewed_by", ""),
            )
        for field, value in updates.items():
            setattr(document.control_info, field, value)
        if "measured_by" in updates:
            sync_measured_by(document, updates["measured_by"])

    def delete_section(self, section_id: str) -> bool:
        document = self._active_document()
        if document is None:
            return False
        is_custom = section_id.startswith("custom_") or any(
            s.get("id") == section_id for s in document.custom_sections
        )
        if not is_custom:
            return False
        document.custom_sections = [
            s for s in document.custom_sections if s.get("id") != section_id
        ]
        if section_id not in document.deleted_section_ids:
            document.deleted_section_ids.append(section_id)
        document.section_overrides.pop(section_id, None)
        self._commit_document_change(preview=True, summary=True, layout_dirty=True)
        return True

    def add_custom_section(self, title: str) -> str | None:
        document = self._active_document()
        if document is None or not title.strip():
            return None
        next_index = len(document.custom_sections) + 1
        section_id = f"custom_{next_index}"
        while any(s.get("id") == section_id for s in document.custom_sections):
            next_index += 1
            section_id = f"custom_{next_index}"
        document.custom_sections.append({"id": section_id, "title": title.strip(), "custom": True})
        self._commit_document_change(preview=True, summary=True, layout_dirty=True, persist=False)
        return section_id

    def get_section_page_map(self) -> dict[str, int]:
        document = self._active_document()
        if document is None:
            return {}
        exporter = self._exporter
        if hasattr(exporter, "_last_section_anchor_map"):
            return {
                sid: (info or {}).get("page", 0)
                for sid, info in exporter._last_section_anchor_map.items()
            }
        return {}

    # ------------------------------------------------------------------ preview

    def schedule_preview(self) -> None:
        self.preview_generating.emit(True)
        self._preview_timer.start()

    def generate_preview(self) -> None:
        self.schedule_preview()

    def _run_preview(self) -> None:
        document = self._active_document()
        if document is None:
            self.preview_generating.emit(False)
            return
        self._preview_generation += 1
        generation = self._preview_generation
        worker = _PreviewWorker(generation, document, self._preview_service)
        worker.signals.finished.connect(self._on_preview_finished)
        worker.signals.failed.connect(self._on_preview_failed)
        self._thread_pool.start(worker)

    def _on_preview_finished(self, generation: int, pages: list[bytes], anchor_map: dict) -> None:
        if generation != self._preview_generation:
            return
        self.preview_generating.emit(False)
        self.preview_ready.emit(pages)
        self.preview_metadata_ready.emit(anchor_map)

    def _on_preview_failed(self, generation: int, details: str) -> None:
        if generation != self._preview_generation:
            return
        self.preview_generating.emit(False)
        self.error_occurred.emit(
            "Não foi possível atualizar o preview",
            "Alguns dados do relatório podem estar incompletos.",
            details,
        )

    # ------------------------------------------------------------------ media

    def add_image_to_section(self, image_path: Path, section_id: str) -> None:
        document = self._active_document()
        if document is None:
            return
        document.images.append(ReportImage(image_path=image_path, section_id=section_id))
        self._app_state.notify_images_changed()
        self._commit_document_change(preview=True, summary=True, data_dirty_flag=True)

    def remove_image(self, image: ReportImage) -> None:
        document = self._active_document()
        if document is None:
            return
        document.images = [
            img for img in document.images
            if not (
                img.section_id == image.section_id
                and str(img.image_path) == str(image.image_path)
            )
        ]
        self._app_state.notify_images_changed()
        self._commit_document_change(preview=True, summary=True, data_dirty_flag=True)

    def update_image_caption(self, image: ReportImage, caption: str) -> None:
        document = self._active_document()
        if document is None:
            return
        for img in document.images:
            if (
                img.section_id == image.section_id
                and str(img.image_path) == str(image.image_path)
            ):
                img.caption = caption
                break
        # Não dispara images_changed: reconstrói a lista e reseta o cursor da legenda.
        # Preview/PDF ainda atualiza via schedule_preview.
        self._commit_document_change(
            preview=True, summary=False, data_dirty_flag=True,
        )

    def add_annotation(self, image: ReportImage, annotation: Annotation) -> None:
        image.annotations.append(annotation)
        self._app_state.notify_images_changed()
        self._commit_document_change(preview=True, summary=True, data_dirty_flag=True)

    def register_new_version(self, responsible_name: str, description: str) -> None:
        document = self._active_document()
        if document is None:
            return
        existing = document.version_history
        next_number = max((entry.version_number for entry in existing), default=0) + 1
        entry = VersionEntry(
            version_number=next_number,
            timestamp=datetime.now(),
            responsible_name=responsible_name,
            description=description,
        )
        if self._version_history_repo is not None:
            self._version_history_repo.append(
                str(document.source_pdf_path),
                document.client_project,
                document.evaluated_component,
                entry,
            )
        self._app_state.register_version(entry)

    def export_document(self, output_path: Path) -> None:
        document = self._active_document()
        if document is None:
            self.error_occurred.emit(
                "Nenhum documento aberto",
                "Importe um relatório antes de exportar.",
                "",
            )
            return
        issues = validate_export(document)
        errors = [i for i in issues if i.level == "error"]
        if errors:
            self.error_occurred.emit(
                "Exportação bloqueada",
                errors[0].message,
                "",
            )
            return
        try:
            final_path = self._exporter.export(document, output_path)
        except Exception:
            logger.exception("Falha ao exportar o PDF para: %s", output_path)
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            self.error_occurred.emit(
                "Falha ao exportar o PDF",
                "Ocorreu um erro ao gerar o documento final.",
                traceback.format_exc(),
            )
            return

        if self._recent_files_repo is not None:
            try:
                self._recent_files_repo.save(document, str(final_path))
            except Exception:
                logger.exception("Falha ao registrar %s no histórico", final_path)

        self.export_finished.emit(final_path)

    def export_all_documents(self, output_dir: Path) -> list[Path]:
        session = self._app_state.project_session
        if session is None or not session.documents:
            return []
        output_dir.mkdir(parents=True, exist_ok=True)
        exported: list[Path] = []
        original_index = session.active_index
        for index, slot in enumerate(session.documents):
            if slot.document is None:
                continue
            self.switch_document(index)
            safe_name = slot.evaluated_component.replace(" ", "_")[:40]
            out_path = output_dir / f"{safe_name}_{index + 1}.pdf"
            self.export_document(out_path)
            exported.append(out_path)
        self.switch_document(original_index)
        return exported
