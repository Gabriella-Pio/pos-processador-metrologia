"""Shim de compatibilidade — use table_row_specs e table_row_merge diretamente quando possível."""
from src.core.domain.table_row_merge import (
    apply_legacy_introducao_overrides,
    merge_table_rows,
    merge_with_defaults,
    resolve_introducao_table_rows,
)
from src.core.domain.table_row_specs import (
    CONTROLE_TECNICO_TABLE_ROWS,
    CONTROLE_TECNICO_VALUE_IDS,
    IDENTIFICACAO_TABLE_ROWS,
    INTRODUCAO_BLOCK_TITLES,
    INTRODUCAO_PROSE_ROW_IDS,
    INTRODUCAO_ROW_SPECS,
    NUMBERED_SECTION_IDS,
    SECTION_HEADING_DEFAULTS,
    TABLE_SECTIONS,
    TableRowDef,
    apply_control_info_to_rows,
    control_info_updates_from_rows,
    default_discussao_falha_rows,
    default_falha_identificacao_rows,
    default_falha_introducao_rows,
    default_table_rows,
    default_tomo_identificacao_rows,
    default_tomo_introducao_rows,
)

# Alias interno preservado para código que importava _merge_with_defaults
_merge_with_defaults = merge_with_defaults

__all__ = [
    "CONTROLE_TECNICO_TABLE_ROWS",
    "CONTROLE_TECNICO_VALUE_IDS",
    "IDENTIFICACAO_TABLE_ROWS",
    "INTRODUCAO_BLOCK_TITLES",
    "INTRODUCAO_PROSE_ROW_IDS",
    "INTRODUCAO_ROW_SPECS",
    "NUMBERED_SECTION_IDS",
    "SECTION_HEADING_DEFAULTS",
    "TABLE_SECTIONS",
    "TableRowDef",
    "apply_control_info_to_rows",
    "apply_legacy_introducao_overrides",
    "control_info_updates_from_rows",
    "default_discussao_falha_rows",
    "default_falha_identificacao_rows",
    "default_falha_introducao_rows",
    "default_table_rows",
    "default_tomo_identificacao_rows",
    "default_tomo_introducao_rows",
    "merge_table_rows",
    "merge_with_defaults",
    "resolve_introducao_table_rows",
]
