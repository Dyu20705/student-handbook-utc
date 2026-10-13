"""Lazy exports: importing the package never loads models or writes an index."""
from importlib import import_module

_EXPORTS = {
    "loader": ("ragload", "ragchunking"),
    "vectorstore": ("embes", "createvector", "build_vector_store"),
    "retriever": ("BaselineRetriever",),
    "chain": ("StudentHandbookRAG", "createretriever", "arise", "load_system_prompt", "createprompt", "createragchain"),
    "aragog": ("AragogRetriever", "create_aragog_rag_chain"),
    "corrective": ("CorrectiveRAG",),
    "memory": ("conversational_rag", "create_conversational_rag_chain"),
}
__all__ = [name for names in _EXPORTS.values() for name in names]


def __getattr__(name):
    for module, names in _EXPORTS.items():
        if name in names:
            value = getattr(import_module(f"{__name__}.{module}"), name)
            globals()[name] = value
            return value
    raise AttributeError(name)
