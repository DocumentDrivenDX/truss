# SPDX-License-Identifier: MIT OR Apache-2.0
"""Transactional migration effects; public tool owns settlement and recovery."""
import json
from hashlib import sha256
from time import monotonic
from psycopg import sql
from ._migration_verify import verify,verify_artifact,verify_profile,preservation,canonical,acl


class MigrationCursor:
    """Bound each native statement by the remaining whole-operation deadline."""
    def __init__(self,cursor,timeout_ms,statement_timeout_ms=10000):
        self.cursor=cursor;self.deadline=monotonic()+timeout_ms/1000;self.statement_timeout=statement_timeout_ms

    def __getattr__(self,name):return getattr(self.cursor,name)

    def check(self):
        remaining=int((self.deadline-monotonic())*1000)
        if remaining<1:raise TimeoutError('Migration operation deadline exceeded')
        self.cursor.connection.execute("SELECT pg_catalog.set_config('statement_timeout',%s,true)",(str(min(remaining,self.statement_timeout)),))

    def execute(self,*args,**kwargs):
        self.check();self.cursor.execute(*args,**kwargs);self.check()
        return self


def exclude(cursor):
    cursor.execute('SELECT pg_try_advisory_xact_lock(1953658227,1735549296)',prepare=False)
    if cursor.fetchone()!=(True,):raise ValueError('Installation administration busy')
    cursor.execute("SELECT relname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss' AND c.relkind IN ('r','p') ORDER BY relname",prepare=False)
    names=[r[0] for r in cursor.fetchall()]
    if not names:raise ValueError('Original installation missing')
    # One deterministic acquisition order, no internal retries or temporary bypass grants.
    cursor.execute(sql.SQL('LOCK TABLE {} IN ACCESS EXCLUSIVE MODE NOWAIT').format(sql.SQL(',').join(sql.Identifier('truss',n) for n in names)),prepare=False)


def active(cursor):
    cursor.execute('SELECT release_id,release_sha256 FROM truss.runtime_current_installation()',prepare=False)
    rows=cursor.fetchmany(2)
    if len(rows)!=1:raise ValueError('One active runtime required')
    return rows[0]


def receipt(cursor,attempt_id):
    cursor.execute("SELECT to_regclass('truss.runtime_migration_receipt') IS NOT NULL",prepare=False)
    if not cursor.fetchone()[0]:return None
    cursor.execute('SELECT request_bytes,request_sha256,source_sha256,target_sha256,recipe_sha256,preservation_bytes,writer_xid::text FROM truss.runtime_migration_receipt WHERE attempt_id=%s',(attempt_id,),prepare=False)
    row=cursor.fetchone()
    return None if row is None else [bytes(v).hex() if isinstance(v,(bytes,memoryview)) else v for v in row]


def execute(cursor,request,manifest,artifacts,recipe_digest,max_bytes,route):
    exclude(cursor)
    source=json.loads(artifacts[request['source']+'.json'])
    ctx,source=verify_artifact(cursor,source)
    verify_profile(cursor,source)
    if ctx!=request['context']:raise ValueError('Original installation context changed')
    before=preservation(cursor,source['inventory'],max_bytes)
    old_acl=acl(cursor)
    ordered=[];recipes=[]
    def submit(statement,kind):
        original=statement if isinstance(statement,str) else statement.as_string(cursor)
        cursor.execute(statement,prepare=False)
        statuses=[cursor.statusmessage]
        while cursor.nextset():statuses.append(cursor.statusmessage)
        ordered.append({'ordinal':len(ordered),'kind':kind,'statementSha256':sha256(original.encode()).hexdigest(),'nativeCompletions':statuses})
    cursor.execute('SELECT r.rolname FROM truss.catalog_runtime_installation i JOIN pg_roles r ON r.oid=i.owner_oid',prepare=False)
    owner=cursor.fetchone()[0]
    for edge in route:
        raw=artifacts[edge['artifact']];recipe=json.loads(raw)
        if recipe['source']!=edge['source'] or recipe['target']!=edge['target']:
            raise ValueError('Original edge correspondence required')
        recipes.append({'edge':edge,'recipe':recipe})
        for statement in recipe['steps']:submit(statement,'step')
        for statement in recipe['ownership']:submit(sql.SQL(statement).format(sql.Identifier(owner)),'ownership')
        cursor.execute('SELECT DISTINCT reader_role FROM truss.module_access UNION SELECT DISTINCT writer_role FROM truss.module_access',prepare=False)
        for (role,) in cursor.fetchall():
            for signature in recipe['moduleGrants']:
                submit(sql.SQL('GRANT EXECUTE ON FUNCTION truss.{} TO {}').format(sql.SQL(signature),sql.Identifier(role)),'module_grant')
        intermediate=json.loads(artifacts[edge['target']+'.json'])
        verify_artifact(cursor,intermediate)
    # All predecessor tables/sequences, including immutable genesis, remain exact.
    after=preservation(cursor,source['inventory'],max_bytes)
    if before!=after:raise ValueError('Migration changed retained data or sequence state')
    # Each immutable edge declares its exact target privilege profile. Obsolete
    # facades may be retired by a future reviewed edge; preserving old runtime
    # grants forever would violate latest-only support. Retain both observations.
    target=json.loads(artifacts[manifest['target']+'.json'])
    _,target=verify_artifact(cursor,target)
    cursor.execute('INSERT INTO truss.runtime_migration_receipt(attempt_id,request_bytes,request_sha256,source_sha256,target_sha256,target_release,target_layout_profile,target_configuration,recipe_sha256,recipe_bytes,source_inventory_bytes,target_inventory_bytes,step_evidence_bytes,preservation_bytes) VALUES(%s,%s,encode(sha256(%s),\'hex\'),%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s,%s,%s,%s,%s)',
        (request['attemptId'],canonical(request),canonical(request),request['source'],manifest['target'],manifest['targetRelease'],json.dumps(target['manifest']['layoutProfile']),json.dumps(target['configuration']),recipe_digest,canonical(recipes),canonical(source),canonical(target),canonical({'steps':ordered,'sourceAcl':old_acl,'targetAcl':acl(cursor)}),canonical(before)),prepare=False)
    if active(cursor)!=(manifest['targetRelease'],manifest['target']):raise ValueError('Atomic target publication failed')
    verify_profile(cursor,target)
    return before
