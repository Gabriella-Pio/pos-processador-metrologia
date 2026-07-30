# Sistema Inteligente de Pós-processamento de Relatórios de Metrologia

Aplicação desktop desenvolvida para o desafio técnico do SENAI ZEISS. O objetivo da ferramenta é converter relatórios PDF brutos gerados por equipamentos ZEISS (como o software CALYPSO) em um documento enriquecido, claro, rastreável, versionado e com padrão profissional.

## Tecnologias Utilizadas

- **Python 3.11+**
- **PyQt6** (Interface Gráfica)
- **PyMuPDF / fitz** (Extração de dados e leitura de PDFs)
- **ReportLab** (Geração e estilização de novos PDFs)

---

## Estrutura do Projeto

```text
pos-processador-metrologia/
│
├── venv/                # Ambiente virtual Python
├── assets/              # Recursos visuais (logos, imagens, ícones)
├── input_pdfs/          # Relatórios PDF brutos de origem (ex: CALYPSO)
├── output_pdfs/         # Relatórios PDF finais enriquecidos
├── parser_teste.py      # Script de teste para leitura e extração de texto
├── main.py              # Aplicação principal (Interface Gráfica PyQt6)
└── requirements.txt     # Dependências do projeto
```

---

## Como Configurar e Executar o Projeto (Linux / Debian)

Siga os passos abaixo no terminal para configurar o ambiente de desenvolvimento na máquina:

### 1. Clonar ou abrir a pasta do projeto

Certifique-se de estar na pasta raiz `pos-processador-metrologia`.

### 2. Criar e Ativar o Ambiente Virtual

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Instalar as Dependências

Com o ambiente virtual ativado (`(venv)` visível no terminal), instale os pacotes necessários:

```bash
pip install -r requirements.txt

```

*(Caso ainda não tenha o arquivo de dependências, rode: `pip install PyMuPDF reportlab PyQt6` e depois `pip freeze > requirements.txt`)*

### 4. Executar o Teste de Leitura (Núcleo Funcional)

Para validar se o parser está lendo corretamente um relatório bruto (coloque um PDF de teste dentro da pasta `input_pdfs/`):

```bash
python3 parser_teste.py

```

### 5. Executar a Aplicação Principal (Interface Gráfica)

Para iniciar o software desktop:

```bash
python3 -m src.main

```

---

## Cronograma

* **Duração:** 15 dias úteis (3 semanas)
* **Checkpoint 1 (Dia 5):** Arquitetura, protótipos de tela e núcleo funcional de leitura de PDF.
* **Checkpoint 2 (Dia 10):** Demonstração completa (Fim do desenvolvimento de novas funcionalidades).
* **Entrega Final (Dia 15):** Correção de bugs, testes, documentação e apresentação prática de 10 minutos.
