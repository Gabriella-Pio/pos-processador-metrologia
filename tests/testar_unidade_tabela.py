import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from core.parser.table_extractor import TableExtractor

def testar_tolerancia_unilateral_4_valores():
    print("\n--- TESTE UNITÁRIO: Tolerância Unilateral (4 Valores) ---")

    # 1. Simulando linhas de texto bruto que viriam de um PDF da ZEISS com 4 valores (Tol. Superior + Desvio)
    linhas_mock_positivo = [
        "Diametro_Teste_Unilateral_Positivo",
        "10,0050 mm",  # Valor medido
        "10,0000",   # Nominal
        "0,0100",    # Terceiro valor: POSITIVO -> Deve ser tratado como Tol. Superior (+Tol)
        "0,0060"     # Quarto valor: Desvio
    ]

    itens_pos = TableExtractor.extrair(linhas_mock_positivo)
    assert len(itens_pos) == 1, "Deveria ter extraído 1 item"
    item = itens_pos[0]
    
    print(f"[{item.caracteristica}]")
    print(f"  • Tol. Superior: {item.tol_superior} (Esperado: 0,0100)")
    print(f"  • Tol. Inferior: {item.tol_inferior} (Esperado: N/A)")
    print(f"  • Desvio       : {item.desvio} (Esperado: 0,0060)")
    print(f"  • Status       : {item.status} (Esperado: Dentro)")
    
    assert item.tol_superior == "0,0100"
    assert item.tol_inferior == "N/A"
    assert item.desvio == "0,0060"
    assert item.status == "Dentro"

    # 2. Simulando linhas com o 3º valor NEGATIVO (Tol. Inferior -Tol)
    linhas_mock_negativo = [
        "Diametro_Teste_Unilateral_Negativo",
        "9,9940 mm",   # Valor medido
        "10,0000",   # Nominal
        "-0,0100",   # Terceiro valor: NEGATIVO -> Deve ser tratado como Tol. Inferior (-Tol)
        "-0,0080"    # Quarto valor: Desvio
    ]

    itens_neg = TableExtractor.extrair(linhas_mock_negativo)
    assert len(itens_neg) == 1, "Deveria ter extraído 1 item"
    item_neg = itens_neg[0]
    
    print(f"\n[{item_neg.caracteristica}]")
    print(f"  • Tol. Superior: {item_neg.tol_superior} (Esperado: N/A)")
    print(f"  • Tol. Inferior: {item_neg.tol_inferior} (Esperado: -0,0100)")
    print(f"  • Desvio       : {item_neg.desvio} (Esperado: -0,0080)")
    print(f"  • Status       : {item_neg.status} (Esperado: Dentro)")

    assert item_neg.tol_superior == "N/A"
    assert item_neg.tol_inferior == "-0,0100"
    assert item_neg.desvio == "-0,0080"
    assert item_neg.status == "Dentro"

    print("\n✅ Todos os testes unitários de tolerância unilateral passaram com sucesso!")

if __name__ == "__main__":
    testar_tolerancia_unilateral_4_valores()