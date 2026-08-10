"""Flowable que registra a posição de uma foto no PDF para hit test na preview."""
from __future__ import annotations

from reportlab.platypus import Flowable


class AnchoredPhoto(Flowable):
    def __init__(
        self,
        inner,
        *,
        section_id: str,
        image_path: str,
        image_id: str = "",
        anchor_list: list[dict] | None = None,
    ) -> None:
        super().__init__()
        self._inner = inner
        self._section_id = section_id
        self._image_path = image_path
        self._image_id = image_id
        self._anchor_list = anchor_list
        self.width = getattr(inner, "drawWidth", getattr(inner, "width", 0))
        self.height = getattr(inner, "drawHeight", getattr(inner, "height", 0))

    def wrap(self, avail_width, avail_height):  # noqa: N802
        if hasattr(self._inner, "wrap"):
            return self._inner.wrap(avail_width, avail_height)
        return self.width, self.height

    def draw(self) -> None:
        canvas = self.canv
        x = getattr(canvas, "_x", 0)
        y = getattr(canvas, "_y", 0)
        if self._anchor_list is not None:
            self._anchor_list.append(
                {
                    "section_id": self._section_id,
                    "image_path": self._image_path,
                    "image_id": self._image_id,
                    "page": canvas.getPageNumber(),
                    "x": x,
                    "y": y,
                    "width": self.width,
                    "height": self.height,
                }
            )
        self._inner.drawOn(canvas, 0, 0)
