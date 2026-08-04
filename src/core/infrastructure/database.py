import sqlite3
import os

class DatabaseManager:
    def __init__(self, db_path="output_pdfs/historico.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._inicializar_banco()

    def _conectar(self):
        return sqlite3.connect(self.db_path)

    def _inicializar_banco(self):
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome_arquivo TEXT NOT NULL DEFAULT '',
                    cliente_projeto TEXT NOT NULL DEFAULT '',
                    versao TEXT NOT NULL,
                    componente TEXT NOT NULL,
                    data_hora TEXT NOT NULL,
                    responsavel TEXT NOT NULL,
                    caminho_arquivo TEXT NOT NULL
                )
            """)
            conn.commit()
            self._migrar_colunas_legadas(cursor, conn)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS versoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_pdf_path TEXT NOT NULL,
                    client_project TEXT NOT NULL,
                    componente TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    data_hora TEXT NOT NULL,
                    responsavel TEXT NOT NULL,
                    descricao TEXT NOT NULL
                )
            """)
            conn.commit()

    def _migrar_colunas_legadas(self, cursor, conn):
        """Adiciona nome_arquivo/cliente_projeto a bancos criados antes
        dessas colunas existirem, sem quebrar dados já gravados."""
        cursor.execute("PRAGMA table_info(documentos)")
        colunas_existentes = {linha[1] for linha in cursor.fetchall()}
        if "nome_arquivo" not in colunas_existentes:
            cursor.execute("ALTER TABLE documentos ADD COLUMN nome_arquivo TEXT NOT NULL DEFAULT ''")
        if "cliente_projeto" not in colunas_existentes:
            cursor.execute("ALTER TABLE documentos ADD COLUMN cliente_projeto TEXT NOT NULL DEFAULT ''")
        conn.commit()

    def salvar_registro(
        self,
        nome_arquivo: str,
        cliente_projeto: str,
        versao: str,
        componente: str,
        data_hora: str,
        responsavel: str,
        caminho: str,
    ) -> int:
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO documentos (nome_arquivo, cliente_projeto, versao, componente, data_hora, responsavel, caminho_arquivo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nome_arquivo, cliente_projeto, versao, componente, data_hora, responsavel, caminho))
            conn.commit()
            return cursor.lastrowid

    def buscar_todos(self, limite: int = 20) -> list:
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome_arquivo, cliente_projeto, versao, componente, data_hora, responsavel, caminho_arquivo
                FROM documentos ORDER BY id DESC LIMIT ?
            """, (limite,))
            return cursor.fetchall()

    def salvar_versao(
        self,
        source_pdf_path: str,
        client_project: str,
        componente: str,
        version_number: int,
        data_hora: str,
        responsavel: str,
        descricao: str,
    ) -> int:
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO versoes (
                    source_pdf_path, client_project, componente,
                    version_number, data_hora, responsavel, descricao
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                source_pdf_path,
                client_project,
                componente,
                version_number,
                data_hora,
                responsavel,
                descricao,
            ))
            conn.commit()
            return cursor.lastrowid

    def listar_versoes(
        self,
        source_pdf_path: str,
        client_project: str,
        componente: str,
    ) -> list[tuple]:
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT version_number, data_hora, responsavel, descricao
                FROM versoes
                WHERE source_pdf_path = ? AND client_project = ? AND componente = ?
                ORDER BY version_number ASC
            """, (source_pdf_path, client_project, componente))
            return cursor.fetchall()

    def buscar_por_id(self, doc_id: int) -> tuple | None:
        with self._conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, nome_arquivo, cliente_projeto, versao, componente, data_hora, responsavel, caminho_arquivo
                FROM documentos WHERE id = ?
            """, (doc_id,))
            return cursor.fetchone()