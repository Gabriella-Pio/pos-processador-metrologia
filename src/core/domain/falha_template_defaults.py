"""Prose e layout do template de análise de falha (óptico/O-inspect + tomografia)."""
from __future__ import annotations

FALHA_TEMPLATE_ID = "analise_falha"

FALHA_SECTIONS_CONFIG: dict[str, dict] = {
    "cabecalho": {"enabled": True, "order": 0},
    "introducao": {"enabled": True, "order": 1},
    "identificacao": {"enabled": True, "order": 2},
    "metodo_escopo": {"enabled": True, "order": 3},
    "registro_componente": {"enabled": True, "order": 4},
    "inspecao_optica": {"enabled": True, "order": 5},
    "resultados_superficies": {"enabled": True, "order": 6},
    "resultados": {"enabled": False, "order": 7},
    "grafica": {"enabled": False, "order": 8},
    "tomografia": {"enabled": True, "order": 9},
    "resultados_inspecao": {"enabled": True, "order": 10},
    "interpretacao": {"enabled": False, "order": 11},
    "discussao_falha": {"enabled": True, "order": 12},
    "historico_versoes": {"enabled": True, "order": 13},
    "controle_tecnico": {"enabled": True, "order": 14},
    "conclusao": {"enabled": True, "order": 15},
    "observacoes_limitacoes": {"enabled": True, "order": 16},
    "anexos": {"enabled": True, "order": 17},
}

_FALHA_BLOCK_ORDER: tuple[str, ...] = (
    "cabecalho",
    "introducao",
    "identificacao",
    "metodo_escopo",
    "registro_componente",
    "inspecao_optica",
    "resultados_superficies",
    "tomografia",
    "resultados_inspecao",
    "discussao_falha",
    "historico_versoes",
    "controle_tecnico",
    "conclusao",
    "observacoes_limitacoes",
    "anexos",
)

_FALHA_BLOCK_CONFIG: dict[str, dict] = {
    "introducao": {"variant": "falha"},
}


def falha_blocks() -> list[dict]:
    """Blocos oficiais do template de análise de falha."""
    from src.core.domain.section_catalog import catalog_by_id

    by_id = catalog_by_id()
    blocks: list[dict] = []
    for section_id in _FALHA_BLOCK_ORDER:
        meta = by_id[section_id]
        config = dict(meta.block_config or {})
        config.update(_FALHA_BLOCK_CONFIG.get(section_id, {}))
        blocks.append({"tipo": section_id, "config": config})
    return blocks


FALHA_PROSE_DEFAULTS: dict[str, dict[str, str]] = {
    "introducao": {
        "section_title": "RELATÓRIO TÉCNICO — ANÁLISE DE QUEBRA E FALHA",
        "objetivo": (
            "Apresentar os resultados da análise do componente {componente}, contemplando "
            "inspeção visual e macrográfica, observação óptica ampliada e tomografia "
            "computadorizada industrial, com o propósito de caracterizar o mecanismo de "
            "falha mais compatível com as evidências disponíveis."
        ),
        "escopo": (
            "Avaliação qualitativa das superfícies de interesse e das seções tomográficas. "
            "Foram pesquisados indícios de nucleação e propagação de trinca, ruptura final "
            "e descontinuidades internas detectáveis."
        ),
        "referencia": (
            "Interpretação baseada nas características morfológicas observadas e na "
            "correlação com mecanismos usuais de falha. A determinação definitiva da "
            "causa-raiz depende da avaliação do conjunto montado, das condições de "
            "operação e das propriedades do material."
        ),
        "intro": "",
        "nota": "",
        "valor_amostra": "1 peça / segmentos avaliados",
        "valor_tipo_analise": "Qualitativa",
        "valor_metodos": "Visual, óptico e tomográfico",
        "valor_mecanismo": "A definir conforme evidências",
        "valor_nucleacao": "A definir conforme evidências",
        "valor_tomografia": "Sem indicações internas detectáveis",
        "foto_legenda": "Registro do componente avaliado",
    },
    "identificacao": {
        "section_title": "IDENTIFICAÇÃO E CONDIÇÕES DA INSPEÇÃO",
        "intro": (
            "Dados do cliente, componente e condições da inspeção óptica e tomográfica."
        ),
    },
    "metodo_escopo": {
        "section_title": "MÉTODO E ESCOPO DA AVALIAÇÃO",
        "body": (
            "As superfícies de interesse foram documentadas e avaliadas quanto a plano de "
            "ruptura, diferenças de textura, marcas de propagação, região de ruptura final, "
            "danos por contato e relação com concentradores de tensão. Regiões "
            "representativas foram observadas em sistema óptico de medição para registro "
            "ampliado.\n\n"
            "A tomografia foi realizada de forma não destrutiva, com avaliação das "
            "reconstruções e vistas seccionais para pesquisa de trincas, vazios, "
            "porosidades relevantes, inclusões ou outras descontinuidades internas "
            "detectáveis. A avaliação ficou restrita ao volume efetivamente reconstruído "
            "e à capacidade de detecção alcançada."
        ),
    },
    "registro_componente": {
        "section_title": "REGISTRO DO COMPONENTE",
        "intro": "Fotografias do componente e do posicionamento para inspeção.",
    },
    "inspecao_optica": {
        "section_title": "INSPEÇÃO VISUAL, MACROGRÁFICA E ÓPTICA",
        "body": (
            "A superfície de fratura/interesse apresenta morfologia a ser descrita a partir "
            "das imagens anexadas. Observam-se regiões com texturas distintas, possíveis "
            "áreas de propagação progressiva e evidências de contato ou danos secundários "
            "que podem limitar a leitura de parte das marcas originais."
        ),
    },
    "resultados_superficies": {
        "section_title": "RESULTADOS DA AVALIAÇÃO DAS SUPERFÍCIES",
        "intro": "Síntese das evidências observadas nas superfícies avaliadas:",
        "bullet_1": "Plano de fratura / morfologia superficial a descrever.",
        "bullet_2": "Diferenças de textura compatíveis com propagação e ruptura final.",
        "bullet_3": "Concentrador de tensão geométrico identificado nas imagens.",
        "bullet_4": "Danos secundários por contato que limitam parte da leitura original.",
    },
    "tomografia": {
        "section_title": "INSPEÇÃO TOMOGRÁFICA",
        "intro": (
            "As vistas seccionais abaixo apresentam registros representativos do volume "
            "interno do componente {componente}."
        ),
    },
    "resultados_inspecao": {
        "section_title": "RESULTADOS DA INSPEÇÃO TOMOGRÁFICA",
        "body": (
            "Nas reconstruções e vistas seccionais analisadas, não foram identificadas "
            "indicações detectáveis compatíveis com trincas internas, vazios, porosidades "
            "relevantes, inclusões ou outras descontinuidades internas que pudessem ser "
            "associadas à origem da falha.\n\n"
            "A ausência de indicações internas é coerente com um mecanismo cuja nucleação "
            "ocorreu na superfície. Esse resultado não constitui garantia absoluta de "
            "inexistência de descontinuidades abaixo do limite de detecção do ensaio."
        ),
    },
    "discussao_falha": {
        "section_title": "DISCUSSÃO DO MECANISMO DE FALHA",
        "intro": (
            "A hipótese técnica mais coerente com o conjunto das evidências deve ser "
            "ajustada pelo analista a partir das imagens e dos resultados tomográficos. "
            "A tabela abaixo organiza as etapas típicas do mecanismo considerado."
        ),
    },
    "conclusao": {
        "texto": (
            "A análise visual, macrográfica e óptica indica o mecanismo mais compatível "
            "com as evidências disponíveis para o componente {componente}. A inspeção "
            "tomográfica não identificou descontinuidades internas detectáveis no volume "
            "avaliado, reforçando — sem comprovar isoladamente — a hipótese de nucleação "
            "superficial quando aplicável.\n\n"
            "Este relatório caracteriza o mecanismo mais provável, mas não comprova "
            "isoladamente a causa-raiz. A declaração formal depende de critérios de "
            "aceitação, desenho, material e condições operacionais fornecidos pelo cliente."
        ),
        "aprovacao": "Aprovação / Coordenação CEM",
    },
    "observacoes_limitacoes": {
        "section_title": "OBSERVAÇÕES E LIMITAÇÕES",
        "body": (
            "Os resultados são aplicáveis exclusivamente aos segmentos e volumes "
            "efetivamente inspecionados. A interpretação foi realizada sem acesso "
            "obrigatório a desenho, especificação do material, histórico operacional "
            "completo, cálculo de cargas ou medições do conjunto montado. A "
            "detectabilidade tomográfica depende da resolução, do contraste, da "
            "geometria, do material, da espessura atravessada, da orientação da "
            "descontinuidade e dos parâmetros de aquisição e reconstrução. Este "
            "relatório caracteriza o mecanismo mais provável, mas não comprova "
            "isoladamente a causa-raiz."
        ),
    },
    "anexos": {
        "intro": (
            "Seguem anexos, quando disponíveis, os PDFs de origem e demais registros "
            "utilizados na análise."
        ),
    },
    "historico_versoes": {
        "intro": "Registro das versões emitidas deste relatório.",
    },
}

IDENTIFICACAO_FALHA_TABLE_ROWS = (
    ("client_project", "Cliente / Projeto", "{client_project}"),
    ("evaluated_component", "Componente avaliado", "{evaluated_component}"),
    ("tecnica", "Técnicas de inspeção", "Inspeção visual e macrográfica, observação óptica ampliada e tomografia computadorizada industrial"),
    ("equipamento_tomo", "Equipamento de tomografia", "ZEISS BOSELLO MAX 80-150 (Carl Zeiss X-ray Technologies Srl)"),
    ("ident_equipamento", "Identificação do equipamento", "Ano 2024 • Patrimônio SENAI"),
    ("tipo_resultado", "Tipo de resultado", "Avaliação qualitativa"),
    ("unidade", "Unidade executora", "Centro de Excelência em Metrologia SENAI | ZEISS"),
    ("data_hora", "Data de emissão", "{data_hora}"),
)

INTRODUCAO_FALHA_TABLE_ROWS = (
    ("amostra", "AMOSTRA", "1 peça / segmentos avaliados"),
    ("tipo_analise", "TIPO DE ANÁLISE", "Qualitativa"),
    ("metodos", "MÉTODOS", "Visual, óptico e tomográfico"),
    ("mecanismo", "MECANISMO PROVÁVEL", "A definir conforme evidências"),
    ("nucleacao", "NUCLEAÇÃO PROVÁVEL", "A definir conforme evidências"),
    ("tomografia", "TOMOGRAFIA", "Sem indicações internas detectáveis"),
)

DISCUSSAO_FALHA_TABLE_ROWS = (
    ("1", "Geração do esforço transversal", "Deformação, desalinhamento, folga, apoio insuficiente ou carga radial podem produzir flexão."),
    ("2", "Flexão rotativa", "Cada ponto da superfície passa alternadamente por tração e compressão."),
    ("3", "Nucleação superficial", "O concentrador de tensão favorece uma microtrinca."),
    ("4", "Propagação por fadiga", "A trinca avança progressivamente, reduzindo a seção resistente."),
    ("5", "Ruptura final", "A seção remanescente rompe por sobrecarga."),
)
