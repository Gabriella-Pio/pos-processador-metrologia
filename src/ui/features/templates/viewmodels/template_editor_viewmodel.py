"""ViewModel do editor de templates — load/save, dirty state e preview."""
from __future__ import annotations

import copy
import logging
import traceback

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, QTimer, pyqtSignal, pyqtSlot

from src.core.application.template_preview import (
    build_template_preview_document,
    build_template_sections_summary,
    merge_template_content_defaults,
    split_template_content_defaults,
)
from src.core.domain.ports import ReportDocument, ReportExporter, TemplateRepository
from src.core.domain.section_schema import is_custom_section_id, merge_saved_template_config
from src.core.domain.report_field_registry import GLOBAL_FIELDS, effective_media_kinds
from src.ui.features.workspace.services.preview_service import PreviewService

logger = logging.getLogger(__name__)
_PREVIEW_DEBOUNCE_MS = 600


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
            logger.exception("Falha ao gerar preview do template")
            self.signals.failed.emit(self._generation, traceback.format_exc())


class TemplateEditorViewModel(QObject):
    template_loaded = pyqtSignal()
    template_name_changed = pyqtSignal(str)
    dirty_changed = pyqtSignal(bool)
    sections_summary_ready = pyqtSignal(list)
    global_fields_ready = pyqtSignal(dict, object)
    preview_ready = pyqtSignal(list)
    preview_metadata_ready = pyqtSignal(dict)
    preview_generating = pyqtSignal(bool)
    saved = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str, str)

    def __init__(
        self,
        template_repo: TemplateRepository,
        report_exporter: ReportExporter,
    ) -> None:
        super().__init__()
        self._repo = template_repo
        self._preview_service = PreviewService(report_exporter)
        self._preview_generation = 0
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(_PREVIEW_DEBOUNCE_MS)
        self._preview_timer.timeout.connect(self._run_preview)

        self._template_id = "new"
        self._template_name = ""
        self._is_new = True
        self._sections_config: dict = {}
        self._content_defaults: dict = {}
        self._global_defaults: dict = {}
        self._saved_snapshot: dict | None = None
        self._dirty = False
        self._active_section_id: str | None = None

    @property
    def template_id(self) -> str:
        return self._template_id

    @property
    def template_name(self) -> str:
        return self._template_name

    def is_dirty(self) -> bool:
        return self._dirty

    def load(self, template_id: str = "new") -> None:
        self._is_new = template_id == "new"
        if self._is_new:
            self._template_id = self._allocate_template_id()
            self._template_name = "Novo template"
            self._sections_config = self._config_from_sections(merge_saved_template_config({}))
        else:
            self._template_id = template_id
            self._template_name = template_id
            for template in self._repo.list_templates():
                if template["id"] == template_id:
                    self._template_name = template["name"]
                    break
            saved_cfg = self._repo.get_template_config(template_id)
            self._sections_config = dict(saved_cfg) if saved_cfg else self._config_from_sections(
                merge_saved_template_config({})
            )

        raw_content = {
            sid: dict(values)
            for sid, values in self._repo.get_content_defaults(self._template_id).items()
            if isinstance(values, dict)
        }
        section_defaults, self._global_defaults = split_template_content_defaults(raw_content)
        self._content_defaults = section_defaults
        self._saved_snapshot = self._current_snapshot()
        self._dirty = False
        self._active_section_id = None
        self.dirty_changed.emit(False)
        self.template_name_changed.emit(self._template_name)
        self._emit_sections_summary()
        self._emit_global_fields()
        self.schedule_preview()
        self.template_loaded.emit()

    def set_template_name(self, name: str) -> None:
        cleaned = name.strip()
        if cleaned == self._template_name:
            return
        self._template_name = cleaned
        self._mark_dirty()
        self.template_name_changed.emit(self._template_name)

    def set_section_enabled(self, section_id: str, enabled: bool) -> None:
        entry = self._sections_config.setdefault(section_id, {"enabled": True, "order": 999})
        entry["enabled"] = enabled
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()

    def reorder_sections(self, ordered_ids: list[str]) -> None:
        for index, section_id in enumerate(ordered_ids):
            entry = self._sections_config.setdefault(section_id, {"enabled": True, "order": index})
            entry["order"] = index
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()

    def set_active_section(self, section_id: str | None) -> None:
        self._active_section_id = section_id
        self._emit_sections_summary()

    def update_section_field(self, section_id: str, field_key: str, value: str) -> None:
        section = self._content_defaults.setdefault(section_id, {})
        section[field_key] = value
        if is_custom_section_id(section_id) and field_key == "title":
            entry = self._sections_config.setdefault(section_id, {"enabled": True, "order": 999})
            entry["title"] = value
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()

    def update_section_media_kinds(self, section_id: str, kinds: list[str]) -> None:
        section = self._content_defaults.setdefault(section_id, {})
        section["media_kinds"] = list(kinds)
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()

    def add_custom_section(self, title: str) -> str | None:
        cleaned = title.strip()
        if not cleaned:
            return None
        section_id = self._allocate_custom_section_id()
        max_order = max((cfg.get("order", 0) for cfg in self._sections_config.values()), default=0)
        self._sections_config[section_id] = {
            "enabled": True,
            "order": max_order + 1,
            "title": cleaned,
        }
        self._content_defaults[section_id] = {
            "title": cleaned,
            "subtitle": "",
            "body": "",
            "media_kinds": ["photos"],
        }
        self._active_section_id = section_id
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()
        return section_id

    def delete_custom_section(self, section_id: str) -> bool:
        if not is_custom_section_id(section_id):
            return False
        if section_id not in self._sections_config:
            return False
        del self._sections_config[section_id]
        self._content_defaults.pop(section_id, None)
        if self._active_section_id == section_id:
            self._active_section_id = None
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()
        return True

    def get_effective_media_kinds(self, section_id: str) -> list[str]:
        return effective_media_kinds(
            section_id,
            self._content_defaults.get(section_id, {}),
        )

    def update_section_table_rows(self, section_id: str, rows: list[dict[str, str]]) -> None:
        section = self._content_defaults.setdefault(section_id, {})
        section["table_rows"] = rows
        self._mark_dirty()
        self._emit_sections_summary()
        self.schedule_preview()

    def update_global_field(self, field_key: str, value: str) -> None:
        if field_key in {"client_project", "evaluated_component"}:
            self._global_defaults[field_key] = value
        else:
            scalar = self._global_defaults.setdefault("scalar", {})
            scalar[field_key] = value
        self._mark_dirty()
        self._emit_global_fields()
        self.schedule_preview()

    def get_section_defaults(self, section_id: str) -> dict:
        return dict(self._content_defaults.get(section_id, {}))

    def get_section_summary(self, section_id: str) -> dict:
        for section in build_template_sections_summary(
            self._sections_config,
            merge_template_content_defaults(self._content_defaults, self._global_defaults),
            self._active_section_id,
        ):
            if section["id"] == section_id:
                return section
        return {"id": section_id, "title": section_id, "fields": {}}

    def save(self) -> bool:
        if not self._template_name.strip():
            self.error_occurred.emit(
                "Nome obrigatório",
                "Informe um nome para o template antes de salvar.",
                "",
            )
            return False
        content = merge_template_content_defaults(self._content_defaults, self._global_defaults)
        try:
            self._repo.save_full_template(
                self._template_id,
                self._sections_config,
                content,
                self._template_name.strip(),
            )
        except Exception as exc:
            logger.exception("Erro ao salvar template")
            self.error_occurred.emit(
                "Erro ao salvar",
                "Não foi possível salvar o template.",
                str(exc),
            )
            return False
        self._saved_snapshot = self._current_snapshot()
        self._dirty = False
        self.dirty_changed.emit(False)
        self.saved.emit(self._template_id)
        return True

    def schedule_preview(self) -> None:
        self.preview_generating.emit(True)
        self._preview_timer.start()

    def _run_preview(self) -> None:
        document = build_template_preview_document(
            self._template_id,
            self._sections_config,
            merge_template_content_defaults(self._content_defaults, self._global_defaults),
        )
        self._preview_generation += 1
        generation = self._preview_generation
        worker = _PreviewWorker(generation, document, self._preview_service)
        worker.signals.finished.connect(self._on_preview_finished)
        worker.signals.failed.connect(self._on_preview_failed)
        QThreadPool.globalInstance().start(worker)

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
            "Preview indisponível",
            "Não foi possível gerar o preview do template.",
            details,
        )

    def _emit_sections_summary(self) -> None:
        sections = build_template_sections_summary(
            self._sections_config,
            merge_template_content_defaults(self._content_defaults, self._global_defaults),
            self._active_section_id,
        )
        self.sections_summary_ready.emit(sections)

    def _emit_global_fields(self) -> None:
        values: dict[str, str] = {}
        scalar = self._global_defaults.get("scalar", {})
        for field in GLOBAL_FIELDS:
            if field.key in {"client_project", "evaluated_component"}:
                values[field.key] = str(self._global_defaults.get(field.key, ""))
            elif field.dto_key:
                values[field.key] = str(scalar.get(field.dto_key, scalar.get(field.key, "")))
            else:
                values[field.key] = str(scalar.get(field.key, ""))
        if not values.get("client_project"):
            values["client_project"] = "Cliente Exemplo"
        if not values.get("evaluated_component"):
            values["evaluated_component"] = "Componente Exemplo"
        overridden = set(k for k, v in values.items() if v)
        self.global_fields_ready.emit(values, overridden)

    def _mark_dirty(self) -> None:
        dirty = self._current_snapshot() != self._saved_snapshot
        if dirty != self._dirty:
            self._dirty = dirty
            self.dirty_changed.emit(dirty)

    def _current_snapshot(self) -> dict:
        return {
            "name": self._template_name.strip(),
            "sections_config": copy.deepcopy(self._sections_config),
            "content_defaults": copy.deepcopy(
                merge_template_content_defaults(self._content_defaults, self._global_defaults)
            ),
        }

    @staticmethod
    def _config_from_sections(sections: list[dict]) -> dict:
        return {
            section["id"]: {"enabled": section["enabled"], "order": index}
            for index, section in enumerate(sections)
        }

    def _allocate_template_id(self) -> str:
        existing = {t["id"] for t in self._repo.list_templates()}
        index = 1
        while f"custom_{index}" in existing:
            index += 1
        return f"custom_{index}"

    def _allocate_custom_section_id(self) -> str:
        index = 1
        while f"custom_{index}" in self._sections_config:
            index += 1
        return f"custom_{index}"
