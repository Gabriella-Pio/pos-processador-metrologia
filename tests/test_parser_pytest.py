import os
import pytest
from core.parser.parser import PDFParserService

@pytest.mark.parametrize("arquivo", [
    "input_pdfs/pistao de trabalho 1.pdf",
    "input_pdfs/global peca pintada.pdf",
    "input_pdfs/CARCACA DE BOMBA 8.pdf",
    "input_pdfs/pistao do produto 2.pdf"
])
def testar_integridade_relatorios_zeiss(arquivo):
    assert os.path.exists(arquivo), f"Arquivo de teste não encontrado: {arquivo}"
    
    dto = PDFParserService.extrair_dados_avancados(arquivo)
    
    # Validações estruturais obrigatórias
    assert dto.componente != ""
    assert len(dto.itens_medicao) > 0
    
    # Auditoria de tolerâncias por contagem exata
    fora_calculados = sum(1 for item in dto.itens_medicao if item.status == "Fora")
    assert fora_calculados == dto.fora_tolerancia_cabecalho, (
        f"Divergência na auditoria para {arquivo}: "
        f"Cabeçalho indicava {dto.fora_tolerancia_cabecalho}, mas a tabela calculou {fora_calculados}."
    )