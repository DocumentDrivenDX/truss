# SPDX-License-Identifier: MIT OR Apache-2.0
"""Bun executable used by tests: TRUSS_BUN_EXECUTABLE, else bun on PATH."""
import os
import shutil

BUN = os.environ.get('TRUSS_BUN_EXECUTABLE') or shutil.which('bun') or 'bun'
