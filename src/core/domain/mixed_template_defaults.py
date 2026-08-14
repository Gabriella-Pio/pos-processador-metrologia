"""Defaults de prosa/layout para relatório híbrido dimensional + tomográfico."""
from __future__ import annotations

MIXED_TEMPLATE_ID = "mixed"

MIXED_SECTIONS_CONFIG: dict[str, dict] = {
    "cabecalho": {"enabled": True, "order": 0},
    "introducao": {"enabled": True, "order": 1},
    "identificacao": {"enabled": True, "order": 2},
    "metodo_escopo": {"enabled": False, "order": 3},
    "registro_componente": {"enabled": False, "order": 4},
    "resultados": {"enabled": True, "order": 5},
    "grafica": {"enabled": True, "order": 6},
    "tomografia": {"enabled": True, "order": 7},
    "resultados_inspecao": {"enabled": False, "order": 8},
    "interpretacao": {"enabled": True, "order": 9},
    "observacoes_limitacoes": {"enabled": False, "order": 10},
    "historico_versoes": {"enabled": True, "order": 11},
    "controle_tecnico": {"enabled": True, "order": 12},
    "conclusao": {"enabled": True, "order": 13},
    "anexos": {"enabled": True, "order": 14},
}

MIXED_PROSE_DEFAULTS: dict[str, dict[str, str]] = {
    "introducao": {
        "section_title": "RELATÓRIO TÉCNICO — ANÁLISE DIMENSIONAL E TOMOGRÁFICA",
        "objetivo": (
            "Apresentar os resultados da inspeção dimensional e da análise tomográfica "
            "realizada no componente identificado como {componente}, com base nos métodos "
            "{metodos}."
        ),
        "escopo": (
            "A análise contempla as características cadastradas no programa de medição "
            "e a verificação qualitativa de integridade interna por tomografia, "
            "conforme os métodos {metodos}."
        ),
        "referencia": (
            "Valores nominais, limites de tolerância e resultados dimensionais conforme "
            "relatório emitido pelo software ZEISS CALYPSO. A inspeção tomográfica é "
            "qualitativa e baseada nas reconstruções fornecidas."
        ),
        "valor_amostra": "1 peça",
    },
    "tomografia": {
        "section_title": "INSPEÇÃO TOMOGRÁFICA",
        "intro": (
            "Foram avaliadas imagens tomográficas do componente {componente}. "
            "A inspeção teve como finalidade verificar a existência de possíveis "
            "descontinuidades internas, como trincas, vazios, inclusões, porosidades "
            "ou fraturas internas aparentes."
        ),
    },
    "interpretacao": {
        "intro": (
            "Análise consolidada das características dimensionais e da inspeção "
            "tomográfica do componente {componente}:"
        ),
        "nota": (
            "A inspeção tomográfica não evidenciou defeitos ou descontinuidades "
            "internas aparentes nas imagens avaliadas."
        ),
    },
    "conclusao": {
        "texto_aprovado": (
            "Com base no relatório dimensional e nas imagens tomográficas analisadas, "
            "o componente apresentou resultados dimensionais conformes e a inspeção "
            "tomográfica não indicou presença de anomalias internas aparentes."
        ),
        "texto_reprovado": (
            "Com base no relatório dimensional e nas imagens tomográficas analisadas, "
            "o componente apresentou ocorrências dimensionais indicadas pelo software. "
            "A inspeção tomográfica não indicou presença de anomalias internas aparentes "
            "nas imagens fornecidas."
        ),
    },
    "anexos": {
        "intro": (
            "Imagem da página do relatório dimensional gerado no software ZEISS CALYPSO, "
            "utilizado como base para consolidação dos resultados deste documento."
        ),
    },
}

ESTATISTICO_TEMPLATE_ID = "estatistico"

# Layout base: seções de medida começam desligadas; o unificado liga só o que o lote tem.
ESTATISTICO_SECTIONS_CONFIG: dict[str, dict] = {
    "cabecalho": {"enabled": True, "order": 0},
    "introducao": {"enabled": True, "order": 1},
    "identificacao": {"enabled": True, "order": 2},
    "metodo_escopo": {"enabled": False, "order": 3},
    "registro_componente": {"enabled": False, "order": 4},
    "resultados": {"enabled": False, "order": 5},
    "grafica": {"enabled": False, "order": 6},
    "estat_resumo_diametros": {"enabled": False, "order": 7},
    "estat_resumo_alturas": {"enabled": False, "order": 8},
    "estat_resumo_dimensoes": {"enabled": False, "order": 9},
    "estat_resumo_cilindricidades": {"enabled": False, "order": 10},
    "estat_resumo_paralelismos": {"enabled": False, "order": 11},
    "estat_resumo_perpendicularidades": {"enabled": False, "order": 12},
    "estat_resumo_coaxialidades": {"enabled": False, "order": 13},
    "estat_resumo_angulos": {"enabled": False, "order": 14},
    "estat_resumo_outros": {"enabled": False, "order": 15},
    "estat_graficos": {"enabled": True, "order": 16},
    "estat_graficos_comp": {"enabled": True, "order": 17},
    "estat_detalhe_diametros": {"enabled": False, "order": 18},
    "estat_detalhe_alturas": {"enabled": False, "order": 19},
    "estat_detalhe_dimensoes": {"enabled": False, "order": 20},
    "estat_detalhe_cilindricidades": {"enabled": False, "order": 21},
    "estat_detalhe_paralelismos": {"enabled": False, "order": 22},
    "estat_detalhe_perpendicularidades": {"enabled": False, "order": 23},
    "estat_detalhe_coaxialidades": {"enabled": False, "order": 24},
    "estat_detalhe_angulos": {"enabled": False, "order": 25},
    "estat_detalhe_outros": {"enabled": False, "order": 26},
    "tomografia": {"enabled": False, "order": 27},
    "resultados_inspecao": {"enabled": False, "order": 28},
    "interpretacao": {"enabled": True, "order": 29},
    "observacoes_limitacoes": {"enabled": False, "order": 30},
    "historico_versoes": {"enabled": True, "order": 31},
    "controle_tecnico": {"enabled": False, "order": 32},
    "conclusao": {"enabled": True, "order": 33},
    "anexos": {"enabled": True, "order": 34},
}


ESTATISTICO_PROSE_DEFAULTS: dict[str, dict[str, str]] = {
    "introducao": {
        "section_title": "RELATÓRIO ESTATÍSTICO DIMENSIONAL",
        "objetivo": (
            "Apresentar a análise estatística dimensional das características medidas "
            "nos {n_pecas} componentes identificados como {componente}."
        ),
        "escopo": (
            "Foram avaliadas {escopo_medidas}."
        ),
        "referencia": (
            "Valores nominais, limites de tolerância e resultados "
            "individuais conforme registros emitidos pelo software "
            "ZEISS CALYPSO."
        ),
        "valor_amostra": "{n_pecas} peças",
    },
    "anexos": {
        "intro": (
            "Seguem anexos os PDFs de origem das peças do lote, emitidos pelo "
            "software ZEISS CALYPSO, para consulta e rastreabilidade."
        ),
    },
    "historico_versoes": {
        "intro": "Registro das versões emitidas deste relatório consolidado.",
    },
}
