# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public source-version-selected catalog preparation without a database."""
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import CatalogDocument, PreparedAcceptance, PreparationRejected, _prepare_acceptance, MAX_DOCUMENT
from ._catalog_source_reference import REFERENCE08_PROFILE,RECURSIVE08_PROFILE,DECLARATIVE08_PROFILE,DATE08_PROFILE
from ._catalog_support import DECIMAL207_PROFILE,RECURSIVE07_PROFILE
from ._catalog_report_semantics import canonical_numeric_free


def _configuration(source_version, manifest=None):
    if source_version not in ('0.7.0','0.8.0'):raise ValueError('Explicit original source version required')
    root=files('truss').joinpath('_catalog_runtime')
    if manifest is None:manifest=json.loads(root.joinpath('manifest.json').read_bytes())
    raw=root.joinpath('preparation-baseline.json').read_bytes()
    if sha256(raw).hexdigest()!=manifest['files']['preparation-baseline.json']:
        raise ValueError('Original preparation baseline required')
    configuration=json.loads(raw)
    configuration['layoutProfile']=manifest['layoutProfile']
    configuration['supportProfile']=dict((RECURSIVE08_PROFILE if source_version=='0.8.0' else RECURSIVE07_PROFILE) if manifest['releaseId'] in ('truss-catalog-runtime/0.64-candidate','truss-catalog-runtime/0.65-candidate') else (REFERENCE08_PROFILE if source_version=='0.8.0' else DECIMAL207_PROFILE))
    if manifest['releaseId'] in ('truss-catalog-runtime/0.66-candidate','truss-catalog-runtime/0.67-candidate','truss-catalog-runtime/0.68-candidate','truss-catalog-runtime/0.70-candidate','truss-catalog-runtime/0.71-candidate','truss-catalog-runtime/0.72-candidate'):
        configuration['supportProfile']=dict(DATE08_PROFILE if source_version=='0.8.0' else RECURSIVE07_PROFILE)
    return configuration


def prepare_catalog(documents: tuple[CatalogDocument, ...], *, source_version: str | None=None, bun_executable: str='bun') -> PreparedAcceptance:
    """Prepare original UMF0.7/0.8, selecting its version from the source.

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
        if version not in ('0.7.0','0.8.0'):raise PreparationRejected('unsupported_profile')
        versions.add(version)
    if len(versions)!=1 or source_version is not None and source_version not in versions:
        raise PreparationRejected('unsupported_profile')
    source_version=next(iter(versions))
    return _prepare_acceptance(documents,canonical_numeric_free(_configuration(source_version)),
        bun_executable=bun_executable)
