# Manual do Usuário

**Sistema Inteligente de Pós-processamento de Relatórios de Metrologia**  
Aplicação desktop · Desafio técnico SENAI × ZEISS · Versão 1.0

---

## 1. O que é / para quem

A ferramenta recebe um PDF gerado por equipamentos ZEISS e produz um novo PDF enriquecido: mais claro, rastreável, versionado e com identidade visual SENAI.

**Para quem:** técnicos e responsáveis do laboratório que precisam revisar medições, anexar fotos com marcações, padronizar o layout com templates, registrar controle técnico e emitir o relatório final — sem depender do software proprietário ZEISS na etapa de pós-processamento.

### Três ações que não devem ser confundidas

| Ação | O que faz | Onde |
|---|---|---|
| **Salvar layout…** | Grava ordem/conteúdo padrão como template reutilizável | Workspace → ⋯ (menu) |
| **Nova versão** (`Ctrl+S`) | Registra snapshot no Histórico (entra no PDF) | Aba Histórico |
| **Exportar** (`Ctrl+E`) | Gera o PDF final no disco | Botão Exportar |

---

## 2. Instalação

### Opção A — Executável Windows (quando houver entrega em `.exe`)

O ZIP com `PosProcessadorMetrologia.exe` será gerado se o projeto for escolhido na banca. Até lá, o canal principal é a opção B (código-fonte).

### Opção B — Código-fonte (Python 3.11+)

**Windows**

```bash
cd pos-processador-metrologia
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

**Linux / macOS**

```bash
cd pos-processador-metrologia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

---

## 3. Tela Home

Ao abrir o app você está na Home. No topo: saudação, métricas e atalhos.

### Atalhos da Home

| Controle | Função | Atalho |
|---|---|---|
| Novo arquivo | Abre o wizard Novo Projeto de Medição | `Ctrl+N` |
| Novo template | Abre o editor de templates | `Ctrl+T` |
| Continuar | Retoma o último projeto/export (quando existir) | — |
| Busca | Filtra projetos, exports e templates | `Ctrl+K` |
| Limpar busca/filtros | — | `Esc` |

> *Figura 1 — Tela Home: atalhos, busca e projetos em andamento.*

### Abas

| Aba | Conteúdo |
|---|---|
| **Projetos** | Projetos em andamento — retome a edição sem precisar exportar |
| **Exportados** | PDFs finais já gerados pelo Workspace |
| **Templates** | Modelos oficiais e os que você salvou |

Em cada aba: visualização Lista / Grade, busca e **Refinar resultados** (período, projeto, componente, ordenação).

Nos cards de projeto: badge de modo (MMC, Tomografia, Misto, Análise de falha), abrir com clique, ⋯ para renomear/excluir.

### Barra superior global (vale em qualquer tela)

- **Logo SENAI / Início** — volta à Home
- **?** ou `F1` — Ajuda
- **Preferências** — tema, fonte, limpeza de cache
- **Voltar / Avançar** (`Alt+←` / `Alt+→`) · `F11` tela cheia

---

## 4. Criar um projeto

1. **Novo arquivo** (`Ctrl+N`) ou **Importar PDF** no estado vazio.
2. Preencha **Cliente / Projeto** e **Componente avaliado**.
3. **Adicionar PDFs…** ou arraste arquivos para a zona de drop.
4. Escolha o **Modo do relatório** e o **Template do relatório**.
5. **Abrir workspace**.

> *Figura 2 — Wizard Novo Projeto de Medição.*

### Modos do relatório

| Modo | Quando usar |
|---|---|
| Detectar automaticamente | O app infere CALYPSO (MMC) vs O-Inspect / Bosello |
| Somente MMC (CALYPSO) | Relatório dimensional clássico |
| Somente Tomografia (O-Inspect / Bosello) | PDF de tomografia; template de tomografia |
| Misto (MMC + Tomografia) | Vários PDFs de tipos diferentes no mesmo projeto |
| Análise de falha | Óptico + tomografia; PDF pode ser opcional no início |

O template pode ficar travado em alguns modos (ex.: tomografia / falha usam o modelo correspondente).

---

## 5. Templates

Templates definem quais seções entram no PDF, a ordem, textos padrão e o “esqueleto” do relatório. São o jeito de padronizar a identidade SENAI entre peças e operadores.

### 5.1 Templates oficiais (já vêm no app)

| Nome na UI | Uso típico |
|---|---|
| Template Padrão SENAI/ZEISS | MMC / dimensional (não deletável) |
| Template Tomografia SENAI/Bosello | Bosello |
| Template Análise de Falha (óptico + tomografia) | O-Inspect + Bosello |

Templates criados por você aparecem na mesma lista (podem ser excluídos com ✕).

### 5.2 Gerenciar na Home

1. Aba **Templates**.
2. Clique em um template para editar, ou em **Novo template** (`Ctrl+T`) para criar.
3. Lista ou grade — mesmo padrão das outras abas.

> *Figura 3 — Aba Templates na Home.*

### 5.3 Editor de template

Layout parecido com o Workspace:

- **Sumário** — incluir/excluir seção (checkbox), reordenar (≡), editar defaults (lápis / duplo clique)
- **Dados** — valores de referência do modelo
- **Preview do template** — à direita
- **Nova seção** — seção personalizada no rodapé do sumário
- Nome no topo · **Salvar** · menu ⋯ → **Descartar alterações**

No editor de seção do template você ajusta sobretudo **Conteúdo** e **Layout** (textos e estrutura padrão). Use `{` nos campos de texto para inserir placeholders (ex.: `{componente}`).

> **Dica:** o atalho `Ctrl+S` no Workspace registra versão do relatório; no editor de template use o botão **Salvar**.

> *Figura 4 — Editor de template (sumário, dados e preview).*

### 5.4 Usar um template no projeto

- **Na criação:** combo Template do relatório no wizard.
- **No Workspace:** combo **Layout** na barra do preview, ou ⋯ → **Alterar layout…**

Bolinha laranja **●** ao lado de Layout = layout alterado em relação ao template.

> *Figura 5 — Workspace: menu Exportar e opções de layout.*

### 5.5 Salvar o layout atual como template

Depois de ajustar seções/ordem/textos no Workspace:

1. ⋯ → **Salvar layout…** (habilitado quando o layout está “sujo”).
2. No dialog **Salvar como template**:
   - informe o nome
   - **Criar novo template** ou **Atualizar template atual** (atualizar o template Padrão oficial fica bloqueado — crie um novo)
3. **Salvar**.

Isso **não** gera PDF e **não** cria entrada no Histórico de versões — só grava o modelo para reutilizar.

> *Figura 6 — Dialog Salvar layout como template.*

---

## 6. Workspace — editar o relatório

### Organização da tela

| Região | Função |
|---|---|
| Abas do projeto | Um PDF por peça; **Adicionar PDF** / × remove do projeto (não apaga o arquivo no disco) |
| Lateral **Sumário** | Seções do PDF: checkbox, ordem, editar — clique para ir à seção no preview (bookmarks) |
| Lateral **Dados** | Valores resolvidos dos placeholders (componente, operador, etc.) |
| Lateral **Histórico** | Versões do relatório |
| Centro | Editor da seção aberta |
| Direita | Preview ao vivo + combo Layout + **Exportar** |

Indicadores comuns:

- **● Medições alteradas** — dados da peça mudaram
- **●** no Layout — layout diferente do template (pense em **Salvar layout…**)

> *Figura 7 — Workspace: sumário, editor da seção e preview.*

### 6.1 Sumário e seções

1. **Checkbox** — inclui ou omite a seção no PDF.
2. **Clique** — destaca no preview; duplo clique ou lápis — edita.
3. Arraste **≡** para reordenar.
4. **Nova seção** — cria seção personalizada (pode trocar depois por uma do catálogo oficial no editor).

Abas do editor (conforme a seção): **Conteúdo**, **Tabela**, **Fotografias**, **Gráficos**, **Layout**.

Textos longos: **B** / **I** (`Ctrl+B` / `Ctrl+I`). Botão **?** = ajuda da seção.

### 6.2 Placeholders

Em campos de texto, digite `{` para abrir o catálogo (ex.: `{componente}`, `{operador}`, `{data_hora}`).

- Os valores vêm do PDF importado e podem ser ajustados na aba **Dados**.
- No PDF final, o placeholder é substituído pelo valor atual.

### 6.3 Fotografias da peça

1. Seção desejada → aba **Fotografias**.
2. **+ Escolher arquivo…** ou arraste PNG/JPG (fotos da peça, CAD ou renders).
3. Em tomografia/Bosello: use **Capturas Bosello…** quando o botão aparecer (capturas extraídas do PDF INSPECT).
4. Legenda e ordem conforme necessário — o preview atualiza.

As fotos ficam ligadas à seção (organização automática no PDF).

> *Figura 8 — Aba Fotografias da seção.*

### 6.4 Marcações sobre as imagens

1. Abra o editor de anotações da foto.
2. Ferramentas:
   - **Seta** (`S`) · **Círculo** (`C`) · **Texto** (`T`) · **Nº** (`N`) · **Recorte**
3. Use **+ / − / 100%** para zoom da região medida; **Recorte** recorta o enquadramento que entra no PDF.
4. Desfazer / `Ctrl+Z` na janela de anotações; `Del` remove seleção.
5. **Salve.** As marcações entram no PDF exportado.

> *Figura 9 — Editor de marcações sobre a fotografia.*

### 6.5 Tomografia / Bosello (resumo)

1. Wizard no modo **Tomografia** (ou detecção automática de PDF INSPECT).
2. Após importar, o app pode avisar sobre imagens Bosello.
3. Na aba Fotografias → **Capturas Bosello…** → escolha as vistas → confirme.
4. Anote e exporte como nos demais modos.

Cache de renderizações: **Preferências → Armazenamento** → limpar Bosello, se precisar.

### 6.6 Relatório unificado (vários PDFs)

1. Projeto com ≥ 2 PDFs.
2. ⋯ → **Exportar um único PDF**.
3. Surge a aba **Relatório unificado (N arquivos)** — preview e edição do consolidado.
4. Para voltar às abas por arquivo: ⋯ → **Exportar PDFs individuais**.

Tipos típicos do unificado: lote estatístico (vários MMC) ou híbrido (MMC + Bosello).

> *Figura 10 — Relatório unificado (vários PDFs no mesmo projeto).*

---

## 7. Controle técnico e histórico de versões

### 7.1 Controle Técnico

1. Sumário → seção **Controle Técnico**.
2. Preencha a tabela (rótulos padrão do template):
   - Medido por · Revisado por · Aprovado por (se houver)
   - Cargo · E-mail institucional · Data/Hora
3. Confira no preview — a página faz parte do PDF final.

> *Figura 11 — Seção Controle Técnico.*

### 7.2 Histórico de Versões

1. Aba **Histórico**.
2. **Nova versão** ou `Ctrl+S` → informe responsável e descrição breve.
3. Em cada entrada (⋯ / botão direito): **Visualizar**, **Restaurar e editar**, **Exportar esta versão**.
4. A tabela de versões **compõe o PDF final** (seção Histórico de Versões).

> *Figura 12 — Aba Histórico de versões.*

---

## 8. Exportar o PDF

1. **Exportar** ou `Ctrl+E`.
2. Escolha pasta e nome.
3. Modo definido no menu ⋯:
   - **Exportar PDFs individuais** — um arquivo por aba/peça
   - **Exportar um único PDF** — consolidado (exige 2+ PDFs)

Os exports aparecem na Home → aba **Exportados**.

### O que conferir no leitor

- Logo SENAI e seções ativas
- Fotos e marcações
- Controle técnico e histórico de versões
- **Anexos:** o PDF ZEISS original entra no final, página a página, sem reprocessar o conteúdo — qualidade do documento de origem preservada

Dados locais da sessão: `output_pdfs/` (banco, `templates.json`, logs, preferências).

> *Figura 13 — Preview do relatório pronto para exportar.*

---

## 9. Preferências e acessibilidade

Cabeçalho → **Preferências**:

| Aba | Opções |
|---|---|
| **Acessibilidade** | Tema Escuro / Claro · contraste · tamanho da fonte (85%–140%) · restaurar padrão |
| **Armazenamento** | Limpar cache de preview, renders Bosello, fotos órfãs; remover projetos antigos em andamento |

Alterações de tema/fonte aplicam na hora e são lembradas na próxima abertura.

`F1` / **?** abre a Ajuda com atalhos e dicas rápidas.

> *Figura 14 — Preferências: armazenamento e limpeza de cache.*

---

## 10. Atalhos

| Atalho | Onde | Ação |
|---|---|---|
| `Ctrl+N` | App | Novo projeto |
| `Ctrl+T` | App | Novo template |
| `Ctrl+K` | Home | Busca |
| `Esc` | Home | Limpa busca/filtros |
| `F1` | App | Ajuda |
| `F11` | App | Tela cheia |
| `Alt+←` / `Alt+→` | App | Voltar / avançar |
| `Ctrl+S` | Workspace | Nova versão |
| `Ctrl+E` | Workspace | Exportar |
| `Ctrl+B` / `Ctrl+I` | Editor de texto | Negrito / itálico |
| `S` · `C` · `T` · `N` · `Del` · `Ctrl+Z` | Anotações | Ferramentas / apagar / desfazer |

---

## 11. FAQ / problemas comuns

| Problema | O que tentar |
|---|---|
| App não abre (Python) | Python 3.11+, venv ativo, `pip install -r requirements.txt` |
| App não abre (`.exe`) | Extrair o ZIP inteiro; não mover só o `.exe` |
| PDF sem dados / vazio | Use PDF CALYPSO ou INSPECT real; ajuste template/modo |
| Template “errado” no projeto | Troque no combo Layout ou recrie o projeto no modo certo |
| Não consigo atualizar o template Padrão | Esperado — salve como novo template |
| **Salvar layout…** desabilitado | Só habilita com layout alterado (**●**) |
| Preview lento | PDFs grandes / muitas fotos — aguarde o debounce |
| Logos sumiram | Mantenha `assets/` (fonte) ou rebuild do packaging |
| Unificado indisponível | Precisa de ≥ 2 PDFs no projeto |
| Marcações fora do PDF | Salve o editor de anotações antes de exportar |
| Histórico vazio no PDF | Registre ≥ 1 versão (`Ctrl+S` / Nova versão) |
| Capturas Bosello não aparecem | Confirme PDF INSPECT + modo tomografia; botão só após haver capturas |
| Onde estão os logs? | `output_pdfs/logs/app.log` |

---

## 12. Fluxo rápido (demo / dia a dia)

```text
Home → Novo arquivo → PDFs + modo + template → Workspace
    → seções / fotos / marcações
    → (opcional) ⋯ → Salvar layout…
    → Controle Técnico
    → Ctrl+S  (versão)
    → Ctrl+E  (exportar e abrir o PDF)
```

1. Home → **Novo arquivo** → PDFs + modo + template → Workspace
2. Ajustar seções / fotos / marcações
3. (Opcional) ⋯ → **Salvar layout…** se quiser reutilizar o modelo
4. Preencher **Controle Técnico**
5. `Ctrl+S` — registrar versão
6. `Ctrl+E` — exportar e abrir o PDF
