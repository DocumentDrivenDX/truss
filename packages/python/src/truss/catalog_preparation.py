# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public source-version-selected catalog preparation without a database."""
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import CatalogDocument, PreparedAcceptance, PreparationRejected, _prepare_acceptance, MAX_DOCUMENT
from ._catalog_source_reference import DATE10_PROFILE,TEMPORAL_PROFILE
from ._catalog_report_semantics import canonical_numeric_free


def _configuration(manifest=None,support_profile=DATE10_PROFILE):
    root=files('truss').joinpath('_catalog_runtime')
    if manifest is None:manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    raw=root.joinpath('preparation-baseline.json').read_bytes()
    if sha256(raw).hexdigest()!=manifest['files']['preparation-baseline.json']:
        raise ValueError('Original preparation baseline required')
    configuration=json.loads(raw)
    configuration['layoutProfile']=manifest['layoutProfile']
    if support_profile not in (DATE10_PROFILE,TEMPORAL_PROFILE):
        raise ValueError('Original selected catalog support profile required')
    configuration['supportProfile']=dict(support_profile)
    owner=json.loads(files('truss').joinpath('_umf_core10/producer-manifest.json').read_bytes())
    configuration['validatorProfile']={'identity':'umf-core-document-validation',
        'version':owner['revision'],'sha256':owner['bundleSha256']}
    return configuration


def prepare_catalog(documents: tuple[CatalogDocument, ...], *, source_version: str | None=None, bun_executable: str='bun', support_profile=DATE10_PROFILE) -> PreparedAcceptance:
    """Prepare original UMF 0.10.0 documents for the current catalog route.

    Native acceptance and compatibility with installed data remain transaction
    operations. The ordinary profile retains core validation; the explicit
    temporal profile additionally retains the exact pinned owner inspection
    required to derive a distinct local timestamp storage family. Neither path
    establishes installation authority.
    """
    if type(documents) is not tuple or not 1<=len(documents)<=512:
        raise PreparationRejected('invalid_input')
    versions=set()
    for document in documents:
        if type(document) is not CatalogDocument or type(document.content) is not bytes:
            raise PreparationRejected('invalid_input')
        if not 1<=len(document.content)<=MAX_DOCUMENT:raise PreparationRejected('resource')
        try:
            value=json.loads(document.content.decode('utf8'))
            version=value.get('umf') if type(value) is dict else None
        except (ValueError,UnicodeError,RecursionError):raise PreparationRejected('invalid_document') from None
        if version is None:raise PreparationRejected('invalid_document')
        if version!='0.10.0':raise PreparationRejected('unsupported_profile')
        versions.add(version)
    if versions!={'0.10.0'} or source_version not in (None,'0.10.0'):
        raise PreparationRejected('unsupported_profile')
    configuration=canonical_numeric_free(_configuration(support_profile=support_profile))
    prepared=_prepare_acceptance(documents,configuration,bun_executable=bun_executable)
    if support_profile==DATE10_PROFILE:return prepared
    from ._catalog_access_admission import inspect_access_views
    from .preparation import _with_access_admission,_reject
    inspections=[]
    for document in documents:
        source=json.loads(document.content)
        selected=[{'module':module['id'],'element':element['id']}
            for module in source['modules'] for element in module['elements'] if element.get('kind')=='record']
        try:inspection=inspect_access_views(source,selected)
        except (ValueError,UnicodeError,TimeoutError):_reject('producer_unavailable')
        if inspection['diagnostics']:
            raise PreparationRejected('unsupported_profile',diagnostics=tuple(canonical_numeric_free(d) for d in inspection['diagnostics']))
        inspections.append(inspection)
    bridge_manifest=files('truss').joinpath('_umf_access_admission/producer-manifest.json').read_bytes()
    return _with_access_admission(prepared,inspections,sha256(bridge_manifest).hexdigest())
