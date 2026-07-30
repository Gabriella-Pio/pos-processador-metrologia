import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from core.parser.parser import PDFParserService

def testar():
    arquivos = [
        "input_pdfs/pistao de trabalho 1.pdf",
        "input_pdfs/global peca pintada.pdf",
        "input_pdfs/CARCACA DE BOMBA 8.pdf",
        "input_pdfs/pistao do produto 2.pdf"
    ]
    
    for arq in arquivos:
        if not os.path.exists(arq):
            print(f"[Aviso] Arquivo não encontrado: {arq}")
            continue
            
        print(f"\n" + "="*60)
        print(f"TESTANDO ARQUIVO: {arq}")
        print(f"="*60)
        
        dto = PDFParserService.extrair_dados_avancados(arq)
        
        # Contagem dinâmica dos itens fora de tolerância na tabela extraída
        itens_fora_calculados = sum(1 for item in dto.itens_medicao if item.status == "Fora")
        
        print(f"Componente        : {dto.componente}")
        print(f"MMC               : {dto.maquina_mmc} (Nº: {dto.numero_mmc})")
        print(f"Operador          : {dto.operador}")
        print(f"Data/Hora         : {dto.data_hora}")
        print(f"Duração           : {dto.duracao_medicao}")
        print(f"Total Medições    : {dto.numero_medicoes_cabecalho} (Itens na tabela: {len(dto.itens_medicao)})")
        print(f"Fora de Tolerância: Cabeçalho = {dto.fora_tolerancia_cabecalho} | Calculado da Tabela = {itens_fora_calculados}")
        
        # Mini relatório de auditoria final
        if dto.fora_tolerancia_cabecalho == itens_fora_calculados:
            print(f"✅ Auditoria de Tolerância: OK (Bateu perfeitamente!)")
        else:
            print(f"⚠️ Atenção: Divergência entre cabeçalho e contagem da tabela!")

        if dto.avisos_auditoria:
            print(f"⚠️ Alerta: {dto.avisos_auditoria}")

        print(f"\n--- DETALHAMENTO DA TABELA DIMENSIONAL ---")
        for idx, item in enumerate(dto.itens_medicao, 1):
            print(f"  [{idx}] {item.caracteristica} | Medido: {item.valor_medido} | Desvio: {item.desvio} | Status: {item.status}")

if __name__ == "__main__":
    testar()