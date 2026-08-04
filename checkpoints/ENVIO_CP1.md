# Envio do Checkpoint 1 — checklist e rascunho de e-mail

## Checklist (≈45 min)

- [ ] `python main.py` — tema claro, janela maximizada
- [ ] Capturar PNGs conforme [GUIA_CAPTURAS_TELA.md](./GUIA_CAPTURAS_TELA.md) → salvar em `checkpoints/assets/`
- [ ] Preencher no relatório: **equipe**, **URL do GitHub**
- [ ] (Opcional) Descomentar/inserir figuras no `.md` ou colar capturas no Google Docs
- [ ] Exportar PDF:

```bash
pandoc checkpoints/CHECKPOINT_1_RELATORIO_TECNICO.md \
  -o checkpoints/CHECKPOINT_1_RELATORIO_TECNICO.pdf \
  --resource-path=checkpoints
```

- [ ] Enviar e-mail ao orientador (modelo abaixo)

## Rascunho de e-mail

**Assunto:** Checkpoint 1 — Pós-processador de Relatórios de Metrologia (SENAI × ZEISS)

Olá,

Segue o **Relatório Técnico do Checkpoint 1** (Dia 5) do projeto de pós-processamento e enriquecimento de relatórios PDF de metrologia.

**Repositório:** _[URL do GitHub]_

**Resumo:** Protótipo desktop (PyQt6) com arquitetura hexagonal, parser ZEISS, gerador ReportLab, workspace de edição com preview e exportação PDF. Checkpoint 2 focará em marcações sobre imagens, testes com PDFs reais e refinamento do editor de templates.

Anexo: relatório PDF + link do repositório.

Atenciosamente,  
_[Nome da equipe]_
