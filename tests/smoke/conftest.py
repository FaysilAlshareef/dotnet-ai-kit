"""Smoke-test gate.

Smoke tests require:
  1. The environment variable ``CLAUDE_CODE_SMOKE=1``.
  2. The ``claude`` CLI on PATH.

If either is absent, every test in ``tests/smoke/`` is skipped.
"""

from __future__ import annotations

import os
import shutil

import pytest


def pytest_collection_modifyitems(config, items):
    smoke_enabled = os.environ.get("CLAUDE_CODE_SMOKE") == "1"
    claude_present = shutil.which("claude") is not None

    if smoke_enabled and claude_present:
        return

    if not smoke_enabled:
        reason = "smoke tests disabled (set CLAUDE_CODE_SMOKE=1 to enable)"
    else:
        reason = "smoke tests require the `claude` CLI on PATH"

    skip_marker = pytest.mark.skip(reason=reason)
    for item in items:
        if "smoke" in item.keywords or "tests/smoke" in str(item.fspath).replace("\\", "/"):
            item.add_marker(skip_marker)
