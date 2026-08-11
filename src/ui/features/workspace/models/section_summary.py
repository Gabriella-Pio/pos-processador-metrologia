"""Modelo tipado para itens do sumário de seções."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SectionSummaryItem:
    id: str
    display_title: str
    title: str
    has_overrides: bool
    section_number: int | None = None
    table_rows: list[dict[str, str]] | None = None
    fields: dict[str, str] = field(default_factory=dict)
    custom: bool = False
    subtitle: str = ""
    body: str = ""
    image_count: int = 0
    has_images: bool = False
    has_graphics: bool = False
    media_kinds: list[str] = field(default_factory=list)
    disabled_chart_ids: list[str] = field(default_factory=list)
    page_start: int | None = None
    anchor_rect: dict | None = None
    global_fields: list[dict[str, str]] = field(default_factory=list)
    override_keys: list[str] = field(default_factory=list)
    enabled: bool = True
    protected: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "display_title": self.display_title,
            "title": self.title,
            "has_overrides": self.has_overrides,
            "section_number": self.section_number,
            "table_rows": self.table_rows,
            "fields": self.fields,
            "custom": self.custom,
            "subtitle": self.subtitle,
            "body": self.body,
            "image_count": self.image_count,
            "has_images": self.has_images,
            "has_graphics": self.has_graphics,
            "media_kinds": list(self.media_kinds),
            "disabled_chart_ids": list(self.disabled_chart_ids),
            "page_start": self.page_start,
            "anchor_rect": self.anchor_rect,
            "global_fields": self.global_fields,
            "override_keys": self.override_keys,
            "enabled": self.enabled,
            "protected": self.protected,
        }
