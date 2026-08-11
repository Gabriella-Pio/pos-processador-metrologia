"""Feature templates — gestão e editor de templates."""

__all__ = ["TemplateEditorView"]


def __getattr__(name: str):
    if name == "TemplateEditorView":
        from src.ui.features.templates.components.template_editor_view import TemplateEditorView

        return TemplateEditorView
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
