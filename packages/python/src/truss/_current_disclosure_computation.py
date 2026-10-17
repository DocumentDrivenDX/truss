"""Separate held disclosure assets; no fallback to the old query child."""
from contextlib import contextmanager
from hashlib import sha256
from importlib.resources import files
import json
from time import monotonic
from ._current_disclosure_pipe import CurrentDisclosurePipe

# Owner-reviewed packaged cohort must be installed before this profile can run.
_ASSET_MANIFEST_SHA256='ca31a592ca8af8e208729445cd2987d80e8f5797a679b6258f6f9bd3aec86f9e'


def verify_current_disclosure_owner_assets():
    if _ASSET_MANIFEST_SHA256 is None:
        raise ValueError('Reviewed original disclosure assets are not enrolled')
    root=files('truss').joinpath('_current_disclosure_owner')
    raw=root.joinpath('consumer-manifest.json').read_bytes()
    if sha256(raw).hexdigest()!=_ASSET_MANIFEST_SHA256:
        raise ValueError('Exact original disclosure owner manifest required')
    manifest=json.loads(raw)
    for name,digest in manifest['files'].items():
        if (not isinstance(name,str) or name.startswith('/') or '\\' in name
                or any(part in ('','.','..') for part in name.split('/'))
                or sha256(root.joinpath(name).read_bytes()).hexdigest()!=digest):
            raise ValueError('Exact original disclosure owner assets required')
    return root


@contextmanager
def open_current_disclosure_computation(*,bun_executable='bun',timeout_seconds=5):
    end=monotonic()+timeout_seconds;root=verify_current_disclosure_owner_assets()
    from ._embedded import EmbeddedOwnerPipe
    remaining=end-monotonic()
    if remaining<=0:raise TimeoutError('Original disclosure launch deadline expired')
    try:
        with EmbeddedOwnerPipe(str(root.joinpath('current-native-disclosure-child.mjs')),timeout_seconds=remaining,disclosure=True) as child:
            yield child
    finally:
        verify_current_disclosure_owner_assets()
