"""
Implementação real de ``TemplateRepository`` usando um arquivo JSON leve
em disco, substituindo o ``SafeTemplateRepositoryStub`` temporário do
``main.py``. Guarda tanto a lista de templates disponíveis quanto a
configuração de seções (ativas/ordem) de cada um.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.core.ports import TemplateRepository

_TEMPLATE_PADRAO = {
    "id": "default",
    "name": "Template Padrão SENAI/ZEISS",
    "is_default": True,
}


class JSONTemplateRepository(TemplateRepository):
    """Persiste templates customizados em ``templates.json``.

    Estrutura do arquivo:
        {
          "templates": [{"id": ..., "name": ..., "is_default": ...}, ...],
          "configs": {"<template_id>": {"<section_id>": {"enabled": bool, "order": int}}}
        }
    """

    def __init__(self, storage_path: str = "output_pdfs/templates.json") -> None:
        self._path = Path(storage_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._salvar_estado({"templates": [_TEMPLATE_PADRAO], "configs": {}})

    def list_templates(self) -> list[dict]:
        estado = self._carregar_estado()
        return estado["templates"]

    def save_template(self, template_id: str, sections_config: dict) -> None:
        estado = self._carregar_estado()
        estado["configs"][template_id] = sections_config

        ja_existe = any(t["id"] == template_id for t in estado["templates"])
        if not ja_existe:
            estado["templates"].append({
                "id": template_id,
                "name": template_id,
                "is_default": False,
            })
        self._salvar_estado(estado)

    def get_template_config(self, template_id: str) -> dict:
        """Método auxiliar (fora da porta) usado pela ``TemplateView`` para
        recarregar a configuração salva de um template ao reabrir o modal.
        """
        estado = self._carregar_estado()
        return estado["configs"].get(template_id, {})

    def _carregar_estado(self) -> dict:
        with self._path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _salvar_estado(self, estado: dict) -> None:
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
