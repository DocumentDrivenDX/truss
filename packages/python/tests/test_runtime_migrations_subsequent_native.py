# SPDX-License-Identifier: MIT OR Apache-2.0
"""One actual published47 upgrade, then latest-tool upgrade preserving its receipt."""
import json,os,subprocess,sys,zipfile
from pathlib import Path
import psycopg
from truss import Ok
from truss._migration_recipe import load_recipe
import test_runtime_migrations_native as fixtures

class SubsequentRuntimeMigrationTests(fixtures.RuntimeMigrationNativeTests):
    for name in tuple(n for n in dir(fixtures.RuntimeMigrationNativeTests) if n.startswith('test_')):locals()[name]=None

    def previous(self):
        manifest,_,_=load_recipe();entry=manifest['sourceWheels']['source47']
        root=Path(os.environ.get('TRUSS_MIGRATION_WHEELHOUSE','/private/tmp/truss-runtime-migration-wheelhouse'))
        wheel=root/entry['filename']
        if not wheel.exists():wheel=Path('/private/tmp/truss-public-047-assets')/entry['filename']
        from hashlib import sha256
        self.assertEqual(sha256(wheel.read_bytes()).hexdigest(),entry['sha256'])
        old=self.root/'published47';zipfile.ZipFile(wheel).extractall(old)
        program='''import sys,psycopg,json
from truss.migrations import RuntimeMigrations
from truss.recovery_registry import HostRecoveryRegistry
params=json.loads(sys.argv[1]);tool=RuntimeMigrations(lambda:psycopg.connect(**params,autocommit=True),HostRecoveryRegistry(sys.argv[2]));request=tool.prepare();result=tool.apply(request.reference);assert result.outcome=='migrated',result;print(request.reference)
'''
        produced=subprocess.run([sys.executable,'-c',program,json.dumps(self.params),str(self.root/'previous.sqlite')],env={**os.environ,'PYTHONPATH':str(old)},capture_output=True,text=True,timeout=120)
        self.assertEqual(produced.returncode,0,produced.stdout+produced.stderr)
        self.previous_reference=produced.stdout.strip()
        self.assertEqual(self.tool.status()['manifestSha256'],entry['runtimeManifestSha256'])
        return old

    def ledger(self):
        return dict(self.admin.execute("SELECT attempt_id::text,encode(sha256(convert_to(to_jsonb(r)::text,'UTF8')),'hex') FROM truss.runtime_migration_receipt r ORDER BY attempt_id").fetchall())

    def test_previously_upgraded47_keeps_original_receipt_and_publishes_one_new_head(self):
        old=self.previous();before=self.ledger();self.assertEqual(len(before),1);request=self.tool.prepare()
        self.assertEqual(self.tool.apply(request.reference).outcome,'migrated');after=self.ledger();self.assertEqual(len(after),2)
        self.assertEqual({key:after[key] for key in before},before)
        self.assertEqual(self.tool.status()['state'],'current')
        from runtime_migration_fixture import assembly
        with psycopg.connect(**{**self.params,'user':'migration_person'},autocommit=True,options='-c statement_timeout=10000') as person:
            person.execute('BEGIN');host,engine,tx=assembly(person)
            try:
                status=engine.person_runtime_status_in_transaction(tx);self.assertIsInstance(status,Ok,status);self.assertEqual(status.value.installation,'compatible')
            finally:host.detach();person.rollback()
        original=json.loads(__import__('base64').b64decode(self.tool.receipt(request.reference)['recipe']['bytesBase64']))
        from truss._migration_recipe import plan_route
        manifest,_,_=load_recipe()
        self.assertEqual(len(original),len(plan_route(manifest,manifest['sourceWheels']['source47']['runtimeManifestSha256'])))
        from truss.migrations import RuntimeMigrations
        from truss.recovery_registry import HostRecoveryRegistry
        historical=RuntimeMigrations(self.connect,HostRecoveryRegistry(self.root/'previous.sqlite')).reconcile(self.previous_reference)
        self.assertEqual(historical.outcome,'already_applied',historical)
        self.assertEqual(self.ledger(),after,'Historical reconciliation executes no older target')

    def test_previous_receipt_survives_lost_latest_commit_response_and_reconciliation(self):
        self.previous();before=self.ledger()
        # Reuse actual socket/COMMIT-response loss producer, now with a retained
        # previous publication rather than an empty ledger.
        from security_commit_loss_proxy import CommitResponseDropProxy
        from truss.migrations import RuntimeMigrations
        from truss.recovery_registry import HostRecoveryRegistry
        request=self.tool.prepare();proxy=CommitResponseDropProxy(self.params,maximum_backend_frame_bytes=16777216);self.addCleanup(proxy.close);calls=0
        def factory():
            nonlocal calls
            calls+=1
            if calls!=2:return self.connect()
            c=psycopg.connect(**{**self.params,'host':'127.0.0.1','port':proxy.port,'sslmode':'disable','gssencmode':'disable'},autocommit=True,options='-c statement_timeout=10000');proxy.armed.set();return c
        result=RuntimeMigrations(factory,self.registry).apply(request.reference)
        self.assertEqual(result.outcome,'commit_unknown',repr(result))
        self.assertTrue(proxy.dropped.wait(2));self.assertEqual(proxy.errors,[])
        resolved=RuntimeMigrations(self.connect,HostRecoveryRegistry(self.registry.path)).reconcile(request.reference)
        self.assertEqual(resolved.outcome,'already_applied');after=self.ledger();self.assertEqual(len(after),2);self.assertEqual({key:after[key] for key in before},before)

    def test_legacy_relationship_only_incomplete_owner_header_survives_without_fabricated_backfill(self):
        old=self.previous()
        program='''import sys,json,psycopg
from truss import Ok,CatalogDocument,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly
from truss.batched_import import EdgeImportDraft
from truss.groups import NullOrderKey
from truss.contracts import MapValue
params=json.loads(sys.argv[1]);params['user']='migration_person';seed=json.loads(sys.argv[2])
with psycopg.connect(**params,autocommit=True,options='-c statement_timeout=10000') as c:
 c.execute('BEGIN');h=adopt_psycopg_host(c);t=h.adopt_transaction().value;a=create_reference_assembly(CatalogRuntimeConfiguration(),h).value
 left=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='A',object_id=int(seed['objectId'])).value.object.identity
 right=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id='B',object_id=int(seed['importedId'])).value.object.identity
 built=a.build_import_records_in_transaction(t,(EdgeImportDraft(document_id='adoc',module_id='m',relationship_id='A-B',source_endpoint=left,target_endpoint=right,values=(),order_key=NullOrderKey()),));assert isinstance(built,Ok),built
 selected=built.value.context.input(built.value.records,load_id='legacy-edge-only',asserted_origin=MapValue(entries=()),chunk_size=128)
 result=a.import_batched_in_transaction(t,selected,documents=(CatalogDocument('adoc','r1',seed['document'].encode()),));assert result.result.report.counts.skipped=='1',result
 h.detach();c.commit();print(result.result.report.attempt_id)
'''
        produced=subprocess.run([sys.executable,'-c',program,json.dumps(self.params),json.dumps(self.seed)],env={**os.environ,'PYTHONPATH':str(old)},capture_output=True,text=True,timeout=120)
        self.assertEqual(produced.returncode,0,produced.stdout+produced.stderr)
        header=self.admin.execute("SELECT owner_inventory_complete,encode(sha256(convert_to(to_jsonb(r)::text,'UTF8')),'hex') FROM truss.runtime_import_load_chunk r WHERE load_id='legacy-edge-only'").fetchone()
        self.assertEqual(header[0],False,'Real public47 producer retains an incomplete header for this path')
        request=self.tool.prepare();self.assertEqual(self.tool.apply(request.reference).outcome,'migrated')
        self.assertEqual(self.admin.execute("SELECT owner_inventory_complete,encode(sha256(convert_to(to_jsonb(r)::text,'UTF8')),'hex') FROM truss.runtime_import_load_chunk r WHERE load_id='legacy-edge-only'").fetchone(),header)
        from runtime_migration_fixture import assembly
        from truss import ModuleAuditGrant,LoadAuditUnavailable,LoadAuditListingEnd,LoadAuditCursor
        self.admin.execute('BEGIN');host,engine,tx=assembly(self.admin)
        try:self.assertIsInstance(engine.grant_module_audit_access_in_transaction(tx,ModuleAuditGrant(document_id='adoc',module_id='m',auditor_role='migration_audit')),Ok)
        finally:host.detach();self.admin.commit()
        with psycopg.connect(**{**self.params,'user':'migration_person'},autocommit=True,options='-c statement_timeout=10000') as person:
            person.execute('BEGIN');host,engine,tx=assembly(person)
            try:
                observed=engine.page_import_load_audit_in_transaction(tx,filters={'documentId':'adoc','moduleId':'m','loadId':'legacy-edge-only'})
                self.assertIsInstance(observed,Ok,observed);self.assertIsInstance(observed.value,LoadAuditListingEnd)
                direct=engine.read_import_load_chunk_in_transaction(tx,cursor=LoadAuditCursor(invocation_id=produced.stdout.strip(),chunk_index='0'))
                self.assertIsInstance(direct,Ok,direct);self.assertIsInstance(direct.value,LoadAuditUnavailable)
            finally:host.detach();person.rollback()
