# Sistema Inteligente de Pós-processamento de Relatórios de Metrologia

Aplicação desktop desenvolvida para o desafio técnico do SENAI ZEISS. Converte relatórios PDF gerados por equipamentos ZEISS (CALYPSO / MMC e INSPECT / Bosello) em um documento enriquecido, claro, rastreável, versionado e com padrão profissional.

Ferramenta **independente** dos softwares ZEISS: o original entra como evidência (anexo); o valor entregue é o relatório novo.

## Documentação

| Documento | Público | Conteúdo |
|---|---|---|
| [docs/arquitetura.md](docs/arquitetura.md) | Banca / manutenção | Arquitetura, fluxo, decisões, persistência, limitações |
| [docs/manual-usuario.md](docs/manual-usuario.md) | Técnico do laboratório / demo | Como usar a interface no dia a dia |
| Este README | Quem clona o repositório | Instalar, executar e testar |

## Tecnologias

- Python 3.11+
- PyQt6 (interface desktop)
- QtAwesome (ícones)
- PyMuPDF (leitura do PDF de origem e anexo no PDF final)
- ReportLab (geração do relatório enriquecido)
- Pillow (crop e marcações nas fotografias)
- SQLite (projetos, versões, sessões)

## Estrutura do projeto

```text
pos-processador-metrologia/
├── main.py                 # Entry point
├── docs/arquitetura.md     # Documentação técnica
├── docs/manual-usuario.md  # Manual de utilização
├── assets/                 # Logos SENAI / ZEISS (cabeçalho do PDF)
├── input_pdfs/             # PDFs de teste (origem do laboratório)
├── output_pdfs/            # Exportações, templates.json, historico.db, logs
├── src/
│   ├── app/                # Composition root (bootstrap / DI)
│   ├── core/
│   │   ├── domain/         # Ports, entidades, catálogo de seções
│   │   ├── application/    # Casos de uso
│   │   ├── infrastructure/ # Adapters, repos, SQLite/JSON
│   │   ├── parser/         # Extração de PDFs ZEISS
│   │   └── generator/      # Geração ReportLab + anexo do original
│   └── ui/
│       ├── accessibility/  # Tema / escala de fonte
│       ├── components/     # Widgets compartilhados
│       ├── controllers/    # AppState, navegação
│       ├── features/
│       │   ├── home/       # Dashboard e novo projeto
│       │   ├── workspace/  # Edição e exportação
│       │   └── templates/  # Editor de templates
│       └── shared/         # Preview + editor de seções
└── tests/
```

Detalhes de camadas, fluxo PDF→PDF e decisões: [docs/arquitetura.md](docs/arquitetura.md).

## Executar

```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

```bash
# Windows (PowerShell)
py -m venv venv
venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py main.py
```

```bash
# Windows (cmd)
py -m venv venv
venv\Scripts\activate.bat
py -m pip install -r requirements.txt
py main.py
```

Logs da sessão: `output_pdfs/logs/app.log`.

## Fluxo principal

1. **Home** — abas **Arquivos** (projetos / recentes) e **Templates**
2. **Novo projeto** — wizard (projeto → PDFs → template)
3. **Workspace** — preview à esquerda, editor de seções à direita, abas por PDF
4. **Exportar** — PDF individual ou lote (o original ZEISS vai no anexo)

## Testes

```bash
python -m pytest tests/ -q
```

A suíte cobre parser, geração, repositórios e UI. Scripts manuais em `tests/legacy/` não entram no pytest.

## Cronograma do desafio

* **Duração:** 15 dias úteis (3 semanas)
* **Checkpoint 1 (Dia 5):** Arquitetura, protótipos de tela e núcleo de leitura de PDF
* **Checkpoint 2 (Dia 10):** Aplicação funcional (fim de funcionalidades novas)
* **Entrega final (Dia 15):** Bugs, UX, testes, documentação, manual e apresentação (máx. 10 min)

