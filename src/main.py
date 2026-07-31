import sys
from PyQt6.QtWidgets import QApplication
from src.ui.main_window import JanelaPrincipal

def main():
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()