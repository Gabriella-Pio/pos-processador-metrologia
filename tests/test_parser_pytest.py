import pytest

from src.core.parser.parser import PDFParserService


@pytest.mark.parametrize(
    "arquivo",
    [
        "input_pdfs/pistao de trabalho 1.pdf",
        "input_pdfs/global peca pintada.pdf",
        "input_pdfs/CARCACA DE BOMBA 8.pdf",
        "input_pdfs/pistao do produto 2.pdf",
    ],
)
def testar_integridade_relatorios_zeiss(arquivo: str, project_root) -> None:
    path = project_root / arquivo
    if not path.is_file():
        pytest.skip(f"Arquivo de teste não encontrado: {path}")

    dto = PDFParserService.extrair_dados_avancados(str(path))

    assert dto.componente != ""
    assert len(dto.itens_medicao) > 0

    fora_calculados = sum(1 for item in dto.itens_medicao if item.status == "Fora")
    assert fora_calculados == dto.fora_tolerancia_cabecalho, (
        f"Divergência na auditoria para {arquivo}: "
        f"Cabeçalho indicava {dto.fora_tolerancia_cabecalho}, "
        f"mas a tabela calculou {fora_calculados}."
    )
