from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme
from ..components.image_handler import ReportImageHandler
from ..prose_helpers import get_section_prose, get_section_heading
from src.core.domain.report_field_registry import PROSE_TEMPLATES
from src.core.domain.table_row_registry import SECTION_HEADING_DEFAULTS, INTRODUCAO_BLOCK_TITLES
from src.core.domain.placeholder_utils import resolve_placeholders

class IntroducaoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        heading = get_section_heading(
            contexto_extra, "introducao", SECTION_HEADING_DEFAULTS["introducao"],
        )
        story.append(anchored_section_title(heading, styles['subtitulo'], "introducao", contexto_extra.get("section_anchor_map")))
        ctx = contexto_extra.get("placeholder_context", {})
        componente_heading = resolve_placeholders("{componente}", ctx)
        story.append(Paragraph(componente_heading, styles['titulo']))
        story.append(Spacer(1, 8))

        estilo_titulo_tabela = ParagraphStyle(
            'TituloTabelaCabecalho',
            parent=styles['texto'],
            textColor=colors.white,
            fontName="Helvetica-Bold"
        )

        # Gestão dinâmica de fotos por seção
        fotos_secao = contexto_extra.get("fotos_secoes", {}).get("cabecalho", [])
        if not fotos_secao:
            fotos_secao = contexto_extra.get("fotos_secoes", {}).get("introducao", [])
        if not fotos_secao:
            foto_legada = contexto_extra.get("opcoes_extras", {}).get("caminho_foto_peca")
            if foto_legada:
                fotos_secao = [foto_legada]

        caminho_foto_principal = fotos_secao[0] if fotos_secao else None

        conteudo_coluna_foto = ReportImageHandler.criar_elemento_foto(
            caminho_foto_principal, styles=styles
        )

        tmpl = PROSE_TEMPLATES.get("introducao", {})
        prose = contexto_extra.get("section_prose", {}).get("introducao", {})
        texto_objetivo = get_section_prose(contexto_extra, "introducao", "objetivo", tmpl.get("objetivo", ""))
        texto_escopo = get_section_prose(contexto_extra, "introducao", "escopo", tmpl.get("escopo", ""))
        texto_referencia = get_section_prose(contexto_extra, "introducao", "referencia", tmpl.get("referencia", ""))

        def block_title(key: str, default: str) -> str:
            return str(prose.get(key, INTRODUCAO_BLOCK_TITLES.get(key, default)))

        dados_tabela_unica = [
            [
                Paragraph(block_title("title_objetivo", "OBJETIVO"), estilo_titulo_tabela),
                conteudo_coluna_foto 
            ],
            [Paragraph(texto_objetivo, styles['texto']), ""],
            [
                Paragraph(block_title("title_escopo", "ESCOPO DA ANÁLISE"), estilo_titulo_tabela),
                "" 
            ],
            [Paragraph(texto_escopo, styles['texto']), ""],
            [
                Paragraph(block_title("title_referencia", "REFERÊNCIA DE MEDIÇÃO"), estilo_titulo_tabela),
                "" 
            ],
            [Paragraph(texto_referencia, styles['texto']), ""],
            [
                Paragraph(block_title("title_amostra", "AMOSTRA"), estilo_titulo_tabela),
                Paragraph(block_title("title_valores", "VALORES AVALIADOS"), estilo_titulo_tabela)
            ],
            [
                Paragraph(
                    resolve_placeholders(
                        str(prose.get("valor_amostra", "1 peça")),
                        ctx,
                    ),
                    styles['texto'],
                ),
                Paragraph(
                    f"<b>{resolve_placeholders(str(prose.get('valor_valores', '{numero_medicoes_cabecalho}')), ctx)}</b>",
                    styles['texto'],
                )
            ],
            [
                Paragraph(block_title("title_fora", "FORA DOS LIMITES"), estilo_titulo_tabela),
                Paragraph(block_title("title_mmc", "MÁQUINA DE MEDIÇÃO (MMC)"), estilo_titulo_tabela)
            ],
            [
                Paragraph(
                    f"<font color='{ReportTheme.COR_ALERTA.hexval()}'><b>"
                    f"{resolve_placeholders(str(prose.get('valor_fora', '{total_fora} valores')), ctx)}"
                    f"</b></font>",
                    styles['texto'],
                ),
                Paragraph(
                    f"<b>{resolve_placeholders(str(prose.get('valor_mmc', '{maquina_mmc}')), ctx)}</b>",
                    styles['texto'],
                )
            ]
        ]

        tabela_unica = Table(dados_tabela_unica, colWidths=[270, 270])
        
        tabela_unica.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            
            ('BACKGROUND', (0, 0), (0, 0), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 2), (0, 2), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 4), (0, 4), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 6), (0, 6), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (0, 8), (0, 8), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (1, 6), (1, 6), ReportTheme.COR_PRIMARIA),
            ('BACKGROUND', (1, 8), (1, 8), ReportTheme.COR_PRIMARIA),

            ('BOX', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('INNERGRID', (0,0), (-1,-1), 0.5, ReportTheme.COR_LINHA),
            ('PADDING', (0,0), (-1,-1), 4),
            
            ('SPAN', (1, 0), (1, 5)),
            ('BACKGROUND', (1, 0), (1, 5), colors.HexColor("#F2F4F7")),
        ]))

        story.append(tabela_unica)
        story.append(Spacer(1, 10))