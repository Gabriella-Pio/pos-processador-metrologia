"""
Adapter que implementa ``RecentFilesRepository`` (a porta esperada pela
UI) por cima do ``DatabaseManager`` já existente — sem precisar alterar
os nomes de método em português que ele já usa (``salvar_registro``,
``buscar_todos``). Só traduz formatos nos dois sentidos.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.core.infrastructure.database import DatabaseManager
from src.core.domain.ports import RecentFilesRepository, ReportDocument


class SQLiteRecentFilesAdapter(RecentFilesRepository):
    """Traduz entre o schema em português do ``DatabaseManager`` e o
    formato de dict (``id``, ``file_name``, ``client_project``,
    ``version``, ``updated_at``) que ``HomeViewModel``/``RecentFileSummary``
    esperam.
    """

    _FORMATO_DATA = "%d/%m/%Y %H:%M:%S"

    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def list_recent(self, limit: int = 20) -> list[dict]:
        linhas = self._db.buscar_todos(limite=limit)
        resultado = []
        for (id_, nome_arquivo, cliente_projeto, versao, componente, data_hora, responsavel, caminho) in linhas:
            resultado.append({
                "id": str(id_),
                "file_name": nome_arquivo or Path(caminho).name,
                "client_project": cliente_projeto or componente,
                "evaluated_component": componente or "",
                "version": versao,
                "updated_at": self._parse_data(data_hora),
            })
        return resultado

    def save(self, document: ReportDocument, file_name: str) -> str:
        """``file_name`` aqui é o caminho completo do PDF exportado
        (``WorkspaceViewModel`` passa o ``output_path`` recebido do
        ``ReportExporter``). O nome de exibição vira o basename dele.
        """
        output_path = Path(file_name)
        versao_atual = (
            f"v{document.version_history[-1].version_number}"
            if document.version_history
            else "v1"
        )
        responsavel = (
            document.version_history[-1].responsible_name
            if document.version_history
            else (document.control_info.measured_by if document.control_info else "Não informado")
        )
        novo_id = self._db.salvar_registro(
            nome_arquivo=output_path.name,
            cliente_projeto=document.client_project,
            versao=versao_atual,
            componente=document.evaluated_component,
            data_hora=datetime.now().strftime(self._FORMATO_DATA),
            responsavel=responsavel,
            caminho=str(output_path),
        )
        return str(novo_id)

    def get_by_id(self, file_id: str) -> dict | None:
        try:
            doc_id = int(file_id)
        except (TypeError, ValueError):
            return None
        linha = self._db.buscar_por_id(doc_id)
        if linha is None:
            return None
        id_, nome_arquivo, cliente_projeto, versao, componente, data_hora, responsavel, caminho = linha
        return {
            "id": str(id_),
            "file_name": nome_arquivo or Path(caminho).name,
            "client_project": cliente_projeto or componente,
            "evaluated_component": componente,
            "version": versao,
            "updated_at": self._parse_data(data_hora),
            "file_path": caminho,
            "responsible": responsavel,
        }

    def _parse_data(self, data_hora: str) -> datetime:
        try:
            return datetime.strptime(data_hora, self._FORMATO_DATA)
        except (ValueError, TypeError):
            return datetime.now()
