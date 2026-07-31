from reportlab.lib import colors

class ReportTheme:
    COR_PRIMARIA = colors.HexColor("#254aa5")  
    COR_SECUNDARIA = colors.HexColor("#4A607A")
    COR_ALERTA = colors.HexColor("#D9534F")    
    COR_SUCESSO = colors.HexColor("#5CB85C")   
    COR_LINHA = colors.HexColor("#E0E0E0")     

# Template padrão oficial que mapeia a ordem das seções executivas
TEMPLATE_PADRAO_OFICIAL = [
    {"tipo": "cabecalho", "config": {}},
    {"tipo": "introducao", "config": {}},
    {"tipo": "identificacao", "config": {}},
    {"tipo": "resultados", "config": {}},
    {"tipo": "grafica", "config": {}},
    {"tipo": "tomografia", "config": {}},
    {"tipo": "interpretacao", "config": {}},
    {"tipo": "conclusao", "config": {}}
]