# Guia rápido — capturas para o Checkpoint 1

Use este roteiro **antes** de montar o PDF/e-mail. Salve as imagens em `checkpoints/assets/` com os nomes sugeridos.

## Preparação (5 min)

```bash
cd /caminho/pos-processador-metrologia
source venv/bin/activate
python main.py
```

Recomendações visuais:

- Tema **claro** (Ajuda → Acessibilidade) — imprime melhor no relatório.
- Janela **maximizada** (`F11` alterna tela cheia).
- Use um PDF real do laboratório ZEISS/CALYPSO (pasta local ou amostra do desafio).

Opcional — popular a Home com histórico de demo:

```bash
python scripts/prepare_checkpoint_screenshots.py --pdf /caminho/para/relatorio_zeiss.pdf
```

---

## Roteiro de capturas (ordem sugerida)

| # | Arquivo sugerido | Como chegar na tela | O que deve aparecer |
|---|------------------|---------------------|---------------------|
| 1 | `01-home-arquivos.png` | Tela inicial → aba **Arquivos** | Hero com ações, métricas, lista de recentes (ou empty state limpo) |
| 2 | `02-home-templates.png` | Home → aba **Templates** | Grade de templates institucionais |
| 3 | `03-novo-projeto.png` | `Ctrl+N` ou botão **Novo relatório** | Modal: Cliente, Componente, drop zone de PDFs, combo de template |
| 4 | `04-workspace-visao-geral.png` | Após **Abrir workspace** com PDF carregado | Abas do projeto, barra de ação, sumário à esquerda, preview à direita |
| 5 | `05-workspace-sumario.png` | Workspace → aba **Sumário** | Lista com linhas maiores, botão **PDF** visível na barra superior, **+ Nova seção** em estilo ghost, um único **Dados do relatório** acima da lista |
| 6 | `06-workspace-edicao-secao.png` | Clicar **Editar** em Introdução ou Identificação | Painel de edição **abaixo** da lista (sumário permanece visível); placeholders `{componente}` com popup ao digitar `{` |
| 7 | `07-workspace-dados-relatorio.png` | Botão **Dados do relatório** acima da lista (aba Sumário) | Campos globais (operador, componente, etc.) |
| 8 | `08-workspace-fotografias.png` | Editar seção com mídia → **Fotografias** expandido | Painel de imagens + botão **+ Inserir foto** |
| 9 | `09-workspace-historico.png` | Aba **Histórico** no sidebar | Lista de versões + botão nova versão |
| 10 | `10-editor-template.png` | Home → **Gerenciar templates** | Editor com lista de seções, painel de **texto padrão** por seção e preview esqueleto |
| 11 | `11-preview-paginas.png` | Workspace com preview gerado | Pelo menos 2 páginas do PDF enriquecido visíveis |
| 12 | `12-exportacao.png` | Clicar **Exportar** (pode cancelar o diálogo após abrir) | Barra superior com template, **Salvar layout…**, **Exportar** |

---

## Dados sugeridos para o modal “Novo Projeto”

| Campo | Exemplo |
|-------|---------|
| Cliente / Projeto | `Cargill — Inspeção dimensional` |
| Componente avaliado | `Pistão de trabalho` |
| PDFs | 1 arquivo CALYPSO real |
| Template | `Template Padrão SENAI/ZEISS` |

---

## Dicas para o relatório

- Legenda cada figura: *Figura X — [nome da tela] — [o que demonstra]*.
- No Checkpoint 1, deixe claro o que é **protótipo funcional** vs **planejado para CP2** (ex.: marcações avançadas no preview, exportação mesclada).
- Inclua 1 captura do **PDF exportado** aberto no leitor (prova do motor ReportLab).

---

## Checklist antes de enviar

- [ ] 8–12 capturas nítidas (PNG, largura ≥ 1280 px)
- [ ] URL do GitHub preenchida no relatório
- [ ] Nome da equipe / integrantes
- [ ] Data do checkpoint
- [ ] PDF do relatório exportado ou .md anexado ao e-mail
