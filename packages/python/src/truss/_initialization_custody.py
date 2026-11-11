# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private journal initializer custody. PostgreSQL alone derives calendar bounds.

The host/administrator is trusted. Hashes provide byte integrity, not signatures.
No current clock is consulted by readback, preservation or verification.
"""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
import re
from uuid import UUID
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

PROFILE='truss-journal-horizon-initialization/0.1'
POLICY='truss-journal-horizon-admission/0.1'
GROUPS_SHA='8d213c5b1243b2839c1ca6a465a709f20b5e03048da184bd58dea87d04ec95dc'
SCHEMA_SHA='4e5cd88be2eff7152f744053323103dc758f9e3922cee780e5653ae64fc112c4'
ZONES=('America/New_York','UTC')
_FORMAT='YYYY-MM-DD"T"HH24:MI:SS.US"Z"'
_INSTANT=re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z')


class InitializationCustodyRefused(ValueError):
    """Post-DDL failures require confirmed host containment before refusal."""


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()


def _pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('Duplicate initialization custody member')
        result[key]=value
    return result


def _hex(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}',value) is None:raise ValueError('Exact custody SHA256 required')
    return value


def _instant(value):
    if type(value) is not str or not _INSTANT.fullmatch(value) or value[:4]=='0000':raise ValueError('Exact finite native microsecond instant required')
    return value


def source_policy(manifest):
    root=files('truss');native=root.joinpath('_catalog_runtime')
    expected={'groups.sql':GROUPS_SHA,'initialization-custody.schema.json':SCHEMA_SHA,
              'initialization-custody.sql':sha256(native.joinpath('initialization-custody.sql').read_bytes()).hexdigest(),
              '../_initialization_custody.py':sha256(root.joinpath('_initialization_custody.py').read_bytes()).hexdigest()}
    if manifest.get('releaseId')!='truss-catalog-runtime/0.76-candidate':raise ValueError('Custody belongs only to explicit native0.76')
    for name,digest in expected.items():
        raw=(root.joinpath('_initialization_custody.py') if name.startswith('../') else native.joinpath(name)).read_bytes()
        if manifest['files'].get(name)!=digest or sha256(raw).hexdigest()!=digest:raise ValueError('Qualified custody source changed:'+name)
    return {'profile':POLICY,'surface':'relations','identity':['journal_runtime_horizon'],'boundIndex':7,
        'custodyRelation':'runtime_initialization_custody','witnessProfile':PROFILE,'witnessSchemaSha256':SCHEMA_SHA,
        'initializerSha256':GROUPS_SHA,'installerSha256':expected['../_initialization_custody.py'],
        'qualifiedTimeZones':list(ZONES),'maxWindowMicros':'300000000'}


def validate_policy(policy,manifest):
    if type(policy) is not dict or canonical(policy)!=canonical(source_policy(manifest)):
        raise ValueError('Closed checksum-pinned initialization policy required')
    return policy


def validate_bytes(raw,digest,*,policy,runtime_digest):
    if type(raw) is not bytes or not 0<len(raw)<=16384 or sha256(raw).hexdigest()!=_hex(digest):raise ValueError('Original bounded custody bytes/digest required')
    value=json.loads(raw,object_pairs_hook=_pairs,parse_float=lambda _:(_ for _ in ()).throw(ValueError('No custody float')),parse_constant=lambda _:(_ for _ in ()).throw(ValueError('No nonfinite custody value')))
    if canonical(value)!=raw:raise ValueError('Canonical original witness bytes required')
    schema=files('truss').joinpath('_catalog_runtime/initialization-custody.schema.json').read_bytes()
    if sha256(schema).hexdigest()!=SCHEMA_SHA:raise ValueError('Qualified witness schema changed')
    Draft202012Validator(json.loads(schema)).validate(value)
    for name,limit in (('databaseOid',4294967295),('ownerOid',4294967295),('backendPid',2147483647)):
        if type(value[name]) is not int or not 1<=value[name]<=limit:raise ValueError('Exact native identity integer required')
    xid=value['writerXid']
    if type(xid) is not str or re.fullmatch('[1-9][0-9]{0,19}',xid) is None or int(xid)>18446744073709551615:raise ValueError('Positive exact uint64 writerXid required')
    if str(UUID(value['installationId']))!=value['installationId']:raise ValueError('Canonical installation UUID required')
    if (value['profile']!=PROFILE or value['runtimeManifestSha256']!=runtime_digest or value['initializerSha256']!=policy['initializerSha256'] or value['installerSha256']!=policy['installerSha256']):raise ValueError('Original initializer/producer/native identity differs')
    _hex(runtime_digest);_instant(value['clockBeforeUtc']);_instant(value['clockAfterUtc'])
    if len(value['candidateBoundPairs']) not in (1,3):raise ValueError('Complete one-or-three candidate set required')
    for pair in value['candidateBoundPairs']:_instant(pair['lowerUtc']);_instant(pair['upperUtc'])
    if value['timeZone'] not in ZONES:raise ValueError('Unqualified initialization zone')
    if value['candidateBoundPairs']!=sorted(value['candidateBoundPairs'],key=lambda p:(p['lowerUtc'],p['upperUtc'])):raise ValueError('Complete canonical candidate ordering required')
    return value


# Native timestamps are parsed once, round-trip checked, bounded, and month
# arithmetic is executed in the RETAINED zone. No installed helper is invoked.
_DERIVE="""WITH p AS MATERIALIZED (SELECT %s::pg_catalog.timestamptz a,%s::pg_catalog.timestamptz b),
 m AS MATERIALIZED (SELECT a,b,pg_catalog.date_trunc('month',a) old,pg_catalog.date_trunc('month',b) new FROM p),
 anchors AS (SELECT old t,0 ord FROM m UNION SELECT new,1 FROM m WHERE new<>old),
 candidates AS (SELECT l.t-interval '1 month' lo,u.t+interval '13 months' hi FROM anchors l CROSS JOIN anchors u WHERE l.ord<=u.ord)
 SELECT pg_catalog.to_char(lo AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
 pg_catalog.to_char(hi AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
 FROM candidates,m WHERE pg_catalog.isfinite(a) AND pg_catalog.isfinite(b) AND a<=b AND b-a<=interval '300 seconds'
 AND new<=old+interval '1 month'
 AND NOT EXISTS (SELECT 1 FROM candidates c WHERE NOT pg_catalog.isfinite(c.lo) OR NOT pg_catalog.isfinite(c.hi)
   OR EXTRACT(YEAR FROM c.lo) NOT BETWEEN 1 AND 9999 OR EXTRACT(YEAR FROM c.hi) NOT BETWEEN 1 AND 9999)
 AND pg_catalog.to_char(a AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')=%s
 AND pg_catalog.to_char(b AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"')=%s ORDER BY lo,hi"""


def _zone(cursor):
    cursor.execute("SELECT pg_catalog.current_setting('TimeZone')",prepare=False);return cursor.fetchone()[0]


def _set_zone(cursor,zone):
    cursor.execute("SELECT pg_catalog.set_config('TimeZone',%s,true)",(zone,),prepare=False)
    if cursor.fetchone()!=(zone,):raise ValueError('Native timezone restoration/selection failed')


def derive(cursor,before,after,zone):
    _instant(before);_instant(after)
    if zone not in ZONES:raise ValueError('Unqualified initialization zone')
    original=_zone(cursor)
    try:
        # An existing installer/verifier transaction gets a SAVEPOINT, never an
        # independent transaction. Rollback restores SET LOCAL even if a native
        # cast errors, before any restoration query is attempted.
        with cursor.connection.transaction():
            _set_zone(cursor,zone)
            cursor.execute(_DERIVE,(before,after,before,after),prepare=False);rows=cursor.fetchall()
            if len(rows) not in (1,3):raise ValueError('Finite ordered native window/candidate set required')
            pairs=[{'lowerUtc':_instant(row[0]),'upperUtc':_instant(row[1])} for row in rows]
            _set_zone(cursor,'UTC');bounds=[]
            for pair in pairs:
                cursor.execute("SELECT pg_catalog.format('FOR VALUES FROM (%%L) TO (%%L)',%s::pg_catalog.timestamptz,%s::pg_catalog.timestamptz)",(pair['lowerUtc'],pair['upperUtc']),prepare=False)
                bounds.append(cursor.fetchone()[0])
            if len({canonical(p) for p in pairs})!=len(pairs):raise ValueError('Duplicate native candidate pair')
            _set_zone(cursor,original)
        return pairs,bounds
    except BaseException as error:
        try:
            if _zone(cursor)!=original:_set_zone(cursor,original)
        except BaseException as cleanup:
            # Preserve the original PG exception/type/SQLSTATE. The installing
            # host must retain an Error, never map uncertain cleanup to refusal.
            error.initialization_cleanup_error=cleanup
            error.add_note('Initialization derivation timezone cleanup is uncertain')
        raise


def observe(cursor):
    cursor.execute("""WITH t AS MATERIALIZED (SELECT pg_catalog.clock_timestamp() value)
        SELECT pg_catalog.to_char(value AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        pg_catalog.current_setting('TimeZone'),pg_catalog.pg_backend_pid(),pg_catalog.pg_current_xact_id()::pg_catalog.text,
        (SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()) FROM t""",prepare=False)
    row=cursor.fetchone()
    if row is None or len(row)!=5 or row[1] not in ZONES:raise ValueError('Qualified native observation context required')
    _instant(row[0])
    if type(row[2]) is not int or type(row[4]) is not int or type(row[3]) is not str:raise ValueError('Exact native backend/transaction/database context required')
    return tuple(row)


def bracket(cursor,sources,manifest,execute):
    source_policy(manifest)
    positions=[i for i,s in enumerate(sources) if sha256(s.encode()).hexdigest()==GROUPS_SHA]
    if len(positions)!=1:raise ValueError('Exactly one unchanged original groups.sql unit required')
    i=positions[0]
    # Pre-DDL unsupported timezone refusal: original source checks precede this.
    if _zone(cursor) not in ZONES:raise ValueError('Unqualified initialization zone')
    execute(cursor,sources[:i])
    try:
        before=observe(cursor);execute(cursor,(sources[i],));after=observe(cursor)
        if before[1:]!=after[1:]:raise ValueError('Original backend/transaction/zone changed inside initializer')
        pairs,bounds=derive(cursor,before[0],after[0],before[1])
    except (ValueError,ValidationError) as error:
        if getattr(error,'initialization_cleanup_error',None) is not None:raise
        raise InitializationCustodyRefused('Native initializer custody refused') from error
    execute(cursor,sources[i+1:])
    return before,after,pairs,bounds


def relation(cursor):
    from ._migration_verify import _STRUCTURE
    # SET LOCAL must share a real transaction even for an administrative
    # autocommit observer. Native errors roll back the nested scope before
    # the caller regains control, preserving both its zone and original error.
    with cursor.connection.transaction():
        original=_zone(cursor)
        _set_zone(cursor,'UTC');cursor.execute(_STRUCTURE['relations'],prepare=False)
        rows=[list(row) for row in cursor.fetchall() if row[0]=='journal_runtime_horizon']
        if len(rows)!=1 or len(rows[0])!=11:raise ValueError('One exact original horizon row required')
        _set_zone(cursor,original)
        return rows[0]


def store(cursor,installation_id,owner_oid,manifest,runtime_digest,observations):
    try:
        before,after,pairs,bounds=observations;row=relation(cursor)
        if row[7] not in bounds:raise ValueError('Observed horizon does not derive from independent native window')
        # Recheck original backend/transaction without taking another clock read.
        cursor.execute('SELECT pg_catalog.pg_backend_pid(),pg_catalog.pg_current_xact_id()::text,(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database())',prepare=False)
        if cursor.fetchone()!=(before[2],before[3],before[4]):raise ValueError('Installation custody context changed')
        witness={'profile':PROFILE,'installationId':installation_id,'runtimeManifestSha256':runtime_digest,
            'initializerSha256':GROUPS_SHA,'installerSha256':source_policy(manifest)['installerSha256'],
            'databaseOid':before[4],'ownerOid':owner_oid,'backendPid':before[2],'writerXid':before[3],
            'timeZone':before[1],'clockBeforeUtc':before[0],'clockAfterUtc':after[0],
            'candidateBoundPairs':pairs,'originalRelation':row}
        raw=canonical(witness);validate_bytes(raw,sha256(raw).hexdigest(),policy=source_policy(manifest),runtime_digest=runtime_digest)
        cursor.execute('INSERT INTO truss.runtime_initialization_custody(installation_id,witness_bytes) VALUES(%s::uuid,%s::bytea)',(installation_id,raw),prepare=False)
        checked=verify_stored(cursor,{'sha256':runtime_digest,'manifest':manifest},row)
        if checked.raw!=raw:raise ValueError('Original witness readback changed')
        return checked
    except (ValueError,ValidationError) as error:
        if getattr(error,'initialization_cleanup_error',None) is not None:raise
        raise InitializationCustodyRefused('Post-DDL custody publication refused') from error


@dataclass(frozen=True)
class VerifiedCustody:
    raw:bytes
    digest:str
    original_relation:tuple
    policy_bytes:bytes
    candidate_bounds:tuple


def verify_stored(cursor,profile,actual_relation):
    policy=source_policy(profile['manifest'])
    cursor.execute('SELECT installation_id::text,owner_oid,(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()) FROM ONLY truss.catalog_runtime_installation WHERE singleton',prepare=False)
    installations=cursor.fetchmany(2)
    if len(installations)!=1:raise ValueError('One original installation identity required')
    identity,owner,database=installations[0]
    cursor.execute('SELECT installation_id::text,witness_bytes,pg_catalog.encode(witness_sha256,\'hex\') FROM ONLY truss.runtime_initialization_custody',prepare=False);rows=cursor.fetchmany(2)
    if len(rows)!=1 or rows[0][0]!=identity:raise ValueError('One protected original initialization witness required')
    raw=bytes(rows[0][1]);value=validate_bytes(raw,rows[0][2],policy=policy,runtime_digest=profile['sha256'])
    if value['installationId']!=identity or value['ownerOid']!=owner or value['databaseOid']!=database:raise ValueError('Original installation/database/owner custody differs')
    pairs,bounds=derive(cursor,value['clockBeforeUtc'],value['clockAfterUtc'],value['timeZone'])
    if pairs!=value['candidateBoundPairs'] or value['originalRelation']!=actual_relation or actual_relation[7] not in bounds:raise ValueError('Stored complete candidates/original literal row do not derive')
    return VerifiedCustody(raw,rows[0][2],tuple(actual_relation),canonical(policy),tuple(bounds))


def static_inventory_matches(observed,profile):
    """Classification ONLY, never dynamic-bound admission or native authority."""
    policies=profile.get('initializationPolicies')
    if type(policies) is not list or len(policies)!=1:return False
    validate_policy(policies[0],profile['manifest'])
    if profile.get('definitionAlternatives') or profile.get('initializationAlternatives'):return False
    expected=json.loads(canonical(profile['inventory']));actual=json.loads(canonical(observed))
    for inventory in (expected,actual):
        rows=[r for r in inventory.get('relations',[]) if r and r[0]=='journal_runtime_horizon']
        if len(rows)!=1 or len(rows[0])!=11:return False
        rows[0][7]=None
    return canonical(expected)==canonical(actual)


def custody_matches(observed,profile,verified):
    if not isinstance(verified,VerifiedCustody) or not static_inventory_matches(observed,profile):return False
    policy=profile['initializationPolicies'][0]
    row=[r for r in observed['relations'] if r[0]=='journal_runtime_horizon'][0]
    return verified.policy_bytes==canonical(policy) and canonical(row)==canonical(list(verified.original_relation))


def validate_observation(profile):
    """Validate original qualified capture transport, not a caller authority."""
    proof=profile.get('initializationCustody')
    if type(proof) is not dict:raise ValueError('Private original initialization custody observation required')
    policy=validate_policy(proof['policy'],profile['manifest'])
    if type(proof['witnessHex']) is not str:raise ValueError('Original immutable witness transport required')
    raw=bytes.fromhex(proof['witnessHex'])
    if raw.hex()!=proof['witnessHex']:raise ValueError('Canonical witness transport required')
    value=validate_bytes(raw,proof['sha256'],policy=policy,runtime_digest=profile['sha256'])
    rows=[r for r in profile['inventory']['relations'] if r[0]=='journal_runtime_horizon']
    if len(rows)!=1 or rows[0]!=value['originalRelation']:raise ValueError('Original literal capture row differs')
    native=proof['nativeDerivation']
    if (native['beforeUtc']!=value['clockBeforeUtc'] or native['afterUtc']!=value['clockAfterUtc'] or native['timeZone']!=value['timeZone'] or native['pairs']!=value['candidateBoundPairs'] or native['installerSha256']!=policy['installerSha256']
            or len(native['bounds'])!=len(native['pairs']) or rows[0][7] not in native['bounds']):raise ValueError('Original independent native derivation capture differs')
    if value['timeZone']!=profile['initializationTimeZone']:raise ValueError('Capture initialization zone differs from original witness')
    return policy,value
