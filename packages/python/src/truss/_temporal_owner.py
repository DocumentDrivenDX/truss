# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pinned public owner inspection; no semantic resolver or JavaScript sidecar."""
from hashlib import sha256
from importlib import metadata
from importlib.resources import files
import json

from .preparation import PreparationRejected
from .catalog_preparation import prepare_catalog
from ._owner_evidence_json import decode_owner_evidence_json
from ._temporal_preparation import inspection_packet, retain_temporal_preparation


def _inspector():
    # Canonical owner bytes/resources are a reviewed packaging input. An absent
    # manifest cannot be replaced with an ambient source checkout or old bridge.
    try:
        root=files('truss').joinpath('_temporal_owner')
        manifest_raw=root.joinpath('manifest.json').read_bytes()
        manifest=decode_owner_evidence_json(manifest_raw)
        from .catalog_runtime import _release
        native,_,_=_release()
        if native['files']['../_temporal_owner/manifest.json']!=sha256(manifest_raw).hexdigest():
            raise ValueError('Exact enrolled inspection owner required')
        if manifest['operation']!='inspectAccessViews' or metadata.version(manifest['distribution'])!=manifest['version']:
            raise ValueError('Exact public inspection distribution required')
        from umf.rust_codegen import CodegenEngine
        import umf
        owner=files('umf')
        for name,digest in manifest['installedFiles'].items():
            if sha256(owner.joinpath(name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Actual installed inspection module source changed')
        resources={}
        for name,entry in manifest['resources'].items():
            raw=root.joinpath(entry['file']).read_bytes()
            if sha256(raw).hexdigest()!=entry['sha256']:raise ValueError('Original canonical inspection resource required')
            decode_owner_evidence_json(raw)  # Reject duplicate/nonfinite/invalid Unicode framing.
            resources[name]=json.loads(raw)
        engine=CodegenEngine(resources,max_work=manifest['maximumWork'])
        if not callable(getattr(engine,'inspect_access_views',None)):
            raise ValueError('Actual public inspection operation required')
        return engine,manifest['profile']
    except (ImportError,FileNotFoundError,KeyError,ValueError,TypeError) as error:
        raise PreparationRejected('producer_unavailable') from error


def prepare_temporal_catalog(documents, *, bun_executable='bun', source_version=None):
    original=prepare_catalog(documents,bun_executable=bun_executable,source_version=source_version)
    engine,profile=_inspector()
    packets=[]
    for document in documents:
        source=decode_owner_evidence_json(document.content)
        selected=[{'module':module['id'],'element':element['id']} for module in source['modules']
                  for element in module['elements'] if element['kind']=='record']
        try:
            result=engine.inspect_access_views(source,selected,(),source_id='logical')
        except (TypeError,ValueError) as error:
            # The public owner binding owns its numeric/resource envelope. Never
            # coerce unsupported source values through binary floats here.
            raise PreparationRejected('producer_unavailable') from error
        raw=json.dumps(result,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
        try:
            packets.append(inspection_packet(document,selected=selected,bindings=[],source_id='logical',
                                             owner_profile=profile,result_bytes=raw))
        except ValueError as error:
            raise PreparationRejected('unsupported_profile') from error
    return retain_temporal_preparation(original,tuple(packets))
