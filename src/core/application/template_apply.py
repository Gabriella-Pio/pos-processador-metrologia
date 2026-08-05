"""Aplica estrutura salva de template ao ReportDocument."""
from __future__ import annotations

from src.core.application.template_preview import split_template_content_defaults
from src.core.domain.ports import ReportDocument, TemplateRepository
from src.core.domain.section_schema import is_custom_section_id

_FIXED_SECTION_IDS = frozenset({"cabecalho", "historico_versoes", "anexos"})


def apply_template_layout(document: ReportDocument, template_repo: TemplateRepository | None) -> None:
    if template_repo is None:
        return
    config = template_repo.get_template_config(document.template_id) or {}
    document.custom_sections = [
        {
            "id": section_id,
            "title": cfg.get("title", section_id),
            "custom": True,
        }
        for section_id, cfg in config.items()
        if is_custom_section_id(section_id)
    ]
    ordered = sorted(
        (sid for sid in config if not sid.startswith("_")),
        key=lambda sid: config[sid].get("order", 999),
    )
    enabled = [
        sid for sid in ordered
        if config[sid].get("enabled", True) and sid not in _FIXED_SECTION_IDS
    ]
    disabled = [
        sid for sid in ordered
        if not config[sid].get("enabled", True) and sid not in _FIXED_SECTION_IDS
    ]
    document.section_order = enabled
    document.deleted_section_ids = disabled


def apply_template_content_defaults(document: ReportDocument, template_repo: TemplateRepository | None) -> None:
    if template_repo is None:
        return
    raw = template_repo.get_content_defaults(document.template_id) or {}
    section_defaults, global_defaults = split_template_content_defaults(raw)
    for section_id, defaults in section_defaults.items():
        if isinstance(defaults, dict):
            document.section_overrides[section_id] = dict(defaults)
    if global_defaults.get("client_project"):
        document.client_project = str(global_defaults["client_project"])
    if global_defaults.get("evaluated_component"):
        document.evaluated_component = str(global_defaults["evaluated_component"])
    scalar = global_defaults.get("scalar", {})
    if isinstance(scalar, dict) and scalar:
        document.parsed_overrides.setdefault("scalar", {}).update(scalar)
