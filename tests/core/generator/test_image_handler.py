"""Testes de tratamento de imagens no PDF."""
from __future__ import annotations

from pathlib import Path

from PIL import Image
from reportlab.platypus import Image as RLImage

from src.core.generator.components.image_handler import ReportImageHandler
from src.core.generator.styles import ReportStyles


def test_criar_elemento_foto_preserva_proporcao_sem_reprocessar(tmp_path: Path) -> None:
    image_path = tmp_path / "foto.png"
    Image.new("RGB", (400, 200), (30, 30, 30)).save(image_path)
    styles = ReportStyles.criar_estilos()

    elemento = ReportImageHandler.criar_elemento_foto(
        str(image_path),
        styles,
        largura=200,
        altura=150,
        preserve_original=True,
    )

    assert isinstance(elemento, RLImage)
    assert elemento.drawWidth == 200
    assert elemento.drawHeight == 100
