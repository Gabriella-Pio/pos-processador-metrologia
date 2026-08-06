from .base import BaseSection
from ..prose_helpers import render_kv_table, render_section_header
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import default_table_rows, default_tomo_identificacao_rows


class IdentificacaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "identificacao",
            prose_default=PROSE_TEMPLATES.get("identificacao", {}).get("intro", ""),
            spacer_after_intro=8,
        )

        ctx = contexto_extra.get("placeholder_context", {})
        table_rows = (contexto_extra.get("table_rows") or {}).get("identificacao", [])
        if not table_rows:
            if contexto_extra.get("report_kind") == "tomografia":
                table_rows = default_tomo_identificacao_rows()
            else:
                table_rows = default_table_rows("identificacao")

        render_kv_table(
            story,
            styles,
            table_rows,
            ctx,
            bold_value_row_ids=frozenset({"numero_mmc"}),
            fallback_row=(
                "Componente",
                str(contexto_extra.get("componente_avaliado", "")),
            ),
        )
