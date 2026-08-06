"""Fixtures compartilhadas para a suíte pytest."""
from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent
INPUT_PDFS_DIR = PROJECT_ROOT / "input_pdfs"


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "historico.db"


@pytest.fixture
def insp_ect_fixture() -> Path:
    return TESTS_DIR / "fixtures" / "insp_ect_peca_uf.pdf"


@pytest.fixture
def insp_ect_fixture_exists(insp_ect_fixture: Path) -> bool:
    return insp_ect_fixture.is_file()


@pytest.fixture
def calypso_sample_pdfs() -> list[Path]:
    """PDFs CALYPSO de exemplo em ``input_pdfs/`` (podem estar ausentes no CI)."""
    names = [
        "pistao de trabalho 1.pdf",
        "global peca pintada.pdf",
        "CARCACA DE BOMBA 8.pdf",
        "pistao do produto 2.pdf",
    ]
    return [INPUT_PDFS_DIR / name for name in names]


@pytest.fixture
def calypso_sample_pdf(calypso_sample_pdfs: list[Path]) -> Path:
    """Primeiro PDF CALYPSO disponível; pula o teste se nenhum existir."""
    for path in calypso_sample_pdfs:
        if path.is_file():
            return path
    pytest.skip("Nenhum PDF CALYPSO em input_pdfs/")


@pytest.fixture
def require_insp_ect_fixture(insp_ect_fixture: Path) -> Path:
    if not insp_ect_fixture.is_file():
        pytest.skip("fixture INSP ECT ausente")
    return insp_ect_fixture
