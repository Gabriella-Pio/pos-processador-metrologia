"""DTOs de exibição do dashboard — sem dependência de Qt."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

PeriodKey = Literal["all", "today", "7d", "30d", "90d"]
SortKey = Literal["recent", "oldest", "name", "project"]

PERIOD_ALL: PeriodKey = "all"
PERIOD_TODAY: PeriodKey = "today"
PERIOD_7D: PeriodKey = "7d"
PERIOD_30D: PeriodKey = "30d"
PERIOD_90D: PeriodKey = "90d"

SORT_RECENT: SortKey = "recent"
SORT_OLDEST: SortKey = "oldest"
SORT_NAME: SortKey = "name"
SORT_PROJECT: SortKey = "project"

PERIOD_LABELS: dict[PeriodKey, str] = {
    PERIOD_ALL: "Todo o período",
    PERIOD_TODAY: "Hoje",
    PERIOD_7D: "Últimos 7 dias",
    PERIOD_30D: "Últimos 30 dias",
    PERIOD_90D: "Últimos 90 dias",
}

SORT_LABELS: dict[SortKey, str] = {
    SORT_RECENT: "Mais recente",
    SORT_OLDEST: "Mais antigo",
    SORT_NAME: "Nome A–Z",
    SORT_PROJECT: "Projeto A–Z",
}


@dataclass(frozen=True)
class TemplateSummary:
    """DTO simples para exibição de um template na grade (sem lógica)."""
    template_id: str
    name: str
    is_default: bool = False


@dataclass(frozen=True)
class RecentFileSummary:
    """DTO simples para exibição de um arquivo recente (sem lógica)."""
    file_id: str
    file_name: str
    client_project: str
    version: str
    updated_at: datetime
    evaluated_component: str = ""


@dataclass
class RecentFilesFilterState:
    """Estado dos filtros estruturados da aba Arquivos."""
    query: str = ""
    period: PeriodKey = PERIOD_ALL
    project: str = ""
    component: str = ""
    sort: SortKey = SORT_RECENT

    def is_default(self) -> bool:
        return (
            not self.query.strip()
            and self.period == PERIOD_ALL
            and not self.project
            and not self.component
            and self.sort == SORT_RECENT
        )

    def active_labels(self) -> list[str]:
        labels: list[str] = []
        if self.period != PERIOD_ALL:
            labels.append(PERIOD_LABELS[self.period])
        if self.project:
            labels.append(self.project)
        if self.component:
            labels.append(self.component)
        if self.sort != SORT_RECENT:
            labels.append(SORT_LABELS[self.sort])
        if self.query.strip():
            labels.append(f'Busca: "{self.query.strip()}"')
        return labels

    def summary_chip_labels(self) -> list[str]:
        """Rótulos curtos para chip na busca (sem ordenação nem texto de busca)."""
        labels: list[str] = []
        if self.period != PERIOD_ALL:
            labels.append(PERIOD_LABELS[self.period])
        if self.project:
            labels.append(self.project)
        if self.component:
            labels.append(self.component)
        return labels


def empty_results_messages(
    query: str = "",
    *,
    has_active_filters: bool = False,
) -> tuple[str, str]:
    """Título e subtítulo padronizados para busca/filtros sem resultados."""
    title = "Nenhum resultado encontrado"
    q = query.strip()
    if q:
        subtitle = f'Nenhum resultado corresponde a "{q}".'
    elif has_active_filters:
        subtitle = "Nenhum resultado corresponde aos filtros selecionados."
    else:
        subtitle = "Tente outro termo ou limpe os filtros."
    return title, subtitle


def distinct_projects(files: list[RecentFileSummary]) -> list[str]:
    values = {f.client_project.strip() for f in files if f.client_project.strip()}
    return sorted(values, key=str.lower)


def distinct_components(files: list[RecentFileSummary]) -> list[str]:
    values = {f.evaluated_component.strip() for f in files if f.evaluated_component.strip()}
    return sorted(values, key=str.lower)


def _period_cutoff(period: PeriodKey, now: datetime) -> datetime | None:
    if period == PERIOD_ALL:
        return None
    if period == PERIOD_TODAY:
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    days = {"7d": 7, "30d": 30, "90d": 90}[period]
    return now - timedelta(days=days)


def apply_recent_files_filters(
    files: list[RecentFileSummary],
    state: RecentFilesFilterState,
    *,
    now: datetime | None = None,
) -> list[RecentFileSummary]:
    """Aplica busca textual, período, projeto, componente e ordenação."""
    reference = now or datetime.now()
    result = list(files)

    needle = state.query.strip().lower()
    if needle:
        result = [
            item for item in result
            if needle in item.file_name.lower()
            or needle in item.client_project.lower()
            or needle in item.evaluated_component.lower()
        ]

    cutoff = _period_cutoff(state.period, reference)
    if cutoff is not None:
        result = [item for item in result if item.updated_at >= cutoff]

    if state.project:
        result = [item for item in result if item.client_project == state.project]

    if state.component:
        result = [item for item in result if item.evaluated_component == state.component]

    if state.sort == SORT_RECENT:
        result.sort(key=lambda f: f.updated_at, reverse=True)
    elif state.sort == SORT_OLDEST:
        result.sort(key=lambda f: f.updated_at)
    elif state.sort == SORT_NAME:
        result.sort(key=lambda f: f.file_name.lower())
    elif state.sort == SORT_PROJECT:
        result.sort(key=lambda f: (f.client_project.lower(), f.file_name.lower()))

    return result


def filter_recent_files(
    files: list[RecentFileSummary],
    query: str,
) -> list[RecentFileSummary]:
    """Filtra recentes por nome de arquivo ou cliente/projeto (compatibilidade)."""
    return apply_recent_files_filters(files, RecentFilesFilterState(query=query))


def filter_templates(
    templates: list[TemplateSummary],
    query: str,
) -> list[TemplateSummary]:
    """Filtra templates pelo nome."""
    needle = query.strip().lower()
    if not needle:
        return list(templates)
    return [item for item in templates if needle in item.name.lower()]
