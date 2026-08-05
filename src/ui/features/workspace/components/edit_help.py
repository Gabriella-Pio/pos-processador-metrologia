"""Textos de ajuda contextual para o editor de seções."""
from __future__ import annotations

_GENERAL = """\
**Edição de seção**
• O preview à direita atualiza automaticamente após cada alteração.
• Use **Restaurar** para voltar ao valor padrão do template.
"""

_PLACEHOLDERS = """\
**Dados globais ({chave})**
• Digite `{` para ver a lista de dados globais e escolher um.
• Chips como `{componente}` aparecem abaixo do campo — clique no ✕ para remover.
• Edite valores globais em **Dados do relatório** no Sumário.
"""

_TABLE_ROWS = """\
**Linhas da tabela**
• Cada linha espelha o preview: **[rótulo] [valor]**.
• Arraste ⠿ para reordenar linhas.
• Valores podem usar placeholders `{client_project}`, `{componente}`, etc.
"""

_MEDIA = """\
**Fotografias, gráficos e tabelas**
• Use a barra superior para inserir ou localizar mídia.
• Arraste PNG/JPG para Fotografias ou clique no botão para escolher arquivo.
• Ferramentas de anotação ficam disponíveis quando há fotos na seção.
"""

_SECTION_HINTS: dict[str, str] = {
    "introducao": (
        "Edite Objetivo, Escopo, Referência e a nota de rodapé no Conteúdo. "
        "Na aba Fotografias, defina a legenda e remova fotos se necessário. "
        "Na Tabela, edite as métricas (Amostra, Valores, Fora…)."
    ),
    "identificacao": (
        "Edite o texto introdutório, o título e as linhas da tabela de identificação."
    ),
    "resultados": "Edite o texto introdutório e a grade de medições extraída do CALYPSO.",
    "grafica": "Texto introdutório e fotografias/gráficos do componente.",
    "tomografia": "Texto introdutório e fotografias da inspeção tomográfica.",
    "interpretacao": (
        "Texto introdutório, itens de interpretação e nota de rodapé. "
        "No template, edite o parágrafo inicial; os itens por medição são gerados "
        "automaticamente no workspace."
    ),
    "conclusao": (
        "Texto da conclusão e o rótulo centrado de Aprovação / Coordenação CEM "
        "(espaço para assinatura gov.br posterior)."
    ),
    "anexos": (
        "Lista e anexa ao final do relatório o(s) PDF(s) importado(s) pelo usuário."
    ),
    "controle_tecnico": "Edite o título, o subtítulo e as linhas da tabela de responsáveis (arraste para reordenar).",
}


def build_help_text(section_id: str, *, has_table: bool = False, has_media: bool = False) -> str:
    parts = [_GENERAL.strip()]
    section_hint = _SECTION_HINTS.get(section_id)
    if section_hint:
        parts.append(section_hint)
    parts.append(_PLACEHOLDERS.strip())
    if has_table or section_id in ("introducao", "identificacao", "controle_tecnico", "resultados"):
        parts.append(_TABLE_ROWS.strip())
    if has_media or section_id in ("introducao", "grafica", "tomografia"):
        parts.append(_MEDIA.strip())
    return "\n\n".join(parts)
