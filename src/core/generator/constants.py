from reportlab.lib import colors

class ReportTheme:
    COR_PRIMARIA = colors.HexColor("#254aa5")
    COR_SECUNDARIA = colors.HexColor("#4A607A")
    COR_ALERTA = colors.HexColor("#D9534F")
    COR_SUCESSO = colors.HexColor("#5CB85C")
    COR_LINHA = colors.HexColor("#E0E0E0")

# Template padrão oficial que mapeia a ordem das seções executivas.
# "controle_tecnico" e "historico_versoes" foram adicionados para atender
# às funcionalidades obrigatórias 4 e 5 da proposta de desafio.
# Título amigável de cada seção — usado pelo RealReportExporterAdapter
# para montar o sumário (bookmarks) real exibido no Workspace, mantendo
# a UI sincronizada com o que o engine realmente vai gerar no PDF.
SECTION_TITLES = {
    "cabecalho": "Cabeçalho institucional",
    "introducao": "Introdução",
    "identificacao": "Identificação e condições de medição",
    "controle_tecnico": "Controle técnico",
    "resultados": "Resultados dimensionais",
    "grafica": "Análise gráfica dos resultados",
    "tomografia": "Inspeção tomográfica",
    "interpretacao": "Interpretação dos resultados",
    "conclusao": "Conclusão",
    "historico_versoes": "Histórico de versões",
}

TEMPLATE_PADRAO_OFICIAL = [
    {"tipo": "cabecalho", "config": {}},
    {"tipo": "introducao", "config": {}},
    {"tipo": "identificacao", "config": {}},
    {"tipo": "controle_tecnico", "config": {}},
    {"tipo": "resultados", "config": {}},
    {"tipo": "grafica", "config": {}},
    {"tipo": "tomografia", "config": {}},
    {"tipo": "interpretacao", "config": {}},
    {"tipo": "conclusao", "config": {}},
    {"tipo": "historico_versoes", "config": {}},
]