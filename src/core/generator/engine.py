from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate
from .styles import ReportStyles
from .constants import ReportTheme, TEMPLATE_PADRAO_OFICIAL
from .sections import (
    CabecalhoSection, IntroducaoSection, IdentificacaoSection, ResultadosSection,
    GraficaSection, TomografiaSection, InterpretacaoSection, ConclusaoSection
)

class ReportGenerator:
    REGISTRY_SECOES = {
        "cabecalho": CabecalhoSection,
        "introducao": IntroducaoSection,
        "identificacao": IdentificacaoSection,
        "resultados": ResultadosSection,
        "grafica": GraficaSection,
        "tomografia": TomografiaSection,
        "interpretacao": InterpretacaoSection,
        "conclusao": ConclusaoSection
    }

    @classmethod
    def gerar_relatorio_enriquecido(
        cls, 
        dados_parseados, 
        caminho_saida: str, 
        cliente_projeto: str = "Não informado", 
        componente_avaliado: str = "Não informado",
        opcoes_extras: dict = None,
        template_config: list = None,
        fotos_secoes: dict = None,
        logo_senai_path: str = None,
        logo_zeiss_path: str = None,
        versao_relatorio: str = "v1.0"
    ):
        if opcoes_extras is None:
            opcoes_extras = {"incluir_tomografia": False}

        if template_config is None:
            template_config = TEMPLATE_PADRAO_OFICIAL

        doc = SimpleDocTemplate(
            caminho_saida, pagesize=letter,
            rightMargin=36, leftMargin=36,
            topMargin=36, bottomMargin=36
        )
        
        story = []
        styles = ReportStyles.criar_estilos()
        
        contexto_extra = {
            "cliente_projeto": cliente_projeto,
            "componente_avaliado": componente_avaliado,
            "opcoes_extras": opcoes_extras,
            "fotos_secoes": fotos_secoes or {},
            "logo_senai_path": logo_senai_path,
            "logo_zeiss_path": logo_zeiss_path,
            "versao_relatorio": versao_relatorio
        }

        for bloco in template_config:
            tipo = bloco.get("tipo")
            config = bloco.get("config", {})
            
            if tipo == "tomografia" and not opcoes_extras.get("incluir_tomografia", False):
                continue

            if tipo in cls.REGISTRY_SECOES:
                secao_classe = cls.REGISTRY_SECOES[tipo]
                instancia_secao = secao_classe(config)
                instancia_secao.render(story, styles, dados_parseados, contexto_extra)

        doc.build(story, onFirstPage=cls._adicionar_rodape, onLaterPages=cls._adicionar_rodape)
        print(f"[Engine] Relatório modular gerado com sucesso em: {caminho_saida}")
    @staticmethod
    def _adicionar_rodape(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(ReportTheme.COR_SECUNDARIA)
        canvas.drawString(36, 18, "CEM SENAI | ZEISS Goiânia - GO • Uso restrito ao cliente")
        canvas.drawRightString(letter[0] - 36, 18, f"Página {doc.page}")
        canvas.restoreState()