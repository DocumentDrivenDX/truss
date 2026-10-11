"""Native single-use pending revision registration; every fixture rolls back."""
import hashlib
import json
import unittest
import test_catalog_report_write_candidate_native as report_fixture
from test_catalog_staging import ROOT
from truss._acceptance_json import decode_acceptance_json


class RevisionRegistrationNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.addClassCleanup(report_fixture.ReportWriteCandidateNativeTests.tearDownClass)
        report_fixture.ReportWriteCandidateNativeTests.setUpClass()
        cls.Connection=report_fixture.ReportWriteCandidateNativeTests.Connection
        cls.kwargs=report_fixture.ReportWriteCandidateNativeTests.kwargs
        c=cls.Connection(**cls.kwargs)
        try:c.run((ROOT/'packages/postgresql/native/catalog-report/revision-registration-candidate.sql').read_text())
        finally:c.close()
    @classmethod
    def tearDownClass(cls):report_fixture.ReportWriteCandidateNativeTests.tearDownClass()
    setUp=report_fixture.ReportWriteCandidateNativeTests.setUp
    tearDown=report_fixture.ReportWriteCandidateNativeTests.tearDown
    stage=report_fixture.ReportWriteCandidateNativeTests.stage
    admit=report_fixture.ReportWriteCandidateNativeTests.admit
    invoke=report_fixture.ReportWriteCandidateNativeTests.invoke

    def archive(self):
        report_fixture.ReportWriteCandidateNativeTests.archive(self)
        path='packages/python/src/truss/_profiles/catalog-revision-registration-candidate.json'
        original=(ROOT/path).read_bytes();profile=json.loads(original)
        artifacts=[(path,getattr(self,'recipe_bytes',original))]
        artifacts.extend((ref['path'],(ROOT/ref['path']).read_bytes()) for ref in profile['sources'].values())
        if getattr(self,'omit_recipe',False):artifacts=artifacts[1:]
        if getattr(self,'duplicate_recipe',False):artifacts.append((path,original))
        for identity,raw in artifacts:
            self.connection.run("""INSERT INTO truss.installation_archive(installation_id,artifact_role,
                artifact_identity,artifact_bytes,artifact_identity_sha256) VALUES('guard-fixture','input',
                :identity,:raw,sha256(convert_to(:identity,'UTF8')))""",identity=identity,raw=raw)

    def register(self,generation=None):
        return self.connection.run("""SELECT * FROM truss.runtime_write_catalog_report_and_register_revision_candidate(
            :writer,:ordinal,:generation,:identity,:registration,:lifecycle,:indexes)""",
            writer=self.writer,ordinal=self.ordinal,generation=self.generation if generation is None else generation,
            identity=self.identity,registration=self.registration_bytes,
            lifecycle=(ROOT/'packages/python/src/truss/_profiles/fresh-catalog-lifecycle.json').read_bytes(),
            indexes=(ROOT/'packages/python/src/truss/_profiles/absent-binding-index-declarations.json').read_bytes())[0]

    def assert_rolled_back(self):
        for name in ('catalog_acceptance_report','feed_tx','feed_member','feed_prerequisite','feed_configuration_prerequisite'):
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.'+name),[[0]])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        self.assertEqual(self.connection.run('SELECT effect_generation::text FROM truss.row_home_operation'),[[self.generation]])

    def trigger(self,table,timing,event,body):
        self.connection.run("CREATE FUNCTION truss.fixture_registration_drift() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN "+body+" END $$; CREATE TRIGGER fixture_registration_drift "+timing+' '+event+' ON truss.'+table+' FOR EACH ROW EXECUTE FUNCTION truss.fixture_registration_drift()')

    def test_pending_revision_registration_complete_original_rows(self):
        self.stage();row=self.register()
        self.assertEqual(row[:3],[self.writer,self.ordinal,str(int(self.generation)+1)])
        self.assertEqual(row[7:],['administrative_single_original_operation_fresh_catalog_rollback_only',False,False])
        self.assertEqual(self.connection.run("SELECT encode(record_send(t),'hex') FROM truss.feed_tx t"),[[row[5]]])
        self.assertEqual(self.connection.run("SELECT encode(record_send(m),'hex') FROM truss.feed_member m"),[[row[6]]])
        self.assertEqual(self.connection.run('SELECT registration_counter,prerequisite_registration_counter,configuration_registration_counter,membership_generation,finalized_generation,manifest_bytes,manifest_sha256 FROM truss.feed_tx'),[[1,0,0,1,None,None,None]])
        member=self.connection.run('SELECT original_fact_key_bytes,original_payload_bytes,original_payload_sha256,original_payload_profile_bytes,original_owner_context_bytes,delivery_ordinal FROM truss.feed_member')[0]
        self.assertEqual(decode_acceptance_json(member[0]),{'kind':'revision','revision':'1'})
        self.assertEqual(member[1],bytes.fromhex(row[4]));self.assertEqual(member[2],hashlib.sha256(member[1]).digest())
        self.assertEqual(member[3],(ROOT/'packages/python/src/truss/_profiles/catalog-revision-composition-candidate.json').read_bytes())
        # Independent private-envelope oracle; public acceptance decoder limits stay intact.
        owner=json.loads(member[4]);self.assertEqual(''.join(owner['originalContextHexChunks']),self.context.hex())
        self.assertEqual(self.connection.run("SELECT encode(record_send(r),'hex') FROM truss.schema_rev r WHERE rev=1"),[[''.join(owner['originalRevisionRecordHexChunks'])]])
        self.assertEqual(self.connection.run("SELECT encode(record_send(d),'hex') FROM truss.schema_doc d WHERE rev=1 ORDER BY ord"),[[''.join(v)] for v in owner['originalDocumentRecordHexChunks']])
        self.assertEqual(self.connection.run("SELECT encode(record_send(o),'hex') FROM truss.row_home_operation o"),[[''.join(owner['originalOperationRecordHexChunks'])]])
        self.assertEqual(self.connection.run("SELECT encode(record_send(c),'hex') FROM truss.operation_configuration c"),[[''.join(owner['originalConfigurationRecordHexChunks'])]])
        self.assertIsNone(member[5]);self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'),[[0]])
        from pg8000.exceptions import DatabaseError
        with self.assertRaises(DatabaseError) as caught:self.connection.run('COMMIT')
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'complete runtime finalizer is not installed')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.feed_member'),[[0]])

    def test_native_write_clock_and_single_use_refusal(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run("""CREATE FUNCTION truss.fixture_future_acceptance() RETURNS trigger LANGUAGE plpgsql AS $$
          BEGIN NEW.accepted_at:='2099-01-01 00:00:00+00'::timestamptz; RETURN NEW; END $$;
          CREATE TRIGGER fixture_future_acceptance BEFORE INSERT ON truss.schema_rev
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_future_acceptance()""")
        self.stage();before=self.connection.run('SELECT clock_timestamp()')[0][0];row=self.register()
        after=self.connection.run('SELECT clock_timestamp()')[0][0]
        timestamp,clock_bytes=self.connection.run('SELECT original_write_at,original_fact_clock_bytes FROM truss.feed_member')[0]
        self.assertLessEqual(before,timestamp);self.assertLessEqual(timestamp,after)
        self.assertLess(timestamp,self.connection.run('SELECT accepted_at FROM truss.schema_rev WHERE rev=1')[0][0])
        envelope=decode_acceptance_json(clock_bytes)
        self.assertEqual(envelope['originalWriteAt'],self.connection.run("SELECT to_char(original_write_at AT TIME ZONE 'UTC','YYYY-MM-DD\"T\"HH24:MI:SS.US\"Z\"') FROM truss.feed_member")[0][0])
        self.connection.run('SAVEPOINT repeat')
        with self.assertRaises(DatabaseError):self.register(generation=row[2])
        self.connection.run('ROLLBACK TO repeat');self.connection.run('RELEASE repeat')
        self.assertEqual(self.connection.run("SELECT encode(record_send(m),'hex') FROM truss.feed_member m"),[[row[6]]])

    def test_suppressed_writes_refuse_and_preserve_host_state(self):
        from pg8000.exceptions import DatabaseError
        self.stage();self.connection.run("CREATE TEMP TABLE registration_host_work(value text); INSERT INTO registration_host_work VALUES('keep')")
        for table,event in [('feed_tx','INSERT'),('feed_tx','UPDATE'),('feed_member','INSERT')]:
            self.connection.run('SAVEPOINT suppression');self.trigger(table,'BEFORE',event,'RETURN NULL;')
            with self.subTest(table=table,event=event),self.assertRaises(DatabaseError) as caught:self.register()
            self.assertEqual(caught.exception.args[0]['C'],'P0002')
            self.connection.run('ROLLBACK TO suppression');self.connection.run('RELEASE suppression')
            self.assert_rolled_back();self.assertEqual(self.connection.run('SELECT value FROM registration_host_work'),[['keep']])

    def test_rewritten_writes_refuse(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        for table,event,body in [('feed_tx','INSERT',"NEW.original_context_bytes:=decode('01','hex'); RETURN NEW;"),
                                 ('feed_tx','UPDATE','NEW.registration_counter:=2; RETURN NEW;'),
                                 ('feed_member','INSERT',"NEW.original_write_at:='2000-01-01+00'::timestamptz; RETURN NEW;")]:
            self.connection.run('SAVEPOINT rewrite');self.trigger(table,'BEFORE',event,body)
            with self.subTest(table=table,event=event),self.assertRaises(DatabaseError) as caught:self.register()
            self.assertEqual(caught.exception.args[0]['C'],'55000')
            self.connection.run('ROLLBACK TO rewrite');self.connection.run('RELEASE rewrite');self.assert_rolled_back()

    def test_extra_member_refuses_final_delta(self):
        from pg8000.exceptions import DatabaseError
        self.stage();self.connection.run('SAVEPOINT extra')
        self.trigger('feed_member','AFTER','INSERT',"IF NEW.registration_address=1 THEN NEW.registration_address:=2; INSERT INTO truss.feed_member SELECT NEW.*; END IF; RETURN NEW;")
        with self.assertRaises(DatabaseError) as caught:self.register()
        self.assertEqual(caught.exception.args[0]['M'],'complete original pending revision registration delta required')
        self.connection.run('ROLLBACK TO extra');self.connection.run('RELEASE extra');self.assert_rolled_back()

    def test_late_catalog_or_report_change_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.stage()
        for body in ('UPDATE truss.type_def SET retired_rev=1; RETURN NEW;','DELETE FROM truss.catalog_acceptance_report; RETURN NEW;'):
            self.connection.run('SAVEPOINT catalog_drift');self.trigger('feed_member','AFTER','INSERT',body)
            with self.subTest(body=body),self.assertRaises(DatabaseError):self.register()
            self.connection.run('ROLLBACK TO catalog_drift');self.connection.run('RELEASE catalog_drift');self.assert_rolled_back()

    def test_registration_profile_missing_changed_and_duplicate_refuse(self):
        from pg8000.exceptions import DatabaseError
        for mode in ('missing','changed','duplicate'):
            self.connection.run('SAVEPOINT recipe_setup')
            self.omit_recipe=mode=='missing';self.duplicate_recipe=mode=='duplicate'
            self.recipe_bytes=b'{}' if mode=='changed' else (ROOT/'packages/python/src/truss/_profiles/catalog-revision-registration-candidate.json').read_bytes()
            self.stage();self.connection.run('SAVEPOINT recipe_call')
            with self.subTest(mode=mode),self.assertRaises(DatabaseError):self.register()
            self.connection.run('ROLLBACK TO recipe_call');self.connection.run('RELEASE recipe_call');self.assert_rolled_back()
            self.connection.run('ROLLBACK TO recipe_setup');self.connection.run('RELEASE recipe_setup')

    def test_late_relation_scope_change_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.stage();self.connection.run('SAVEPOINT new_relation')
        self.trigger('feed_member','AFTER','INSERT','CREATE TABLE truss.fixture_uncovered(value text); RETURN NEW;')
        with self.assertRaises(DatabaseError) as caught:self.register()
        self.assertEqual(caught.exception.args[0]['M'],'complete original pending revision registration delta required')
        self.connection.run('ROLLBACK TO new_relation');self.connection.run('RELEASE new_relation');self.assert_rolled_back()

    def test_original_byte_chunk_boundaries_and_refusal(self):
        from pg8000.exceptions import DatabaseError
        for count in (32768,32769):
            original=bytes((i%256 for i in range(count)))
            chunks=self.connection.run('SELECT truss.runtime_registration_original_hex_chunks(:original)',original=original)[0][0]
            self.assertEqual(bytes.fromhex(''.join(chunks)),original)
            self.assertEqual([len(bytes.fromhex(c)) for c in chunks],[32768] if count==32768 else [32768,1])
        self.connection.run('SAVEPOINT excessive_original')
        with self.assertRaises(DatabaseError) as caught:
            self.connection.run('SELECT truss.runtime_registration_original_hex_chunks(:original)',original=b'a'*786433)
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.connection.run('ROLLBACK TO excessive_original');self.connection.run('RELEASE excessive_original')

    def test_extra_pending_prerequisite_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.stage();self.connection.run('SAVEPOINT prerequisite_drift')
        self.trigger('feed_member','AFTER','INSERT',"""INSERT INTO truss.feed_prerequisite
          VALUES(NEW.source_epoch,NEW.feed_profile,NEW.original_writer_xid,1,1,
          decode('01','hex'),decode('02','hex'),decode('03','hex'),sha256(decode('02','hex')),decode('04','hex')); RETURN NEW;""")
        with self.assertRaises(DatabaseError) as caught:self.register()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'original non-feed graph must remain empty')
        self.connection.run('ROLLBACK TO prerequisite_drift');self.connection.run('RELEASE prerequisite_drift');self.assert_rolled_back()

    def test_aggregate_owner_capacity_rolls_back_report_and_preserves_host_work(self):
        from pg8000.exceptions import DatabaseError
        # Original opaque group custody is supplied at admission, never rewritten later.
        self.group_bytes=b'g'*800000
        self.stage();self.connection.run("CREATE TEMP TABLE owner_capacity_host_work(value text); INSERT INTO owner_capacity_host_work VALUES('keep')")
        self.connection.run('SAVEPOINT owner_capacity')
        with self.assertRaises(DatabaseError) as caught:self.register()
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.assertEqual(caught.exception.args[0]['M'],'aggregate original registration owner capacity')
        self.connection.run('ROLLBACK TO owner_capacity');self.connection.run('RELEASE owner_capacity')
        self.assert_rolled_back()
        self.assertEqual(self.connection.run('SELECT value FROM owner_capacity_host_work'),[['keep']])
        self.assertEqual(self.connection.run('SELECT original_group_custody_bytes FROM truss.row_home_operation'),[[self.group_bytes]])

    def test_configuration_capsule_crosses_aggregate_capacity_from_original_admission(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('SAVEPOINT measure_originals')
        self.stage()
        capsule_size=self.connection.run('SELECT octet_length(record_send(c)) FROM truss.operation_configuration c')[0][0]
        without_capsule=self.connection.run("""SELECT octet_length(record_send(o))+octet_length(o.original_context_bytes)
            +(SELECT octet_length(record_send(r)) FROM truss.schema_rev r WHERE rev=1)
            +(SELECT sum(octet_length(record_send(d))) FROM truss.schema_doc d WHERE rev=1)
            FROM truss.row_home_operation o""")[0][0]
        self.connection.run('ROLLBACK TO measure_originals');self.connection.run('RELEASE measure_originals')
        self.group_bytes=b'g'*(786432-without_capsule+1-capsule_size//2)
        self.stage()
        actual=self.connection.run("""SELECT octet_length(record_send(o))+octet_length(o.original_context_bytes)
            +(SELECT octet_length(record_send(r)) FROM truss.schema_rev r WHERE rev=1)
            +(SELECT sum(octet_length(record_send(d))) FROM truss.schema_doc d WHERE rev=1)
            FROM truss.row_home_operation o""")[0][0]
        self.assertLessEqual(actual,786432);self.assertGreater(actual+capsule_size,786432)
        self.connection.run("CREATE TEMP TABLE capsule_host_work(value text); INSERT INTO capsule_host_work VALUES('keep')")
        self.connection.run('SAVEPOINT capsule_capacity')
        with self.assertRaises(DatabaseError) as caught:self.register()
        self.assertEqual(caught.exception.args[0]['C'],'54000')
        self.assertEqual(caught.exception.args[0]['M'],'aggregate original registration owner capacity')
        self.connection.run('ROLLBACK TO capsule_capacity');self.connection.run('RELEASE capsule_capacity')
        self.assert_rolled_back();self.assertEqual(self.connection.run('SELECT value FROM capsule_host_work'),[['keep']])

    def test_late_configuration_capsule_change_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run((ROOT/'packages/postgresql/native/operation-configuration-immutability.sql').read_text())
        self.stage()
        original=self.connection.run("SELECT encode(record_send(c),'hex') FROM truss.operation_configuration c")
        guard=self.connection.run("SELECT tgenabled FROM pg_trigger WHERE tgname='runtime_operation_configuration_immutable' AND tgrelid='truss.operation_configuration'::regclass")
        self.assertEqual(guard,[['A']])
        self.connection.run("CREATE TEMP TABLE capsule_drift_host(value text); INSERT INTO capsule_drift_host VALUES('keep')")
        self.connection.run('SAVEPOINT capsule_drift')
        # Administrative adversarial trigger; ordinary capsule writes remain forbidden.
        self.trigger('feed_member','AFTER','INSERT',"""ALTER TABLE truss.operation_configuration DISABLE TRIGGER runtime_operation_configuration_immutable;
            UPDATE truss.operation_configuration SET selected_binding_bytes=decode('aabb','hex'); RETURN NEW;""")
        with self.assertRaises(DatabaseError) as caught:self.register()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.assertEqual(caught.exception.args[0]['M'],'current configuration differs from original admission capsule')
        self.connection.run('ROLLBACK TO capsule_drift');self.connection.run('RELEASE capsule_drift');self.assert_rolled_back()
        self.assertEqual(self.connection.run("SELECT encode(record_send(c),'hex') FROM truss.operation_configuration c"),original)
        self.assertEqual(self.connection.run("SELECT tgenabled FROM pg_trigger WHERE tgname='runtime_operation_configuration_immutable' AND tgrelid='truss.operation_configuration'::regclass"),guard)
        self.assertEqual(self.connection.run('SELECT value FROM capsule_drift_host'),[['keep']])
