# SPDX-License-Identifier: MIT OR Apache-2.0
"""Current runtime declaration only; grants no caller authority."""
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files

@lru_cache(maxsize=1)
def runtime_digest():
    return sha256(files('truss').joinpath('_catalog_runtime','manifest.json').read_bytes()).hexdigest()

@lru_cache(maxsize=1)
def person_entrypoints():
    import json
    root=files('truss').joinpath('_catalog_runtime')
    raw=root.joinpath('person-entrypoints.json').read_bytes()
    manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    if sha256(raw).hexdigest()!=manifest['files']['person-entrypoints.json']:
        raise ValueError('Exact person invocation declarations required')
    value=json.loads(raw)
    if value['interfaceVersion']!='truss-person-invocations/0.1':
        raise ValueError('Selected person invocation profile required')
    return tuple(value['functions'])
