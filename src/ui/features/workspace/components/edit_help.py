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
    "introducao": "Edite o título da seção e cada bloco (título + texto) como aparecem na tabela do preview.",
    "identificacao": "Edite o título e as linhas da tabela de identificação.",
    "resultados": "Edite o texto introdutório e a grade de medições extraída do CALYPSO.",
    "grafica": "Texto introdutório e fotografias/gráficos do componente.",
    "tomografia": "Texto introdutório e fotografias da inspeção tomográfica.",
    "interpretacao": "Texto gerado a partir das medições (somente leitura).",
    "conclusao": "Texto da conclusão conforme resultado das medições.",
    "controle_tecnico": "Responsáveis técnicos pela medição e revisão.",
}


def build_help_text(section_id: str, *, has_table: bool = False, has_media: bool = False) -> str:
    parts = [_GENERAL.strip()]
    section_hint = _SECTION_HINTS.get(section_id)
    if section_hint:
        parts.append(section_hint)
    parts.append(_PLACEHOLDERS.strip())
    if has_table or section_id in ("identificacao", "resultados"):
        parts.append(_TABLE_ROWS.strip())
    if has_media or section_id in ("introducao", "grafica", "tomografia"):
        parts.append(_MEDIA.strip())
    return "\n\n".join(parts)
