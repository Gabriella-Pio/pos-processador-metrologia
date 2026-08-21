"""Preferências de aparência — tema, contraste e zoom de fonte."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from collections.abc import Callable
from typing import Literal

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication

from src.ui.accessibility.themes import (
    apply_font_scale,
    apply_high_contrast,
    copy_palette_into_global,
    dark_palette,
    light_palette,
)
from src.ui.styles.helpers import base_stylesheet, restore_link_color
from src.ui.styles.qss_loader import clear_style_cache
from src.ui.styles.tokens import PALETTE, TYPOGRAPHY

ThemeMode = Literal["dark", "light"]
ContrastMode = Literal["normal", "high"]

DEFAULT_PREFS_PATH = Path("output_pdfs/user_preferences.json")

FONT_SCALE_PRESETS: tuple[tuple[str, float], ...] = (
    ("Pequeno (85%)", 0.85),
    ("Padrão (100%)", 1.0),
    ("Médio (110%)", 1.1),
    ("Grande (125%)", 1.25),
    ("Extra grande (140%)", 1.4),
)


@dataclass
class AppearanceSettings:
    theme: ThemeMode = "dark"
    contrast: ContrastMode = "normal"
    font_scale: float = 1.0

    def normalized(self) -> AppearanceSettings:
        scale = self.font_scale
        for _label, preset in FONT_SCALE_PRESETS:
            if abs(scale - preset) < 0.001:
                return AppearanceSettings(self.theme, self.contrast, preset)
        closest = min(FONT_SCALE_PRESETS, key=lambda item: abs(item[1] - scale))
        return AppearanceSettings(self.theme, self.contrast, closest[1])


class AppearanceManager(QObject):
    """Singleton que aplica e persiste preferências visuais."""

    changed = pyqtSignal(object)  # AppearanceSettings

    _instance: AppearanceManager | None = None

    def __init__(self, storage_path: Path | None = None) -> None:
        super().__init__()
        self._storage_path = storage_path or DEFAULT_PREFS_PATH
        self._settings = AppearanceSettings()
        self._refresh_callbacks: list[Callable[[], None]] = []

    @classmethod
    def instance(cls, storage_path: Path | None = None) -> AppearanceManager:
        if cls._instance is None:
            cls._instance = cls(storage_path)
        return cls._instance

    @property
    def settings(self) -> AppearanceSettings:
        return AppearanceSettings(
            self._settings.theme,
            self._settings.contrast,
            self._settings.font_scale,
        )

    def register_refresh(self, callback: Callable[[], None]) -> None:
        if callback not in self._refresh_callbacks:
            self._refresh_callbacks.append(callback)

    def load(self) -> AppearanceSettings:
        path = self._storage_path
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                appearance = raw.get("appearance", raw)
                self._settings = AppearanceSettings(
                    theme=appearance.get("theme", "dark"),
                    contrast=appearance.get("contrast", "normal"),
                    font_scale=float(appearance.get("font_scale", 1.0)),
                ).normalized()
            except (json.JSONDecodeError, TypeError, ValueError):
                self._settings = AppearanceSettings()
        self.apply(self._settings, persist=False)
        return self.settings

    def save(self) -> None:
        path = self._storage_path
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"appearance": asdict(self._settings.normalized())}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def apply(self, settings: AppearanceSettings, *, persist: bool = True) -> None:
        self._settings = settings.normalized()
        palette = light_palette() if self._settings.theme == "light" else dark_palette()
        if self._settings.contrast == "high":
            palette = apply_high_contrast(palette)
        copy_palette_into_global(palette)
        apply_font_scale(self._settings.font_scale)
        clear_style_cache()

        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(base_stylesheet())
            font = QFont(TYPOGRAPHY.font_family.split(",")[0].strip(), TYPOGRAPHY.size_body)
            font.setPointSize(TYPOGRAPHY.size_body)
            app.setFont(font)
            self._apply_qt_chrome_palette(app)

        for callback in self._refresh_callbacks:
            callback()

        self.changed.emit(self.settings)
        if persist:
            self.save()

    @staticmethod
    def _apply_qt_chrome_palette(app: QApplication) -> None:
        """Ajusta roles que o QSS não cobre bem (tooltip, placeholder)."""
        qt_palette = app.palette()
        tooltip_bg = QColor(PALETTE.tooltip_bg)
        tooltip_text = QColor(PALETTE.tooltip_text)
        placeholder = QColor(PALETTE.text_secondary)
        link = QColor(restore_link_color())
        for group in (
            QPalette.ColorGroup.Active,
            QPalette.ColorGroup.Inactive,
            QPalette.ColorGroup.Disabled,
        ):
            qt_palette.setColor(group, QPalette.ColorRole.ToolTipBase, tooltip_bg)
            qt_palette.setColor(group, QPalette.ColorRole.ToolTipText, tooltip_text)
            qt_palette.setColor(group, QPalette.ColorRole.PlaceholderText, placeholder)
            qt_palette.setColor(group, QPalette.ColorRole.Link, link)
            qt_palette.setColor(group, QPalette.ColorRole.LinkVisited, link)
        app.setPalette(qt_palette)
