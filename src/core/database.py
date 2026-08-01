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