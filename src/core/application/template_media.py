"""Baseline de mídia por seção a partir do template ou do catálogo."""
from __future__ import annotations

from src.core.application.template_preview import split_template_content_defaults
from src.core.domain.field_definitions import CHART_SECTION_IDS, get_media_blocks
from src.core.domain.ports import ReportDocument, TemplateRepository
from src.core.domain.section_schema import is_custom_section_id
from src.core.domain.table_row_registry import TABLE_SECTIONS

_MEDIA_LABELS = frozenset({"photos", "graphics", "tables"})
_ADDABLE_KINDS = ("photos", "graphics", "tables")


def template_baseline_media_kinds(
    section_id: str,
    template_id: str,
    template_repo: TemplateRepository | None,
) -> list[str]:
    """Tipos de mídia definidos pelo template ou pelos defaults da seção."""
    if section_id in CHART_SECTION_IDS:
        return [block.kind for block in get_media_blocks(section_id)]
    if template_repo is not None:
        raw = template_repo.get_content_defaults(template_id) or {}
        section_defaults, _global = split_template_content_defaults(raw)
        stored = section_defaults.get(section_id, {})
        if isinstance(stored, dict) and isinstance(stored.get("media_kinds"), list):
            kinds = [k for k in stored["media_kinds"] if k in _MEDIA_LABELS]
            if kinds:
                return kinds
    return [block.kind for block in get_media_blocks(section_id)]


def locked_workspace_media_kinds(
    section_id: str,
    document: ReportDocument,
    template_repo: TemplateRepository | None,
) -> list[str]:
    """No workspace, o usuário só pode acrescentar mídia — não remover a do template."""
    if section_id in CHART_SECTION_IDS:
        return []
    if is_custom_section_id(section_id):
        return []
    return template_baseline_media_kinds(section_id, document.template_id, template_repo)


def merge_workspace_media_kinds(locked: list[str], selected: list[str]) -> list[str]:
    order = ("photos", "graphics", "tables")
    merged = sorted(set(locked) | set(selected), key=lambda k: order.index(k) if k in order else 99)
    return [k for k in merged if k in _MEDIA_LABELS]


def workspace_addable_media_kinds(section_id: str) -> list[str]:
    """Tipos que o usuário pode acrescentar no workspace (não remover os do template)."""
    if section_id in CHART_SECTION_IDS:
        if section_id == "grafica":
            return ["photos", "graphics"]
        return ["graphics"]
    if is_custom_section_id(section_id):
        return list(_ADDABLE_KINDS)
    addable = ["photos", "graphics"]
    if section_id in TABLE_SECTIONS:
        addable.append("tables")
    return addable


def sanitize_workspace_media_kinds(
    section_id: str,
    locked: list[str],
    selected: list[str],
) -> list[str]:
    """Garante que só permaneçam tipos permitidos para a seção."""
    merged = merge_workspace_media_kinds(locked, selected)
    allowed = set(locked) | set(workspace_addable_media_kinds(section_id))
    return [kind for kind in merged if kind in allowed]
