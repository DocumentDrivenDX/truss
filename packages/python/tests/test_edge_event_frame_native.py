# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native component decoding; no accepted catalog or installed authority claim."""
import base64
import hashlib
import json
from test_row_touch_observer_native import RowTouchObserverNativeTests, ROOT


class EdgeEventFrameNativeTests(RowTouchObserverNativeTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c = cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT / 'packages/postgresql/native/edge-limit/event-frame.sql').read_text())
            c.run((ROOT / 'packages/postgresql/native/edge-limit/observe.sql').read_text())
        finally:
            c.close()

    def edge_image(self):
        return dict(id=9007199254740993, rel_type_id=1, source_id=2, source_type=3,
                    target_id=4, target_type=5, props={}, retained={'unknown':9007199254740993}, order_key=None, rev=0, ver=1,
                    created_at='2026-10-11T12:00:00.123456+00:00', updated_at='2026-10-11T12:00:00.123456+00:00')

    def artifact(self, value):
        return dict(identity='component-fixture', bytesBase64=base64.b64encode(value).decode(),
                    sha256=hashlib.sha256(value).hexdigest())

    def definition(self):
        return dict(document_id='fixture', rel_type_id=1, module='fixture', rel_id='r',
                    name='r', source_min=0, source_max=1, target_min=0, target_max=1,
                    lifecycle='active', directed=True, target_key=None, composition=False,
                    assoc_type_id=None, inverse=None, since_rev=0, doc_ord=0, retired_rev=None,
                    definition_source_kind='accepted_document',definition_rev=0,definition_doc_ord=0,
                    definition_document_id='fixture',binding_source_rev=None,binding_source_pointer=None,
                    binding_source_bytes=None)

    def frame(self, generation='9', opcode='UPDATE'):
        event = dict(relation='edge', opcode=opcode,
                     oldImage=None if opcode == 'INSERT' else self.edge_image(),
                     newImage=None if opcode == 'DELETE' else self.edge_image())
        def side(image):
            return None if image is None else dict(edge=image, definition=self.definition(),
                                                   originalGuard=self.artifact(b'fixture-guard'))
        scope = json.dumps(dict(interfaceVersion='truss-native-edge-event-scope/0.1',
                                old=side(event['oldImage']), new=side(event['newImage']))).encode()
        return dict(effectGeneration=generation, event=event, scope=self.artifact(scope))

    def decode(self, frames, generation=9):
        wire = json.dumps(dict(interfaceVersion='truss-native-edge-event-frames/0.1', frames=frames)).encode()
        return self.connection.run('SELECT truss.edge_limit_frame_original(:wire,:generation)::text',
                                   wire=wire, generation=generation)

    def test_sparse_global_generation_and_exact_integer(self):
        frames = [self.frame('9'), self.frame('12', 'DELETE')]
        self.assertEqual(json.loads(self.decode(frames)[0][0]), frames[0])
        self.assertEqual(json.loads(self.decode(frames, 12)[0][0]), frames[1])

    def test_invalid_unused_frames_are_refused(self):
        invalid = []
        duplicate = self.frame()
        invalid.append(duplicate)
        for value in ('09', '-1', '9223372036854775808', '1' * 5000):
            invalid.append(self.frame(value))
        unknown = self.frame('12'); unknown['event']['relation'] = 'object'
        invalid.append(unknown)
        missing = self.frame('12'); del missing['event']['oldImage']
        invalid.append(missing)
        bad_digest = self.frame('12'); bad_digest['scope']['sha256'] = '0' * 64
        invalid.append(bad_digest)
        for image in ({}, dict(id=True), dict(self.edge_image(), id=2**63),
                      dict(self.edge_image(), extra=1), dict(self.edge_image(), props=[])):
            bad = self.frame('12'); bad['event']['oldImage'] = image
            invalid.append(bad)
        for frame in invalid:
            with self.subTest(frame=str(frame)[:100]), self.assertRaises(Exception):
                self.decode([self.frame(), frame])

    def test_missing_generation_and_null_refuse(self):
        for generation in (8, None, -1):
            with self.subTest(generation=generation), self.assertRaises(Exception):
                self.decode([self.frame()], generation)

    def test_all_three_observers_are_unconditional_and_always(self):
        rows = self.connection.run("""SELECT c.relname,t.tgname,t.tgtype,t.tgenabled,
            t.tgnargs,t.tgqual IS NULL,t.tgattr=''::int2vector
            FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid
            WHERE t.tgfoid IN ('truss.edge_limit_observe()'::regprocedure,
                'truss.edge_limit_catalog_observe()'::regprocedure) ORDER BY c.relname""")
        self.assertEqual(rows, [
            ['edge', 'edge_limit_edge_observe', 29, 'A', 0, True, True],
            ['edge_limit', 'edge_limit_marker_observe', 29, 'A', 0, True, True],
            ['rel_def', 'edge_limit_catalog_observe', 29, 'A', 0, True, True]])
        self.assertEqual(self.connection.run("""SELECT count(*) FROM pg_trigger WHERE
            tgrelid='truss.rel_def'::regclass AND tgname='runtime_catalog_generation'"""), [[0]])

    def test_actual_nine_events_advance_generation_once(self):
        self.exercise_edge_events()

    def test_actual_events_under_changed_timezone(self):
        self.exercise_edge_events(timezone='America/New_York')

    def test_unplanned_event_refuses_without_registry_or_row_change(self):
        self.exercise_edge_events(unplanned=True)

    def test_binding_bytes_under_changed_output(self):
        self.exercise_edge_events(binding=True)

    def test_generation_decimal_boundary_and_late_readiness(self):
        self.exercise_edge_events(start_generation=9, late=True)

    def test_suppressed_registry_update_rolls_back_event(self):
        self.exercise_edge_events(suppress=True)

    def exercise_edge_events(self, timezone=None, unplanned=False, start_generation=0, late=False, suppress=False, binding=False):
        c = self.connection
        wire = lambda value: json.dumps(value, separators=(',', ':')).encode()
        c.run('BEGIN')
        try:
            c.run("SET LOCAL session_replication_role='replica'")
            c.run('LOCK TABLE truss.schema_head IN EXCLUSIVE MODE')
            c.run("INSERT INTO truss.row_home_capacity VALUES(1,0,0,0,0,decode('01','hex'),decode('02','hex'))")
            xid, session, actor, database, pid, actor_oid, session_oid = c.run("""SELECT
                pg_current_xact_id()::text,session_user::text,current_user::text,current_database(),
                pg_backend_pid()::text,(SELECT oid::text FROM pg_roles WHERE rolname=current_user),
                (SELECT oid::text FROM pg_roles WHERE rolname=session_user)""")[0]
            execution = wire(dict(interfaceVersion='truss-native-operation-context/0.2',
                xid=xid, ordinal='0', sessionUser=session, actingUser=actor, database=database,
                backendPid=pid, actorRoleOid=actor_oid, sessionRoleOid=session_oid))
            profile = dict(identity='administrative-component-fixture',version='0.1',sha256='0'*64)
            admission = self.artifact(b'fixture-not-installed-authority')
            context = dict(interfaceVersion='truss-row-operation-context/0.1.0',profile=profile,
                installationIdentity='fixture',originalWriterXid=xid,operationOrdinal='0',
                addressDomain='truss-row-operation-address/0.1.0',
                authority='actual-protected-native-registry-correspondence',
                durability='transaction-local-until-original-commit-observation',originalGroupAdmission=admission)
            for name, value in dict(originalInstallation=b'fixture',originalLayout=b'\x01',
                originalResourceProfile=b'\x02',originalOperationDefinition=b'definition',
                originalExecutionContext=execution,originalActingRoleContext=execution,
                originalCatalogAuthorityCut=b'fixture-cut',originalOwnerUnion=b'fixture-union').items():
                context[name] = self.artifact(value)
            group = wire(dict(interfaceVersion='truss-row-group-custody/0.1.0',profile=profile,
                addressDomain='truss-row-operation-address/0.1.0',
                operationIdentity=wire(['truss-row-operation-address/0.1.0','fixture',xid,'0']).decode(),
                operationKind='catalog-acceptance',originalGroupAdmission=admission,
                authority='actual-original-operation-admission-not-caller-address',
                completionEvidence='resolved-independently-not-embedded-future-digest'))
            c.run("SET LOCAL TimeZone='UTC'")
            c.run("SET LOCAL DateStyle='ISO, YMD'")
            c.run("SET LOCAL bytea_output='hex'")
            definition=self.definition()
            if binding:
                definition.update(definition_source_kind='accepted_binding',definition_rev=None,
                    definition_doc_ord=None,definition_document_id=None,binding_source_rev=0,
                    binding_source_pointer='/fixture',binding_source_bytes='\\x00ff01')
            images = {}
            for relation, values in [('rel_def',definition),('edge',self.edge_image()),
                ('edge_limit',dict(rel_type_id=1,side='s',endpoint_id=2,edge_id=9007199254740993))]:
                images[relation] = json.loads(c.run(f'SELECT to_jsonb(jsonb_populate_record(NULL::truss.{relation},:value::jsonb))::text',value=json.dumps(values))[0][0])
            events = [(r,op) for r in ('rel_def','edge','edge_limit') for op in ('INSERT','UPDATE','DELETE')]
            frames = []
            for generation,(relation,opcode) in enumerate(events,start_generation):
                image=images[relation]
                event=dict(relation=relation,opcode=opcode,oldImage=None if opcode=='INSERT' else image,newImage=None if opcode=='DELETE' else image)
                side=dict(edge=None if relation=='rel_def' else images['edge'],definition=images['rel_def'],originalGuard=self.artifact(b'fixture-guard'))
                scope=wire(dict(interfaceVersion='truss-native-edge-event-scope/0.1',old=None if opcode=='INSERT' else side,new=None if opcode=='DELETE' else side))
                frames.append(dict(effectGeneration=str(generation),event=event,scope=self.artifact(scope)))
            plan=wire(dict(interfaceVersion='truss-native-edge-event-frames/0.1',frames=frames))
            original=wire(context)
            c.run('SELECT truss.capacity_reserve_original(0,:context,:plan,10,1000000,:layout,:resource)',context=original,plan=plan,layout=b'\x01',resource=b'\x02')
            if suppress:
                c.run("CREATE FUNCTION truss.fixture_suppress_edge_registry() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
                c.run("CREATE TRIGGER fixture_suppress_edge_registry BEFORE UPDATE ON truss.row_home_operation FOR EACH ROW EXECUTE FUNCTION truss.fixture_suppress_edge_registry()")
                c.run("ALTER TABLE truss.row_home_operation ENABLE ALWAYS TRIGGER fixture_suppress_edge_registry")
            c.run("""INSERT INTO truss.row_home_operation(original_writer_xid,operation_ordinal,
                operation_kind,phase,effect_generation,original_context_bytes,original_definition_bytes,
                original_input_bytes,original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,
                original_group_custody_bytes) VALUES(:xid::xid8,0,'catalog-acceptance','admitted',:generation,
                :context,:definition,:input,:before,:after,:plan,:group)""",xid=xid,generation=start_generation,context=original,
                definition=b'definition',input=b'fixture',before=b'fixture',after=b'fixture',plan=plan,group=group)
            if suppress:
                from pg8000.exceptions import DatabaseError
                c.run('SAVEPOINT suppressed_event')
                with self.assertRaises(DatabaseError):
                    c.run('INSERT INTO truss.rel_def SELECT (jsonb_populate_record(NULL::truss.rel_def,:value::jsonb)).*',value=json.dumps(images['rel_def']))
                c.run('ROLLBACK TO SAVEPOINT suppressed_event')
                self.assertEqual(c.run('SELECT count(*) FROM truss.rel_def'),[[0]])
                self.assertEqual(c.run('SELECT effect_generation FROM truss.row_home_operation'),[[start_generation]])
                self.assert_capacity_matches_original_rows()
                return
            if binding:
                c.run("SET LOCAL bytea_output='escape'")
            if timezone is not None:
                c.run("SELECT set_config('TimeZone',:zone,true)",zone=timezone)
            if unplanned:
                from pg8000.exceptions import DatabaseError
                c.run('SAVEPOINT rejected_event')
                with self.assertRaises(DatabaseError) as caught:
                    c.run('INSERT INTO truss.edge SELECT (jsonb_populate_record(NULL::truss.edge,:value::jsonb)).*',value=json.dumps(images['edge']))
                self.assertEqual(caught.exception.args[0]['C'],'55000')
                c.run('ROLLBACK TO SAVEPOINT rejected_event')
                self.assertEqual(c.run('SELECT count(*) FROM truss.edge'),[[0]])
                self.assertEqual(c.run('SELECT effect_generation FROM truss.row_home_operation'),[[0]])
                self.assert_capacity_matches_original_rows()
                return
            for generation,(relation,opcode) in enumerate(events,start_generation):
                if binding:
                    c.run("SET LOCAL bytea_output='escape'")
                if late:
                    c.run("UPDATE truss.row_home_operation SET phase='effects_ready',readiness_generation=effect_generation")
                if opcode=='INSERT':
                    c.run(f'INSERT INTO truss.{relation} SELECT (jsonb_populate_record(NULL::truss.{relation},:value::jsonb)).*',value=json.dumps(images[relation]))
                elif opcode=='UPDATE':
                    field='rel_type_id' if relation!='edge' else 'id'
                    c.run(f'UPDATE truss.{relation} SET {field}={field}')
                else:
                    c.run(f'DELETE FROM truss.{relation}')
                self.assertEqual(c.run('SELECT effect_generation,phase FROM truss.row_home_operation'),[[generation+1,'admitted']])
                if binding:
                    c.run("SET LOCAL bytea_output='hex'")
                self.assertEqual(c.run('SELECT readiness_generation,sealed_generation,application_generation,application_result_bytes FROM truss.row_home_operation'),[[None,None,None,None]])
                self.assert_capacity_matches_original_rows()
        finally:
            c.run('ROLLBACK')
