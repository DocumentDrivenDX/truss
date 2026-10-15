"""Public source-version-selected catalog preparation without a database."""
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import CatalogDocument, PreparedAcceptance, prepare_acceptance, prepare_core08_acceptance
from ._catalog_source_reference import REFERENCE08_PROFILE,RECURSIVE08_PROFILE,DECLARATIVE08_PROFILE
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
    if manifest['releaseId'] in ('truss-catalog-runtime/0.66-candidate','truss-catalog-runtime/0.67-candidate','truss-catalog-runtime/0.68-candidate'):
        configuration['supportProfile']=dict(DECLARATIVE08_PROFILE if source_version=='0.8.0' else RECURSIVE07_PROFILE)
    return configuration


def prepare_catalog(documents: tuple[CatalogDocument, ...], *, source_version: str='0.7.0', bun_executable: str='bun') -> PreparedAcceptance:
    """Prepare original UMF0.7/0.8 without a connection or host transaction.

    Native acceptance and compatibility with installed data remain transaction
    operations. Preparation does not establish installation authority.
    """
    producer=prepare_core08_acceptance if source_version=='0.8.0' else prepare_acceptance
    return producer(documents,canonical_numeric_free(_configuration(source_version)),bun_executable=bun_executable)
