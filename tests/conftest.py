"""Offline by default; opt in explicitly to model-dependent suites."""

import pytest


def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true")


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(pytest.mark.integration)
            if not config.getoption("--run-integration"):
                item.add_marker(
                    pytest.mark.skip(reason="Pass --run-integration for local Ollama tests")
                )
