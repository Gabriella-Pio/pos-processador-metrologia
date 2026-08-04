from reportlab.lib import colors

class ReportTheme:
    COR_PRIMARIA = colors.HexColor("#254aa5")
    COR_SECUNDARIA = colors.HexColor("#4A607A")
    COR_ALERTA = colors.HexColor("#D9534F")
    COR_SUCESSO = colors.HexColor("#5CB85C")
    COR_LINHA = colors.HexColor("#E0E0E0")

# Re-exporta do schema central — evita divergência de IDs entre UI e generator.
from src.core.domain.section_schema import SECTION_TITLES, TEMPLATE_PADRAO_OFICIAL