"""Overlay de ocupado — feedback visual para operações longas (lote, parse)."""
from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class BusyOverlay(QWidget):
    """Cobre o ``host`` com fundo semitransparente, mensagem e barra indeterminada."""

    OBJECT_NAME = "AppBusyOverlay"
    _CARD_MIN_W = 320
    _CARD_MAX_W = 720
    _CARD_PAD_X = 56  # margens horizontais do layout do card

    def __init__(self, host: QWidget) -> None:
        super().__init__(host)
        self._host = host
        self.setObjectName(self.OBJECT_NAME)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.addStretch(1)

        self._card = QFrame()
        self._card.setObjectName("AppBusyCard")
        self._card.setMinimumWidth(self._CARD_MIN_W)
        self._card.setMaximumWidth(self._CARD_MAX_W)
        self._card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(28, 22, 28, 22)
        card_layout.setSpacing(14)

        self._title = QLabel("Carregando…")
        self._title.setObjectName("AppBusyTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)
        self._title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        self._detail = QLabel("")
        self._detail.setObjectName("AppBusyDetail")
        self._detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail.setWordWrap(True)
        self._detail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self._detail.setMinimumHeight(20)
        self._detail.hide()

        self._bar = QProgressBar()
        self._bar.setObjectName("AppBusyIndicator")
        self._bar.setRange(0, 0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)

        card_layout.addWidget(self._title)
        card_layout.addWidget(self._detail)
        card_layout.addWidget(self._bar)

        root.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignHCenter)
        root.addStretch(1)

        self.hide()
        self._sync_geometry()
        host.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:  # noqa: ANN001
        if obj is self._host and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Move,
        ):
            self._sync_geometry()
            if self.isVisible():
                self._fit_card_to_content()
        return False

    def _sync_geometry(self) -> None:
        self.setGeometry(self._host.rect())

    def _host_cap_width(self) -> int:
        return max(self._CARD_MIN_W, self._host.width() - 48)

    def _fit_card_to_content(self) -> None:
        """Larga o card conforme o nome do PDF; altura acompanha o wrap."""
        cap = min(self._CARD_MAX_W, self._host_cap_width())

        needed = self._CARD_MIN_W
        for label in (self._title, self._detail):
            if not label.isVisible():
                continue
            text = label.text().strip()
            if not text:
                continue
            needed = max(needed, label.fontMetrics().horizontalAdvance(text) + self._CARD_PAD_X)

        width = min(max(self._CARD_MIN_W, needed), cap)
        self._card.setMinimumWidth(width)
        self._card.setMaximumWidth(width)

        content_w = max(80, width - self._CARD_PAD_X)
        for label in (self._title, self._detail):
            if not label.isVisible():
                continue
            h = max(label.fontMetrics().height() + 6, label.heightForWidth(content_w))
            label.setMinimumHeight(h)

        self._card.adjustSize()
        self._card.updateGeometry()

    def set_busy(self, busy: bool, message: str = "", detail: str = "") -> None:
        if not busy:
            self.hide()
            return
        self.set_message(message or "Carregando…", detail)
        self._sync_geometry()
        self.show()
        self.raise_()

    def set_message(self, message: str, detail: str = "") -> None:
        self._title.setText(message or "Carregando…")
        text = str(detail or "").strip()
        self._detail.setText(text)
        self._detail.setVisible(bool(text))
        self._fit_card_to_content()

    def set_progress(self, current: int, total: int, *, detail: str = "") -> None:
        if total > 0:
            self.set_message(f"Lendo PDF {current} de {total}…", detail)
            self._bar.setRange(0, total)
            self._bar.setValue(max(0, min(current, total)))
        else:
            self._bar.setRange(0, 0)
            self.set_message("Carregando…", detail)
        if self.isVisible():
            self.raise_()
