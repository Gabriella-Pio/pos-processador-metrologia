"""Ponto de entrada legado — redireciona para main.py na raiz."""
import runpy
from pathlib import Path

runpy.run_path(str(Path(__file__).resolve().parent.parent / "main.py"), run_name="__main__")
