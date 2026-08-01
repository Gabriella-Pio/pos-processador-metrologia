import datetime
import os
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from .base import BaseSection, anchored_section_title
from ..constants import ReportTheme

class CabecalhoSection(BaseSection):
    def render(self, story, styles, dados_parseados, contexto_extra):
        anchor_map = contexto_extra.get("section_anchor_map")
        data_geracao = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        versao_sistema = contexto_extra.get("versao_relatorio", "v1.0")

        # Caminhos padrão das logos institucionais
        logo_senai_path = contexto_extra.get("logo_senai_path") or "assets/logo-senai.png"
        logo_zeiss_path = contexto_extra.get("logo_zeiss_path") or "assets/logo-centro.png"

        # Estilos customizados locais herdando de styles['texto'] (padrão seguro da nossa arquitetura)
        estilo_institucional = ParagraphStyle(
            'HeaderInstitucional',
            parent=styles['texto'],
            fontName='Helvetica-Bold',
            fontSize=11,          # Fonte maior para o destaque institucional
            leading=14,
            textColor=ReportTheme.COR_PRIMARIA,
            alignment=1           # Centralizado
        )

        estilo_data_hora = ParagraphStyle(
            'HeaderDataHora',
            parent=styles['texto'],
            fontName='Helvetica',
            fontSize=8,           # Fonte menor e discreta para data/hora e versão
            leading=10,
            textColor=colors.HexColor('#666666'),
            alignment=1           # Centralizado
        )

        def criar_logo(caminho, texto_fallback, largura_desejada=90):
            if caminho and os.path.exists(caminho):
                try:
                    with PILImage.open(caminho) as img_pil:
                        orig_w, orig_h = img_pil.size
                    
                    # Calcula a altura exata mantendo a proporção (aspect ratio) a partir da largura fixa
                    altura_proporcional = (largura_desejada * orig_h) / orig_w

                    img = Image(caminho, width=largura_desejada, height=altura_proporcional)
                    img.hAlign = 'CENTER'
                    img.preserveAspectRatio = True
                    return img
                except Exception:
                    pass
            return Paragraph(f"<b>{texto_fallback}</b>", styles['celula_centro'])

        elemento_logo_zeiss = criar_logo(logo_zeiss_path, "CENTRO DE EXCELÊNCIA EM METROLOGIA", largura_desejada=150)
        elemento_logo_senai = criar_logo(logo_senai_path, "SENAI", largura_desejada=100) # Corrigido o typo anterior (largura_desejada)

        dados_topo = [
            [
                elemento_logo_zeiss,
                anchored_section_title(
                    "<b>CENTRO DE EXCELÊNCIA EM METROLOGIA</b><br/>SENAI ZEISS — GOIÂNIA / GO",
                    estilo_institucional,
                    "cabecalho",
                    anchor_map,
                ),
                elemento_logo_senai
            ],
            [
                "", 
                Paragraph(f"Data/Hora: {data_geracao} | Versão: {versao_sistema}", estilo_data_hora), 
                ""
            ]
        ]

        tabela_topo = Table(dados_topo, colWidths=[115, 310, 115])
        tabela_topo.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('SPAN', (1, 1), (1, 1)),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))

        story.append(tabela_topo)
        story.append(Spacer(1, 10))

        # Linha divisória limpa e elegante ao final do cabeçalho
        story.append(HRFlowable(
            width="100%", 
            thickness=1.0, 
            color=ReportTheme.COR_PRIMARIA, 
            spaceBefore=2, 
            spaceAfter=12
        ))