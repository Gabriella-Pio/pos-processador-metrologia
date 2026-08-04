"""Sincronização de campos canônicos entre DTO, overrides e control_info."""
from __future__ import annotations

from src.core.domain.ports import ReportDocument, TechnicalControlInfo


def sync_operador_control_info(document: ReportDocument, value: str) -> None:
    document.parsed_overrides.setdefault("scalar", {})["operador"] = value
    if document.control_info is None:
        document.control_info = TechnicalControlInfo(
            measured_by=value,
            reviewed_by="Supervisor SENAI",
        )
    else:
        document.control_info.measured_by = value


def sync_measured_by_to_operador(document: ReportDocument, measured_by: str) -> None:
    document.parsed_overrides.setdefault("scalar", {})["operador"] = measured_by
