"""Public create group → caller commit → direct read → original receipt replay."""
import base64
from dataclasses import replace
import hashlib
import json
import os
import psycopg
from truss import (Ok,Error,ModuleAccessGrant,CatalogRuntimeConfiguration,create_reference_assembly,
    adopt_psycopg_host,ObjectFound)
from truss.contracts import MapValue,MapEntry,TextValue
from truss.groups import (CreateObject,RootlessOwnership,AuthoredValue,GroupSuccess,GroupFailed,GroupUnavailable,
    AppliedPending,SameTransactionReplay,CommittedReceiptReplay,RequestNone)
import test_catalog_runtime_native as catalog_tests

class PublicCreateGroupTests(catalog_tests.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(catalog_tests.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name]=None
    def ready(self,mutate_source=None,*,document_ids=('zdoc','adoc')):
        self.install()
        connection,host,assembly,tx=self.consumer()
        from truss import CatalogDocument
        from test_catalog_relational_support import relational_document
        documents=[]
        for identity in document_ids:
            source=relational_document();source['id']=identity
            if mutate_source is not None:mutate_source(source)
            documents.append(CatalogDocument(identity,'r1',json.dumps(source,indent=2,ensure_ascii=False).encode()))
        prepared=assembly.prepare_catalog(tuple(documents),source_version=json.loads(documents[0].content)['umf'],bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.documents=tuple(d.document for d in prepared.documents)
        registered=assembly.accept_in_transaction(tx,prepared,request_key='create-model')
        self.assertIsInstance(registered,Ok,repr(registered)+" "+str(host._custody.last_attempt.error))
        view=assembly.catalog_view_in_transaction(tx,assembly.catalog_view_request()).value.view
        self.types={(d.reference.owner.document_id,d.reference.authored_identity):d.reference
                    for d in view.definitions if d.reference.kind=='type'}
        host.detach();connection.commit()
        for role in ('group_reader','group_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN');self.host=adopt_psycopg_host(self.admin);self.tx=self.host.adopt_transaction().value
        self.assembly=create_reference_assembly(CatalogRuntimeConfiguration(),self.host).value
        configured=self.assembly.configure_module_access_in_transaction(self.tx,(ModuleAccessGrant('adoc','m','group_reader','group_writer'),))
        self.assertIsInstance(configured,Ok);self.host.detach();self.admin.commit()
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        return self.consumer()
    def create(self,label='one',value='value',alias='item',document='adoc',record='A'):
        return CreateObject(type_definition_pin=self.types[(document,record)].definition_pin,
            values=(AuthoredValue(name=record+'-label',value=TextValue(kind='string',text=label)),
                    AuthoredValue(name=record+'-value',value=TextValue(kind='string',text=value))),ownership=RootlessOwnership(),alias=alias)
    def input(self,assembly,tx,operations=None,action='create'):
        context=assembly.group_context_in_transaction(tx)
        self.assertIsInstance(context,Ok)
        input=context.value.input((self.create(),) if operations is None else operations,
            MapValue(entries=(MapEntry(key='x-action',value=TextValue(kind='string',text=action)),)))
        return input,context.value.request('stable-request')
    def apply(self,assembly,tx,input,request):
        result=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        if isinstance(result,Error):self.fail(repr(result.error)+' '+str(assembly._host._custody.last_attempt.error))
        return result.value
    def test_create_commit_read_and_original_durable_replay(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        applied=self.apply(assembly,tx,input,request)
        self.assertIsInstance(applied,GroupSuccess);self.assertIsInstance(applied.response,AppliedPending)
        created=applied.response.semantic.results[0]
        self.assertEqual(created.identity.definition_pin,input.operations[0].type_definition_pin)
        self.assertEqual(applied.response.semantic.aliases[0].identity,created.identity)
        self.assertEqual(created.alias,'item');self.assertEqual(created.version,'1')
        self.assertIsInstance(self.apply(assembly,tx,input,request).response,SameTransactionReplay)
        row_count=self.admin.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(row_count,0)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),(1,))
        connection,host,assembly,tx=self.consumer()
        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(created.identity.id))
        self.assertIsInstance(read.value,ObjectFound);self.assertEqual(dict(read.value.object.values),{'A-label':'one','A-value':'value'})
        before=self.admin.execute('SELECT last_value FROM truss.id_seq').fetchone()
        replay=self.apply(assembly,tx,input,request)
        self.assertIsInstance(replay.response,CommittedReceiptReplay)
        self.assertEqual(replay.response.semantic,applied.response.semantic)
        self.assertEqual(self.admin.execute('SELECT last_value FROM truss.id_seq').fetchone(),before)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(),(1,))
        observation=json.loads(base64.b64decode(replay.response.replay.evidence.bytes_base64))
        self.assertNotEqual(observation['observingXid'],observation['originalWriterXid'])
        self.assertEqual(observation['basis'],'committed_receipt')
    def test_group_failure_and_rollback_preserve_caller_work(self):
        connection,host,assembly,tx=self.ready()
        connection.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        input,request=self.input(assembly,tx,(self.create('first',alias='first'),self.create('first',alias='second')))
        failed=self.apply(assembly,tx,input,request);self.assertIsInstance(failed,GroupFailed)
        self.assertEqual(connection.execute('TABLE prior').fetchall(),[('kept',)])
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
        input,request=self.input(assembly,tx)
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.request_receipt').fetchone(),(0,))
    def test_changed_request_origin_and_none_has_no_cache(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        changed,_=self.input(assembly,tx,action='different')
        failed=self.apply(assembly,tx,changed,request);self.assertIsInstance(failed,GroupFailed)
        self.assertEqual(failed.failure.code,'request_conflict')
        none,_=self.input(assembly,tx,(self.create('second',alias='second'),))
        self.assertIsInstance(self.apply(assembly,tx,none,RequestNone()),GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(2,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.request_receipt').fetchone(),(1,))

    def test_genuine_type_reference_and_profile_definitions(self):
        connection,host,assembly,tx=self.ready()
        reference=assembly.get_type_reference_in_transaction(tx,document_id='adoc',module_id='m',record_id='A')
        self.assertEqual(reference.value,self.types[('adoc','A')])
        self.assertIsNone(assembly.get_type_reference_in_transaction(tx,document_id='zdoc',module_id='m',record_id='A').value)
        from importlib.resources import files
        definitions=json.loads(files('truss').joinpath('_catalog_runtime/group-profiles.json').read_bytes())['profiles']
        selected=self.admin.execute('SELECT truss.runtime_group_profiles()').fetchone()[0]
        for definition in definitions:
            self.assertEqual(hashlib.sha256(definition['definition'].encode()).hexdigest(),definition['pin']['sha256'])
        declared={definition['name']:definition['pin'] for definition in definitions}
        self.assertEqual(selected,{name:declared[name] for name in selected})
        self.assertEqual(set(selected),{'creationTransitionProfile','mutationProfile','valueProfile','canonicalizationProfile',
                                        'requestFingerprintProfile','adapterProfile','positionProfile','policyProfile'})
    def test_asymmetric_relationship_minimum_is_checked_on_the_right_endpoint(self):
        def require_target(source):source['modules'][0]['relationships'][0]['targetMultiplicity']['min']=1
        connection,host,assembly,tx=self.ready(require_target)
        input,request=self.input(assembly,tx)
        failed=self.apply(assembly,tx,input,request)
        self.assertIsInstance(failed,GroupFailed)
        self.assertEqual(json.loads(base64.b64decode(failed.failure.inner_error.bytes_base64))['nativeState'],'P1005')
        target,_=self.input(assembly,tx,(self.create(record='B'),))
        self.assertIsInstance(self.apply(assembly,tx,target,RequestNone()),GroupSuccess)
        host.detach();connection.commit()
    def test_current_writer_revocation_refuses_replay(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.commit()
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE');self.admin.execute('REVOKE group_writer FROM consumer')
        connection,host,assembly,tx=self.consumer()
        refused=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupFailed)
        self.assertEqual(refused.value.failure.code,'unauthorized_person')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
    def test_raw_facade_rejects_missing_values_and_duplicate_json(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        from truss._group_runtime import _bytes,_wire
        from truss.catalog_runtime import _release
        manifest,digest,_=_release();documents=_bytes([{'documentId':d.document_id,'sourceText':d.content.decode()} for d in self.documents])
        valid=_wire(input)
        for mutation in ('missing-value','missing-text','origin-value','duplicate-json'):
            candidate=json.loads(json.dumps(valid))
            if mutation=='missing-value':candidate['operations'][0]['values'].append({'name':'note'})
            elif mutation=='missing-text':candidate['operations'][0]['values'].append({'name':'note','value':{'kind':'string'}})
            elif mutation=='origin-value':candidate['assertedOrigin']['entries'].append({'key':'x-missing'})
            raw=_bytes(candidate)
            if mutation=='duplicate-json':raw=raw.replace(b'"interfaceVersion":"truss-group-input/0.1.0"',b'"interfaceVersion":"wrong","interfaceVersion":"truss-group-input/0.1.0"')
            connection.execute('SAVEPOINT malformed')
            try:
                returned=connection.execute('SELECT truss.apply_group(%s,%s,%s,%s,%s)',
                    (raw,documents,b'{"state":"none"}',manifest['releaseId'],digest)).fetchone()[0]
                self.assertEqual(json.loads(bytes(returned))['outcome'],'failed')
            finally:connection.execute('ROLLBACK TO SAVEPOINT malformed');connection.execute('RELEASE SAVEPOINT malformed')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
    def test_native_late_journal_and_receipt_failures_are_atomic(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        connection.execute("CREATE TEMP TABLE prior(value text);INSERT INTO prior VALUES('kept')")
        self.admin.execute("CREATE FUNCTION public.suppress_create_fact() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.suppress_create_fact()')
        for table in ('journal','request_receipt'):
            self.admin.execute(psycopg.sql.SQL('CREATE TRIGGER suppress_fact BEFORE INSERT ON truss.{} FOR EACH ROW EXECUTE FUNCTION public.suppress_create_fact()').format(psycopg.sql.Identifier(table)))
            failed=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
            self.assertIsInstance(failed,Error);self.assertEqual(failed.error.sql_state,'55000')
            self.assertEqual(host._custody.last_attempt.phase,'contained')
            self.assertEqual(connection.execute('TABLE prior').fetchall(),[('kept',)])
            for name in ('object','journal','object_key_bucket','object_key_reservation_bucket','request_receipt','runtime_create_group'):
                self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(name))).fetchone(),(0,))
            self.admin.execute(psycopg.sql.SQL('DROP TRIGGER suppress_fact ON truss.{}').format(psycopg.sql.Identifier(table)))
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
    def test_rewritten_group_and_extra_entity_event_refuse(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        self.admin.execute("CREATE FUNCTION public.rewrite_create_group() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.after_object:=jsonb_set(NEW.after_object,'{ver}','2'::jsonb);RETURN NEW;END $$")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.rewrite_create_group()')
        self.admin.execute('CREATE TRIGGER rewrite_group BEFORE INSERT ON truss.runtime_object_transition FOR EACH ROW EXECUTE FUNCTION public.rewrite_create_group()')
        failed=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(failed,Error);self.assertEqual(failed.error.sql_state,'55000')
        self.assertEqual(host._custody.last_attempt.phase,'contained')
        self.admin.execute('DROP TRIGGER rewrite_group ON truss.runtime_object_transition')
        self.admin.execute("""CREATE FUNCTION public.duplicate_create_event() RETURNS trigger LANGUAGE plpgsql AS $$
         BEGIN IF pg_trigger_depth()=1 THEN INSERT INTO truss.journal SELECT (jsonb_populate_record(NULL::truss.journal,to_jsonb(NEW)||jsonb_build_object('seq',nextval('truss.journal_seq'),'ver',2))).*;END IF;RETURN NULL;END $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.duplicate_create_event()')
        self.admin.execute('CREATE TRIGGER duplicate_event AFTER INSERT ON truss.journal FOR EACH ROW EXECUTE FUNCTION public.duplicate_create_event()')
        pending=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(pending,Ok);self.assertIsInstance(pending.value,GroupSuccess)
        host.detach()
        with self.assertRaises(psycopg.errors.ObjectNotInPrerequisiteState):
            connection.commit()
        connection.rollback()
        for table in ('object','journal','request_receipt','runtime_object_attempt','runtime_object_transition'):
            self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone(),(0,))
        self.admin.execute('DROP TRIGGER duplicate_event ON truss.journal')
    def test_deferred_corruption_aborts_outer_commit(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        result=self.apply(assembly,tx,input,request);self.assertIsInstance(result,GroupSuccess)
        identity=int(result.response.semantic.results[0].identity.id)
        # Inject corruption without granting raw table access: raw privileges
        # independently refuse the person before the final object check runs.
        self.admin.execute("""CREATE FUNCTION public.corrupt_created_object(selected_id bigint) RETURNS void
         LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
          BEGIN UPDATE truss.object SET ver=2 WHERE id=selected_id; END
         $$""")
        self.addCleanup(self.admin.execute,'DROP FUNCTION public.corrupt_created_object(bigint)')
        connection.execute('SELECT public.corrupt_created_object(%s)',(identity,))
        host.detach()
        with self.assertRaisesRegex(psycopg.errors.ObjectNotInPrerequisiteState,'exact final object/key state required'):
            connection.commit()
        connection.rollback()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))

    def test_noinherit_set_role_raw_privilege_is_refused_after_reset(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.commit()
        self.admin.execute('CREATE ROLE dangerous_reader NOLOGIN')
        self.addCleanup(self.admin.execute,'DROP ROLE dangerous_reader')
        self.admin.execute('GRANT USAGE ON SCHEMA truss TO dangerous_reader')
        self.admin.execute('GRANT SELECT ON truss.object TO dangerous_reader')
        self.admin.execute('GRANT dangerous_reader TO consumer WITH INHERIT FALSE,SET TRUE')
        connection,host,assembly,tx=self.consumer()
        self.assertEqual(connection.execute("SELECT has_table_privilege(current_user,'truss.object','SELECT')").fetchone(),(False,))
        connection.execute('SET ROLE dangerous_reader')
        self.assertEqual(connection.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
        connection.execute('RESET ROLE')
        refused=assembly.group_context_in_transaction(tx)
        self.assertIsInstance(refused,Error);self.assertEqual(refused.error.sql_state,'42501')
        self.admin.execute('REVOKE dangerous_reader FROM consumer')
        self.assertIsInstance(assembly.group_context_in_transaction(tx),Ok)
    def test_selected_group_provider_is_callable_and_disposal_closes_it(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        provider=assembly.groups(assembly.group_selection,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertEqual(provider.status,'ok')
        self.assertEqual(provider.capability.selection,assembly.group_selection)
        result=provider.capability.apply_in_transaction(tx,input,request)
        self.assertIsInstance(result.value,GroupSuccess)
        incompatible=replace(assembly.group_selection,capability_profile=replace(assembly.group_selection.capability_profile,sha256='0'*64))
        self.assertEqual(assembly.groups(incompatible).status,'unavailable')
        assembly.dispose()
        self.assertEqual(assembly.groups(assembly.group_selection).reason,'disposed')
        self.assertIsInstance(provider.capability.apply_in_transaction(tx,input,request),Error)
        host.detach();connection.commit()

    def test_native_retry_states_reach_host_without_internal_retry(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        for state in ('40001','40P01'):
            self.admin.execute(psycopg.sql.SQL("CREATE FUNCTION public.force_retry() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'retry control' USING ERRCODE={}; END $$").format(psycopg.sql.Literal(state)))
            self.admin.execute('CREATE TRIGGER force_retry BEFORE INSERT ON truss.object FOR EACH ROW EXECUTE FUNCTION public.force_retry()')
            result=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
            self.assertIsInstance(result,Error);self.assertEqual(result.error.code,'retry');self.assertEqual(result.error.sql_state,state)
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(0,))
            self.admin.execute('DROP TRIGGER force_retry ON truss.object');self.admin.execute('DROP FUNCTION public.force_retry()')
            host.detach();connection.rollback();connection,host,assembly,tx=self.consumer();input,request=self.input(assembly,tx)

    def test_reader_and_asserted_actor_cannot_authorize_first_create(self):
        connection,host,assembly,tx=self.ready();input,request=self.input(assembly,tx)
        input=replace(input,asserted_origin=MapValue(entries=(MapEntry(key='x-actor',value=TextValue(kind='string',text='group_writer')),)))
        connection.execute("CREATE TEMP TABLE prior_work(value text);INSERT INTO prior_work VALUES('kept')")
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE');self.admin.execute('REVOKE group_writer FROM consumer')
        refused=assembly.apply_in_transaction(tx,input,request,documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,GroupFailed)
        self.assertEqual(refused.value.failure.code,'unauthorized_person')
        self.assertEqual(connection.execute('TABLE prior_work').fetchall(),[('kept',)])
        host.detach();connection.commit()
        for table in ('object','runtime_object_attempt','runtime_object_transition','request_receipt','journal'):
            self.assertEqual(self.admin.execute(psycopg.sql.SQL('SELECT count(*) FROM truss.{}').format(psycopg.sql.Identifier(table))).fetchone(),(0,))
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        connection,host,assembly,tx=self.consumer()
        self.assertIsInstance(self.apply(assembly,tx,input,request),GroupSuccess)
        host.detach();connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(1,))
        self.assertEqual(self.admin.execute("SELECT convert_from(decode(t.journal->0->'new_value'->>'bytesBase64','base64'),'UTF8')::jsonb#>>'{origin,databaseRole}',a.actor_oid=(SELECT oid FROM pg_roles WHERE rolname='consumer') FROM truss.runtime_object_transition t JOIN truss.runtime_object_attempt a ON a.id=t.attempt_id WHERE t.before_object IS NULL").fetchall(),[('consumer',True)])
