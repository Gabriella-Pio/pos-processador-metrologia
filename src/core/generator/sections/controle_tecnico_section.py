from .base import BaseSection
from ..prose_helpers import render_kv_table, render_section_header
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import default_table_rows


class ControleTecnicoSection(BaseSection):
    """Página de Controle Técnico: responsáveis pela medição, revisão e
    aprovação (quando houver), cargo, e-mail institucional, data e horário.
    """

    def render(self, story, styles, dados_parseados, contexto_extra):
        render_section_header(
            story,
            styles,
            contexto_extra,
            "controle_tecnico",
            prose_default=PROSE_TEMPLATES.get("controle_tecnico", {}).get("intro", ""),
            spacer_after_intro=0,
        )

        ctx = contexto_extra.get("placeholder_context", {})
        table_rows = (contexto_extra.get("table_rows") or {}).get("controle_tecnico", [])
        if not table_rows:
            info = contexto_extra.get("controle_tecnico") or {}
            table_rows = default_table_rows("controle_tecnico")
            for row in table_rows:
                row_id = row.get("id", "")
                if row_id in info:
                    row["value"] = info[row_id] or row.get("value", "")

        render_kv_table(
            story,
            styles,
            table_rows,
            ctx,
            value_for_empty={"approved_by": "Não aplicável"},
            default_empty_value="Não informado",
            fallback_row=("Medido por", "Não informado"),
        )
