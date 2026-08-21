# Documentação técnica

Documento para quem avalia ou mantém o código. O **manual de utilização** (entregável separado) descreve o uso no laboratório; este texto descreve como o sistema está organizado e por que.

## Objetivo

Aplicação desktop independente dos softwares ZEISS. Recebe um PDF gerado no laboratório (CALYPSO / MMC ou INSPECT / Bosello), permite enriquecer o conteúdo e exporta um novo PDF: mais claro, versionado, com fotos, marcações, controle técnico e o documento original em anexo.

## Stack

| Camada | Tecnologia | Papel |
|---|---|---|
| UI | Python 3.11+, PyQt6, QtAwesome | Desktop, tema SENAI, acessibilidade |
| Parse de PDF | PyMuPDF (`fitz`) | Extração de texto e detecção do tipo de origem |
| Geração de PDF | ReportLab | Relatório enriquecido (seções, tabelas, gráficos) |
| Imagens | Pillow | Crop, marcações e composição antes do PDF |
| Persistência | SQLite + JSON | Projetos, versões, sessões, templates |
| Testes | pytest | Domínio, application, generator, UI (imports / widgets) |

Ponto de entrada: `main.py` → `src.app.bootstrap.create_main_window()`.

## Arquitetura em camadas

O wiring de dependências fica só no composition root (`src/app/bootstrap.py`). A UI **não** importa parser nem ReportLab diretamente.

```text
src/ui          views, viewmodels, dialogs
      ↓ (ports)
src/core/domain     contratos, entidades, catálogo de seções
      ↑
src/core/application    casos de uso (export, templates, mídia, versões)
      ↑
src/core/infrastructure adapters (SQLite, JSON, parser, gerador)
      ↑
src/core/parser         extração CALYPSO / INSPECT
src/core/generator      montagem ReportLab + anexo PyMuPDF
```

**Inversão de dependência:** `src/core/domain/ports.py` define `ReportParser`, `ReportExporter`, repositórios e o modelo `ReportDocument`. Implementações reais estão em `src/core/infrastructure/adapters.py` (`RealReportParserAdapter`, `RealReportExporterAdapter`). Testes de UI usam fakes em `tests/fakes/`.

### O que cada pasta faz

| Pasta | Responsabilidade |
|---|---|
| `src/app/` | Bootstrap / injeção de dependências |
| `src/core/domain/` | Regras e contratos (sem I/O de PDF) |
| `src/core/application/` | Orquestração: export, sessão, templates, fotos, lote |
| `src/core/infrastructure/` | SQLite, JSON de templates, adapters |
| `src/core/parser/` | Texto do PDF ZEISS → DTO |
| `src/core/generator/` | DTO + edições → PDF enriquecido |
| `src/ui/features/home/` | Dashboard, projetos, importação |
| `src/ui/features/workspace/` | Edição do relatório e exportação |
| `src/ui/features/templates/` | Editor de templates |
| `src/ui/shared/report_editor/` | Preview + editor de seções (workspace e templates) |
| `src/ui/components/` | Widgets reutilizáveis (diálogos, anotações, header) |

## Fluxo de dados

```text
PDF ZEISS
    → detect_source_kind (CALYPSO ou INSPECT/Bosello)
    → parser → ReportDocument (memória)
    → Workspace (fotos, marcações, prosa, controle técnico, versões)
    → persistência (SQLite / sessão)
    → build_export_context
    → ReportGenerator (ReportLab)
    → append_source_pdfs (PyMuPDF concatena o original)
    → PDF enriquecido em output_pdfs/
```

1. **Importação.** O wizard de projeto associa cliente, PDFs e template. O parser preenche cabeçalho, medições e `raw_parsed_data` (payload opaco para a UI).
2. **Edição.** O workspace trabalha sobre `ReportDocument`: seções, fotos por seção, anotações (coordenadas 0–1), controle técnico, ordem de blocos.
3. **Preview.** Um worker gera o mesmo PDF do export (em arquivo temporário) para o painel esquerdo acompanhar o resultado real.
4. **Exportação.** `export_context_builder` junta DTO efetivo, prosa, tabelas, fotos compostas e histórico. O gerador monta as seções do template; se Anexos estiver ativo, o PDF de origem é concatenado no final **sem re-renderizar as páginas originais**.

## Funcionalidades do desafio

| Requisito | Onde vive |
|---|---|
| Importação de PDF | Parser + wizard de projeto (`ProjectSetupDialog`) |
| Fotografias da peça | `ReportImage` por seção; importação Bosello quando a origem é INSPECT |
| Marcações (seta, círculo, caixa, número, crop) | Canvas PyQt → `Annotation`; Pillow aplica na imagem antes do PDF |
| Página de Controle Técnico | Seção `controle_tecnico` (medição, revisão, aprovação, cargo, e-mail, data/hora) |
| Histórico de versões | SQLite (`versoes` / `project_versions`) **e** seção `historico_versoes` no PDF |
| Exportação preservando o original | Corpo novo (ReportLab) + páginas originais anexadas (`pdf_annex.py`) |

Diferenciais cobertos no produto: identidade visual SENAI/ZEISS, bookmarks de seção no workspace, zoom/crop no editor de imagem, templates por tipo de ensaio, organização de fotos por seção, suporte a origem CAD/render (imagens anexadas) e captura de frames Bosello.

## Tipos de relatório e templates

Detecção em `src/core/parser/source_kind.py` (marcadores de texto nas primeiras páginas). Fallback: CALYPSO.

| Template | Uso típico |
|---|---|
| `default` | MMC / CALYPSO (medições dimensionais, gráficos, interpretação) |
| `tomografia` | Bosello / ZEISS INSPECT |
| `analise_falha` | Óptico + tomografia |

Projetos podem ser `mmc_only`, `tomo_only`, `mixed` ou `falha`, com um PDF por aba. Em lote/híbrido existe um relatório unificado (agregação estatística entre peças).

O catálogo canônico de seções está em `src/core/domain/section_catalog.py`. UI e gerador compartilham os mesmos IDs — não duplicar títulos ou ordem em outro arquivo.

## Persistência

Tudo em `output_pdfs/` (criado na primeira execução):

| Artefato | Conteúdo |
|---|---|
| `historico.db` | Projetos, versões, documentos exportados, sessões de workspace |
| `templates.json` | Templates do usuário; builtins (`tomografia`, `analise_falha`) vêm do código |
| PDFs exportados | Relatórios gerados |
| `temp/edited/` | Cache de fotos com crop/marcações |
| `logs/app.log` | Log da aplicação |

Sessão de workspace: rascunho por `(PDF origem, cliente, componente)`, para retomar a edição.

## Decisões de projeto

**Desktop PyQt6, não web.** O laboratório precisa de app offline, arquivos locais e preview pesado de PDF.

**Não reescrever o PDF original página a página.** O original é evidência. O valor do produto é o relatório novo (prosa, fotos, controle, versão); o PDF ZEISS entra como anexo fiel via `insert_pdf`.

**Parser heurístico de texto, não OCR.** CALYPSO e INSPECT já trazem texto extraível. Layouts muito diferentes do laboratório podem exigir ajuste em `header_extractor` / `table_extractor`.

**DTO opaco na UI (`raw_parsed_data`).** A interface edita `ReportDocument` e overrides; o formato interno do parser só reaparece na exportação. Isso permite fake de parser nos testes de UI.

**Marcações rasterizadas na foto, não como anotações PDF.** Coordenadas normalizadas (0–1) sobrevivem a redimensionamento; Pillow gera a imagem final que o ReportLab embute. Preview e PDF ficam iguais.

**Templates como lista de blocos.** Cada seção é uma classe no gerador (`REGISTRY_SECOES`). Ativar, reordenar ou criar seção customizada não exige mudar o engine.

**Histórico no banco e no PDF.** O SQLite é a fonte operacional; a seção de versões no PDF atende o requisito de rastreabilidade do documento entregue ao cliente.

## Como executar

Ver o [README](../README.md) na raiz (venv, `requirements.txt`, `python main.py`).

Logs: `output_pdfs/logs/app.log`.

## Testes

Na raiz do repositório:

```bash
python -m pytest tests/ -q
```

Suíte principal em `tests/core/` (parser, application, generator, infrastructure) e `tests/ui/` (imports, widgets, preview). Fakes em `tests/fakes/`. Alguns testes de parser CALYPSO usam PDFs reais em `input_pdfs/` — se a pasta estiver vazia, esses casos são pulados.

Scripts manuais antigos em `tests/legacy/` **não** entram no pytest.

## Limitações conhecidas

- O parser assume o layout típico dos PDFs do laboratório (CALYPSO e INSPECT/Bosello). Outros geradores ZEISS ou PDFs só-imagem tendem a extrair pouco ou nada.
- Origem não reconhecida é tratada como CALYPSO.
- Relatórios Bosello sem PDF (só capturas) usam documento manual — não há tabela CALYPSO nesse modo.
- Bookmarks do desafio estão na navegação do workspace (sumário de seções), não como outline nativo do Adobe Reader.
- Zoom da região medida é no editor de imagem (crop + zoom do canvas), não um viewer de PDF com lupa sobre a página original.
- A última página do PDF gerado inclui as páginas do arquivo ZEISS; o “miolo” enriquecido é sempre conteúdo novo.
- `output_pdfs/historico.db` e `templates.json` são locais da máquina; não há sync em rede.

## Mapa rápido para a banca

| Pergunta | Arquivo |
|---|---|
| Como a app sobe? | `main.py`, `src/app/bootstrap.py` |
| Contrato UI ↔ core | `src/core/domain/ports.py` |
| Parse CALYPSO | `src/core/parser/parser.py` |
| Detecção CALYPSO vs Bosello | `src/core/parser/source_kind.py` |
| Geração do PDF | `src/core/generator/engine.py` |
| Anexo do original | `src/core/generator/components/pdf_annex.py` |
| Controle técnico | `src/core/generator/sections/controle_tecnico_section.py` |
| Histórico no PDF | `src/core/generator/sections/historico_versoes_section.py` |
| Marcações nas fotos | `src/core/application/image_edit_compositor.py` |
| Catálogo de seções | `src/core/domain/section_catalog.py` |
