"""Testes dos templates de prosa e blocos da introdução."""
from __future__ import annotations

from src.core.domain.prose_templates import (
    INTRODUCAO_BODY_TITLE_KEYS,
    INTRODUCAO_CONTENT_BLOCKS,
    INTRODUCAO_HEADER_ONLY_BLOCKS,
    PROSE_TEMPLATES,
)


def test_prose_templates_cover_key_sections() -> None:
    for section_id in ("introducao", "resultados", "conclusao", "anexos"):
        assert section_id in PROSE_TEMPLATES
        assert PROSE_TEMPLATES[section_id]


def test_introducao_content_blocks_have_title_and_body_keys() -> None:
    for block in INTRODUCAO_CONTENT_BLOCKS:
        assert block.title_key.startswith("title_")
        assert block.body_key
        assert block.label


def test_introducao_body_title_keys_maps_body_to_title() -> None:
    for block in INTRODUCAO_CONTENT_BLOCKS:
        if block.body_key:
            assert INTRODUCAO_BODY_TITLE_KEYS[block.body_key] == block.title_key


def test_introducao_header_only_blocks_use_value_keys() -> None:
    prose = PROSE_TEMPLATES["introducao"]
    for block in INTRODUCAO_HEADER_ONLY_BLOCKS:
        assert block.body_key in prose


def test_conclusao_has_approval_texts() -> None:
    conclusao = PROSE_TEMPLATES["conclusao"]
    assert conclusao["texto_aprovado"]
    assert conclusao["texto_reprovado"]
