"""
Implementação real de ``TemplateRepository`` usando um arquivo JSON leve
em disco. Guarda estrutura (seções ativas/ordem) e defaults de conteúdo.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.core.domain.ports import TemplateRepository
from src.core.domain.template_ids import is_builtin_template_id

# Reexport para compatibilidade com imports antigos do infrastructure.
__all__ = ["JSONTemplateRepository", "is_builtin_template_id"]

_TEMPLATE_PADRAO = {
    "id": "default",
    "name": "Template Padrão SENAI/ZEISS",
    "is_default": True,
}


class JSONTemplateRepository(TemplateRepository):
    def __init__(self, storage_path: str = "output_pdfs/templates.json") -> None:
        self._path = Path(storage_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._salvar_estado({
                "templates": [_TEMPLATE_PADRAO],
                "configs": {},
                "content_defaults": {},
            })
        self.ensure_builtin_templates()

    def ensure_builtin_templates(self) -> None:
        """Garante templates oficiais de tomografia e análise de falha."""
        from src.core.domain.section_schema import (
            TEMPLATE_FALHA_SECTIONS_CONFIG,
            TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG,
        )
        from src.core.domain.tomo_template_defaults import TOMO_PROSE_DEFAULTS
        from src.core.domain.falha_template_defaults import FALHA_PROSE_DEFAULTS

        estado = self._carregar_estado()
        dirty = False
        templates = estado.setdefault("templates", [])
        if not any(t.get("id") == "tomografia" for t in templates):
            templates.append({
                "id": "tomografia",
                "name": "Template Tomografia SENAI/Bosello",
                "is_default": False,
            })
            dirty = True
        if not any(t.get("id") == "analise_falha" for t in templates):
            templates.append({
                "id": "analise_falha",
                "name": "Template Análise de Falha (óptico + tomografia)",
                "is_default": False,
            })
            dirty = True
        configs = estado.setdefault("configs", {})
        # Builtins: código é fonte da verdade (ordem/enabled). Evita JSON antigo travar layout.
        tomo_cfg = dict(TEMPLATE_TOMOGRAFIA_SECTIONS_CONFIG)
        falha_cfg = dict(TEMPLATE_FALHA_SECTIONS_CONFIG)
        if configs.get("tomografia") != tomo_cfg:
            configs["tomografia"] = tomo_cfg
            dirty = True
        if configs.get("analise_falha") != falha_cfg:
            configs["analise_falha"] = falha_cfg
            dirty = True
        content = estado.setdefault("content_defaults", {})
        if not content.get("tomografia"):
            content["tomografia"] = {sid: dict(vals) for sid, vals in TOMO_PROSE_DEFAULTS.items()}
            dirty = True
        if not content.get("analise_falha"):
            content["analise_falha"] = {
                sid: dict(vals) for sid, vals in FALHA_PROSE_DEFAULTS.items()
            }
            dirty = True
        if dirty:
            self._salvar_estado(estado)

    def list_templates(self) -> list[dict]:
        estado = self._carregar_estado()
        return estado["templates"]

    def save_template(self, template_id: str, sections_config: dict) -> None:
        estado = self._carregar_estado()
        estado.setdefault("configs", {})[template_id] = sections_config
        self._ensure_template_metadata(estado, template_id)
        self._salvar_estado(estado)

    def save_content_defaults(self, template_id: str, content: dict) -> None:
        estado = self._carregar_estado()
        estado.setdefault("content_defaults", {})[template_id] = content
        self._ensure_template_metadata(estado, template_id)
        self._salvar_estado(estado)

    def save_full_template(
        self,
        template_id: str,
        sections_config: dict,
        content_defaults: dict,
        name: str,
    ) -> None:
        estado = self._carregar_estado()
        estado.setdefault("configs", {})[template_id] = sections_config
        estado.setdefault("content_defaults", {})[template_id] = content_defaults
        self._ensure_template_metadata(estado, template_id, name=name)
        self._salvar_estado(estado)

    def get_template_config(self, template_id: str) -> dict:
        estado = self._carregar_estado()
        return estado.get("configs", {}).get(template_id, {})

    def get_content_defaults(self, template_id: str) -> dict:
        estado = self._carregar_estado()
        return estado.get("content_defaults", {}).get(template_id, {})

    def update_template_name(self, template_id: str, name: str) -> None:
        estado = self._carregar_estado()
        for template in estado["templates"]:
            if template["id"] == template_id:
                template["name"] = name
                break
        self._salvar_estado(estado)

    def delete_template(self, template_id: str) -> bool:
        if is_builtin_template_id(template_id):
            return False
        estado = self._carregar_estado()
        templates = estado.get("templates", [])
        remaining = [t for t in templates if t.get("id") != template_id]
        if len(remaining) == len(templates):
            return False
        estado["templates"] = remaining
        estado.get("configs", {}).pop(template_id, None)
        estado.get("content_defaults", {}).pop(template_id, None)
        self._salvar_estado(estado)
        return True

    def _ensure_template_metadata(
        self, estado: dict, template_id: str, name: str | None = None
    ) -> None:
        templates = estado.setdefault("templates", [])
        if not any(t["id"] == template_id for t in templates):
            templates.append({
                "id": template_id,
                "name": name or template_id,
                "is_default": False,
            })
        elif name:
            for template in templates:
                if template["id"] == template_id:
                    template["name"] = name
                    break

    def _carregar_estado(self) -> dict:
        with self._path.open("r", encoding="utf-8") as f:
            estado = json.load(f)
        estado.setdefault("content_defaults", {})
        return estado

    def _salvar_estado(self, estado: dict) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
