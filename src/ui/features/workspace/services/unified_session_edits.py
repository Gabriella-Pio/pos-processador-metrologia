"""Mutações de seções no modo PDF unificado (estado na ``ProjectSession``)."""
from __future__ import annotations

from src.core.application.template_media import (
    locked_workspace_media_kinds,
    sanitize_workspace_media_kinds,
)
from src.core.domain.field_definitions import CHART_SECTION_IDS
from src.core.domain.project_session import ProjectSession
from src.core.domain.ports import ReportDocument, TemplateRepository
from src.core.domain.section_schema import PROTECTED_SECTION_IDS, SECTION_TITLES


class UnifiedSessionEdits:
    """Operações sobre overrides/custom/extras unificados — sem Qt."""

    @staticmethod
    def update_section_override(session: ProjectSession, section_id: str, **fields) -> bool:
        overrides = dict(session.unified_section_overrides.get(section_id) or {})
        for key, value in fields.items():
            if value is None:
                overrides.pop(key, None)
            else:
                overrides[key] = value
        session.unified_section_overrides[section_id] = overrides
        return True

    @staticmethod
    def pop_override_keys(session: ProjectSession, section_id: str, *keys: str) -> bool:
        overrides = dict(session.unified_section_overrides.get(section_id) or {})
        for key in keys:
            overrides.pop(key, None)
        if overrides:
            session.unified_section_overrides[section_id] = overrides
        else:
            session.unified_section_overrides.pop(section_id, None)
        return True

    @staticmethod
    def clear_section_override(session: ProjectSession, section_id: str) -> bool:
        session.unified_section_overrides.pop(section_id, None)
        return True

    @staticmethod
    def delete_section(session: ProjectSession, section_id: str) -> bool:
        customs = [
            item for item in session.unified_custom_sections if item.get("id") != section_id
        ]
        if len(customs) == len(session.unified_custom_sections) and not section_id.startswith(
            "custom_"
        ):
            extras = [sid for sid in session.unified_extra_section_ids if sid != section_id]
            session.unified_extra_section_ids = extras
            deleted = list(session.unified_deleted_section_ids)
            if section_id not in deleted:
                deleted.append(section_id)
            session.unified_deleted_section_ids = deleted
        else:
            session.unified_custom_sections = customs
        session.unified_section_overrides.pop(section_id, None)
        return True

    @staticmethod
    def set_section_enabled(session: ProjectSession, section_id: str, enabled: bool) -> bool:
        if section_id in PROTECTED_SECTION_IDS:
            return False
        deleted = list(session.unified_deleted_section_ids)
        if enabled:
            if section_id in deleted:
                deleted.remove(section_id)
        elif section_id not in deleted:
            deleted.append(section_id)
        session.unified_deleted_section_ids = deleted
        return True

    @staticmethod
    def update_section_media_kinds(
        session: ProjectSession,
        section_id: str,
        kinds: list[str],
        *,
        template_repo: TemplateRepository | None,
        active_document: ReportDocument | None,
    ) -> bool:
        locked = (
            []
            if section_id in CHART_SECTION_IDS
            else locked_workspace_media_kinds(section_id, active_document, template_repo)
            if active_document
            else []
        )
        merged = sanitize_workspace_media_kinds(section_id, locked, kinds)
        overrides = dict(session.unified_section_overrides.get(section_id) or {})
        overrides["media_kinds"] = merged
        session.unified_section_overrides[section_id] = overrides
        return True

    @staticmethod
    def update_disabled_chart_ids(
        session: ProjectSession,
        section_id: str,
        disabled_ids: list[str],
    ) -> bool:
        overrides = dict(session.unified_section_overrides.get(section_id) or {})
        if disabled_ids:
            overrides["disabled_chart_ids"] = list(disabled_ids)
        else:
            overrides.pop("disabled_chart_ids", None)
        session.unified_section_overrides[section_id] = overrides
        return True

    @staticmethod
    def add_custom_section(session: ProjectSession, title: str) -> str | None:
        cleaned = (title or "").strip() or "Nova seção"
        customs = list(session.unified_custom_sections)
        next_index = len(customs) + 1
        section_id = f"custom_{next_index}"
        while any(item.get("id") == section_id for item in customs):
            next_index += 1
            section_id = f"custom_{next_index}"
        customs.append({"id": section_id, "title": cleaned, "custom": True})
        session.unified_custom_sections = customs
        session.unified_section_overrides[section_id] = {
            "media_kinds": ["photos", "tables", "graphics"],
            "title": cleaned,
        }
        session.unified_deleted_section_ids = [
            sid for sid in session.unified_deleted_section_ids if sid != section_id
        ]
        return section_id

    @staticmethod
    def add_catalog_section(session: ProjectSession, section_id: str) -> str | None:
        sid = (section_id or "").strip()
        if not sid or sid in PROTECTED_SECTION_IDS or sid not in SECTION_TITLES:
            return None
        extras = list(session.unified_extra_section_ids)
        if sid not in extras:
            extras.append(sid)
        session.unified_extra_section_ids = extras
        session.unified_deleted_section_ids = [
            item for item in session.unified_deleted_section_ids if item != sid
        ]
        return sid
