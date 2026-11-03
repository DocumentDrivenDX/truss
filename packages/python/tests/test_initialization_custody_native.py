# SPDX-License-Identifier: MIT OR Apache-2.0
"""JH installed-custody controls. UNEXECUTED until genuine cohort admission.

Uses only the existing campaign worker. No simulated initializer/server clock.
Administrator mutation controls test consistency, not protection from that admin.
"""
import copy
import json
import os
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.pq import TransactionStatus
from native_fixture import DatabaseFixture
from runtime_migration_fixture import assembly
from truss import Ok
from truss.lifecycle import InstallRefused
from truss.catalog_runtime import _release
from truss import _initialization_custody as custody
from truss._migration_verify import structure,verify_artifact
from truss._migration_recipe import load_recipe
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry


class InitializationCustodyNativeTests(unittest.TestCase):
    def setUp(self):
        worker=os.environ.get('TRUSS_NATIVE_WORKER')
        if not worker:raise RuntimeError('JH installed controls require the campaign-owned worker')
        self.fixture=DatabaseFixture(Path(worker));self.addCleanup(self.fixture.cleanup)
        self.uri=self.fixture.get_uri();self.c=psycopg.connect(self.uri,autocommit=True,options='-c statement_timeout=15000')
        self.addCleanup(self.c.close);self.addCleanup(self.c.rollback)
        self.manifest,self.digest,_=_release();self.profile={'manifest':self.manifest,'sha256':self.digest}

    def install(self):
        self.c.execute('BEGIN');host,a,tx=assembly(self.c)
        try:result=a.install_in_transaction(tx)
        finally:host.detach()
        self.assertIsInstance(result,Ok,repr(result));self.assertNotIsInstance(result.value,InstallRefused,repr(result))
        self.c.commit();self.pending=result.value
        return result.value

    def witness(self,connection=None):
        connection=self.c if connection is None else connection
        with connection.cursor() as cursor:
            row=custody.relation(cursor)
            return custody.verify_stored(cursor,self.profile,row)

    def test_original_witness_and_ordinary_effective_privilege_denials(self):
        installed=self.install();original=self.witness();value=json.loads(original.raw)
        self.assertEqual(value['installationId'],installed.installation_id)
        self.assertEqual(value['initializerSha256'],custody.GROUPS_SHA)
        self.assertEqual(value['runtimeManifestSha256'],self.digest)
        self.assertEqual(value['originalRelation'],list(original.original_relation))
        actors=[installed.registrar_role]
        for kind in ('reader','writer','audit','feed','public'):
            name='jh_'+kind+'_'+uuid4().hex[:12]
            self.c.execute(sql.SQL('CREATE ROLE {} NOLOGIN NOINHERIT').format(sql.Identifier(name)));actors.append(name)
        for actor in actors:
            for command in ('SELECT witness_bytes FROM truss.runtime_initialization_custody',
                'INSERT INTO truss.runtime_initialization_custody(installation_id,witness_bytes) SELECT installation_id,witness_bytes FROM truss.runtime_initialization_custody',
                "UPDATE truss.runtime_initialization_custody SET witness_bytes='x'::bytea",
                'DELETE FROM truss.runtime_initialization_custody','TRUNCATE truss.runtime_initialization_custody'):
                with self.subTest(actor=actor,command=command),self.assertRaises(psycopg.errors.InsufficientPrivilege):
                    with self.c.transaction():
                        self.c.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(actor)));self.c.execute(command)
        self.assertEqual(self.witness().raw,original.raw)
        with self.assertRaises(psycopg.Error):
            with self.c.transaction():self.c.execute('DELETE FROM truss.runtime_initialization_custody')
        self.assertEqual(self.witness().raw,original.raw)

    def test_resigned_cross_context_candidates_literal_bound_and_static_drift_refuse(self):
        self.install();original=self.witness();value=json.loads(original.raw)
        mutations=[]
        for key in ('installationId','ownerOid','databaseOid','runtimeManifestSha256','installerSha256'):
            altered=copy.deepcopy(value)
            altered[key]=str(uuid4()) if key=='installationId' else (value[key]+1 if key.endswith('Oid') else '0'*64)
            mutations.append(altered)
        altered=copy.deepcopy(value);altered['candidateBoundPairs'][0]['upperUtc']='2099-01-01T00:00:00.000000Z';mutations.append(altered)
        altered=copy.deepcopy(value);altered['originalRelation'][7]='FOR VALUES FROM (MINVALUE) TO (MAXVALUE)';mutations.append(altered)
        class RollbackCase(Exception):pass
        for altered in mutations:
            with self.subTest(altered=altered),self.assertRaises(RollbackCase):
                with self.c.transaction():
                    self.c.execute('ALTER TABLE truss.runtime_initialization_custody DISABLE TRIGGER USER')
                    self.c.execute('UPDATE truss.runtime_initialization_custody SET witness_bytes=%s',(custody.canonical(altered),))
                    with self.assertRaises(ValueError):self.witness()
                    raise RollbackCase()
            self.assertEqual(self.witness().raw,original.raw)
        recipe,artifacts,_=load_recipe();profile=json.loads(artifacts[recipe['target']+'.json'])
        with self.assertRaises(RollbackCase):
            with self.c.transaction():
                self.c.execute('ALTER TABLE truss.runtime_initialization_custody ADD COLUMN unadmitted text')
                with self.c.cursor() as cursor:
                    with self.assertRaises(ValueError):verify_artifact(cursor,profile)
                raise RollbackCase()
        with self.c.cursor() as cursor:verify_artifact(cursor,profile)

    def test_reconnect_observer_zones_backup_and_original_custody_preserved(self):
        self.install();original=self.witness()
        for zone in ('UTC','America/New_York','Pacific/Auckland'):
            with psycopg.connect(self.uri,autocommit=False) as connection:
                connection.execute("SELECT set_config('TimeZone',%s,true)",(zone,))
                before=connection.execute('SHOW TimeZone').fetchone()
                checked=self.witness(connection)
                self.assertEqual(checked.raw,original.raw);self.assertEqual(checked.original_relation,original.original_relation)
                self.assertEqual(connection.execute('SHOW TimeZone').fetchone(),before)
                connection.rollback()
        with tempfile.TemporaryDirectory() as directory:
            tool=RuntimeMigrations(lambda:psycopg.connect(self.uri,autocommit=True),HostRecoveryRegistry(Path(directory)/'backup.sqlite'))
            backup=tool.backup_metadata()
        self.assertEqual(backup['initializationCustody']['witnessHex'],original.raw.hex())
        self.assertEqual(backup['initializationCustody']['sha256'],original.digest)
        self.assertEqual(backup['originalHorizonRelation'],list(original.original_relation))
        # A changed database binding is refused rather than inferred/remapped.
        self.assertEqual(json.loads(original.raw)['databaseOid'],self.c.execute("SELECT oid FROM pg_database WHERE datname=current_database()").fetchone()[0])

    def test_postddl_custody_refusal_is_contained_and_preserves_prior_caller_work(self):
        self.c.execute('BEGIN');self.c.execute('CREATE TEMP TABLE jh_prior_work(value int)');self.c.execute('INSERT INTO jh_prior_work VALUES(7)')
        xid=self.c.execute('SELECT pg_current_xact_id()::text').fetchone()[0]
        before=self.c.execute('SELECT oid,rolname FROM pg_roles ORDER BY oid').fetchall()
        host,a,tx=assembly(self.c)
        try:
            with patch('truss._initialization_custody.store',side_effect=custody.InitializationCustodyRefused('injected post-DDL containment control')):
                result=a.install_in_transaction(tx)
        finally:host.detach()
        self.assertEqual(result,Ok(InstallRefused(code='incompatible')))
        self.assertEqual(self.c.info.transaction_status,TransactionStatus.INTRANS)
        self.assertEqual(self.c.execute('SELECT pg_current_xact_id()::text').fetchone()[0],xid)
        self.assertEqual(self.c.execute('SELECT * FROM jh_prior_work').fetchall(),[(7,)])
        self.assertEqual(self.c.execute("SELECT count(*) FROM pg_namespace WHERE nspname='truss'").fetchone(),(0,))
        self.assertEqual(self.c.execute('SELECT oid,rolname FROM pg_roles ORDER BY oid').fetchall(),before)
        self.c.rollback()
