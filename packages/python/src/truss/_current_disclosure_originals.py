"""Distinct immutable presence-source registration; never native admission."""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import json
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence
from ._current_query_originals import require_current_model_correspondence


@dataclass(frozen=True,slots=True)
class CurrentDisclosureOriginals:
    opaque_sources_bytes:bytes
    consumer_bytes:bytes


# Explicit local reviewed ARM/Python3.11 cohort, not a public release/default.
# Whole selections stay fixed; no ABI2 or unrecognized-module fallback.
_CONSUMER_COHORTS=({
    'profile':'truss-current-disclosure-consumer/0.1-candidate',
    'umfRevision':'11b412e4a783fef8075aeb4109a286650a0bda28',
    'umfBundleSha256':'548b7ff64dabf3bc796afe99ecca265f5bcf242202e367ba7125e62c64f0a735',
    'umfManifestSha256':'45154e0f3bd5973ddc4d6fb40fdebf27afb51fdc018d2f055ba580c9c07437d2',
    'bunVersion':'1.4.2',
    'weftRevision':'b8c34c84f3c8cae8e07680e4960942d685f9bb63',
    'weftWheelSha256':'2b5806d53cb50b95b56f0dda0dee8ea79e6f1d72b839f5ec74304943fe3022ad',
    'weftModuleSha256':'a94439b3949c6db574ded8d95d9b81b23e128b0cbb7570edff65228d3737c402',
    'childProtocol':'umf.security.private-disclosure-child/0.2-candidate',
    'resultAbi':'weft.postgresql.current-presence.sql/0.1-candidate',
},)


def _actual_disclosure_consumer():
    try:
        import weft.weft as native
        digest=sha256(Path(native.__file__).read_bytes()).hexdigest()
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
        return dict(consumer)
    except (ImportError,AttributeError,OSError) as error:
        raise ValueError('Actual original presence consumer required') from error


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
