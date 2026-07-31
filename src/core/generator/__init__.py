from .engine import ReportGenerator

def gerar_relatorio_enriquecido(
    dados_parseados, 
    caminho_saida, 
    cliente_projeto="Não informado", 
    componente_avaliado="Não informado", 
    opcoes_extras=None, 
    template_config=None,
    fotos_secoes=None,
    logo_senai_path=None,
    logo_zeiss_path=None,
    versao_relatorio="v1.0"
):
    ReportGenerator.gerar_relatorio_enriquecido(
        dados_parseados, 
        caminho_saida, 
        cliente_projeto, 
        componente_avaliado, 
        opcoes_extras, 
        template_config,
        fotos_secoes,
        logo_senai_path,
        logo_zeiss_path,
        versao_relatorio
    )