#!/usr/bin/env python3
"""
Prepara dados de demonstração para capturas do Checkpoint 1.

Insere entradas no histórico SQLite para a Home parecer populada.
Opcionalmente valida se o PDF informado existe.

Uso:
    python scripts/prepare_checkpoint_screenshots.py --pdf input_pdfs/amostra.pdf
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.core.infrastructure.database import DatabaseManager  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed de demo para capturas CP1")
    parser.add_argument(
        "--pdf",
        type=Path,
        help="Caminho de um PDF ZEISS para registrar no histórico (opcional)",
    )
    parser.add_argument("--cliente", default="Cargill — Inspeção dimensional")
    parser.add_argument("--componente", default="Pistão de trabalho")
    args = parser.parse_args()

    db = DatabaseManager()
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    samples = [
        ("Relatorio_Pistao_Cargill.pdf", args.cliente, args.componente),
        ("Relatorio_Bomba_Hidraulica.pdf", "Cliente Beta", "Carcaça de bomba"),
        ("Relatorio_Gas_Generator.pdf", "GE Vernova", "Gas Generator Case"),
    ]

    if args.pdf:
        if not args.pdf.exists():
            print(f"AVISO: PDF não encontrado: {args.pdf}")
        else:
            samples.insert(
                0,
                (args.pdf.name, args.cliente, args.componente),
            )

    for nome, cliente, componente in samples:
        caminho = str(args.pdf.resolve()) if args.pdf and nome == args.pdf.name else f"input_pdfs/{nome}"
        db.salvar_registro(
            nome_arquivo=nome,
            cliente_projeto=cliente,
            versao="v1",
            componente=componente,
            data_hora=now,
            responsavel="Equipe Metrologia SENAI",
            caminho=caminho,
        )
        print(f"Registrado: {nome} ({cliente})")

    print("\nPronto. Execute: python main.py")
    print("Capturas: veja checkpoints/GUIA_CAPTURAS_TELA.md")


if __name__ == "__main__":
    main()
