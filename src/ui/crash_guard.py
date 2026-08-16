"""Rede de segurança: exceções não tratadas não derrubam a UI em produção."""
from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

_SHOWING_DIALOG = False


def _format_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_tb: TracebackType | None,
) -> str:
    return "".join(traceback.format_exception(exc_type, exc_value, exc_tb))


def _show_error_dialog(title: str, message: str, details: str) -> None:
    global _SHOWING_DIALOG
    if _SHOWING_DIALOG:
        return
    app = QApplication.instance()
    if app is None:
        return
    _SHOWING_DIALOG = True
    try:
        from src.ui.components.feedback import show_friendly_error

        parent = app.activeWindow()
        show_friendly_error(parent, title, message, details=details)
    except Exception:
        logger.exception("Falha ao exibir diálogo de erro global")
    finally:
        _SHOWING_DIALOG = False


def install_exception_guard() -> None:
    """Instala ``sys.excepthook`` que registra o erro e mostra diálogo sem abortar."""
    previous = sys.excepthook

    def _hook(
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_tb: TracebackType | None,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            previous(exc_type, exc_value, exc_tb)
            return

        details = _format_exception(exc_type, exc_value, exc_tb)
        logger.error("Exceção não tratada:\n%s", details)

        # Não bloquear o hook: agenda o diálogo no próximo tick do event loop.
        QTimer.singleShot(
            0,
            lambda: _show_error_dialog(
                "Ocorreu um erro inesperado",
                "A operação falhou, mas o aplicativo continua aberto. "
                "Se o problema persistir, reinicie e verifique o log.",
                details,
            ),
        )

    sys.excepthook = _hook
