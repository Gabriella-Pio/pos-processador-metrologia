"""Testes do repositório de templates."""
from __future__ import annotations

from src.core.infrastructure.template_repository import JSONTemplateRepository, is_builtin_template_id


def test_is_builtin_template_id() -> None:
    assert is_builtin_template_id("default")
    assert is_builtin_template_id("tomografia")
    assert not is_builtin_template_id("custom_lab")


def test_delete_template_removes_custom_entry(tmp_path) -> None:
    repo = JSONTemplateRepository(storage_path=str(tmp_path / "templates.json"))
    repo.save_full_template(
        "custom_lab",
        {"introducao": {"enabled": True, "order": 0}},
        {"introducao": {"objetivo": "Texto"}},
        "Template Lab",
    )
    assert repo.delete_template("custom_lab")
    ids = {item["id"] for item in repo.list_templates()}
    assert "custom_lab" not in ids
    assert repo.get_template_config("custom_lab") == {}
    assert repo.get_content_defaults("custom_lab") == {}


def test_delete_template_protects_builtins(tmp_path) -> None:
    repo = JSONTemplateRepository(storage_path=str(tmp_path / "templates.json"))
    assert not repo.delete_template("default")
    assert not repo.delete_template("tomografia")
    ids = {item["id"] for item in repo.list_templates()}
    assert "default" in ids
    assert "tomografia" in ids


def test_delete_template_returns_false_for_missing(tmp_path) -> None:
    repo = JSONTemplateRepository(storage_path=str(tmp_path / "templates.json"))
    assert not repo.delete_template("nao_existe")
