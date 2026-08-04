from abc import ABC, abstractmethod

from reportlab.platypus import Paragraph

class BaseSection(ABC):
    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    def render(self, story: list, styles: dict, dados_parseados, contexto_extra: dict):
        """Método polimórfico obrigatório para injetar elementos no PDF."""
        pass


class SectionTitleParagraph(Paragraph):
    """Título de seção que registra a página e a caixa desenhada.

    Isso permite mapear o clique do sumário para a posição exata do título
    no preview renderizado, sem alterar o layout do PDF.
    """

    def __init__(self, text: str, style, section_id: str, anchor_map: dict | None = None):
        super().__init__(text, style)
        self._section_id = section_id
        self._anchor_map = anchor_map

    def drawOn(self, canvas, x, y, _sW=0):  # noqa: N802
        self._anchor_x = x
        self._anchor_y = y
        self._anchor_width = self.width
        self._anchor_height = self.height
        self._anchor_text = getattr(self, "text", "")
        if self._anchor_map is not None:
            self._anchor_map[self._section_id] = {
                "page": canvas.getPageNumber(),
                "x": x,
                "y": y,
                "width": self.width,
                "height": self.height,
                "text": self._anchor_text,
            }
        return super().drawOn(canvas, x, y, _sW)


def anchored_section_title(text: str, style, section_id: str, anchor_map: dict | None = None):
    return SectionTitleParagraph(text, style, section_id, anchor_map)