# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pinned public owner inspection; no semantic resolver or JavaScript sidecar."""
from hashlib import sha256
from importlib import metadata
from importlib.resources import files
import json
from pathlib import Path
import sys

from .preparation import PreparationRejected
from .catalog_preparation import prepare_catalog
from ._owner_evidence_json import decode_owner_evidence_json
from ._temporal_preparation import inspection_packet, retain_temporal_preparation


_RESOURCE_NAMES={'coreSchema','referenceSchema','packageSchema','constraints','domainPolicy',
                 'tablesPackage','actionsPackage','bindingPackage','stableBindingPackage'}


def _source_resources(root,native):
    raw=root.joinpath('source.json').read_bytes()
    digest=sha256(raw).hexdigest()
    if native['files'].get('../_temporal_owner/source.json')!=digest:
        raise ValueError('Exact enrolled original inspector source resources required')
    source=decode_owner_evidence_json(raw)
    if (set(source)!={'operation','resourceProfile','sourceCommit','sourceReview','resources'}
            or source['operation']!='inspectAccessViews' or source['resourceProfile']!='umf.codegen-resources/1'
            or type(source['sourceCommit']) is not str or len(source['sourceCommit'])!=40
            or any(c not in '0123456789abcdef' for c in source['sourceCommit'])
            or set(source['resources'])!=_RESOURCE_NAMES):
        raise ValueError('Complete original Core inspector resource cohort required')
    resources={}
    for name,entry in source['resources'].items():
        path=entry['file']
        if (set(entry)!={'file','sourcePath','sha256'} or type(path) is not str
                or Path(path).is_absolute() or '..' in Path(path).parts or not path.startswith('resources/')):
            raise ValueError('Original bounded inspector resource path required')
        content=root.joinpath(path).read_bytes()
        if sha256(content).hexdigest()!=entry['sha256']:raise ValueError('Original canonical inspector resource changed')
        decode_owner_evidence_json(content)
        resources[name]=json.loads(content)
    return resources,source,digest


def _inspector():
    # Canonical owner bytes/resources are a reviewed packaging input. An absent
    # manifest cannot be replaced with an ambient source checkout or old bridge.
    try:
        root=files('truss').joinpath('_temporal_owner')
        from .catalog_runtime import _release
        native,_,_=_release()
        resources,source,source_digest=_source_resources(root,native)
        # A source enrollment does not issue a compiled binding enrollment.
        # The final approved combined Core cohort supplies these actual bytes.
        manifest_raw=root.joinpath('manifest.json').read_bytes()
        manifest=decode_owner_evidence_json(manifest_raw)
        manifest_digest=sha256(manifest_raw).hexdigest()
        if native['files'].get('../_temporal_owner/manifest.json')!=manifest_digest:
            raise ValueError('Exact enrolled inspection owner required')
        if (set(manifest)!={'distribution','version','sourceSha256','sourceCommit','installedFiles','maximumWork'}
                or manifest['distribution']!='umf-core' or manifest['sourceSha256']!=source_digest
                # The compiled cohort can compose reviewed descendants while
                # retaining the same original resource bytes. Bind both: the
                # binary source identity and this exact resource manifest SHA.
                or type(manifest['sourceCommit']) is not str or len(manifest['sourceCommit'])!=40
                or any(c not in '0123456789abcdef' for c in manifest['sourceCommit'])
                or type(manifest['maximumWork']) is not int or not 1<=manifest['maximumWork']<=sys.maxsize
                or metadata.version(manifest['distribution'])!=manifest['version']):
            raise ValueError('Exact public inspection distribution required')
        from umf.rust_codegen import CodegenEngine
        from umf import _rust
        import umf
        if getattr(umf,'__version__',None)!=manifest['version']:
            raise ValueError('Actual inspection runtime and distribution version must agree')
        owner=files('umf')
        expected=manifest['installedFiles']
        if type(expected) is not dict or not {'__init__.py','rust_codegen.py','_rust.py'}<=set(expected):
            raise ValueError('Complete actual inspection binding files required')
        for name,digest in expected.items():
            if type(name) is not str or Path(name).is_absolute() or '..' in Path(name).parts:
                raise ValueError('Closed installed inspector module path required')
            if sha256(owner.joinpath(name).read_bytes()).hexdigest()!=digest:
                raise ValueError('Actual installed inspection module source changed')
        owner_root=Path(umf.__file__).resolve().parent
        loaded_native=Path(_rust._rust_core.__file__).resolve()
        if not loaded_native.is_relative_to(owner_root) or str(loaded_native.relative_to(owner_root)) not in expected:
            raise ValueError('Actual loaded inspection native module required')
        engine=CodegenEngine(resources,max_work=manifest['maximumWork'])
        if not callable(getattr(engine,'inspect_access_views',None)) or not callable(getattr(engine,'call',None)):
            raise ValueError('Actual public inspection operation required')
        return engine,{'identity':manifest['distribution'],'version':manifest['version'],'sha256':manifest_digest}
    except (ImportError,FileNotFoundError,KeyError,ValueError,TypeError,AttributeError,OSError) as error:
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
            # Keep the owner's full ordered diagnostics, including unknown
            # members, on the existing public rejection carrier. The cause
            # retains the whole result bytes rather than an empty replacement.
            error.original_result_json=raw
            diagnostics=tuple(json.dumps(item,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
                              for item in result.get('diagnostics',())) if type(result) is dict else ()
            raise PreparationRejected('unsupported_profile',diagnostics=diagnostics) from error
    return retain_temporal_preparation(original,tuple(packets))
