"""Comandos de mídia (imagens e anotações) no documento."""
from __future__ import annotations

from pathlib import Path

from src.core.domain.ports import Annotation, ReportDocument, ReportImage


class MediaCommands:
    @staticmethod
    def add_image(document: ReportDocument, image_path: Path, section_id: str) -> ReportImage:
        image = ReportImage(image_path=image_path, section_id=section_id)
        document.images.append(image)
        return image

    @staticmethod
    def remove_image(document: ReportDocument, image: ReportImage) -> None:
        document.images = [
            img for img in document.images
            if not (
                img.section_id == image.section_id
                and str(img.image_path) == str(image.image_path)
            )
        ]

    @staticmethod
    def update_image_caption(document: ReportDocument, image: ReportImage, caption: str) -> None:
        for img in document.images:
            if (
                img.section_id == image.section_id
                and str(img.image_path) == str(image.image_path)
            ):
                img.caption = caption
                break

    @staticmethod
    def add_bosello_capture(
        document: ReportDocument,
        image_path: Path,
        section_id: str,
    ) -> ReportImage | None:
        from src.core.application.bosello_image_import import attach_bosello_captures

        added = attach_bosello_captures(document, [image_path], section_id)
        if added == 0:
            return None
        for img in reversed(document.images):
            if img.section_id == section_id and str(img.image_path) == str(image_path):
                return img
        return None

    @staticmethod
    def add_bosello_captures(
        document: ReportDocument,
        image_paths: list[Path],
        section_id: str,
    ) -> int:
        from src.core.application.bosello_image_import import attach_bosello_captures

        return attach_bosello_captures(document, image_paths, section_id)

    @staticmethod
    def add_annotation(image: ReportImage, annotation: Annotation) -> None:
        image.annotations.append(annotation)
