# SPDX-License-Identifier: MIT OR Apache-2.0
"""Distinct immutable presence-source registration; never native admission."""
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence
from ._current_query_originals import require_current_model_correspondence,_actual_weft_module_sha256
from ._embedded_release import MANIFEST_SHA256 as EMBEDDED_MANIFEST_SHA256


@dataclass(frozen=True,slots=True)
class CurrentDisclosureOriginals:
    opaque_sources_bytes:bytes
    consumer_bytes:bytes


# Current selected Weft0.4.51 only, with exact qualified wheel/module identities.
# Historical consumer snapshots remain evidence, not runtime compatibility modes.
_EMBEDDED_CONSUMER={
    'embeddedRuntime':'mini-racer==0.14.1',
    'embeddedProfile':'truss.embedded-v8/2',
    'embeddedV8Version':'14.4.258.23',
    'embeddedManifestSha256':EMBEDDED_MANIFEST_SHA256,
}
_GRAPH_SHA256='9875a58cf96d0cdbe178018a3c0bb27459b1771d7e1b9a378d391448514ca377'
_DISCLOSURE_CONSUMER={
    'profile':'truss-current-disclosure-consumer/0.1-candidate',
    'umfRevision':'9ff2ba12271be889aad81c09695487e14655893d',
    'umfBundleSha256':'bf3e2af7728fe056ef8b3aba37ad048b0b8ac9485ec31920a1f585a6b72d10d8',
    'umfManifestSha256':'153d939786bb01dd2cd206302b3696dd5d5c8e4e1092fbfa4fd64155d09c483c',
    **_EMBEDDED_CONSUMER,
    'weftRevision':'db1e0dc5b1ec6aec0f12646421cefc314989d974',
    'weftVersion':'0.4.48',
    'weftWheelSha256':'def824d16bc00f9deb50c7c63bc08a728cff631eef25cf2616032b761e1c679c',
    'weftModuleSha256':'36224fd006f525e26e79ad2504bee7ffd75439ce1c8367564cfeb7c826e736a4',
    'weftShimSha256':'cd0fa27c9580742333d14e24d5ebfd74babb47d31720bb4c577278d05486f11d',
    'graphSha256':_GRAPH_SHA256,
    'childProtocol':'umf.security.private-disclosure-child/0.2-candidate',
    'resultAbi':'weft.postgresql.current-presence.sql/0.1-candidate',
}
_CONSUMER_COHORTS=(
    {**_DISCLOSURE_CONSUMER,
        'weftRevision':'86c092178bb8ca1a0d84edfebc175009d8862493',
        'weftVersion':'0.4.51',
        'weftWheelSha256':'a21faed75304e730c7cc9782394001be2ba1772b429e587f0d1910c2269dabbe',
        'weftModuleSha256':'93bee228350743286073a9400bdf5ec92e387c5e35431bbf34b0f81279c460a2'},
)


@lru_cache(maxsize=1)
def _actual_disclosure_consumer_json():
    try:
        import weft.weft as native
        digest=_actual_weft_module_sha256()
        selected=[c for c in _CONSUMER_COHORTS if c['weftModuleSha256']==digest]
        if len(selected)!=1:raise ValueError('Explicit reviewed disclosure consumer required')
        for name in ('native_request_json','json','lower_postgresql_current_presence_candidate_json','check_postgresql_current_presence_candidate_json'):
            if not callable(getattr(native.CurrentPresencePreparation,name,None)):
                raise ValueError('Actual original presence descriptors required')
        from ._current_disclosure_computation import verify_current_disclosure_owner_assets
        root=verify_current_disclosure_owner_assets();consumer=selected[0]
        if (sha256(root.joinpath('manifest.json').read_bytes()).hexdigest()!=consumer['umfManifestSha256']
                or sha256(root.joinpath('current-native-disclosure-child.mjs').read_bytes()).hexdigest()!=consumer['umfBundleSha256']):
            raise ValueError('Exact original disclosure producer cohort required')
        return json.dumps(consumer,separators=(',',':')).encode()
    except (ImportError,AttributeError,OSError) as error:
        raise ValueError('Actual original presence consumer required') from error


def _actual_disclosure_consumer():
    # The selected native module and installed UMF assets are immutable for
    # this process. Return a fresh mapping so callers cannot mutate the cache.
    return decode_owner_evidence_json(_actual_disclosure_consumer_json())


def _check_disclosure_sources(raw,initialize_bytes,accepted_request_bytes):
    """Transport/model correspondence only; UMF owns policy/owner semantics."""
    if type(raw) is not bytes or not 1<=len(raw)<=4194304:
        raise ValueError('Bounded immutable original disclosure sources required')
    rows=decode_owner_evidence_json(raw)
    roles=('policy','ontology','catalog','owner','native-binding','presence-designation')
    if type(rows) is not list or len(rows)!=len(roles):
        raise ValueError('Complete distinct original disclosure-source roles required')
    by_role={}
    for row in rows:
        if (type(row) is not dict or set(row)!={'role','identity','mediaType','utf8','sha256'}
                or type(row['role']) is not str or row['role'] not in roles or row['role'] in by_role
                or row['mediaType']!='application/json' or type(row['utf8']) is not str
                or type(row['identity']) is not dict or set(row['identity'])!={'documentId','revision'}
                or any(type(v) is not str or not v for v in row['identity'].values())
                or sha256(row['utf8'].encode()).hexdigest()!=row['sha256']):
            raise ValueError('Exact original disclosure-source transport required')
        by_role[row['role']]=row
    decoded={role:decode_owner_evidence_json(row['utf8'].encode()) for role,row in by_role.items()}
    initial=decode_owner_evidence_json(initialize_bytes)['sources']
    require_current_model_correspondence(initialize_bytes,accepted_request_bytes)
    for role in ('policy','ontology','catalog'):
        if not same_owner_evidence(decoded[role],initial[role]):
            raise ValueError('Original initializer/disclosure source correspondence required')
    for role in ('policy','catalog','owner','presence-designation'):
        source=decoded[role]
        if type(source) is not dict or by_role[role]['identity']!={'documentId':source.get('id'),'revision':source.get('revision')}:
            raise ValueError('Original disclosure-source identity required')
    ontology=decoded['ontology']
    if type(ontology) is not dict or by_role['ontology']['identity']!={'documentId':ontology.get('documentId'),'revision':ontology.get('revision')}:
        raise ValueError('Original disclosure ontology identity required')
    profile=decoded['presence-designation']
    pins=[m['pin'] for m in decode_owner_evidence_json(accepted_request_bytes)['modules']]
    source_pins=profile.get('sources')
    if (type(source_pins) is not list or len(source_pins)!=4
            or any(type(p) is not dict or set(p)!={'role','identity','sha256'}
                or type(p['role']) is not str or p['role'] not in ('policy','ontology','catalog','owner') for p in source_pins)
            or len({p['role'] for p in source_pins})!=4
            or any(not same_owner_evidence(p,{k:by_role[p['role']][k] for k in ('role','identity','sha256')}) for p in source_pins)):
        raise ValueError('Exact distinct original presence source pins required')
    if (profile.get('version')!='weft.current-presence.designation-profile/0.1-candidate'
            or profile.get('capabilities')!=['tagged-current-projection']
            or not same_owner_evidence(profile.get('modelPins'),pins)):
        raise ValueError('Original presence model/source designation required')
    binding=profile.get('binding')
    if (type(binding) is not dict or set(binding)!={'backendId','backendVersion','targetProfile','source','sha256'}
            or binding['source']!=by_role['native-binding']['identity']
            or binding['sha256']!=by_role['native-binding']['sha256']):
        raise ValueError('Original static presence binding correspondence required')
    return by_role,decoded


def check_disclosure_originals(originals,initialize_bytes,accepted_request_bytes):
    if type(originals) is not CurrentDisclosureOriginals:
        raise ValueError('Distinct immutable original disclosure sources required')
    _check_disclosure_sources(originals.opaque_sources_bytes,initialize_bytes,accepted_request_bytes)
    if type(originals.consumer_bytes) is not bytes or not 1<=len(originals.consumer_bytes)<=4194304:
        raise ValueError('Bounded exact disclosure consumer selection required')
    consumer=decode_owner_evidence_json(originals.consumer_bytes)
    if not same_owner_evidence(consumer,_actual_disclosure_consumer()):
        raise ValueError('Exact original disclosure consumer required')
    return originals


def prepare_current_disclosure_originals(opaque_sources_bytes):
    if type(opaque_sources_bytes) is not bytes or not 1<=len(opaque_sources_bytes)<=4194304:
        raise ValueError('Bounded immutable original disclosure sources required')
    return CurrentDisclosureOriginals(opaque_sources_bytes,json.dumps(_actual_disclosure_consumer(),separators=(',',':')).encode())


def is_graph_disclosure_originals(originals):
    """Select a complete already-validated registered cohort, never a hash alone."""
    if type(originals) is not CurrentDisclosureOriginals:
        return False
    consumer=decode_owner_evidence_json(originals.consumer_bytes)
    if any(same_owner_evidence(consumer,cohort) for cohort in _CONSUMER_COHORTS):return True
    raise ValueError('Exact registered disclosure consumer cohort required')
