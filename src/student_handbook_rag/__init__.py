"""Lazy exports: importing the package never loads models or writes an index."""

from importlib import import_module

_EXPORTS = {
    "loader": ("ragload", "ragchunking"),
    "vectorstore": ("get_embedding_function", "build_vector_store"),
    "retriever": ("BaselineRetriever",),
    "chain": ("StudentHandbookRAG", "create_llm"),
}
__all__ = [name for names in _EXPORTS.values() for name in names]


def __getattr__(name):
    for module, names in _EXPORTS.items():
        if name in names:
            value = getattr(import_module(f"{__name__}.{module}"), name)
            globals()[name] = value
            return value
    raise AttributeError(name)
