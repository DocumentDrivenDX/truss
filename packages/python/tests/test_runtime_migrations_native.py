# SPDX-License-Identifier: MIT OR Apache-2.0
"""Real published-wheel → installed latest migration, preservation and settlement."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4
import zipfile
from hashlib import sha256
import psycopg
from truss import LocalPostgres,Ok,ObjectFound,CatalogDocument
from truss._migration_recipe import load_recipe
from truss._migration_verify import structure,preservation
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
from runtime_migration_fixture import assembly
from test_catalog_relational_support import relational_document


class RuntimeMigrationNativeTests(unittest.TestCase):
    source_label='source44'
    wheel_environment='TRUSS_MIGRATION_SOURCE_WHEEL'
    wheel_default='/private/tmp/truss-release44-public-download/truss_toolkit-0.0.44-py3-none-any.whl'

    @classmethod
    def setUpClass(cls):
        cls.root=Path(tempfile.mkdtemp(prefix='truss-runtime-migrations-'))
        cls.runtime=LocalPostgres(cls.root/'data');cls.runtime.__enter__()
        import shutil
        cls.addClassCleanup(shutil.rmtree,cls.root)
        cls.addClassCleanup(cls.runtime.close)
        cls.uri=cls.runtime.info.connection_uri
        manifest,_,_=load_recipe();wheel=Path(os.environ.get(cls.wheel_environment,cls.wheel_default))
        if not wheel.is_file():raise AssertionError('Real predecessor wheel required: '+str(wheel))
        if sha256(wheel.read_bytes()).hexdigest()!=manifest['sourceWheels'][cls.source_label]['sha256']:
            raise AssertionError('Exact published predecessor wheel required')
        cls.old=cls.root/'predecessor';zipfile.ZipFile(wheel).extractall(cls.old)
        cls.model=relational_document();cls.model['id']='adoc'
        cls.model['vocabularies']={'x-migration-opaque':{'version':'1.0.0'}}
        cls.model['extensions']={'x-migration-opaque':{'future':[3,1,4],'null':None}}
        if cls.source_label=='source44':
            # v0.0.44 admitted unnamed UMF records/fields. Registration's newer
            # authored-name rule must not strand that already accepted data.
            for element in cls.model['modules'][0]['elements']:
                if element['id'].startswith('B'):element.pop('name',None)
        cls.model_path=cls.root/'model.json';cls.model_path.write_text(json.dumps(cls.model,indent=2))
        with psycopg.connect(cls.uri,autocommit=True) as c:c.execute('CREATE DATABASE migration_template')
        params=psycopg.conninfo.conninfo_to_dict(cls.uri);params['dbname']='migration_template'
        source_uri=psycopg.conninfo.make_conninfo(**params)
        producer=Path(__file__).with_name('runtime_migration_fixture.py')
        result=subprocess.run([sys.executable,str(producer),source_uri,str(cls.model_path),str(cls.root/'seed.json')],
            env={**os.environ,'PYTHONPATH':str(cls.old)},text=True,capture_output=True,timeout=120)
        if result.returncode:raise AssertionError(result.stdout+result.stderr)
        cls.seed=json.loads((cls.root/'seed.json').read_bytes())
        if directory:=os.environ.get('TRUSS_MIGRATION_EVIDENCE_DIRECTORY'):
            # Test-only raw catalog evidence: diagnose real platform differences
            # without changing admission or normalizing away native definitions.
            from truss._migration_verify import canonical,matches_inventory
            _,artifacts,_=load_recipe()
            expected=json.loads(artifacts[manifest['sourceWheels'][cls.source_label]['runtimeManifestSha256']+'.json'])
            with psycopg.connect(source_uri,autocommit=True) as connection,connection.cursor() as cursor:
                cursor.execute('SET search_path=pg_catalog,pg_temp')
                observed=structure(cursor)
                cursor.execute('SELECT datcollate,datctype,datlocprovider FROM pg_database WHERE datname=current_database()')
                locale=cursor.fetchone()
            differences={}
            for category,rows in expected['inventory'].items():
                actual=observed[category]
                if actual==rows:continue
                wanted={canonical(row) for row in rows};found={canonical(row) for row in actual}
                def sample(values):
                    return [{'sha256':sha256(value).hexdigest(),'prefix':value.decode()[:1000]} for value in sorted(values)[:3]]
                differences[category]={'expectedRows':len(rows),'observedRows':len(actual),
                    'expectedOnly':sample(wanted-found),'observedOnly':sample(found-wanted),
                    'orderingOnly':wanted==found}
            diagnostic={'source':cls.source_label,'locale':locale,'matches':matches_inventory(observed,expected),
                'differences':differences,'inventory':observed}
            Path(directory,cls.source_label+'-native-inventory.json').write_text(json.dumps(diagnostic,indent=2)+'\n')
            if not diagnostic['matches']:print('Native inventory admission diagnostic: '+json.dumps({k:v for k,v in diagnostic.items() if k!='inventory'}),flush=True)

    def setUp(self):
        self.database='migration_'+uuid4().hex[:12]
        with psycopg.connect(self.uri,autocommit=True) as c:
            c.execute(psycopg.sql.SQL('CREATE DATABASE {} TEMPLATE migration_template').format(psycopg.sql.Identifier(self.database)))
        self.params=psycopg.conninfo.conninfo_to_dict(self.uri);self.params['dbname']=self.database
        self.admin=psycopg.connect(**self.params,autocommit=True,options='-c statement_timeout=10000')
        self.registry=HostRecoveryRegistry(self.root/(self.database+'.sqlite'))
        self.tool=RuntimeMigrations(self.connect,self.registry)

    def tearDown(self):
        self.admin.close()
        with psycopg.connect(self.uri,autocommit=True) as c:
            c.execute(psycopg.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(psycopg.sql.Identifier(self.database)))

    def connect(self):return psycopg.connect(**self.params,autocommit=True,options='-c statement_timeout=10000')

    def state(self):
        with self.admin.transaction(), self.admin.cursor() as cursor:
            cursor.execute('SET search_path=pg_catalog,pg_temp')
            observed=structure(cursor)
            return observed,preservation(cursor,observed)

    def test_clean_installed_cli_prepare_apply_verify_and_receipt(self):
        """@covers US-045-AC8: separate CLI processes retain one original attempt."""
        def command(action,*args):
            completed=subprocess.run([sys.executable,'-c','from truss.cli import migrate_main; migrate_main()',
                action,'--registry',str(self.root/(self.database+'-cli.sqlite')),*args],
                env={**os.environ,'TRUSS_DATABASE_URI':psycopg.conninfo.make_conninfo(**self.params)},
                capture_output=True,text=True,timeout=60)
            self.assertEqual(completed.returncode,0,completed.stdout+completed.stderr)
            return json.loads(completed.stdout)
        self.assertEqual(command('status')['state'],'upgrade_required')
        prepared=command('prepare');reference=prepared['reference']
        self.assertEqual(command('apply','--reference',reference)['outcome'],'migrated')
        self.assertEqual(command('verify')['state'],'current')
        self.assertEqual(command('reconcile','--reference',reference)['outcome'],'already_applied')
        self.assertEqual(command('receipt','--reference',reference)['attemptId'],prepared['attempt_id'])

    def test_observer_timezone_cannot_convert_native_partition_bounds(self):
        """@covers US-045-AC6 @covers US-045-AC7"""
        before=self.state()[0]
        original_zone=self.admin.execute('SHOW TimeZone').fetchone()[0]
        try:
            for zone in ('America/New_York','Pacific/Auckland'):
                self.admin.execute("SELECT set_config('TimeZone',%s,false)",(zone,))
                with self.admin.cursor() as cursor:self.assertEqual(structure(cursor),before)
                self.assertEqual(self.admin.execute('SHOW TimeZone').fetchone(),(zone,))
            tool=RuntimeMigrations(lambda:psycopg.connect(**self.params,autocommit=True,
                options='-c statement_timeout=10000 -c TimeZone=Pacific/Auckland'),self.registry)
            result=tool.apply(tool.prepare().reference)
            self.assertEqual(result.outcome,'migrated',result)
            after=self.state()[0]
            self.assertEqual(next(r for r in before['relations'] if r[0]=='journal_runtime_horizon'),
                             next(r for r in after['relations'] if r[0]=='journal_runtime_horizon'))
        finally:self.admin.execute("SELECT set_config('TimeZone',%s,false)",(original_zone,))

    def test_other_qualified_bounds_cannot_replace_original_initialization(self):
        """@covers US-045-AC7: rollback even a separately qualified horizon change."""
        from truss import _migration_execute
        manifest,artifacts,_=load_recipe();before=self.state()
        profile=json.loads(artifacts[manifest['target']+'.json'])
        original=next(r for r in before[0]['relations'] if r[0]=='journal_runtime_horizon')
        other=next(r for r in profile['initializationAlternatives'][0]['rows'] if r!=original)
        verify=_migration_execute.verify_artifact;changed=False
        def replace_bounds(cursor,selected):
            nonlocal changed
            if selected['sha256']==manifest['target'] and not changed:
                cursor.execute('ALTER TABLE truss.journal DETACH PARTITION truss.journal_runtime_horizon',prepare=False)
                cursor.execute('ALTER TABLE truss.journal ATTACH PARTITION truss.journal_runtime_horizon '+other[7],prepare=False)
                changed=True
            return verify(cursor,selected)
        prepared=self.tool.prepare()
        with patch('truss._migration_execute.verify_artifact',side_effect=replace_bounds):
            result=self.tool.apply(prepared.reference)
        self.assertTrue(changed)
        self.assertEqual(result.outcome,'rolled_back',result)
        self.assertIn('original native initialization',result.detail)
        self.assertEqual(self.state(),before)

    def test_fresh_latest_has_empty_ledger_and_requires_no_migration(self):
        """@covers US-045-AC6 @covers US-045-AC8"""
        name='fresh_'+uuid4().hex[:12]
        self.admin.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(name)))
        try:
            params={**self.params,'dbname':name}
            with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as connection:
                connection.execute('BEGIN');host,engine,tx=assembly(connection)
                try:self.assertIsInstance(engine.install_in_transaction(tx),Ok)
                finally:host.detach()
                connection.commit()
                self.assertEqual(connection.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(),(0,))
            tool=RuntimeMigrations(lambda:psycopg.connect(**params,autocommit=True),self.registry)
            self.assertEqual(tool.verify()['state'],'current')
            with self.assertRaisesRegex(ValueError,'Already at latest'):tool.prepare()
        finally:self.admin.execute(psycopg.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(psycopg.sql.Identifier(name)))

    def test_populated_latest_read_preservation_replay_and_old_runtime_refusal(self):
        """@covers US-045-AC6 @covers US-045-AC8"""
        before=self.state();prepared=self.tool.prepare()
        result=self.tool.apply(prepared.reference)
        self.assertEqual(result.outcome,'migrated',result)
        self.assertEqual(self.tool.status()['state'],'current')
        after=self.state()
        for name,value in before[1].items():self.assertEqual(after[1][name],value,name)
        self.assertEqual(self.tool.apply(prepared.reference).outcome,'already_applied')
        original=self.tool.receipt(prepared.reference)
        import base64
        for name in ('originalRequest','recipe','sourceInventory','targetInventory','orderedStepEvidence','preservation'):
            raw=base64.b64decode(original[name]['bytesBase64'],validate=True)
            self.assertEqual(sha256(raw).hexdigest(),original[name]['sha256'])
            self.assertTrue(json.loads(raw))
        if directory:=os.environ.get('TRUSS_MIGRATION_EVIDENCE_DIRECTORY'):
            decoded=lambda name:json.loads(base64.b64decode(original[name]['bytesBase64'],validate=True))
            evidence={'source':self.source_label,'attemptId':prepared.attempt_id,
                'sourceManifestSha256':prepared.source,'targetManifestSha256':prepared.target,
                'preservationBefore':before[1],'preservationAfter':{name:after[1][name] for name in before[1]},
                'preservationMatched':True,'originalRequest':decoded('originalRequest'),
                'orderedStepEvidence':decoded('orderedStepEvidence'),
                'originalArtifactSha256':{name:original[name]['sha256'] for name in
                    ('originalRequest','recipe','sourceInventory','targetInventory','orderedStepEvidence','preservation')},
                'captureLimits':'Complete original bodies stay in native receipt; this test archive retains preservation, ordered effects, request and all artifact digests, not full native inventories or recipe bodies.'}
            Path(directory,self.source_label+'-original-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(),(1,))
        params={**self.params,'user':'migration_person'}
        completed=False
        with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as person:
            person.execute('BEGIN');host,engine,tx=assembly(person)
            try:
                read=engine.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(self.seed['objectId']))
                self.assertIsInstance(read,Ok,read);self.assertIsInstance(read.value,ObjectFound,read)
                self.assertEqual(dict(read.value.object.values),{'A-label':'one','A-value':'exact-value'})
                for key,values in (('a-primary',('exact-value','one')),('z-alt',('one',))):
                    found=engine.lookup_key_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',key_id=key,values=values)
                    self.assertIsInstance(found,Ok,found)
                    self.assertIsInstance(found.value,ObjectFound,found)
                    self.assertEqual(found.value.object.id,int(self.seed['objectId']))
                from truss import QueryRows
                queried=engine.query_in_transaction(tx,sql='SELECT a."A-value" FROM "A" a WHERE a."A-label"=:label',
                    document_ids=('adoc',),parameters={'label':'one'})
                self.assertIsInstance(queried,Ok,queried)
                self.assertIsInstance(queried.value,QueryRows,queried)
                self.assertEqual(queried.value.rows,(('exact-value',),))
                context=engine.group_context_in_transaction(tx).value
                from truss.groups import CreateObject,AuthoredValue,RootlessOwnership,CommittedReceiptReplay,UpdateObject,StoredObjectReference
                from truss.contracts import MapValue,TextValue
                operation=CreateObject(type_definition_pin=self.seed['definitionPin'],values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='one')),AuthoredValue(name='A-value',value=TextValue(kind='string',text='exact-value'))),ownership=RootlessOwnership(),alias='seed')
                replay=engine.apply_in_transaction(tx,context.input((operation,),MapValue(entries=())),context.request('migration-seed'),documents=(CatalogDocument('adoc','r1',self.seed['document'].encode()),))
                self.assertIsInstance(replay,Ok,replay)
                self.assertIsInstance(replay.value.response,CommittedReceiptReplay,replay)
                feed=engine.read_feed_in_transaction(tx,consumer_id='migration-feed')
                self.assertIsInstance(feed,Ok,feed)
                checkpoint=bytes(self.admin.execute("SELECT checkpoint_bytes FROM truss.runtime_feed_consumer WHERE consumer_id='migration-feed'").fetchone()[0])
                self.assertEqual(feed.value.prior.content,checkpoint)
                imported=engine.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='B',object_id=int(self.seed['importedId']))
                self.assertIsInstance(imported,Ok,imported)
                self.assertEqual(dict(imported.value.object.values)['B-value'],'updated-import')
                self.assertEqual(dict(imported.value.object.retained),{'future':None})
                edge=engine.get_edge_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B',edge_id=int(self.seed['edgeId']))
                self.assertIsInstance(edge,Ok,edge)
                # Commit a new latest-runtime operation after checking exact migration preservation.
                latest=CreateObject(type_definition_pin=self.seed['definitionPin'],values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='latest-created')),AuthoredValue(name='A-value',value=TextValue(kind='string',text='latest-value'))),ownership=RootlessOwnership(),alias='latest')
                updated=UpdateObject(target=StoredObjectReference(identity=imported.value.object.identity),set=(AuthoredValue(name='B-value',value=TextValue(kind='string',text='latest-B')),),unset=(),expected_version=str(imported.value.object.version))
                written=engine.apply_in_transaction(tx,context.input((latest,updated),MapValue(entries=())),context.request('latest-write'),documents=(CatalogDocument('adoc','r1',self.seed['document'].encode()),))
                self.assertIsInstance(written,Ok,written)
                self.assertEqual(written.value.response.semantic.results[0].outcome,'created')
                self.assertEqual(written.value.response.semantic.results[1].outcome,'changed')
                completed=True
            finally:
                host.detach()
                person.commit() if completed else person.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(3,))
        # Actual predecessor host cannot stamp the new cohort, even on APIs with no digest argument.
        script="""import sys,psycopg
from truss import Ok,CatalogRuntimeConfiguration,create_reference_assembly,adopt_psycopg_host
p=__import__('json').loads(sys.argv[1]);p['user']='migration_person'
with psycopg.connect(**p,autocommit=True,options='-c statement_timeout=10000') as c:
 c.execute('BEGIN');h=adopt_psycopg_host(c);t=h.adopt_transaction().value;a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value
 r=a.group_context_in_transaction(t);assert not isinstance(r,Ok),r
 h.detach();c.rollback()
"""
        old=subprocess.run([sys.executable,'-c',script,json.dumps(self.params)],env={**os.environ,'PYTHONPATH':str(self.old)},text=True,capture_output=True,timeout=30)
        self.assertEqual(old.returncode,0,old.stderr)

    def test_source_definition_and_grant_drift_refuse_without_effects(self):
        """@covers US-045-AC6"""
        self.admin.execute('GRANT SELECT ON truss.object TO PUBLIC')
        before=self.state()
        with self.assertRaisesRegex(ValueError,'privilege|grant'):self.tool.prepare()
        self.assertEqual(self.state(),before)

    def test_busy_original_writer_preserves_source(self):
        """@covers US-045-AC7"""
        prepared=self.tool.prepare();before=self.state()
        with self.connect() as other:
            other.execute('BEGIN');other.execute('SELECT id FROM truss.object FOR UPDATE')
            result=self.tool.apply(prepared.reference)
            self.assertEqual(result.outcome,'rolled_back',result)
            other.rollback()
        self.assertEqual(self.state(),before)

    def test_changed_definition_and_unexpected_namespace_object_refuse(self):
        """@covers US-045-AC6"""
        self.admin.execute("CREATE COLLATION truss.unexpected (provider=libc,locale='C')")
        before=self.state()
        with self.assertRaisesRegex(ValueError,'definitions drifted'):self.tool.prepare()
        self.assertEqual(self.state(),before)

        self.admin.execute('DROP COLLATION truss.unexpected')
        prepared=self.tool.prepare()
        definition=self.admin.execute("SELECT pg_get_functiondef('truss.runtime_current_installation()'::regprocedure)").fetchone()[0]
        self.admin.execute(definition.replace('RETURN NEXT installation;',"PERFORM pg_catalog.nextval('truss.id_seq'::pg_catalog.regclass); RETURN NEXT installation;"))
        before=self.state()
        with self.assertRaisesRegex(ValueError,'definitions drifted'):self.tool.prepare()
        self.assertEqual(self.state(),before)
        result=self.tool.apply(prepared.reference)
        self.assertEqual(result.outcome,'rolled_back',result)
        self.assertIn('definitions drifted',result.detail)
        # nextval is not rolled back by PostgreSQL: this proves the drifted
        # installation routine was never called before source verification.
        self.assertEqual(self.state(),before)

    def test_source_configuration_drift_is_not_relabelled_as_latest(self):
        """@covers US-045-AC6"""
        command="UPDATE truss.catalog_runtime_installation SET preparation_configuration=jsonb_set(preparation_configuration,'{policy,loss}','\"report\"'::jsonb)"
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.admin.execute(command)
        # Deliberate preexisting-corruption fixture outside migration execution.
        # Restore the exact ALWAYS guard before testing source admission.
        self.admin.execute('ALTER TABLE truss.catalog_runtime_installation DISABLE TRIGGER catalog_immutable')
        try:self.admin.execute(command)
        finally:self.admin.execute('ALTER TABLE truss.catalog_runtime_installation ENABLE ALWAYS TRIGGER catalog_immutable')
        before=self.state()
        with self.assertRaisesRegex(ValueError,'profile drifted'):self.tool.prepare()
        self.assertEqual(self.state(),before)

    def test_no_receipt_does_not_prove_rollback_while_original_backend_lives(self):
        """@covers US-045-AC7: cover the durable intent → BEGIN dispatch gap."""
        prepared=self.tool.prepare();retained,request,*_=self.tool._original(prepared.reference)
        original=self.connect()
        try:
            original.execute("SET TIME ZONE 'America/New_York'")
            session=list(original.execute('SELECT pid,backend_start::text FROM pg_stat_activity WHERE pid=pg_backend_pid()').fetchone())
            self.tool._observe(prepared.reference,retained,request,'submission','unknown',session=session)
            self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'recovery_required')
        finally:original.close()
        self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'rolled_back')

    def test_active_caller_transaction_is_not_adopted_or_settled(self):
        """@covers US-045-AC7"""
        self.admin.execute('BEGIN')
        self.admin.execute('CREATE TEMP TABLE migration_caller_work(value text)')
        self.admin.execute("INSERT INTO migration_caller_work VALUES('kept')")
        try:
            with self.assertRaisesRegex(ValueError,'idle autocommit'):
                RuntimeMigrations(lambda:self.admin,self.registry).status()
            self.assertEqual(self.admin.execute('TABLE migration_caller_work').fetchall(),[('kept',)])
        finally:self.admin.rollback()

    def test_census_exhaustion_preserves_original_installation(self):
        """@covers US-045-AC7"""
        bounded=RuntimeMigrations(self.connect,self.registry,maximum_preservation_bytes=1)
        prepared=bounded.prepare();before=self.state()
        result=bounded.apply(prepared.reference)
        self.assertEqual(result.outcome,'rolled_back',result)
        self.assertIn('byte limit',result.detail)
        self.assertEqual(self.state(),before)

    def test_latest_application_refuses_source_without_automatic_migration(self):
        """@covers US-045-AC8"""
        before=self.state()
        with self.connect() as connection:
            connection.execute('BEGIN');host,engine,tx=assembly(connection)
            try:self.assertNotIsInstance(engine.status_in_transaction(tx),Ok)
            finally:host.detach();connection.rollback()
        self.assertEqual(self.state(),before)

    def test_later_native_step_failure_rolls_back_initializer(self):
        """@covers US-045-AC7"""
        prepared=self.tool.prepare();before=self.state()
        class FailingCursor(psycopg.Cursor):
            def execute(self,query,*args,**kwargs):
                if isinstance(query,str) and query.startswith('CREATE OR REPLACE FUNCTION truss.catalog_accept_with_keys'):
                    return super().execute('SELECT 1/0')
                return super().execute(query,*args,**kwargs)
        def connect():return psycopg.connect(**self.params,autocommit=True,options='-c statement_timeout=10000',cursor_factory=FailingCursor)
        result=RuntimeMigrations(connect,self.registry).apply(prepared.reference)
        self.assertEqual(result.outcome,'rolled_back',result)
        self.assertEqual(self.state(),before)
        self.assertIsNone(self.admin.execute("SELECT to_regclass('truss.runtime_migration_receipt')").fetchone()[0])

    def test_original_commit_reply_loss_recovers_after_restart(self):
        """@covers US-045-AC7"""
        from security_commit_loss_proxy import CommitResponseDropProxy
        prepared=self.tool.prepare();proxy=CommitResponseDropProxy(self.params)
        self.addCleanup(proxy.close)
        def connect():
            c=psycopg.connect(**{**self.params,'host':'127.0.0.1','port':proxy.port,'sslmode':'disable','gssencmode':'disable'},autocommit=True,options='-c statement_timeout=10000')
            proxy.armed.set();return c
        # Only the effects connection is relayed; context observation is independent.
        calls=0
        def factory():
            nonlocal calls
            calls+=1
            return connect() if calls==2 else self.connect()
        result=RuntimeMigrations(factory,self.registry).apply(prepared.reference)
        self.assertEqual(result.outcome,'commit_unknown',result)
        self.assertTrue(proxy.dropped.wait(2));self.assertEqual(proxy.errors,[])
        restarted=RuntimeMigrations(self.connect,HostRecoveryRegistry(self.registry.path))
        resolved=restarted.reconcile(prepared.reference)
        self.assertEqual(resolved.outcome,'already_applied',resolved)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(),(1,))

    def test_committed_verification_failure_is_not_rollback(self):
        """@covers US-045-AC7"""
        prepared=self.tool.prepare()
        with patch.object(self.tool,'status',side_effect=ValueError('verification unavailable')):
            result=self.tool.apply(prepared.reference)
        self.assertEqual(result.outcome,'committed_unverified',result)
        self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'already_applied')

    def test_visible_commit_does_not_fabricate_original_resource_release(self):
        """@covers US-045-AC7"""
        from threading import Event,Thread
        committed=Event();release=Event();results=[];calls=0
        class ParkedCommit(psycopg.Connection):
            def commit(self):
                super().commit();committed.set()
                if not release.wait(20):raise RuntimeError('Test cleanup barrier expired')
        def connect():
            nonlocal calls
            calls+=1
            cls=ParkedCommit if calls==2 else psycopg.Connection
            return cls.connect(**self.params,autocommit=True,options='-c statement_timeout=10000')
        prepared=self.tool.prepare();tool=RuntimeMigrations(connect,self.registry)
        thread=Thread(target=lambda:results.append(tool.apply(prepared.reference)));thread.start()
        try:
            self.assertTrue(committed.wait(15))
            observed=self.tool.reconcile(prepared.reference)
            self.assertEqual(observed.outcome,'committed_unverified',observed)
            self.assertIn('cleanup',observed.detail)
        finally:release.set();thread.join(20)
        self.assertFalse(thread.is_alive())
        self.assertTrue(results)
        self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'already_applied')

    def test_rollback_observation_waits_for_original_connection_close(self):
        """@covers US-045-AC7: a rollback acknowledgment is not resource release."""
        from threading import Event,Thread
        closing=Event();release=Event();results=[];calls=0
        class FailLater(psycopg.Cursor):
            def execute(self,query,*args,**kwargs):
                if isinstance(query,str) and query.startswith('CREATE OR REPLACE FUNCTION truss.catalog_accept_with_keys'):
                    return super().execute('SELECT 1/0')
                return super().execute(query,*args,**kwargs)
        class ParkedClose(psycopg.Connection):
            def rollback(self):
                super().rollback();self.original_rolled_back=True
            def close(self):
                if getattr(self,'original_rolled_back',False) and not self.closed:
                    closing.set()
                    if not release.wait(20):raise RuntimeError('Test cleanup barrier expired')
                super().close()
        def connect():
            nonlocal calls
            calls+=1
            if calls!=2:return self.connect()
            return ParkedClose.connect(**self.params,autocommit=True,options='-c statement_timeout=10000',cursor_factory=FailLater)
        before=self.state();prepared=self.tool.prepare();tool=RuntimeMigrations(connect,self.registry)
        thread=Thread(target=lambda:results.append(tool.apply(prepared.reference)));thread.start()
        try:
            self.assertTrue(closing.wait(15))
            context=self.tool.status()['context']
            retained=self.registry.inspect(prepared.reference,context)
            self.assertFalse(any(o['resourceRelease']=='confirmed' for o in retained['observations']))
            self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'recovery_required')
        finally:release.set();thread.join(20)
        self.assertFalse(thread.is_alive());self.assertTrue(results)
        self.assertEqual(results[0].outcome,'rolled_back',results)
        retained=self.registry.inspect(prepared.reference,self.tool.status()['context'])
        self.assertEqual(retained['observations'][-1]['resourceRelease'],'confirmed')
        self.assertEqual(self.state(),before)

    def test_committed_receipt_does_not_override_current_native_drift(self):
        """@covers US-045-AC7"""
        prepared=self.tool.prepare();result=self.tool.apply(prepared.reference)
        self.assertEqual(result.outcome,'migrated',result)
        self.admin.execute('GRANT SELECT ON truss.object TO PUBLIC')
        result=self.tool.reconcile(prepared.reference)
        self.assertEqual(result.outcome,'committed_unverified',result)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_migration_receipt').fetchone(),(1,))
        self.admin.execute('REVOKE SELECT ON truss.object FROM PUBLIC')
        self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'already_applied')

    def test_receipts_are_immutable_and_changed_request_cannot_repeat(self):
        """@covers US-045-AC7"""
        prepared=self.tool.prepare();result=self.tool.apply(prepared.reference)
        self.assertEqual(result.outcome,'migrated',result)
        for command in ['DELETE FROM truss.runtime_migration_receipt','TRUNCATE truss.runtime_migration_receipt','UPDATE truss.runtime_migration_receipt SET target_release=target_release']:
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.admin.execute(command)
        self.admin.execute("SET session_replication_role='replica'")
        try:
            with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):self.admin.execute('DELETE FROM truss.runtime_migration_receipt')
        finally:self.admin.execute("SET session_replication_role='origin'")
        self.assertEqual(self.tool.reconcile(prepared.reference).outcome,'already_applied')

    def test_logical_backup_restore_then_migrate_without_old_application_runtime(self):
        """@covers US-045-AC8: restore into a new database identity before any target writes."""
        from importlib.resources import files
        binaries=Path(str(files('pgserver')))/'pginstall/bin'
        backup=self.root/(self.database+'.dump')
        uri=psycopg.conninfo.make_conninfo(**self.params)
        subprocess.run([str(binaries/'pg_dump'),'--dbname',uri,'--format=custom','--file',str(backup)],check=True,capture_output=True,timeout=60)
        original_context=self.tool.status()['context']
        companion=self.tool.backup_metadata()
        first=self.tool.apply(self.tool.prepare().reference)
        self.assertEqual(first.outcome,'migrated',first)
        self.admin.close()
        with psycopg.connect(self.uri,autocommit=True) as c:
            c.execute(psycopg.sql.SQL('DROP DATABASE {} WITH (FORCE)').format(psycopg.sql.Identifier(self.database)))
            c.execute(psycopg.sql.SQL('CREATE DATABASE {}').format(psycopg.sql.Identifier(self.database)))
        subprocess.run([str(binaries/'pg_restore'),'--dbname',uri,'--exit-on-error',str(backup)],check=True,capture_output=True,timeout=60)
        self.admin=self.connect()
        # pg_dump omits table row-type ACLs. Restore the exact verified source
        # companion before opening any application or attempting migration.
        with self.assertRaisesRegex(ValueError,'privileges drifted'):self.tool.status()
        for statement in companion['rowTypePrivilegeRestoreSql']:self.admin.execute(statement)
        restored=self.tool.status()
        self.assertEqual(restored['state'],'upgrade_required')
        self.assertNotEqual(restored['context']['databaseIdentity'],original_context['databaseIdentity'])
        result=self.tool.apply(self.tool.prepare().reference)
        self.assertEqual(result.outcome,'migrated',result)
        self.assertEqual(self.tool.status()['state'],'current')


class CurrentTupleMigrationNativeTests(RuntimeMigrationNativeTests):
    source_label='source46'
    wheel_environment='TRUSS_MIGRATION_CURRENT_WHEEL'
    wheel_default='/private/tmp/truss-release-0.0.46-public-assets/truss_toolkit-0.0.46-py3-none-any.whl'
