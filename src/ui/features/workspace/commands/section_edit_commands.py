"""Comandos de edição de seções e campos do documento."""
from __future__ import annotations

from src.core.application.document_editing import sync_measured_by
from src.core.domain.ports import ReportDocument, TechnicalControlInfo
from src.core.domain.section_schema import PROTECTED_SECTION_IDS


class SectionEditCommands:
    @staticmethod
    def update_section_field(
        document: ReportDocument,
        section_id: str,
        field: str,
        value: str,
    ) -> None:
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

    @staticmethod
    def restore_section_block(
        document: ReportDocument,
        section_id: str,
        title_key: str,
        body_key: str,
    ) -> None:
        section_ov = document.section_overrides.get(section_id, {})
        section_ov.pop(title_key, None)
        if body_key:
            section_ov.pop(body_key, None)

    @staticmethod
    def restore_section(document: ReportDocument, section_id: str) -> None:
        document.section_overrides.pop(section_id, None)

    @staticmethod
    def restore_section_field(document: ReportDocument, section_id: str, field: str) -> None:
        from src.core.domain.report_field_registry import INTRODUCAO_BODY_TITLE_KEYS

        section_ov = document.section_overrides.get(section_id, {})
        section_ov.pop(field, None)
        title_key = INTRODUCAO_BODY_TITLE_KEYS.get(field)
        if title_key:
            section_ov.pop(title_key, None)
        else:
            for body_key, paired_title in INTRODUCAO_BODY_TITLE_KEYS.items():
                if field == paired_title:
                    section_ov.pop(body_key, None)
                    break

    @staticmethod
    def update_section_table_rows(
        document: ReportDocument,
        section_id: str,
        rows: list[dict[str, str]],
    ) -> None:
        document.section_overrides.setdefault(section_id, {})["table_rows"] = rows
        if section_id == "controle_tecnico":
            SectionEditCommands._sync_control_info_from_table_rows(document, rows)

    @staticmethod
    def restore_section_table_rows(document: ReportDocument, section_id: str) -> None:
        document.section_overrides.get(section_id, {}).pop("table_rows", None)

    @staticmethod
    def update_disabled_chart_ids(
        document: ReportDocument,
        section_id: str,
        disabled_ids: list[str],
    ) -> None:
        section = document.section_overrides.setdefault(section_id, {})
        if disabled_ids:
            section["disabled_chart_ids"] = list(disabled_ids)
        else:
            section.pop("disabled_chart_ids", None)

    @staticmethod
    def update_section_media_kinds(
        document: ReportDocument,
        section_id: str,
        kinds: list[str],
    ) -> None:
        document.section_overrides.setdefault(section_id, {})["media_kinds"] = list(kinds)

    @staticmethod
    def set_section_enabled(document: ReportDocument, section_id: str, enabled: bool) -> None:
        if section_id in PROTECTED_SECTION_IDS:
            return
        if enabled:
            if section_id in document.deleted_section_ids:
                document.deleted_section_ids.remove(section_id)
        elif section_id not in document.deleted_section_ids:
            document.deleted_section_ids.append(section_id)

    @staticmethod
    def ensure_fixed_sections_enabled(document: ReportDocument) -> None:
        if not document.deleted_section_ids:
            return
        document.deleted_section_ids = [
            sid for sid in document.deleted_section_ids if sid not in PROTECTED_SECTION_IDS
        ]

    @staticmethod
    def delete_section(document: ReportDocument, section_id: str) -> bool:
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
        return True

    @staticmethod
    def add_custom_section(document: ReportDocument, title: str) -> str | None:
        if not title.strip():
            return None
        next_index = len(document.custom_sections) + 1
        section_id = f"custom_{next_index}"
        while any(s.get("id") == section_id for s in document.custom_sections):
            next_index += 1
            section_id = f"custom_{next_index}"
        document.custom_sections.append({"id": section_id, "title": title.strip(), "custom": True})
        document.section_overrides.setdefault(section_id, {})["media_kinds"] = ["photos", "tables", "graphics"]
        document.section_overrides[section_id].setdefault("title", title.strip())
        return section_id

    @staticmethod
    def _sync_control_info_from_table_rows(
        document: ReportDocument,
        rows: list[dict[str, str]],
    ) -> None:
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
