from reportlab.platypus import Paragraph, Spacer
from src.core.parser.utils import ParserUtils
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS

class InterpretacaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "interpretacao", SECTION_HEADING_DEFAULTS["interpretacao"],
        )
        story.append(anchored_section_title(heading, styles['secao'], "interpretacao", contexto_extra.get("section_anchor_map")))
        intro_default = PROSE_TEMPLATES.get("interpretacao", {}).get("intro", "")
        intro_text = get_section_prose(contexto_extra, "interpretacao", "intro", intro_default)
        if intro_text.strip():
            story.append(Paragraph(intro_text, styles["texto"]))
            story.append(Spacer(1, 4))

        report_kind = contexto_extra.get("report_kind") or getattr(dados_parseados, "source_kind", "")
        prose = contexto_extra.get("section_prose", {}).get("interpretacao", {})
        bullet_keys = sorted(
            (k for k in prose if k.startswith("bullet_") and str(prose.get(k) or "").strip()),
            key=lambda k: int(k.split("_", 1)[1]) if k.split("_", 1)[1].isdigit() else 999,
        )
        has_edited_bullets = bool(bullet_keys)

        if report_kind in {"tomografia", "insp_ect"} or has_edited_bullets:
            keys = bullet_keys or [f"bullet_{i}" for i in range(1, 5)]
            for key in keys:
                bullet = get_section_prose(contexto_extra, "interpretacao", key, "")
                if bullet:
                    story.append(Paragraph(f"•  {bullet}", styles["bullet"]))
            story.append(Spacer(1, 10))
            return

        for item in dados_parseados.itens_medicao:
            tem_tol = item.tol_superior != "N/A" and item.tol_inferior != "N/A"
            
            if tem_tol:
                val_medido_f = ParserUtils.converter_para_float(item.valor_medido)
                nominal_f = ParserUtils.converter_para_float(item.nominal)
                sup_f = ParserUtils.converter_para_float(item.tol_superior)
                inf_f = ParserUtils.converter_para_float(item.tol_inferior)

                limite_superior = nominal_f + sup_f
                limite_inferior = nominal_f - abs(inf_f)

                if item.status == "Dentro":
                    texto_item = (
                        f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                        f"<b>{item.valor_medido}</b>, permanecendo <b>dentro</b> dos limites cadastrados de "
                        f"{limite_inferior:.4f} a {limite_superior:.4f}."
                    )
                else:
                    if val_medido_f > limite_superior:
                        excedente = val_medido_f - limite_superior
                        texto_item = (
                            f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                            f"<b>{item.valor_medido}</b>, ficando <b>acima</b> dos limites cadastrados de {limite_inferior:.4f} a {limite_superior:.4f}, "
                            f"resultando em um excedente de <font color='{ReportTheme.COR_ALERTA.hexval()}'><b>+{excedente:.4f}</b></font>."
                        )
                    elif val_medido_f < limite_inferior:
                        faltante = limite_inferior - val_medido_f
                        texto_item = (
                            f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                            f"<b>{item.valor_medido}</b>, ficando <b>abaixo</b> dos limites cadastrados de {limite_inferior:.4f} a {limite_superior:.4f}, "
                            f"resultando em um déficit de <font color='{ReportTheme.COR_ALERTA.hexval()}'><b>-{faltante:.4f}</b></font>."
                        )
                    else:
                        texto_item = (
                            f"• A característica <b>{item.caracteristica}</b> ({item.tipo}) apresentou valor medido de "
                            f"<b>{item.valor_medido}</b> fora dos limites."
                        )
            else:
                texto_item = (
                    f"• A característica <b>{item.caracteristica}</b>, do tipo {item.tipo}, apresentou valor medido de "
                    f"<b>{item.valor_medido}</b>, sem valores de tolerância cadastrados no relatório de origem."
                )

            story.append(Paragraph(texto_item, styles['bullet']))

        story.append(Spacer(1, 10))
