from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate
from .styles import ReportStyles
from .constants import ReportTheme, TEMPLATE_PADRAO_OFICIAL
from src.core.domain.section_numbering import build_section_number_map
from .sections import (
    CabecalhoSection, IntroducaoSection, IdentificacaoSection, ControleTecnicoSection,
    ResultadosSection, GraficaSection, TomografiaSection, InterpretacaoSection,
    ConclusaoSection, HistoricoVersoesSection
)

class ReportGenerator:
    REGISTRY_SECOES = {
        "cabecalho": CabecalhoSection,
        "introducao": IntroducaoSection,
        "identificacao": IdentificacaoSection,
        "controle_tecnico": ControleTecnicoSection,
        "resultados": ResultadosSection,
        "grafica": GraficaSection,
        "tomografia": TomografiaSection,
        "interpretacao": InterpretacaoSection,
        "conclusao": ConclusaoSection,
        "historico_versoes": HistoricoVersoesSection,
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
        versao_relatorio: str = "v1.0",
        controle_tecnico: dict = None,
        historico_versoes: list = None,
        section_page_map: dict | None = None,
        section_prose: dict | None = None,
        placeholder_context: dict | None = None,
        table_rows: dict | None = None,
    ):
        if opcoes_extras is None:
            opcoes_extras = {"incluir_tomografia": False}

        if template_config is None:
            template_config = TEMPLATE_PADRAO_OFICIAL

        doc = _TrackingDocTemplate(
            caminho_saida, pagesize=letter,
            rightMargin=36, leftMargin=36,
            topMargin=36, bottomMargin=36,
            section_page_map=section_page_map,
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
            "versao_relatorio": versao_relatorio,
            "controle_tecnico": controle_tecnico or {},
            "historico_versoes": historico_versoes or [],
            "section_anchor_map": section_page_map if section_page_map is not None else {},
            "section_prose": section_prose or {},
            "placeholder_context": placeholder_context or {},
            "table_rows": table_rows or {},
            "section_number_map": build_section_number_map(template_config),
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
            elif tipo.startswith("custom_"):
                from .sections.custom_section import CustomSection
                CustomSection({**config, "section_id": tipo}).render(
                    story, styles, dados_parseados, contexto_extra
                )

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


class _TrackingDocTemplate(SimpleDocTemplate):
    def __init__(self, *args, section_page_map: dict | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._section_page_map = section_page_map

    def afterFlowable(self, flowable):
        if self._section_page_map is None:
            return
        section_id = getattr(flowable, "_section_id", None)
        if section_id:
            self._section_page_map[section_id] = {
                "page": self.page,
                "x": getattr(flowable, "_anchor_x", None),
                "y": getattr(flowable, "_anchor_y", None),
                "width": getattr(flowable, "_anchor_width", None),
                "height": getattr(flowable, "_anchor_height", None),
                "text": getattr(flowable, "_anchor_text", None),
            }
