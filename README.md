# Sistema Inteligente de Pós-processamento de Relatórios de Metrologia

Aplicação desktop desenvolvida para o desafio técnico do SENAI ZEISS. O objetivo da ferramenta é converter relatórios PDF brutos gerados por equipamentos ZEISS (como o software CALYPSO) em um documento enriquecido, claro, rastreável, versionado e com padrão profissional.

## Tecnologias

- Python 3.11+
- PyQt6 (interface desktop)
- QtAwesome (ícones corporativos)
- PyMuPDF (leitura / preview)
- ReportLab (geração de PDF)

## Estrutura do projeto

```text
pos-processador-metrologia/
├── main.py                 # Entry point
├── assets/                 # Logos SENAI
├── input_pdfs/             # PDFs de teste (origem)
├── output_pdfs/            # PDFs exportados, templates.json, histórico SQLite
├── src/
│   ├── app/                # Composition root (bootstrap / DI)
│   ├── core/
│   │   ├── domain/         # Ports, entidades, schemas, registries
│   │   ├── application/    # Casos de uso
│   │   ├── infrastructure/ # Adapters, repos, SQLite/JSON
│   │   ├── parser/         # Extração de PDFs ZEISS
│   │   └── generator/      # Geração ReportLab
│   └── ui/
│       ├── accessibility/  # Tema / escala de fonte (global)
│       ├── components/     # Widgets compartilhados
│       ├── controllers/    # AppState, navegação (app-wide)
│       ├── dialogs/        # Dialogs realmente compartilhados
│       ├── features/
│       │   ├── home/       # components, models, dialogs, viewmodels
│       │   ├── workspace/  # components, dialogs, services, viewmodels
│       │   └── templates/  # editor / gestão de templates
│       └── styles/
└── tests/
```

## Executar

```bash
# Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

```bash
# Windows
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

## Fluxo principal

1. **Home** — abas **Arquivos** (recentes + novo relatório) e **Templates**
2. **Novo projeto** — wizard em 3 passos (projeto → PDFs → template)
3. **Workspace** — preview à esquerda, editor de seções à direita, abas por PDF do projeto
4. **Exportar** — PDF individual ou lote

## Testes UI

```bash
python -m pytest tests/ui/test_ui_imports.py -v
```

## Cronograma

* **Duração:** 15 dias úteis (3 semanas)
* **Checkpoint 1 (Dia 5):** Arquitetura, protótipos de tela e núcleo funcional de leitura de PDF.
* **Checkpoint 2 (Dia 10):** Demonstração completa (Fim do desenvolvimento de novas funcionalidades).
* **Entrega Final (Dia 15):** Correção de bugs, testes, documentação e apresentação prática de 10 minutos.

