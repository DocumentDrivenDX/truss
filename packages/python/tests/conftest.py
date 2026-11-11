# SPDX-License-Identifier: MIT OR Apache-2.0
"""Marks slow modules so the pull-request job can run `-m "not slow"`; nightly runs `-m slow`."""
import pytest

# Test module basenames (without .py) that exceed the fast-job budget.
SLOW_MODULES: set[str] = set()


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.module.__name__.split('.')[-1] in SLOW_MODULES:
            item.add_marker(pytest.mark.slow)


def pytest_configure(config):
    config.addinivalue_line('markers', 'slow: long-running native module, run by the nightly job')
