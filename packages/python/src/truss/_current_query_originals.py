"""Static original query-source correspondence, never consumer admission."""
from dataclasses import dataclass
from hashlib import sha256
import re
from importlib import import_module
from pathlib import Path
from ._current_query_computation import verify_current_query_owner_assets
from ._owner_evidence_json import decode_owner_evidence_json, same_owner_evidence
from ._umf_key_tuples import _same_json_meaning


@dataclass(frozen=True, slots=True)
class CurrentQueryOriginals:
    opaque_sources_bytes: bytes
    consumer_bytes: bytes


_ABI2_CONSUMER={
    'profile':'truss-current-query-consumer/0.1-candidate',
    'umfRevision':'579675bdad79c349b06e25979108f8ac1bb7f7e0',
    'umfBundleSha256':'36e2c63fb0d942c9b94141f1753bcd9b56aad9e32dec5aa1a9ee27aabc674248',
    'umfManifestSha256':'98eed644128b6f77d087293360e062fc06cce941dcb686e09c35632a5560f03d',
    'bunVersion':'1.4.2',
    'weftRevision':'718a9649413baa4e3ede5c0c3b7ed24f4ae48d46',
    'weftWheelSha256':'3e9bd6f6ac42c944dd12e36ce3ea0481ca116a3ab639ef2c2ede933751ff17a8',
    'weftModuleSha256':'6b8af80b8d6da4216b1338e79e869faee4f5cd25af8500034368ef709005f523',
    'resultAbi':'weft.postgresql.current-values/0.2-candidate',
}
# Actual standard-feature CI wheel, qualified only for the existing ABI2 flow.
# Extra APIs in that wheel do not enroll aggregates or a newer result ABI.
_ABI2_WEFT_033_CI_ARM={**_ABI2_CONSUMER,
    'weftRevision':'cc943a2f0ad87e3742cccdc171184bad7d4dbf60',
    'weftWheelSha256':'dfe0fa7f8286758c6e1f24e417e62e11f252dce9896ecf99800f5151b49c9fb3',
    'weftModuleSha256':'60b977a1c8b8a355b86be40375aab209ed894b172dbed972498721eab8bbddae',
}
_CONSUMER_COHORTS=(_ABI2_CONSUMER,_ABI2_WEFT_033_CI_ARM)


def _actual_consumer():
    try:
        native=import_module('weft.weft')
        digest=sha256(Path(native.__file__).read_bytes()).hexdigest()
        cohorts=[c for c in _CONSUMER_COHORTS if c['weftModuleSha256']==digest]
        if (len(cohorts)!=1 or not callable(native.CurrentQueryPreparation.native_request_json)
                or not callable(native.CurrentQueryPreparation.lower_postgresql_current_rows_candidate_json)):
            raise ValueError('Actual selected original Weft ABI2 module required')
    except (ImportError,AttributeError,OSError) as error:
        raise ValueError('Actual selected original Weft ABI2 module required') from error
    return dict(cohorts[0])


def _match_consumer(consumer):
    # Compare the whole retained selection with the actual module's exact
    # cohort. Another known wheel still requires explicit source migration.
    if not same_owner_evidence(consumer,_actual_consumer()):
        raise ValueError('Unsupported exact query consumer selection')
    root=verify_current_query_owner_assets()
    if (sha256(root.joinpath('manifest.json').read_bytes()).hexdigest()!=consumer['umfManifestSha256']
            or sha256(root.joinpath('current-query-child.mjs').read_bytes()).hexdigest()!=consumer['umfBundleSha256']):
        raise ValueError('Actual original UMF consumer required')


def prepare_current_query_originals(opaque_sources_bytes):
    """Select known installed computation bytes; native registration validates sources."""
    if type(opaque_sources_bytes) is not bytes or not 1<=len(opaque_sources_bytes)<=4194304:
        raise ValueError('Bounded immutable original opaque source bytes required')
    consumer=_actual_consumer()
    _match_consumer(consumer)
    import json
    return CurrentQueryOriginals(opaque_sources_bytes,json.dumps(consumer,separators=(',',':')).encode())


def require_current_model_correspondence(initialize_bytes,accepted_request_bytes):
    sources=decode_owner_evidence_json(initialize_bytes)['sources']
    request=decode_owner_evidence_json(accepted_request_bytes)
    if type(sources) is not dict or type(request) is not dict or type(request.get('modules')) is not list:
        raise ValueError('Complete original query model sources required')
    modules={}
    for module in request['modules']:
        if type(module) is not dict or type(module.get('pin')) is not dict or type(module.get('documentJson')) is not str:
            raise ValueError('Original accepted model source required')
        pin=module['pin'];name=pin['documentId']
        if type(name) is not str or not name or name in modules:
            raise ValueError('Distinct original accepted model documents required')
        if sha256(module['documentJson'].encode()).hexdigest()!=pin['sha256']:
            raise ValueError('Original accepted model document hash required')
        modules[name]=module
    closure=sources.get('closure')
    if (type(closure) is not dict or set(closure)!={'documents','pins'}
            or type(closure['documents']) is not list or type(closure['pins']) is not list
            or not modules or len(closure['documents'])!=len(modules) or len(closure['pins'])!=len(modules)):
        raise ValueError('Complete original query model closure required')
    expected={name:module['pin']['revision'] for name,module in modules.items()}
    seen=set()
    for pin in closure['pins']:
        if (type(pin) is not dict or set(pin)!={'documentId','revision'}
                or type(pin['documentId']) is not str or pin['documentId'] in seen
                or pin['documentId'] not in expected or pin['revision']!=expected[pin['documentId']]):
            raise ValueError('Exact distinct original closure pins required')
        seen.add(pin['documentId'])
    seen=set()
    for entry in closure['documents']:
        if (type(entry) is not dict or set(entry)!={'document','revision'} or type(entry['document']) is not dict
                or type(entry['document'].get('id')) is not str):
            raise ValueError('Closed original model closure documents required')
        document=entry['document'];name=document['id']
        if (name in seen or name not in modules or entry['revision']!=expected[name]
                or not _same_json_meaning(document,decode_owner_evidence_json(modules[name]['documentJson'].encode()))):
            raise ValueError('Original accepted model/closure document correspondence required')
        seen.add(name)
    return modules


def check_query_originals(originals, initialize_bytes, accepted_request_bytes):
    """Check retained transport and source correspondence; owners check semantics."""
    if type(originals) is not CurrentQueryOriginals:
        raise ValueError('Immutable original query sources required')
    for raw in (originals.opaque_sources_bytes, originals.consumer_bytes):
        if type(raw) is not bytes or not 1 <= len(raw) <= 4*1024*1024:
            raise ValueError('Bounded original query sources required')
    rows=decode_owner_evidence_json(originals.opaque_sources_bytes)
    roles=('policy','ontology','catalog','owner','native-binding','query-designation')
    if type(rows) is not list or len(rows)!=len(roles):
        raise ValueError('Complete original query-source roles required')
    by_role={}
    for row in rows:
        if (type(row) is not dict or set(row)!={'role','identity','mediaType','utf8','sha256'}
                or row['role'] not in roles or row['role'] in by_role
                or row['mediaType']!='application/json' or type(row['utf8']) is not str
                or type(row['identity']) is not dict or set(row['identity'])!={'documentId','revision'}
                or any(type(v) is not str or not v for v in row['identity'].values())
                or sha256(row['utf8'].encode()).hexdigest()!=row['sha256']):
            raise ValueError('Exact original query-source transport required')
        by_role[row['role']]=row
    decoded={role:decode_owner_evidence_json(row['utf8'].encode()) for role,row in by_role.items()}
    initialize=decode_owner_evidence_json(initialize_bytes)['sources']
    require_current_model_correspondence(initialize_bytes,accepted_request_bytes)
    for role in ('policy','ontology','catalog'):
        if not same_owner_evidence(decoded[role],initialize[role]):
            raise ValueError('Original initializer/query source correspondence required')
    for role in ('policy','catalog','owner','query-designation'):
        source=decoded[role]
        if type(source) is not dict or by_role[role]['identity']!={'documentId':source.get('id'),'revision':source.get('revision')}:
            raise ValueError('Original query-source identity required')
    ontology=decoded['ontology']
    if (type(ontology) is not dict
            or by_role['ontology']['identity']!={'documentId':ontology.get('documentId'),'revision':ontology.get('revision')}):
        raise ValueError('Original query ontology identity required')
    profile=decoded['query-designation']
    pins=[m['pin'] for m in decode_owner_evidence_json(accepted_request_bytes)['modules']]
    if (profile.get('version')!='weft.current-query.designation-profile/0.1-candidate'
            or not same_owner_evidence(profile.get('modelPins'),pins)
            or not same_owner_evidence(profile.get('sources'),[
                {k:by_role[role][k] for k in ('role','identity','sha256')}
                for role in ('policy','ontology','catalog','owner')])):
        raise ValueError('Original Weft designation/model/source correspondence required')
    binding=profile.get('binding')
    if (type(binding) is not dict or set(binding)!={'backendId','backendVersion','targetProfile','source','sha256'}
            or binding['source']!=by_role['native-binding']['identity']
            or binding['sha256']!=by_role['native-binding']['sha256']):
        raise ValueError('Original static Weft binding correspondence required')
    consumer=decode_owner_evidence_json(originals.consumer_bytes)
    fields={'profile','umfRevision','umfBundleSha256','umfManifestSha256','bunVersion',
            'weftRevision','weftWheelSha256','weftModuleSha256','resultAbi'}
    if (type(consumer) is not dict or set(consumer)!=fields
            or consumer['profile']!='truss-current-query-consumer/0.1-candidate'
            or any(type(v) is not str or not v for v in consumer.values())
            or any(re.fullmatch('[0-9a-f]{64}',consumer[k]) is None for k in fields if k.endswith('Sha256'))
            or any(re.fullmatch('[0-9a-f]{40}',consumer[k]) is None for k in ('umfRevision','weftRevision'))
            or consumer['resultAbi']!='weft.postgresql.current-values/0.2-candidate'):
        raise ValueError('Explicit exact query consumer/result ABI selection required')
    _match_consumer(consumer)
    # Exact installed computation bytes do not authenticate a native query,
    # admit the policy, or qualify a private executor's result release.
    return originals
