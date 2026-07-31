# src/core/generator/sections/base.py
from abc import ABC, abstractmethod

class BaseSection(ABC):
    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    def render(self, story: list, styles: dict, dados_parseados, contexto_extra: dict):
        """Método polimórfico obrigatório para injetar elementos no PDF."""
        pass