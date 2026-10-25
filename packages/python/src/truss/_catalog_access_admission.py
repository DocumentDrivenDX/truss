# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pinned UMF-owned access-admission bridge for temporal prep 2.1."""
from hashlib import sha256
from importlib.resources import files
import json

BRIDGE_ARCHIVE_SHA256='972396293616cf930a99c29249ff0490f131fc76c832931b6def2d3278f491cb'
BRIDGE_BUNDLE_SHA256='7f2a434b4b1bd0a2b8c1fe6ef47130f9f1543848a49445679c372d3fa6099856'
BRIDGE_MANIFEST_SHA256='5df7d94ab20d02c76b34016429207bb1d4fcb97f8c1e8d9fce234d1139725bcb'
BRIDGE_PROFILE='truss.umf-access-admission-bridge/0.1-candidate'


def inspect_access_views(document, selected):
    """Run the exact bundled UMF public re-export in the bounded embedded V8."""
    root=files('truss').joinpath('_umf_access_admission')
    manifest_bytes=root.joinpath('producer-manifest.json').read_bytes()
    manifest=json.loads(manifest_bytes)
    archive=root.joinpath('source.tar.gz').read_bytes()
    source=root.joinpath('access-admission.js').read_bytes()
    if (sha256(archive).hexdigest()!=BRIDGE_ARCHIVE_SHA256
        or sha256(manifest_bytes).hexdigest()!=BRIDGE_MANIFEST_SHA256
        or manifest.get('archiveSha256')!=BRIDGE_ARCHIVE_SHA256
        or manifest.get('bundleSha256')!=BRIDGE_BUNDLE_SHA256
        or manifest.get('entrypoint')!='@umf/core/access-admission'
        or manifest.get('operation')!='inspectAccessViews'
        or sha256(source).hexdigest()!=BRIDGE_BUNDLE_SHA256):
        raise ValueError('Exact owner access-admission bridge required')
    source_text=source.decode('utf8')
    export='export {\n  inspectAccessViews\n};'
    if source_text.count(export)!=1:
        raise ValueError('Exact UMF public entrypoint export required')
    # This is only an ESM-to-global wrapper for the embedded V8 evaluator. The
    # owner-produced bundled implementation is otherwise byte-identical.
    executable=source_text.replace(export,'globalThis.__umf_inspectAccessViews=inspectAccessViews;')
    request=json.dumps({'document':document,'selected':selected},ensure_ascii=True,separators=(',',':'))
    if len(request.encode('utf8'))>16777216:
        raise ValueError('Bounded access-admission request required')
    from ._embedded import OwnerVM
    with OwnerVM('_umf_core10/preparation.mjs',timeout=10) as owner:
        owner.eval(executable)
        owner.eval('globalThis.__umf_admission_request='+request)
        encoded=owner.eval('JSON.stringify(globalThis.__umf_inspectAccessViews(globalThis.__umf_admission_request.document,globalThis.__umf_admission_request.selected))')
    if type(encoded) is not str or len(encoded.encode('utf8'))>16777216:
        raise ValueError('Bounded owner access-admission result required')
    result=json.loads(encoded)
    if type(result) is not dict or set(result)!={'records','diagnostics'} or type(result['records']) is not list or type(result['diagnostics']) is not list:
        raise ValueError('Exact UMF access-admission result required')
    return result

