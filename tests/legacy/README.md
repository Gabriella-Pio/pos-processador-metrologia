# Scripts legados de teste manual

Scripts `testar_*.py` usados antes da suíte pytest estruturada. **Não entram na CI** — execute manualmente a partir da raiz do projeto:

```bash
python tests/legacy/testar_parser.py
python tests/legacy/testar_gerador.py
python tests/legacy/testar_unidade_tabela.py
python tests/legacy/testar_linhas_pdf.py
```

Equivalentes pytest (preferidos):

| Legado | Substituição |
|--------|----------------|
| `testar_parser.py` | `tests/core/parser/test_parser_pytest.py` |
| `testar_gerador.py` | `tests/core/generator/test_generator_tomografia.py` |
| `testar_unidade_tabela.py` | cobertura parcial em `test_parser_pytest.py` |
| `testar_linhas_pdf.py` | diagnóstico ad-hoc; gera `diagnostico_saida.txt` nesta pasta |
