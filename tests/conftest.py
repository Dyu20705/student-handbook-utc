"""Offline by default; opt in explicitly to model-dependent suites."""
import pytest

EXPERIMENTAL = {"test_aragog.py", "test_corrective.py", "test_memory.py", "test_rerank.py"}


def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true")
    parser.addoption("--run-experimental", action="store_true")


def pytest_ignore_collect(collection_path, config):
    if collection_path.name in EXPERIMENTAL and not config.getoption("--run-experimental"):
        return True


def pytest_collection_modifyitems(config, items):
    for item in items:
        if ("integration" in item.path.parts
                or item.name in {"test_createretriever", "test_createragchain", "test_rag_invoke",
                                 "test_createvector", "test_similarity_search"}):
            item.add_marker(pytest.mark.integration)
            if not config.getoption("--run-integration"):
                item.add_marker(pytest.mark.skip(reason="Pass --run-integration for local Ollama tests"))
