from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from .constants import ReportTheme

class ReportStyles:
    @staticmethod
    def criar_estilos():
        styles = getSampleStyleSheet()
        return {
            'titulo': ParagraphStyle('TituloRelatorio', parent=styles['Heading1'], fontSize=15, textColor=ReportTheme.COR_PRIMARIA, spaceAfter=4, alignment=1, fontName="Helvetica-Bold"),
            'subtitulo': ParagraphStyle('SubTituloRelatorio', parent=styles['Normal'], fontSize=10, textColor=ReportTheme.COR_SECUNDARIA, spaceAfter=10, alignment=1, fontName="Helvetica"),
            'secao': ParagraphStyle('SecaoCabecalho', parent=styles['Heading2'], fontSize=11, textColor=ReportTheme.COR_PRIMARIA, spaceBefore=10, spaceAfter=4, fontName="Helvetica-Bold"),
            'texto': ParagraphStyle('TextoPadrao', parent=styles['Normal'], fontSize=9, textColor=colors.black, fontName="Helvetica", spaceAfter=4),
            'celula': ParagraphStyle('CelulaTabela', parent=styles['Normal'], fontSize=8, textColor=colors.black, fontName="Helvetica"),
            'celula_centro': ParagraphStyle('CelulaTabelaCentro', parent=styles['Normal'], fontSize=8, textColor=colors.black, fontName="Helvetica", alignment=1),
            'bullet': ParagraphStyle('TextoBullet', parent=styles['Normal'], fontSize=8.5, textColor=colors.black, fontName="Helvetica", leftIndent=15, spaceAfter=4)
        }