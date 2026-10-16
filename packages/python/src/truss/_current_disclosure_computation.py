"""Separate held disclosure assets; no fallback to the old query child."""
from contextlib import contextmanager
from hashlib import sha256
from importlib.resources import as_file,files
import json,shutil,subprocess
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
    executable=shutil.which(bun_executable)
    if executable is None:raise ValueError('Original Bun runtime required')
    remaining=end-monotonic()
    if remaining<=0:raise TimeoutError('Original disclosure launch deadline expired')
    version=subprocess.run((executable,'--version'),stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=min(5,remaining),check=True)
    if version.stdout.strip()!=b'1.4.2':raise ValueError('Original Bun1.4.2 runtime required')
    with as_file(root.joinpath('current-native-disclosure-child.mjs')) as script:
        remaining=end-monotonic()
        if remaining<=0:raise TimeoutError('Original disclosure launch deadline expired')
        try:
            with CurrentDisclosurePipe((executable,str(script)),timeout_seconds=remaining) as child:
                yield child
        finally:
            # Closing endpoint correspondence; this is not held-file/ABA proof.
            verify_current_disclosure_owner_assets()
