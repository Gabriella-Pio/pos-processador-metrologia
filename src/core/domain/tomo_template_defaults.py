"""Prose e campos padrão do template de inspeção tomográfica (modelo CEMSZ)."""
from __future__ import annotations

TOMO_PROSE_DEFAULTS: dict[str, dict[str, str]] = {
    "introducao": {
        "section_title": "RELATÓRIO TÉCNICO — INSPEÇÃO TOMOGRÁFICA INDUSTRIAL",
        "objetivo": (
            "Apresentar os resultados da inspeção por tomografia computadorizada industrial "
            "realizada no componente {componente}, com foco na avaliação não destrutiva de "
            "sua estrutura interna."
        ),
        "escopo": (
            "Ensaio não destrutivo por raios X, com aquisição de projeções em múltiplos ângulos "
            "e reconstrução tomográfica tridimensional do volume interno do componente. Foram "
            "pesquisadas indicações compatíveis com trincas, inclusões ou impurezas, corpos "
            "estranhos e obstruções. A aquisição foi realizada no sistema ZEISS BOSELLO MAX 80-150, "
            "com parâmetros informados de até 225 kV de tensão e 6,2 mA de corrente."
        ),
        "referencia": (
            "Avaliação qualitativa das reconstruções tomográficas e das vistas seccionais do "
            "volume efetivamente inspecionado. A interpretação considera a capacidade de detecção "
            "decorrente da geometria da peça, do material, da espessura atravessada, do contraste "
            "radiográfico, da resolução obtida e dos parâmetros de aquisição e reconstrução."
        ),
        "title_valores": "TIPO DE ANÁLISE",
        "title_fora": "MÉTODO",
        "title_mmc": "EQUIPAMENTO",
        "valor_amostra": "1 peça",
        "valor_tipo_analise": "Qualitativa",
        "valor_metodo": "Não destrutivo",
        "valor_equipamento": "ZEISS BOSELLO MAX 80-150",
        "title_trincas": "TRINCAS INTERNAS",
        "title_impurezas": "IMPUREZAS",
        "title_obstrucoes": "OBSTRUÇÕES",
        "valor_trincas": "Não identificadas",
        "valor_impurezas": "Não identificadas",
        "valor_obstrucoes": "Não identificadas",
        "nota_deteccao": (
            "Nota: “não identificadas” indica ausência de indicações detectáveis nas condições "
            "do ensaio e não constitui garantia absoluta de inexistência de descontinuidades "
            "abaixo do limite de detecção."
        ),
    },
    "identificacao": {
        "section_title": "IDENTIFICAÇÃO E CONDIÇÕES DA INSPEÇÃO",
        "intro": (
            "Dados do cliente, componente e condições de aquisição no sistema ZEISS BOSELLO."
        ),
    },
    "metodo_escopo": {
        "section_title": "MÉTODO E ESCOPO DA AVALIAÇÃO",
        "body": (
            "A inspeção foi executada no sistema industrial ZEISS BOSELLO MAX 80-150 por meio de "
            "um tubo gerador de raios X. O feixe é produzido eletricamente apenas quando o gerador "
            "está energizado; o equipamento não utiliza fonte radioisotópica selada para gerar a "
            "radiação. Foram adquiridas projeções radiográficas do componente em múltiplas "
            "posições angulares e, em seguida, realizada a reconstrução computacional "
            "tridimensional do volume. A avaliação qualitativa das reconstruções e vistas "
            "seccionais permitiu observar regiões internas não acessíveis por inspeção visual "
            "direta. A interpretação ficou restrita ao volume efetivamente reconstruído e não "
            "incluiu quantificação dimensional de descontinuidades nem ensaios funcionais."
        ),
    },
    "registro_componente": {
        "section_title": "REGISTRO DO COMPONENTE",
        "intro": "Fotografias do posicionamento do componente para aquisição tomográfica.",
    },
    "tomografia": {
        "section_title": "INSPEÇÃO TOMOGRÁFICA",
        "intro": (
            "As vistas reconstruídas abaixo apresentam registros representativos da geometria "
            "interna do componente {componente}."
        ),
    },
    "resultados_inspecao": {
        "section_title": "RESULTADOS DA INSPEÇÃO",
        "body": (
            "Nas reconstruções e vistas seccionais analisadas, não foram identificadas indicações "
            "detectáveis compatíveis com trincas internas, inclusões ou impurezas significativas, "
            "corpos estranhos ou obstruções. As passagens observadas apresentaram continuidade "
            "aparente no volume avaliado."
        ),
    },
    "interpretacao": {
        "section_title": "INTERPRETAÇÃO DOS RESULTADOS",
        "intro": "Síntese qualitativa das indicações pesquisadas no volume inspecionado:",
        "bullet_1": "Não foram observadas indicações compatíveis com trincas no volume analisado.",
        "bullet_2": (
            "Não foram observadas inclusões, impurezas ou materiais estranhos detectáveis "
            "nas imagens avaliadas."
        ),
        "bullet_3": (
            "Não foram observadas regiões de bloqueio aparente nos canais internos inspecionados."
        ),
        "bullet_4": (
            "A geometria interna visualizada apresentou continuidade aparente, considerando "
            "as condições e limitações do ensaio."
        ),
    },
    "conclusao": {
        "texto": (
            "A inspeção por tomografia computadorizada industrial, realizada no sistema "
            "ZEISS BOSELLO MAX 80-150, permitiu avaliar de forma não destrutiva a estrutura "
            "interna do componente {componente}. Considerando as reconstruções analisadas e a "
            "capacidade de detecção alcançada nas condições do ensaio, não foram identificadas "
            "indicações detectáveis compatíveis com trincas internas, inclusões ou impurezas "
            "significativas, corpos estranhos ou obstruções. Dessa forma, a peça não apresentou "
            "descontinuidades internas detectáveis que possam ser associadas a comprometimento "
            "aparente de sua integridade estrutural, dentro do escopo desta inspeção."
        ),
        "texto_aprovado": (
            "A inspeção por tomografia computadorizada industrial não identificou indicações "
            "detectáveis compatíveis com descontinuidades relevantes no volume inspecionado."
        ),
        "texto_reprovado": (
            "A inspeção por tomografia computadorizada industrial identificou indicações que "
            "requerem avaliação complementar do setor de engenharia e qualidade."
        ),
    },
    "observacoes_limitacoes": {
        "section_title": "OBSERVAÇÕES E LIMITAÇÕES",
        "body": (
            "Os resultados são aplicáveis exclusivamente ao componente e ao volume efetivamente "
            "inspecionados. A ausência de indicação significa que não foram observadas "
            "descontinuidades detectáveis nas condições empregadas; não constitui garantia "
            "absoluta de inexistência de descontinuidades abaixo do limite de detecção. Este "
            "relatório não estabelece conformidade com desenho, norma de produto ou critério de "
            "aceitação não fornecido e não substitui ensaios funcionais do componente."
        ),
        "aprovacao": "",
    },
}

IDENTIFICACAO_TOMO_TABLE_ROWS = (
    ("client_project", "Cliente / Projeto", "{client_project}"),
    ("evaluated_component", "Componente avaliado", "{evaluated_component}"),
    ("tecnica", "Técnica de inspeção", "Ensaio não destrutivo com reconstrução tomográfica 3D"),
    ("equipamento", "Equipamento", "ZEISS BOSELLO MAX 80-150 (Carl Zeiss X-ray Technologies Srl)"),
    ("ident_equipamento", "Identificação do equipamento", "Ano 2024 • Patrimônio SENAI"),
    ("parametros", "Parâmetros informados", "Tensão do tubo: até 225 kV • Corrente do tubo: até 6,2 mA"),
    ("geracao", "Geração da radiação", "Gerador elétrico por tubo de raios X; sem fonte radioisotópica selada"),
    ("unidade", "Unidade executora", "Centro de Excelência em Metrologia SENAI | ZEISS"),
    ("data_hora", "Data de emissão", "{data_hora}"),
)
