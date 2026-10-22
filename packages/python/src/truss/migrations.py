# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit latest-only administrative migrations over an idle host connection.

The tool owns transaction settlement. The host supplies a connection factory and
CONTRACT-007 restart-durable HostRecoveryRegistry; no caller transaction is adopted.
"""
from __future__ import annotations
from dataclasses import dataclass
from uuid import uuid4,UUID
import base64
import json
from hashlib import sha256
import psycopg
from ._migration_recipe import load_recipe,plan_route
from ._migration_verify import context,verify,verify_artifact,verify_profile,installed_profile,canonical,profile_for
from ._migration_execute import active,exclude,execute,receipt,MigrationCursor


@dataclass(frozen=True)
class MigrationResult:
    outcome: str
    reference: str | None = None
    attempt_id: str | None = None
    source: str | None = None
    target: str | None = None
    detail: str | None = None
    receipt: object = None
    current_verification: object = None


_PROFILE={'identity':'truss-runtime-migration','version':'0.1',
          'sha256':sha256(b'latest-only transactional UMF0.10 migration; installed-target recovery; native inventory and preservation').hexdigest()}


def _artifact(value,identity):
    raw=canonical(value)
    return {'identity':identity,'sha256':sha256(raw).hexdigest(),'bytesBase64':base64.b64encode(raw).decode()}


def _original_bytes(raw,identity):
    raw=bytes(raw)
    return {'identity':identity,'sha256':sha256(raw).hexdigest(),'bytesBase64':base64.b64encode(raw).decode()}


def _evidence(artifact):
    raw=base64.b64decode(artifact['bytesBase64'],validate=True)
    if sha256(raw).hexdigest()!=artifact['sha256']:raise ValueError('Original recovery evidence changed')
    return json.loads(raw)


class RuntimeMigrations:
    def __init__(self,connect,recovery_registry,*,maximum_preservation_bytes=268435456,operation_timeout_ms=30000,statement_timeout_ms=10000):
        if recovery_registry.retention!='restart_durable':raise ValueError('Restart-durable HostRecoveryRegistry required')
        if type(maximum_preservation_bytes) is not int or not 1<=maximum_preservation_bytes<=2**63-1:
            raise ValueError('Finite migration preservation limit required')
        if type(operation_timeout_ms) is not int or not 1<=operation_timeout_ms<=2147483647:raise ValueError('Finite migration deadline required')
        if type(statement_timeout_ms) is not int or not 1<=statement_timeout_ms<=2147483647:raise ValueError('Finite statement timeout required')
        self.timeout=operation_timeout_ms;self.statement_timeout=statement_timeout_ms
        self.connect=connect;self.registry=recovery_registry;self.max_bytes=maximum_preservation_bytes

    def _resources(self):
        return {'maximumPreservationBytes':self.max_bytes,'operationTimeoutMs':self.timeout,'statementTimeoutMs':self.statement_timeout}

    def _connection(self):
        connection=self.connect()
        if not isinstance(connection,psycopg.Connection) or not connection.autocommit or connection.info.transaction_status!=psycopg.pq.TransactionStatus.IDLE:
            # Never settle or close a caller's active transaction.
            raise ValueError('Owned idle autocommit psycopg connection required')
        return connection

    @staticmethod
    def _begin(connection,*,read_only=False):
        connection.execute('BEGIN ISOLATION LEVEL READ COMMITTED, READ ONLY' if read_only else 'BEGIN ISOLATION LEVEL READ COMMITTED, READ WRITE')
        connection.execute("SET LOCAL search_path=pg_catalog,pg_temp")
        connection.execute("SET LOCAL statement_timeout='10000ms'")
        connection.execute("SET LOCAL idle_in_transaction_session_timeout='30000ms'")

    def status(self):
        manifest,artifacts,_=load_recipe()
        with self._connection() as connection:
            self._begin(connection,read_only=True)
            with connection.cursor() as raw_cursor:
                cursor=MigrationCursor(raw_cursor,self.timeout,self.statement_timeout)
                ctx,expected=installed_profile(cursor,manifest,artifacts)
                release,digest=expected['manifest']['releaseId'],expected['sha256']
            connection.rollback()
        return {'context':ctx,'releaseId':release,'manifestSha256':digest,'target':manifest['target'],
                'state':'current' if digest==manifest['target'] else 'upgrade_required'}

    verify=status

    def backup_metadata(self):
        """Companion to logical backup: pg_dump omits table-row-type ACLs.

        Return only the qualified source's private type closure. Applying this
        companion belongs to an explicit offline restore, never migration repair.
        """
        state=self.status();manifest,artifacts,_=load_recipe()
        profile=profile_for(manifest,artifacts,state['manifestSha256'])
        names={row[0] for row in profile['inventory']['relations'] if row[1] in ('r','p')}
        for kind,grants in profile['acl'].items():
            if kind=='owner':continue
            if any(row[0]=='type' and row[1] in names for row in grants):
                raise ValueError('This source needs a separately qualified logical-backup privilege profile')
        commands=[psycopg.sql.SQL('REVOKE ALL ON TYPE {} FROM PUBLIC').format(psycopg.sql.Identifier('truss',name)).as_string() for name in sorted(names)]
        return {'context':state['context'],'sourceManifestSha256':state['manifestSha256'],
                'rowTypePrivilegeRestoreSql':commands}

    def prepare(self,*,attempt_id=None):
        manifest,artifacts,digest=load_recipe();state=self.status()
        if state['state']=='current':raise ValueError('Already at latest; no migration receipt is manufactured')
        attempt_id=str(UUID(attempt_id)) if attempt_id is not None else str(uuid4())
        request={'interfaceVersion':'truss-layout-migration-request/0.1.0',
                 'attemptId':attempt_id,'context':state['context'],
                 'resource':self._resources(),
                 'source':state['manifestSha256'],'target':manifest['target'],'recipe':digest}
        # Same installed-target registry protocol and identity; no second recovery namespace.
        obligation={'obligationId':request['attemptId'],'assemblyId':'runtime-migrations',
                    'target':request['context'],'assemblyProfile':_PROFILE,
                    'observationProfile':_PROFILE,'ownership':'assembly_owned',
                    'originalEvidence':_artifact({'request':request,'sourceObservation':state},'layout-migration-attempt')}
        reference=self.registry.register(obligation)
        return MigrationResult('prepared',reference,request['attemptId'],request['source'],request['target'])

    def _original(self,reference):
        # Registry owns authorization and context association. Context must come from
        # current independently observed installation, never from a caller JSON permit.
        with self._connection() as connection:
            self._begin(connection,read_only=True)
            with connection.cursor() as cursor:ctx,_,_=context(cursor)
            connection.rollback()
        retained=self.registry.inspect(reference,ctx)
        request=_evidence(retained['obligation']['originalEvidence'])['request']
        manifest,artifacts,digest=load_recipe()
        original_manifest=manifest
        if request['recipe']!=digest:
            name=request['recipe']+'.manifest.json'
            raw=artifacts.get(name)
            if raw is None or sha256(raw).hexdigest()!=request['recipe']:
                raise ValueError('Original published migration manifest unavailable')
            original_manifest=json.loads(raw)
        if request['context']!=ctx or request['target']!=original_manifest['target'] or request['source'] not in original_manifest['sources']:
            raise ValueError('Original request/recipe correspondence required')
        return retained,request,manifest,artifacts,digest

    def _observe(self,reference,retained,request,phase,durability,session=None,resource_released=True):
        observations=retained['observations']
        observation={'obligationId':request['attemptId'],'observationId':str(uuid4()),
            'expectedPreviousObservationId':observations[-1]['observationId'] if observations else None,
            'observationProfile':_PROFILE,
            'nativeTermination':'confirmed' if durability in ('committed','rolled_back') else 'unknown',
            'resourceRelease':'confirmed' if resource_released and durability in ('committed','rolled_back') else 'unknown',
            'applicationDurability':durability}
        evidence={'phase':phase,'requestSha256':sha256(canonical(request)).hexdigest()}
        if session is not None:evidence['session']=session
        observation['evidence']=_artifact(evidence,'layout-migration-observation')
        self.registry.append(reference,observation);observations.append(observation)

    def apply(self,reference):
        retained,request,manifest,artifacts,digest=self._original(reference)
        if retained['observations']:return self.reconcile(reference)
        if request['target']!=manifest['target'] or request['recipe']!=digest:
            raise ValueError('Unsubmitted requests must be prepared for latest; no old target execution')
        if request['resource']!=self._resources():
            raise ValueError('Original resource profile required for execution')
        # Durable submission intent precedes BEGIN/steps; restart never guesses permission to replay.
        connection=self._connection();committing=False
        try:
            row=connection.execute('SELECT pid,backend_start::text FROM pg_stat_activity WHERE pid=pg_backend_pid()').fetchone()
            self._observe(reference,retained,request,'submission','unknown',session=list(row))
        except BaseException:
            connection.close();raise
        try:
            self._begin(connection)
            with connection.cursor() as raw_cursor:
                cursor=MigrationCursor(raw_cursor,self.timeout,self.statement_timeout)
                execute(cursor,request,manifest,artifacts,digest,self.max_bytes,plan_route(manifest,request['source']))
                cursor.check()
            committing=True;connection.commit()
        except BaseException as error:
            outcome='commit_unknown' if committing else 'recovery_required'
            if not committing:
                try:
                    connection.rollback()
                    connection.close()
                    self._observe(reference,retained,request,'rollback','rolled_back');outcome='rolled_back'
                except BaseException:pass
            return MigrationResult(outcome,reference,request['attemptId'],request['source'],request['target'],str(error))
        finally:
            connection.close()
        try:self._observe(reference,retained,request,'commit','committed')
        except Exception as error:
            return MigrationResult('committed_unverified',reference,request['attemptId'],request['source'],request['target'],str(error))
        return self._verify_commit(reference,request,'migrated')

    def _verify_commit(self,reference,request,outcome):
        try:
            manifest,artifacts,_=load_recipe()
            with self._connection() as connection:
                self._begin(connection,read_only=True)
                with connection.cursor() as raw_cursor:
                    cursor=MigrationCursor(raw_cursor,self.timeout,self.statement_timeout)
                    installed_profile(cursor,manifest,artifacts)
                    row=receipt(cursor,request['attemptId'])
                    if row is None:raise ValueError('Original committed receipt not visible')
                    self._require_receipt(row,request)
                connection.rollback()
            current=self.status()
            if current['state']!='current':raise ValueError('Original migration committed; further migration to latest required')
            return MigrationResult(outcome,reference,request['attemptId'],request['source'],request['target'],receipt=row,current_verification=current)
        except Exception as error:
            return MigrationResult('committed_unverified',reference,request['attemptId'],request['source'],request['target'],str(error))

    @staticmethod
    def _require_receipt(row,request):
        if row[0]!=canonical(request).hex() or row[1]!=sha256(canonical(request)).hexdigest() or row[2:5]!=[request['source'],request['target'],request['recipe']]:
            raise ValueError('Original receipt correspondence failed')

    def receipt(self,reference):
        """Read the complete immutable original body through the latest tool."""
        _,request,manifest,artifacts,_=self._original(reference)
        with self._connection() as connection:
            self._begin(connection,read_only=True)
            with connection.cursor() as raw_cursor:
                cursor=MigrationCursor(raw_cursor,self.timeout,self.statement_timeout)
                installed_profile(cursor,manifest,artifacts)
                row=receipt(cursor,request['attemptId'])
                if row is None:raise ValueError('Original committed receipt not visible')
                self._require_receipt(row,request)
                cursor.execute('SELECT request_bytes,recipe_bytes,source_inventory_bytes,target_inventory_bytes,step_evidence_bytes,preservation_bytes,writer_xid::text,applied_at::text FROM truss.runtime_migration_receipt WHERE attempt_id=%s',(request['attemptId'],),prepare=False)
                values=cursor.fetchone()
                names=('originalRequest','recipe','sourceInventory','targetInventory','orderedStepEvidence','preservation')
                result={name:_original_bytes(raw,'layout-migration-'+name) for name,raw in zip(names,values[:6],strict=True)}
                result.update(attemptId=request['attemptId'],writerXid=values[6],preparedAt=values[7])
            connection.rollback()
        return result

    def reconcile(self,reference):
        retained,request,manifest,artifacts,digest=self._original(reference)
        # Same exclusion used by apply: a still-running original transaction cannot
        # be mistaken for an absent/rolled-back receipt under a concurrent snapshot.
        try:
            with self._connection() as connection:
                self._begin(connection)
                with connection.cursor() as raw_cursor:
                    cursor=MigrationCursor(raw_cursor,self.timeout,self.statement_timeout)
                    exclude(cursor)
                    installed_profile(cursor,manifest,artifacts)
                    row=receipt(cursor,request['attemptId'])
                    evidence=[_evidence(o['evidence']) for o in retained['observations']]
                    original_sessions=[e['session'] for e in evidence if 'session' in e]
                    if not original_sessions:raise ValueError('Original dispatch session was not recorded')
                    alive=False
                    for pid,started in original_sessions:
                        cursor.execute('SELECT EXISTS(SELECT 1 FROM pg_stat_activity WHERE pid=%s AND (backend_start IS NULL OR backend_start=%s::pg_catalog.timestamptz))',(pid,started),prepare=False)
                        exists=cursor.fetchone()[0];alive=alive or exists
                    if row is not None:
                        self._require_receipt(row,request)
                        outcome='already_applied';durability='committed'
                    elif active(cursor)[1]==request['source']:
                        if alive:raise ValueError('Original dispatch backend remains alive')
                        source=profile_for(manifest,artifacts,request['source'])
                        verify_profile(cursor,source)
                        verify_artifact(cursor,source)
                        outcome='rolled_back';durability='rolled_back'
                    else:raise ValueError('Original outcome cannot be resolved from target state')
                connection.rollback()
        except Exception as error:
            known=any(o['applicationDurability']=='committed' for o in retained['observations'])
            return MigrationResult('committed_unverified' if known else 'recovery_required',reference,request['attemptId'],request['source'],request['target'],str(error))
        self._observe(reference,retained,request,'reconcile',durability,resource_released=not alive)
        if alive:
            return MigrationResult('committed_unverified',reference,request['attemptId'],request['source'],request['target'],'Original backend cleanup unconfirmed',receipt=row)
        return self._verify_commit(reference,request,outcome) if durability=='committed' else MigrationResult(outcome,reference,request['attemptId'],request['source'],request['target'])
