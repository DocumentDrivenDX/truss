"""Pinned original UMF computation isolate; no native query authorization."""
from contextlib import contextmanager
from hashlib import sha256
from importlib.resources import files
import json
from time import monotonic
from ._current_query_pipe import CurrentQueryPipe

_MANIFEST = '4fe89ac2d318c9df10de578c31d1f955b5bc57baf843c036a05a178802a8796f'


@contextmanager
def open_current_query_computation(*, bun_executable='bun', timeout_seconds=5):
    """Retain original owner assets and isolate custody through the invocation."""
    end=monotonic()+timeout_seconds
    root=verify_current_query_owner_assets()
    from ._embedded import EmbeddedOwnerPipe
    remaining=end-monotonic()
    if remaining<=0:raise TimeoutError('Original computation launch deadline expired')
    with EmbeddedOwnerPipe(str(root.joinpath('current-query-child.mjs')),timeout_seconds=remaining) as child:
        yield child


def verify_current_query_owner_assets():
    """Verify original packaged bytes without starting or admitting execution."""
    root = files('truss').joinpath('_current_query_owner')
    raw = root.joinpath('consumer-manifest.json').read_bytes()
    if sha256(raw).hexdigest() != _MANIFEST:
        raise ValueError('Original current-query owner manifest required')
    manifest = json.loads(raw)
    for path, digest in manifest['files'].items():
        if sha256(root.joinpath(path).read_bytes()).hexdigest() != digest:
            raise ValueError('Original current-query owner bytes required')
    return root
