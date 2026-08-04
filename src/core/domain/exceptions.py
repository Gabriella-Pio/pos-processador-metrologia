# src/core/exceptions.py

class RelatorioMetrologiaError(Exception):
    """Exceção base para todos os erros de domínio da aplicação."""
    pass

class ParserPDFError(RelatorioMetrologiaError):
    """Lançada quando o PDF da ZEISS está corrompido, vazio ou fora do layout esperado."""
    pass

class TemplateConfigError(RelatorioMetrologiaError):
    """Lançada quando a configuração de um template ou seção dinâmica for inválida."""
    pass