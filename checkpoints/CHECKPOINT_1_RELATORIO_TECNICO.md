# RELATÓRIO TÉCNICO — CHECKPOINT 1

**Projeto:** Sistema de Pós-Processamento e Enriquecimento de Relatórios de Metrologia  
**Desafio:** SENAI × ZEISS — Pós-processamento de relatórios PDF  
**Equipe:** _[Nome dos integrantes]_  
**Data:** 04/08/2026  
**Repositório GitHub:** _[https://github.com/…/pos-processador-metrologia]_  

---

## 1. Visão geral e alinhamento técnico

A aplicação foi projetada para operar de forma **independente dos softwares proprietários ZEISS** (como o CALYPSO), oferecendo uma experiência de software corporativo voltada ao pós-processamento de relatórios técnicos de metrologia industrial.

**Objetivo do produto:** receber um relatório PDF gerado por equipamentos ZEISS e produzir um **novo PDF enriquecido** — mais claro, rastreável, versionado e com identidade visual SENAI.

**Escopo do Checkpoint 1 (Dia 5):** conforme a proposta do desafio, esta entrega comprova:

1. **Arquitetura da solução** definida e implementada em código.
2. **Protótipo de telas** navegável (Home, importação, Workspace).
3. **Estratégia de desenvolvimento** e cronograma das próximas duas semanas.
4. **Núcleo técnico inicial:** parser de PDF ZEISS + motor de geração ReportLab integrados via ports/adapters.

---

## 2. Stack tecnológica

| Camada | Tecnologia | Papel |
|--------|------------|--------|
| Linguagem | Python 3.11+ | Tipagem estrita, testes pytest |
| UI desktop | PyQt6 | MVVM, QStackedWidget, design tokens (QSS) |
| Ícones | QtAwesome | Iconografia corporativa |
| Leitura PDF | PyMuPDF (fitz) | Preview interativo no Workspace |
| Parser ZEISS | Módulo próprio (`src/core/parser/`) | Metadados CALYPSO, tabelas de medição |
| Geração PDF | ReportLab | Seções modulares (Cabeçalho, Introdução, Resultados…) |
| Imagens | Pillow | Proporção e tratamento de fotografias |
| Persistência | SQLite3 + JSON | Histórico de versões, arquivos recentes, templates |
| Marcações (roadmap) | QPainter / OpenCV | Setas, círculos e numeração sobre fotos |

---

## 3. Arquitetura de software

### 3.1 Padrão adotado

O projeto segue **Ports and Adapters (Arquitetura Hexagonal)** com camada de **casos de uso** (`src/core/application/`), garantindo que a UI não dependa diretamente do parser ZEISS nem do ReportLab.

```text
┌─────────────────────────────────────────────────────────┐
│  UI (PyQt6)                                             │
│  features/home · features/workspace · features/templates│
│  ViewModels · Presenters · Services                   │
└──────────────────────────┬──────────────────────────────┘
                           │ ports (interfaces)
┌──────────────────────────▼──────────────────────────────┐
│  core/application/   casos de uso (export, edição, layout)│
│  core/domain/        entidades, ports, schemas            │
│  core/infrastructure/ adapters, repos SQLite/JSON        │
│  core/parser/        extração PDF ZEISS                 │
│  core/generator/     montagem PDF ReportLab               │
└───────────────────────────────────────────────────────────┘
```

### 3.2 Estrutura de pacotes (resumo)

| Pacote | Responsabilidade |
|--------|------------------|
| `src/ui/features/home/` | Dashboard, importação, arquivos recentes |
| `src/ui/features/workspace/` | Editor, preview, sumário, histórico |
| `src/ui/features/templates/` | Editor de templates institucionais |
| `src/ui/components/` | Design system compartilhado (botões, cards, header) |
| `src/core/domain/ports.py` | Contratos: Parser, Exporter, Repositories |
| `src/core/infrastructure/adapters.py` | Ponte única parser + generator ↔ UI |
| `src/core/application/` | Validação de export, dirty state, sync de campos |
| `src/app/bootstrap.py` | Composition root (injeção de dependências) |

### 3.3 Fluxo principal de dados

1. **Importação** — PDF CALYPSO → `ReportParser` → `ReportDocument` (DTO + metadados opacos).
2. **Edição** — overrides em `section_overrides` / `parsed_overrides` + imagens por seção.
3. **Preview** — export temporário + rasterização fitz (worker assíncrono).
4. **Exportação** — `ReportExporter` → PDF final com Controle Técnico e Histórico de Versões.

### 3.4 Decisões de projeto relevantes ao CP1

- **MVVM** na UI: Views emitem sinais; ViewModels orquestram core e services.
- **Feature folders** (`features/workspace/…`) para colocar componentes, VM e services juntos.
- **Templates JSON** com `content_defaults` para salvar layout a partir do Workspace.
- **Separação layout vs dados** (`is_layout_dirty` / `is_data_dirty`) para “Salvar layout” vs exportação.

---

## 4. Funcionalidades — status no Checkpoint 1

Referência: proposta do desafio (funcionalidades obrigatórias + diferenciais).

| # | Funcionalidade | Status CP1 | Observação |
|---|----------------|------------|------------|
| 1 | Importação de PDF | ✅ Implementado | Drag-and-drop, lote, wizard de projeto |
| 2 | Fotografias da peça | ✅ Implementado | Associação por seção, painel de imagens |
| 3 | Marcações sobre imagens | 🟡 Parcial | Toolbar e estrutura; interação no preview em evolução (CP2) |
| 4 | Página Controle Técnico | ✅ Implementado | Campos editáveis + geração no PDF |
| 5 | Histórico de versões | ✅ Implementado | SQLite + registro manual + bloco no PDF |
| 6 | Exportação PDF | ✅ Implementado | Individual e lote; validação pré-export |
| — | Bookmarks / sumário | ✅ Implementado | Navegação por seções no Workspace |
| — | Identidade SENAI | ✅ Implementado | Logos, tipografia, templates oficiais |
| — | Preview interativo | ✅ Implementado | PyMuPDF, atualização debounced |

Legenda: ✅ concluído · 🟡 em progresso · ⬜ planejado

---

## 5. Protótipo de telas

Layout real do **Workspace:** coluna esquerda = sumário + edição inline abaixo da lista; coluna direita = preview do PDF enriquecido. Template é escolhido apenas na barra de ação superior (sem duplicata no sidebar).

**Polish CP1 (pré-capturas):** botão **Adicionar PDF** com ícone e rótulo; linhas do sumário ampliadas; **Nova seção** em estilo ghost; edição de seção sem substituir o sumário; popup de placeholders `{` em campos multilinha; editor de templates com painel de texto padrão por seção (MVP — refinamento completo no CP2).

### 5.1 Telas capturadas

> Inserir as imagens em `checkpoints/assets/` (ver `GUIA_CAPTURAS_TELA.md`).

| Figura | Tela | Descrição |
|--------|------|-----------|
| Figura 1 | Dashboard — Arquivos | Hub central: ações rápidas, busca, arquivos recentes |
| Figura 2 | Dashboard — Templates | Catálogo de templates SENAI/ZEISS |
| Figura 3 | Novo projeto | Modal único: cliente, componente, PDFs, template |
| Figura 4 | Workspace — visão geral | Projeto carregado, preview e sumário |
| Figura 5 | Workspace — edição de seção | Painel abaixo do sumário; placeholders com popup `{` |
| Figura 6 | Workspace — dados globais | Botão único “Dados do relatório” acima da lista |
| Figura 7 | Workspace — fotografias | Inserção e gestão de imagens por seção |
| Figura 8 | Workspace — histórico | Versões do relatório |
| Figura 9 | Editor de templates | Estrutura de seções, textos padrão editáveis (MVP) e preview |
| Figura 10 | PDF exportado | Amostra do documento final gerado |

<!-- Exemplo de inclusão no PDF final:
![Figura 1 — Dashboard Arquivos](assets/01-home-arquivos.png)
-->

### 5.2 Fluxo demonstrado na apresentação

1. Abrir aplicação → **Home**.  
2. **Novo relatório** → preencher projeto e arrastar PDF CALYPSO.  
3. **Workspace** → navegar sumário, editar seção, visualizar preview.  
4. (Opcional) Registrar versão e **Exportar** PDF.

---

## 6. Núcleo técnico validado

### 6.1 Parser (`src/core/parser/`)

- Extração de cabeçalho CALYPSO (operador, data, equipamento).
- Tabela de itens de medição (`MedicaoItemDto`).
- Normalização de unidades e status (Dentro/Fora).

### 6.2 Gerador (`src/core/generator/`)

- Registry de seções plugáveis (`engine.py`).
- Numeração dinâmica de seções.
- Placeholders `{componente}`, `{operador}`, etc.
- Fotos agrupadas por seção no PDF final.

### 6.3 Testes automatizados

```bash
python -m pytest tests/test_report_editing.py tests/test_application.py tests/test_ui_imports.py -q
```

Cobertura atual: edição de overrides, presenter de sumário, smoke de imports UI, casos de uso da camada application.

---

## 7. Estratégia de desenvolvimento e cronograma (15 dias úteis)

**Ferramentas:** Git/GitHub, commits convencionais, sprints semanais alinhados aos checkpoints.

| Período | Marco | Entregas |
|---------|-------|----------|
| **Semana 1 (concluída — CP1)** | Dia 5 | Arquitetura, ports/adapters, UI prototipada, parser + generator validados |
| **Semana 2 (até CP2 — 11/08)** | Dia 10 | Integração UI↔core em fluxo completo, testes com PDFs reais, marcações estáveis |
| **Semana 3 (entrega — 18/08)** | Dia 15 | Bugfix, UX, manual, apresentação 10 min, demo com PDF do laboratório |

**Regra pós-CP2:** sem funcionalidades novas na última semana — apenas correções, UX, documentação e testes.

### 7.1 Prioridades imediatas (pós-CP1 → CP2)

1. Consolidar marcações sobre imagens (setas, círculos, texto).
2. Testes de regressão com lote de PDFs ZEISS reais.
3. Refinar preview (performance e sincronização com edição).
4. Manual de utilização (primeiro rascunho na semana 3).

---

## 8. Riscos e mitigações

| Risco | Mitigação |
|-------|-----------|
| Variação de layout entre PDFs CALYPSO | Parser tolerante + overrides manuais no Workspace |
| Complexidade da UI de edição | MVVM + feature folders; preview assíncrono |
| Prazo CP2 | Escopo congelado após dia 10; foco em fluxo feliz com 1–2 PDFs oficiais |

---

## 9. Conclusão do Checkpoint 1

Até o Dia 5, a equipe entrega:

- ✅ Arquitetura hexagonal documentada e refletida no repositório.  
- ✅ Protótipo navegável das telas principais (Home, importação, Workspace, templates).  
- ✅ Motor de leitura e geração de PDF operacional.  
- ✅ Plano claro para Checkpoint 2 e entrega final.

O sistema já demonstra o caminho completo **PDF bruto → edição enriquecida → PDF institucional**, alinhado ao resultado esperado do desafio.

---

## Anexos

- `checkpoints/GUIA_CAPTURAS_TELA.md` — roteiro de screenshots  
- `scripts/prepare_checkpoint_screenshots.py` — seed de demo para Home  
- `README.md` — instruções de execução e estrutura do projeto  

---

_Relatório preparado para envio ao orientador do desafio. Converter para PDF (Pandoc, Typora ou exportação do editor) antes do e-mail, se necessário._
