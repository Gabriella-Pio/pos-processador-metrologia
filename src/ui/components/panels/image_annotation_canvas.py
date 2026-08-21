"""Canvas interativo para crop, zoom e marcações em fotos."""
from __future__ import annotations

import math

from PyQt6.QtCore import QPointF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QKeyEvent,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
    QWheelEvent,
)
from PyQt6.QtWidgets import QSizePolicy, QWidget

from src.core.application.annotation_clipboard import copy_from_image, take_clipboard_copy
from src.core.domain.ports import Annotation, ImageCrop, ReportImage
from src.ui.components.feedback import prompt_text
from src.ui.styles import PALETTE


class ImageAnnotationCanvas(QWidget):
    edits_changed = pyqtSignal(object)
    zoom_changed = pyqtSignal(float)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("ImageAnnotationCanvas")
        self.setMinimumHeight(320)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._image: ReportImage | None = None
        self._pixmap = QPixmap()
        self._tool: str | None = None
        self._zoom = 1.0
        self._drag_start: QPointF | None = None
        self._drag_current: QPointF | None = None
        self._number_counter = 1
        self._selected_index: int | None = None
        self._moving = False
        self._move_origin: tuple[float, float] | None = None
        self._annotation_origin: Annotation | None = None

    def set_image(self, image: ReportImage | None) -> None:
        self._image = image
        self._drag_start = None
        self._drag_current = None
        self._selected_index = None
        self._moving = False
        self._pixmap = QPixmap()
        if image is not None and image.image_path.is_file():
            self._pixmap = QPixmap(str(image.image_path))
        self._number_counter = self._next_number_index(image)
        self._zoom = 1.0
        self._emit_zoom_changed()
        self.update()

    def set_tool(self, tool_id: str | None) -> None:
        self._tool = tool_id or None
        self._drag_start = None
        self._drag_current = None
        self._moving = False
        self.update()

    def zoom_in(self) -> None:
        self._zoom = min(4.0, self._zoom * 1.2)
        self._emit_zoom_changed()
        self.update()

    def zoom_out(self) -> None:
        self._zoom = max(0.35, self._zoom / 1.2)
        self._emit_zoom_changed()
        self.update()

    def reset_zoom(self) -> None:
        self._zoom = 1.0
        self._emit_zoom_changed()
        self.update()

    def current_zoom(self) -> float:
        return self._zoom

    def _emit_zoom_changed(self) -> None:
        self.zoom_changed.emit(self._zoom)

    def undo_last(self) -> None:
        if self._image is None or not self._image.annotations:
            return
        self._image.annotations.pop()
        self._selected_index = None
        self._emit_edits()

    def clear_crop(self) -> None:
        if self._image is None:
            return
        self._image.crop = None
        self._emit_edits()

    def copy_annotations(self) -> None:
        if self._image is None:
            return
        copy_from_image(self._image.annotations, self._image.crop)

    def paste_annotations(self) -> None:
        if self._image is None:
            return
        payload = take_clipboard_copy()
        if payload is None:
            return
        self._image.annotations = list(payload.annotations)
        self._image.crop = payload.crop
        self._selected_index = None
        self._emit_edits()

    def delete_selected(self) -> None:
        if self._image is None or self._selected_index is None:
            return
        if 0 <= self._selected_index < len(self._image.annotations):
            self._image.annotations.pop(self._selected_index)
            self._selected_index = None
            self._emit_edits()

    def _emit_edits(self) -> None:
        if self._image is not None:
            self.edits_changed.emit(self._image)
        self.update()

    @staticmethod
    def _next_number_index(image: ReportImage | None) -> int:
        if image is None:
            return 1
        numbers = [
            int(item.text)
            for item in image.annotations
            if item.kind == "number" and str(item.text).isdigit()
        ]
        return max(numbers, default=0) + 1

    def _image_draw_rect(self) -> tuple[float, float, float, float]:
        if self._pixmap.isNull():
            return 0.0, 0.0, 0.0, 0.0
        available_w = max(1.0, float(self.width() - 16))
        available_h = max(1.0, float(self.height() - 16))
        base_scale = min(available_w / self._pixmap.width(), available_h / self._pixmap.height())
        scale = base_scale * self._zoom
        draw_w = self._pixmap.width() * scale
        draw_h = self._pixmap.height() * scale
        x = (self.width() - draw_w) / 2
        y = (self.height() - draw_h) / 2
        return x, y, draw_w, draw_h

    def _widget_to_normalized(self, point: QPointF) -> tuple[float, float] | None:
        if self._pixmap.isNull():
            return None
        x, y, draw_w, draw_h = self._image_draw_rect()
        if draw_w <= 0 or draw_h <= 0:
            return None
        local_x = point.x() - x
        local_y = point.y() - y
        if local_x < 0 or local_y < 0 or local_x > draw_w or local_y > draw_h:
            return None
        return local_x / draw_w, local_y / draw_h

    def _normalized_rect(self, start: QPointF, end: QPointF) -> tuple[float, float, float, float]:
        p0 = self._widget_to_normalized(start)
        p1 = self._widget_to_normalized(end)
        if p0 is None or p1 is None:
            return 0.0, 0.0, 0.0, 0.0
        x0, y0 = p0
        x1, y1 = p1
        left = max(0.0, min(x0, x1))
        top = max(0.0, min(y0, y1))
        width = min(1.0, abs(x1 - x0))
        height = min(1.0, abs(y1 - y0))
        return left, top, width, height

    def _prompt_text(self, title: str, label: str, default: str = "") -> str | None:
        return prompt_text(self, title, label, default=default)

    def _annotation_index_at(self, norm: tuple[float, float]) -> int | None:
        if self._image is None:
            return None
        for index in range(len(self._image.annotations) - 1, -1, -1):
            if self._hit_annotation(self._image.annotations[index], norm):
                return index
        return None

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setClipRect(self.rect())
        painter.fillRect(self.rect(), QColor(PALETTE.bg_surface_alt))

        if self._pixmap.isNull():
            painter.setPen(QColor(PALETTE.text_muted))
            painter.drawText(
                self.rect(),
                int(Qt.AlignmentFlag.AlignCenter),
                "Selecione uma foto à esquerda.\nAtalhos: S/C/T/N · Del apaga · Ctrl+C/V copia/cola",
            )
            return

        x, y, draw_w, draw_h = self._image_draw_rect()
        painter.drawPixmap(int(x), int(y), int(draw_w), int(draw_h), self._pixmap)

        if self._image and self._image.crop is not None:
            crop = self._image.crop
            cx = x + crop.x * draw_w
            cy = y + crop.y * draw_h
            cw = crop.width * draw_w
            ch = crop.height * draw_h
            dim = QColor(0, 0, 0, 110)
            painter.fillRect(int(x), int(y), int(draw_w), int(cy - y), dim)
            painter.fillRect(int(x), int(cy + ch), int(draw_w), int(y + draw_h - (cy + ch)), dim)
            painter.fillRect(int(x), int(cy), int(cx - x), int(ch), dim)
            painter.fillRect(int(cx + cw), int(cy), int(x + draw_w - (cx + cw)), int(ch), dim)
            painter.setPen(QPen(QColor(PALETTE.senai_orange), 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(int(cx), int(cy), int(cw), int(ch))

        if self._image:
            for index, annotation in enumerate(self._image.annotations):
                selected = index == self._selected_index
                self._paint_annotation(painter, annotation, x, y, draw_w, draw_h, selected=selected)

        if self._drag_start is not None and self._drag_current is not None and not self._moving:
            color = QColor(PALETTE.senai_orange if self._tool == "crop" else PALETTE.senai_blue_light)
            painter.setPen(QPen(color, 2, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            if self._tool == "arrow":
                self._draw_arrow(
                    painter,
                    self._drag_start.x(),
                    self._drag_start.y(),
                    self._drag_current.x(),
                    self._drag_current.y(),
                    QPen(color, 2, Qt.PenStyle.DashLine),
                )
            elif self._tool == "circle":
                painter.drawEllipse(
                    int(min(self._drag_start.x(), self._drag_current.x())),
                    int(min(self._drag_start.y(), self._drag_current.y())),
                    int(abs(self._drag_current.x() - self._drag_start.x())),
                    int(abs(self._drag_current.y() - self._drag_start.y())),
                )
            elif self._tool in {"text_box", "crop"}:
                left, top, width, height = self._normalized_rect(self._drag_start, self._drag_current)
                painter.drawRect(
                    int(x + left * draw_w),
                    int(y + top * draw_h),
                    int(width * draw_w),
                    int(height * draw_h),
                )

    def _paint_annotation(
        self,
        painter: QPainter,
        annotation: Annotation,
        x: float,
        y: float,
        draw_w: float,
        draw_h: float,
        *,
        selected: bool = False,
    ) -> None:
        color = QColor(annotation.color or PALETTE.senai_orange)
        if selected:
            color = QColor(PALETTE.senai_blue_light)
        pen = QPen(color, 3 if selected else 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        ax = x + annotation.x * draw_w
        ay = y + annotation.y * draw_h
        aw = annotation.width * draw_w
        ah = annotation.height * draw_h
        if annotation.kind == "arrow":
            self._draw_arrow(painter, ax, ay, ax + aw, ay + ah, pen)
        elif annotation.kind == "circle":
            painter.drawEllipse(int(ax), int(ay), int(max(aw, 8)), int(max(ah, 8)))
        elif annotation.kind == "text_box":
            box_w = int(max(aw, 64))
            box_h = int(max(ah, 28))
            painter.setPen(QPen(color, 2))
            painter.setBrush(QBrush(QColor(255, 255, 255, 235)))
            painter.drawRect(int(ax), int(ay), box_w, box_h)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            font = QFont()
            font.setBold(True)
            font.setPointSize(max(11, int(min(box_w, box_h) * 0.38)))
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text = annotation.text or "Texto"
            text_w = metrics.horizontalAdvance(text)
            text_h = metrics.height()
            text_x = int(ax + max(6, (box_w - text_w) / 2))
            text_y = int(ay + (box_h + text_h) / 2 - 2)
            painter.setPen(QColor("#1A1A1A"))
            painter.drawText(text_x, text_y, text)
        elif annotation.kind == "number":
            self._draw_number_marker(
                painter,
                ax,
                ay,
                annotation.text or "1",
                color,
                draw_w=draw_w,
                draw_h=draw_h,
            )

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        key = event.key()
        mods = event.modifiers()
        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_C:
            self.copy_annotations()
            event.accept()
            return
        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_V:
            self.paste_annotations()
            event.accept()
            return
        if mods & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Z:
            self.undo_last()
            event.accept()
            return
        if key in {Qt.Key.Key_Delete, Qt.Key.Key_Backspace}:
            self.delete_selected()
            event.accept()
            return
        if key == Qt.Key.Key_Escape:
            self._selected_index = None
            self.set_tool(None)
            self.update()
            event.accept()
            return
        tool_keys = {
            Qt.Key.Key_S: "arrow",
            Qt.Key.Key_C: "circle",
            Qt.Key.Key_T: "text_box",
            Qt.Key.Key_N: "number",
        }
        if key in tool_keys and not (mods & Qt.KeyboardModifier.ControlModifier):
            self.set_tool(tool_keys[key])
            event.accept()
            return
        super().keyPressEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._image is None:
            return
        norm = self._widget_to_normalized(event.position())
        if norm is None:
            return
        index = self._annotation_index_at(norm)
        if index is None:
            return
        annotation = self._image.annotations[index]
        if annotation.kind == "text_box":
            text = self._prompt_text("Texto na foto", "Conteúdo:", annotation.text)
            if text is not None:
                annotation.text = text
                self._emit_edits()
        elif annotation.kind == "number":
            legend = self._prompt_text(
                "Legenda do marcador",
                f"Descrição do marcador {annotation.text}:",
                annotation.legend,
            )
            if legend is not None:
                annotation.legend = legend
                self._emit_edits()

    def _hit_annotation(self, annotation: Annotation, norm: tuple[float, float]) -> bool:
        nx, ny = norm
        if annotation.kind == "number":
            dx = nx - annotation.x
            dy = ny - annotation.y
            return (dx * dx + dy * dy) ** 0.5 < 0.05
        x2 = annotation.x + max(abs(annotation.width), 0.02)
        y2 = annotation.y + max(abs(annotation.height), 0.02)
        left = min(annotation.x, x2)
        top = min(annotation.y, y2)
        right = max(annotation.x, x2)
        bottom = max(annotation.y, y2)
        return left <= nx <= right and top <= ny <= bottom

    @staticmethod
    def _draw_arrow(
        painter: QPainter,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        pen: QPen,
    ) -> None:
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(int(x0), int(y0), int(x1), int(y1))
        angle = math.atan2(y1 - y0, x1 - x0)
        head_len = max(12.0, pen.widthF() * 5.0)
        wing = math.pi / 6
        tip = QPointF(x1, y1)
        left = QPointF(
            x1 - head_len * math.cos(angle - wing),
            y1 - head_len * math.sin(angle - wing),
        )
        right = QPointF(
            x1 - head_len * math.cos(angle + wing),
            y1 - head_len * math.sin(angle + wing),
        )
        painter.setBrush(QBrush(pen.color()))
        painter.drawPolygon(QPolygonF([tip, left, right]))
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _marker_radius(self, draw_w: float, draw_h: float) -> int:
        return max(12, int(min(draw_w, draw_h) * 0.02))

    def _draw_outlined_text(
        self,
        painter: QPainter,
        x: float,
        y: float,
        text: str,
        *,
        fill: QColor,
        outline: QColor,
    ) -> None:
        for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)):
            painter.setPen(QPen(outline, 2))
            painter.drawText(int(x + dx), int(y + dy), text)
        painter.setPen(fill)
        painter.drawText(int(x), int(y), text)

    def _draw_number_marker(
        self,
        painter: QPainter,
        ax: float,
        ay: float,
        label: str,
        color: QColor,
        *,
        draw_w: float,
        draw_h: float,
    ) -> None:
        radius = self._marker_radius(draw_w, draw_h)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 2))
        painter.drawEllipse(int(ax - radius), int(ay - radius), radius * 2, radius * 2)
        font = QFont()
        font.setBold(True)
        font.setPointSize(max(9, int(radius * 0.85)))
        painter.setFont(font)
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(label)
        text_h = metrics.height()
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(int(ax - text_w / 2), int(ay + text_h / 4), label)
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._image is None or event.button() != Qt.MouseButton.LeftButton:
            return
        point = event.position()
        norm = self._widget_to_normalized(point)
        if norm is None:
            return
        self.setFocus()

        if self._tool in (None, ""):
            index = self._annotation_index_at(norm)
            self._selected_index = index
            if index is not None:
                self._moving = True
                self._drag_start = point
                self._move_origin = norm
                self._annotation_origin = self._image.annotations[index]
            self.update()
            return

        if self._tool == "number":
            label = str(self._number_counter)
            legend = self._prompt_text(
                "Marcador numerado",
                f"Descrição do marcador {label}:",
            )
            if legend is None:
                return
            self._image.annotations.append(
                Annotation(kind="number", x=norm[0], y=norm[1], text=label, legend=legend)
            )
            self._number_counter += 1
            self._emit_edits()
            return

        self._drag_start = point
        self._drag_current = point

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._moving and self._annotation_origin is not None and self._move_origin is not None:
            norm = self._widget_to_normalized(event.position())
            if norm is None:
                return
            dx = norm[0] - self._move_origin[0]
            dy = norm[1] - self._move_origin[1]
            self._annotation_origin.x = max(0.0, min(1.0, self._annotation_origin.x + dx))
            self._annotation_origin.y = max(0.0, min(1.0, self._annotation_origin.y + dy))
            self._move_origin = norm
            self.update()
            return
        if self._drag_start is None:
            return
        self._drag_current = event.position()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        if self._moving:
            self._moving = False
            self._move_origin = None
            self._annotation_origin = None
            self._drag_start = None
            self._emit_edits()
            return
        if self._image is None or self._drag_start is None or not self._tool:
            return
        end = event.position()
        left, top, width, height = self._normalized_rect(self._drag_start, end)
        if width < 0.01 and height < 0.01 and self._tool != "arrow":
            self._drag_start = None
            self._drag_current = None
            self.update()
            return

        if self._tool == "crop":
            if width >= 0.02 and height >= 0.02:
                self._image.crop = ImageCrop(x=left, y=top, width=width, height=height)
                self._emit_edits()
        elif self._tool == "arrow":
            start_norm = self._widget_to_normalized(self._drag_start)
            end_norm = self._widget_to_normalized(end)
            if start_norm and end_norm:
                self._image.annotations.append(
                    Annotation(
                        kind="arrow",
                        x=start_norm[0],
                        y=start_norm[1],
                        width=end_norm[0] - start_norm[0],
                        height=end_norm[1] - start_norm[1],
                    )
                )
                self._emit_edits()
        elif self._tool == "circle":
            if width >= 0.01 and height >= 0.01:
                self._image.annotations.append(
                    Annotation(kind="circle", x=left, y=top, width=width, height=height)
                )
                self._emit_edits()
        elif self._tool == "text_box":
            if width >= 0.02 and height >= 0.01:
                text = self._prompt_text("Texto na foto", "Conteúdo:")
                if text is None:
                    self._drag_start = None
                    self._drag_current = None
                    self.update()
                    return
                self._image.annotations.append(
                    Annotation(
                        kind="text_box",
                        x=left,
                        y=top,
                        width=width,
                        height=height,
                        text=text,
                    )
                )
                self._emit_edits()

        self._drag_start = None
        self._drag_current = None
        self.update()
