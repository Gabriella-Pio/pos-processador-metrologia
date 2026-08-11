"""Ordenação estável de peças/PDFs em projetos em lote."""
from __future__ import annotations

import re
from pathlib import Path

from src.core.domain.project_session import ProjectDocumentSlot, ProjectSession

_TRAILING_NUM = re.compile(r"(\d+)(?!.*\d)")


def extract_piece_number_from_name(name: str) -> int | None:
    """Extrai o último número do nome (ex.: ``CARCACA DE BOMBA 8.pdf`` → 8)."""
    stem = Path(name).stem if name else ""
    match = _TRAILING_NUM.search(stem)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def natural_pdf_sort_key(path: Path) -> tuple:
    """Chave de ordenação: número da peça no nome, depois nome."""
    number = extract_piece_number_from_name(path.name if path else "")
    name = (path.name if path else "").lower()
    if number is not None:
        return (0, number, name)
    return (1, 0, name)


def sort_pdf_entries(entries: list[tuple[Path, str]]) -> list[tuple[Path, str]]:
    return sorted(entries, key=lambda entry: natural_pdf_sort_key(entry[0]))


def sort_paths(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=natural_pdf_sort_key)


def sort_session_documents(session: ProjectSession) -> bool:
    """Reordena ``session.documents`` por número natural do arquivo.

    Preserva o documento ativo (por caminho). Retorna True se a ordem mudou.
    """
    if len(session.documents) < 2:
        return False

    active = session.active_slot
    active_key = str(active.source_pdf_path) if active is not None else ""
    before = [str(slot.source_pdf_path) for slot in session.documents]
    session.documents.sort(key=lambda slot: natural_pdf_sort_key(slot.source_pdf_path))
    after = [str(slot.source_pdf_path) for slot in session.documents]
    if before == after:
        return False

    if active_key:
        for index, slot in enumerate(session.documents):
            if str(slot.source_pdf_path) == active_key:
                session.active_index = index
                break
    else:
        session.active_index = min(session.active_index, len(session.documents) - 1)
    return True


def piece_label_for_slot(slot: ProjectDocumentSlot, index: int) -> str:
    """Rótulo curto para tabelas (Peça N), preferindo número do arquivo."""
    number = extract_piece_number_from_name(slot.source_pdf_path.name)
    if number is not None:
        return str(number)
    return str(index)
