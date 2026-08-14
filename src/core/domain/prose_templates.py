"""Templates de prosa por seção (placeholders: {componente}, {numero_medicoes}, etc.)."""
from __future__ import annotations

from dataclasses import dataclass

PROSE_TEMPLATES: dict[str, dict[str, str]] = {
    "introducao": {
        "nota": "",
        "intro": "",
        "objetivo": (
            "Apresentar os resultados da inspeção dimensional realizada no componente "
            "identificado como {componente}, com base no relatório de medição ZEISS CALYPSO."
        ),
        "escopo": (
            "A análise contempla as características cadastradas, avaliando conformidade "
            "com os limites nominais e de tolerância."
        ),
        "referencia": (
            "Valores nominais e limites conforme relatório emitido pelo software ZEISS CALYPSO."
        ),
        "valor_amostra": "1 peça",
        "valor_valores": "{numero_medicoes_cabecalho}",
        "valor_fora": "{total_fora} valores",
        "valor_mmc": "{maquina_mmc}",
    },
    "resultados": {
        "intro": (
            "A tabela abaixo apresenta os resultados extraídos do relatório de medição dimensional. "
            "A classificação “Dentro” ou “Fora” foi determinada com base nos limites cadastrados "
            "no relatório ZEISS CALYPSO."
        ),
        # Gerado automaticamente a partir da tabela; editável no workspace.
        "resumo": "",
    },
    "grafica": {
        "intro": (
            "Análises gráficas das características dimensionais do componente."
        ),
    },
    "tomografia": {
        "intro": (
            "Avaliação qualitativa da integridade interna do componente realizada por ensaio tomográfico."
        ),
    },
    "metodo_escopo": {
        "body": "",
    },
    "registro_componente": {
        "intro": "",
    },
    "resultados_inspecao": {
        "body": "",
    },
    "observacoes_limitacoes": {
        "body": "",
    },
    "interpretacao": {
        "intro": (
            "Análise detalhada das {numero_medicoes} características inspecionadas no "
            "componente {componente}:"
        ),
        "nota": "",
    },
    "controle_tecnico": {
        "intro": (
            "Registro dos responsáveis técnicos pela medição, revisão e, quando aplicável, "
            "aprovação deste relatório."
        ),
    },
    "identificacao": {
        "intro": "",
    },
    "conclusao": {
        "texto": "",
        "texto_aprovado": (
            "O componente analisado atende plenamente aos requisitos dimensionais especificados "
            "no relatório de origem, estando aprovado."
            "Este relatório apresenta os dados consolidados para suporte técnico à avaliação do componente. A declaração "
            "formal de conformidade deve considerar os critérios de aceitação definidos em desenho, norma ou "
            "especificação técnica do cliente."
        ),
        "texto_reprovado": (
            "O componente analisado encontra-se reprovado parcialmente devido às divergências "
            "dimensionais constatadas, cabendo avaliação do setor de engenharia e qualidade "
            "para liberação ou retrabalho."
            "Este relatório apresenta os dados consolidados para suporte técnico à avaliação do componente. A declaração "
            "formal de conformidade deve considerar os critérios de aceitação definidos em desenho, norma ou "
            "especificação técnica do cliente."
        ),
        "aprovacao": "Aprovação / Coordenação CEM",
    },
    "historico_versoes": {
        "intro": "Registro das versões emitidas deste relatório.",
    },
    "anexos": {
        "intro": (
            "Seguem anexos os PDFs de origem, provenientes do software ZEISS CALYPSO, "
            "para consulta e rastreabilidade."
        ),
    },
}


@dataclass(frozen=True)
class IntroducaoBlockDef:
    title_key: str
    body_key: str | None
    label: str


INTRODUCAO_CONTENT_BLOCKS: tuple[IntroducaoBlockDef, ...] = (
    IntroducaoBlockDef("title_objetivo", "objetivo", "Objetivo"),
    IntroducaoBlockDef("title_escopo", "escopo", "Escopo da análise"),
    IntroducaoBlockDef("title_referencia", "referencia", "Referência de medição"),
)

INTRODUCAO_BODY_TITLE_KEYS: dict[str, str] = {
    block.body_key: block.title_key
    for block in INTRODUCAO_CONTENT_BLOCKS
    if block.body_key
}

INTRODUCAO_HEADER_ONLY_BLOCKS: tuple[IntroducaoBlockDef, ...] = (
    IntroducaoBlockDef("title_amostra", "valor_amostra", "Amostra"),
    IntroducaoBlockDef("title_valores", "valor_valores", "Valores avaliados"),
    IntroducaoBlockDef("title_fora", "valor_fora", "Fora dos limites"),
    IntroducaoBlockDef("title_mmc", "valor_mmc", "Máquina de medição (MMC)"),
)
