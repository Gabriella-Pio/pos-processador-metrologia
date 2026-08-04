# Checkpoints — entregas parciais do desafio

| Arquivo | Descrição |
|---------|-----------|
| [CHECKPOINT_1_RELATORIO_TECNICO.md](./CHECKPOINT_1_RELATORIO_TECNICO.md) | Relatório completo do Dia 5 (enviar ao orientador) |
| [GUIA_CAPTURAS_TELA.md](./GUIA_CAPTURAS_TELA.md) | Passo a passo para screenshots do protótipo |
| [assets/](./assets/) | Pasta para salvar as imagens (`01-home-arquivos.png`, etc.) |
| [ENVIO_CP1.md](./ENVIO_CP1.md) | Checklist final e rascunho de e-mail para o orientador |

## Antes de enviar o e-mail

1. Preencher no relatório: **equipe**, **data**, **URL do GitHub**.
2. Seguir o guia de capturas e inserir as figuras no PDF final.
3. Anexar: relatório PDF + link do repositório (e opcionalmente ZIP do tag `checkpoint-1`).

## Gerar PDF do relatório (opcional)

```bash
# Com pandoc instalado:
pandoc checkpoints/CHECKPOINT_1_RELATORIO_TECNICO.md \
  -o checkpoints/CHECKPOINT_1_RELATORIO_TECNICO.pdf \
  --resource-path=checkpoints
```

Ou exporte pelo VS Code / Typora / Google Docs colando o conteúdo do `.md`.
