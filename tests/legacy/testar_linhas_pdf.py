import os
import fitz

def inspecionar_linhas_pdf(caminho_pdf: str):
    if not os.path.exists(caminho_pdf):
        print(f"[Erro] Arquivo não encontrado: {caminho_pdf}")
        return

    print(f"\n[Diagnóstico] Analisando o arquivo: {caminho_pdf}")
    doc = fitz.open(caminho_pdf)
    
    # Cria um arquivo de log para histórico e acompanhamento
    os.makedirs("tests", exist_ok=True)
    log_path = "tests/diagnostico_saida.txt"
    
    with open(log_path, "w", encoding="utf-8") as log_file:
        for num_pag, pagina in enumerate(doc):
            cabecalho_pag = f"\n=== PÁGINA {num_pag + 1} ===\n"
            print(cabecalho_pag)
            log_file.write(cabecalho_pag)
            
            texto = pagina.get_text("text")
            linhas = [l.strip() for l in texto.split("\n") if l.strip()]
            
            for i, linha in enumerate(linhas):
                registro = f"[{i:03d}] -> {linha}\n"
                print(registro, end="")
                log_file.write(registro)
                
    print(f"\n[Sucesso] Relatório de diagnóstico salvo em: {log_path}")

if __name__ == "__main__":
    # Aponta para o seu arquivo real de entrada
    arquivo_alvo = "input_pdfs/CARCACA DE BOMBA 8.pdf"
    inspecionar_linhas_pdf(arquivo_alvo)