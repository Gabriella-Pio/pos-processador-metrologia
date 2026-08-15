"""DTO de item de medição dimensional (independente do parser)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MedicaoItemDto:
    caracteristica: str
    tipo: str
    valor_medido: str
    nominal: str
    tol_superior: str
    tol_inferior: str
    desvio: str
    status: str
