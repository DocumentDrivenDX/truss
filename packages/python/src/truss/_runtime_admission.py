# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current runtime declaration only; grants no caller authority."""
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files

@lru_cache(maxsize=1)
def runtime_digest():
    return sha256(files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()).hexdigest()
