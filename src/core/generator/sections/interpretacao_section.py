from reportlab.platypus import Paragraph, Spacer
from src.core.parser.utils import ParserUtils
from .base import BaseSection
from ..constants import ReportTheme

class InterpretacaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        story.append(Paragraph("5. INTERPRETAÇÃO DOS RESULTADOS", styles['secao']))
        story.append(Paragraph(
            f"Análise detalhada das <b>{len(dados_parseados.itens_medicao)}</b> características inspecionadas no componente <b>{dados_parseados.componente}</b>:",
            styles['texto']
        ))
        story.append(Spacer(1, 4))

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