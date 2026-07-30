# src/core/parser/constants.py

CHAVES_COMPONENTE = ("nome", "part name", "componente")
CHAVES_OPERADOR = ("operador", "operator")
CHAVES_MAQUINA_MMC = ("modelo mmc", "nome da mmc", "machine")
CHAVES_NUMERO_MMC = ("numero da mmc", "nº mmc", "no mmc", "n° mmc", "mmc no")
CHAVES_DATA_HORA = ("data/hora", "time/date", "date")
CHAVES_NUMERO_MEDICOES = ("numero de medicoes", "number measured values")
CHAVES_FORA_TOLERANCIA = ("fora da tolerancia", "values red", "values: red")
CHAVES_DURACAO = ("duracao da medicao", "duration")

MAPA_LABELS = {
    "nome": "componente", "part name": "componente", "componente": "componente",
    "serviço oferecido por": "servico_oferecido", "service offered by": "servico_oferecido",
    "nome da mmc": "maquina_mmc", "mmc model": "maquina_mmc", "modelo mmc": "maquina_mmc",
    "numero da mmc": "numero_mmc", "nº mmc": "numero_mmc", "no mmc": "numero_mmc", 
    "n° mmc": "numero_mmc", "mmc no": "numero_mmc", "serial no": "numero_mmc",
    "operador": "operador", "operator": "operador",
    "data/hora": "data_hora", "time/date": "data_hora", "date": "data_hora",
    "run": "run",
    "numero de medições": "numero_medicoes_cabecalho", "numero de medicoes": "numero_medicoes_cabecalho", 
    "number measured values": "numero_medicoes_cabecalho",
    "medições fora da tolerância": "fora_tolerancia_cabecalho", "medicoes fora da tolerancia": "fora_tolerancia_cabecalho", 
    "number values red": "fora_tolerancia_cabecalho", "number values: red": "fora_tolerancia_cabecalho",
    "duração da medição": "duracao_medicao", "duracao da medicao": "duracao_medicao", "duration": "duracao_medicao"
}

LIXO_TECNICO = {
    "diametros", "distancias", "perpendicularidades", "cocentricidades", "coaxialidades",
    "name", "nominal value", "measured value", "desvio", "+tol", "-tol", "+/-", 
    "event", "text", "page", "zeiss calypso", "max", "min", 
    "pontos", "tipo de filtro", "lc", "upr", "vmess[mm/s]", "raio da sonda", 
    "metodo de avaliacao elemento gauss", "metodo de avaliacao elemento minimo",
    "x", "y", "z", "inch", "mm", "graus", "peca:", "data/hora", "calypso", 
    "part n°", "operador", "ajuste automatico", "angulo", "standardprotocol",
    "standart cem", "todas caracteristicas", "run", "parte", "segment 1"
}

# Parâmetros específicos de máquina que devem ser ignorados na tabela
TERMOS_PARAMETROS_MAQUINA = {
    "raio da sonda", "tipo de filtro", "método de avaliação", 
    "metodo de avaliacao", "corner points", "vmes", "upr"
}

# Termos que identificam características geométricas reais
TERMOS_CARACTERISTICAS = {
    "diametro", "cilindricidade", "paralelismo", 
    "coaxialidade", "angulo", "perpendicularidade"
}

# Termos que indicam o fim de um bloco de dados numéricos
TERMOS_PARADA_BLOCO = {
    "name", "nominal value", "measured value", "diametros", 
    "distancias", "perpendicularidades", "cocentricidades", 
    "coaxialidades", "page", "event", "text"
}

SIGLAS_VALIDAS = {
    "ks", "kb", "ps", "pb", "ls", "lb", "rb", "rs", "ab", "as", "db", "ds", "dj", "jb", "js"
}

SECOES_METROLOGIA = {
    "diametros", "distancias", "perpendicularidades", 
    "cocentricidades", "coaxialidades", "cilindricidade", 
    "paralelismo", "angulo", "posicao", "batimento"
}