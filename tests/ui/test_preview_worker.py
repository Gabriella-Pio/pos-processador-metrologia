"""Testes do debounce de preview."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from src.ui.shared.report_editor.preview_worker import (
    PREVIEW_DEBOUNCE_MS,
    PREVIEW_IMAGE_DEBOUNCE_MS,
    PREVIEW_INDICATOR_DELAY_MS,
    DebouncedPreviewRunner,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_schedule_does_not_emit_generating_immediately(qapp) -> None:
    service = MagicMock()
    runner = DebouncedPreviewRunner(
        service,
        debounce_ms=600,
        indicator_delay_ms=PREVIEW_INDICATOR_DELAY_MS,
    )
    states: list[bool] = []
    runner.generating.connect(states.append)

    runner.schedule()
    QTest.qWait(100)

    assert states == []


def test_indicator_shows_after_delay_while_debouncing(qapp) -> None:
    service = MagicMock()
    runner = DebouncedPreviewRunner(
        service,
        debounce_ms=600,
        indicator_delay_ms=PREVIEW_INDICATOR_DELAY_MS,
    )
    states: list[bool] = []
    runner.generating.connect(states.append)

    runner.schedule()
    QTest.qWait(PREVIEW_INDICATOR_DELAY_MS + 50)

    assert states == [True]


def test_generating_clears_when_debounce_cancelled_before_run(qapp) -> None:
    service = MagicMock()
    runner = DebouncedPreviewRunner(
        service,
        debounce_ms=600,
        indicator_delay_ms=PREVIEW_INDICATOR_DELAY_MS,
    )
    runner.set_document_getter(lambda: None)
    states: list[bool] = []
    runner.generating.connect(states.append)

    runner.schedule()
    QTest.qWait(PREVIEW_INDICATOR_DELAY_MS + 50)
    assert states == [True]

    runner._timer.stop()  # noqa: SLF001 — simula cancelamento sem render
    runner._clear_generating_if_idle()  # noqa: SLF001

    assert states == [True, False]


def test_image_debounce_constant_is_larger_than_default() -> None:
    assert PREVIEW_IMAGE_DEBOUNCE_MS > PREVIEW_DEBOUNCE_MS


def test_schedule_accepts_custom_debounce(qapp) -> None:
    service = MagicMock()
    runner = DebouncedPreviewRunner(service, debounce_ms=600)
    runner.schedule(debounce_ms=PREVIEW_IMAGE_DEBOUNCE_MS)
    assert runner._timer.interval() == PREVIEW_IMAGE_DEBOUNCE_MS  # noqa: SLF001
