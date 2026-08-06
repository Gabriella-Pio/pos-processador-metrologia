import sys
import os

# Garante que a pasta src está no path de execução
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from core.parser.parser import PDFParserService
from core.generator import ReportGenerator

def testar_geracao_modular():
    print("[Teste] Processando o PDF bruto...")
    dados_dto = PDFParserService.extrair_dados_avancados("input_pdfs/global peca pintada.pdf")
    
    # Cria a pasta de saída se não existir
    os.makedirs("output_pdfs", exist_ok=True)
    caminho_saida = "output_pdfs/Relatorio_Enriquecido_Com_Foto.pdf"

    # Caminho para uma imagem de teste (substitua pelo caminho de uma foto real se tiver)
    # Se o arquivo não existir, o gerador usará o placeholder automaticamente de forma segura.
    caminho_foto_teste = "input_pdfs/peca_exemplo.png" 

    print(f"[Teste] Gerando o relatório modular com foto para: {caminho_saida}")
    
    # Gera o relatório componentizado passando a foto nas opções extras
    ReportGenerator.gerar_relatorio_enriquecido(
        dados_parseados=dados_dto,
        caminho_saida=caminho_saida,
        cliente_projeto="Cargill Agrícola S.A. - Lote 02",
        componente_avaliado="Gas Generator Case Pintada",
        logo_senai_path="assets/logo-senai.png",
        logo_zeiss_path="assets/logo-centro.png",
        opcoes_extras={
            "incluir_tomografia": True,
            "caminho_foto_peca": caminho_foto_teste # <--- Passa o caminho aqui!
        }
    )
    
    print("[Teste] Relatório gerado com sucesso!")

if __name__ == "__main__":
    testar_geracao_modular()