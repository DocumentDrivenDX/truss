# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public source-version-selected catalog preparation without a database."""
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import CatalogDocument, PreparedAcceptance, PreparationRejected, _prepare_acceptance, MAX_DOCUMENT
from ._catalog_source_reference import DATE10_PROFILE
from ._catalog_report_semantics import canonical_numeric_free


def _configuration(manifest=None):
    root=files('truss').joinpath('_catalog_runtime')
    if manifest is None:manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    raw=root.joinpath('preparation-baseline.json').read_bytes()
    if sha256(raw).hexdigest()!=manifest['files']['preparation-baseline.json']:
        raise ValueError('Original preparation baseline required')
    configuration=json.loads(raw)
    configuration['layoutProfile']=manifest['layoutProfile']
    configuration['supportProfile']=dict(DATE10_PROFILE)
    owner=json.loads(files('truss').joinpath('_umf_core10/producer-manifest.json').read_bytes())
    configuration['validatorProfile']={'identity':'umf-core-document-validation',
        'version':owner['revision'],'sha256':owner['bundleSha256']}
    return configuration


def prepare_catalog(documents: tuple[CatalogDocument, ...], *, source_version: str | None=None, bun_executable: str='bun') -> PreparedAcceptance:
    """Prepare original UMF 0.10.0 documents for the current catalog route.

    Native acceptance and compatibility with installed data remain transaction
    operations. Preparation retains document validation results, without
    per-operation inspection transcripts. It does not establish installation authority.
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
    return _prepare_acceptance(documents,canonical_numeric_free(_configuration()),
        bun_executable=bun_executable)
