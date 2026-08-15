"""Testes de mutações unificadas na ProjectSession."""
from __future__ import annotations

from src.core.domain.project_session import ProjectSession
from src.ui.features.workspace.services.unified_session_edits import UnifiedSessionEdits


def test_update_and_clear_section_override() -> None:
    session = ProjectSession(client_project="C")
    assert UnifiedSessionEdits.update_section_override(
        session, "introducao", title="X", body="Y"
    )
    assert session.unified_section_overrides["introducao"]["title"] == "X"
    UnifiedSessionEdits.pop_override_keys(session, "introducao", "title")
    assert "title" not in session.unified_section_overrides["introducao"]
    UnifiedSessionEdits.clear_section_override(session, "introducao")
    assert "introducao" not in session.unified_section_overrides


def test_add_custom_and_catalog_sections() -> None:
    session = ProjectSession(client_project="C")
    custom_id = UnifiedSessionEdits.add_custom_section(session, "Minha seção")
    assert custom_id and custom_id.startswith("custom_")
    assert any(item["id"] == custom_id for item in session.unified_custom_sections)

    added = UnifiedSessionEdits.add_catalog_section(session, "estat_resumo_diametros")
    assert added == "estat_resumo_diametros"
    assert "estat_resumo_diametros" in session.unified_extra_section_ids


def test_delete_catalog_extra_marks_deleted() -> None:
    session = ProjectSession(client_project="C")
    UnifiedSessionEdits.add_catalog_section(session, "estat_resumo_diametros")
    UnifiedSessionEdits.delete_section(session, "estat_resumo_diametros")
    assert "estat_resumo_diametros" not in session.unified_extra_section_ids
    assert "estat_resumo_diametros" in session.unified_deleted_section_ids


def test_set_section_enabled_toggles_deleted() -> None:
    session = ProjectSession(client_project="C")
    assert UnifiedSessionEdits.set_section_enabled(session, "grafica", False)
    assert "grafica" in session.unified_deleted_section_ids
    UnifiedSessionEdits.set_section_enabled(session, "grafica", True)
    assert "grafica" not in session.unified_deleted_section_ids
