# src/ui/viewmodels/navigation_controller.py
from PyQt6.QtCore import QObject, pyqtSignal

class NavigationController(QObject):
    """
    Gerencia o histórico de navegação estilo navegador (Voltar/Avançar)
    entre as telas do QStackedWidget.
    """
    changed = pyqtSignal(int, bool, bool)  # index_atual, pode_voltar, pode_avancar

    def __init__(self):
        super().__init__()
        self._history: list[int] = []
        self._pointer: int = -1

    def navigate_to(self, index: int) -> None:
        # Se navegarmos para o mesmo índice atual, não faz nada
        if self._pointer >= 0 and self._history[self._pointer] == index:
            return
            
        # Descarta o histórico à frente do ponteiro atual (padrão navegador)
        self._history = self._history[: self._pointer + 1]
        self._history.append(index)
        self._pointer += 1
        self._emit()

    def back(self) -> None:
        if self.can_go_back:
            self._pointer -= 1
            self._emit()

    def forward(self) -> None:
        if self.can_go_forward:
            self._pointer += 1
            self._emit()

    @property
    def can_go_back(self) -> bool:
        return self._pointer > 0

    @property
    def can_go_forward(self) -> bool:
        return self._pointer < len(self._history) - 1

    def _emit(self) -> None:
        current_index = self._history[self._pointer] if self._pointer >= 0 else 0
        self.changed.emit(current_index, self.can_go_back, self.can_go_forward)