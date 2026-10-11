"""Integrated observer SQL compilation and original image component evidence.

Administrative fixtures do not prove protected installation or public readiness.
"""
import json
from pathlib import Path
import unittest
from test_native_pg8000 import NativeBoundaryFixture

ROOT=Path(__file__).resolve().parents[3]

class RowTouchObserverNativeTests(NativeBoundaryFixture,unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'docs/helix/04-build/evidence/source-epoch-layout-0.16.owner-export.sql').read_text())
            c.run((ROOT/'docs/helix/04-build/evidence/design-audit/capacity-reservation-source.owner-export.sql').read_text())
            for name in ('row-image/codec','row-image/state-owner','row-image/dependent-owner','capacity-reservation/custody-codec','capacity-reservation/custody-size','capacity-reservation/accounting','capacity-reservation/observation','operation-commit-barrier','row-touch/observe'):
                c.run((ROOT/f'packages/postgresql/native/{name}.sql').read_text())
            for table,names in [('row_home_operation',('capacity_operation_insert','capacity_operation_update')),('row_home_touch',('capacity_touch_insert','capacity_touch_update'))]:
                for name in names:c.run(f'ALTER TABLE truss.{table} ENABLE ALWAYS TRIGGER {name}')
        finally:c.close()

    def setUp(self):
        self.connection=self.Connection(**self.kwargs)
    def tearDown(self):self.connection.close()

    def image(self,kind,values):
        return bytes(self.connection.run(f'SELECT truss.row_image_{kind}_original(jsonb_populate_record(NULL::truss.row_home_{kind},:value::jsonb))',value=json.dumps(values))[0][0])

    def scope(self,images):
        wire=json.dumps({'interfaceVersion':'truss-native-row-image-scope/0.1','images':[{'kind':k,'imageHex':v.hex()} for k,v in images]}).encode()
        return self.connection.run('SELECT truss.row_touch_scope_original(:wire)',wire=wire)

    def state(self,identity=1):
        return self.image('state',dict(state_id=identity,owner_kind='object',object_id=-7,object_type_id=-2,property_owner_type_id=-2,property_id=-3,root_node_id=10,definition_bytes='\\x01',home_profile_bytes='\\x02',value_profile_bytes='\\x03',source_bytes='\\x04'))

    def node(self,state=1):
        return self.image('node',dict(state_id=state,node_id=10,slot_kind='root',value_kind='scalar',definition_bytes='\\x01',source_bytes='\\x02'))

    def assert_capacity_matches_original_rows(self):
        total=0;count=0
        for kind,table in [('operation','row_home_operation'),('touch','row_home_touch')]:
            for row in self.connection.run(f'SELECT * FROM truss.{table}'):
                cells=[None if value is None else bytes(value) if isinstance(value,(bytes,bytearray,memoryview)) else str(value).encode('utf8') for value in row]
                total+=len(('truss.custody.'+kind+'/0.1').encode())+3+sum(9+(0 if value is None else len(value)) for value in cells)
                count+=1
        self.assertEqual(self.connection.run('SELECT retained_rows,retained_custody_bytes FROM truss.row_home_capacity'),[[count,total]])

    def test_null_kind_in_unused_owner_union_member_refuses(self):
        import base64,hashlib
        from pg8000.exceptions import DatabaseError
        def artifact(value):return dict(identity='fixture',bytesBase64=base64.b64encode(value).decode(),sha256=hashlib.sha256(value).hexdigest())
        member=dict(ownerKind='object',ownerId='-7',discriminatorId='-2',propertyOwnerTypeId='-2',propertyId='-3',originalHome=artifact(b'home'),originalOwnerProperty=artifact(b'property'))
        invalid=dict(member);invalid['ownerKind']=None
        union=json.dumps(dict(interfaceVersion='truss-row-owner-property-union/0.1',members=[member,invalid])).encode()
        context=json.dumps(dict(originalOwnerUnion=artifact(union)))
        association=json.dumps({k:v for k,v in member.items() if k not in ('originalHome','originalOwnerProperty')})
        with self.assertRaises(DatabaseError) as caught:self.connection.run('SELECT truss.row_touch_member_original(:context::jsonb,:association::jsonb)',context=context,association=association)
        self.assertEqual(caught.exception.args[0]['C'],'22023')

    def test_signed_integer_boundaries(self):
        for n in (-(2**63),-1,0,2**63-1):
            self.assertEqual(self.connection.run('SELECT truss.row_touch_integer_original(:wire)',wire=n.to_bytes(8,'big',signed=True)),[[n]])

    def test_original_state_round_trip(self):
        image=self.state()
        self.assertEqual(bytes(self.connection.run('SELECT truss.row_image_state_original(truss.row_touch_state_from_image_original(:image))',image=image)[0][0]),image)

    def test_complete_scope_and_duplicate_refusal(self):
        self.scope([('state',self.state()),('node',self.node())])
        with self.assertRaises(Exception):self.scope([('state',self.state()),('state',self.state())])

    def test_missing_parent_and_cross_state_node_refusal(self):
        with self.assertRaises(Exception):self.scope([('node',self.node())])
        with self.assertRaises(Exception):self.scope([('state',self.state()),('state',self.state(2)),('node',self.node()),('node',self.node(2))])

    def test_actual_insert_without_operation_refuses_and_preserves_caller_work(self):
        from pg8000.exceptions import DatabaseError
        c=self.connection
        c.run('BEGIN')
        try:
            c.run('CREATE TEMP TABLE caller_work(value text) ON COMMIT DROP')
            c.run("INSERT INTO caller_work VALUES ('keep')")
            # Administrative fixture skips unrelated catalog foreign keys. The
            # observer is ALWAYS and must still refuse this actual row event.
            c.run("SET LOCAL session_replication_role='replica'")
            c.run('SAVEPOINT row_event')
            with self.assertRaises(DatabaseError) as caught:
                c.run("INSERT INTO truss.row_home_state(state_id,owner_kind,object_id,object_type_id,property_owner_type_id,property_id,root_node_id,definition_bytes,home_profile_bytes,value_profile_bytes,source_bytes) VALUES(1,'object',-7,-2,-2,-3,10,decode('01','hex'),decode('02','hex'),decode('03','hex'),decode('04','hex'))")
            self.assertEqual(caught.exception.args[0]['C'],'55000')
            c.run('ROLLBACK TO SAVEPOINT row_event')
            self.assertEqual(c.run('SELECT value FROM caller_work'),[['keep']])
            self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_state'),[[0]])
            self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_touch'),[[0]])
        finally:c.run('ROLLBACK')

    def test_all_nine_events_advance_once_and_preserve_contributor(self):
        self.exercise_events(cascade=False)

    def test_cascade_retains_deleted_state_and_node_images(self):
        self.exercise_events(cascade=True)

    def test_exhausted_reservation_refuses_before_touch_and_preserves_caller(self):
        self.exercise_events(cascade=False,exhausted=True)

    def test_later_event_invalidates_readiness_and_sealing(self):
        for phase in ('effects_ready','row_sealed'):
            with self.subTest(phase=phase):self.exercise_events(cascade=False,late_phase=phase)

    def test_substituted_event_image_rolls_back_all_proof_state(self):
        self.exercise_events(cascade=False,rejected_node=True)

    def test_unrelated_noop_cannot_consume_scalar_insert_step(self):
        self.exercise_events(cascade=False,wrong_event=True)

    def test_suppressed_touch_effect_refuses_atomically(self):
        for opcode in ('INSERT','UPDATE'):
            with self.subTest(opcode=opcode):self.exercise_events(cascade=False,suppress_touch=opcode)

    def test_operation_and_touch_generation_overflow_refuse_atomically(self):
        for target in ('operation','touch'):
            with self.subTest(target=target):self.exercise_events(cascade=False,overflow=target)

    def test_all_six_operation_families_observe_original_row_events(self):
        for kind in ('mutation','import','catalog-transform','catalog-acceptance','home-migration','administrative-repair'):
            with self.subTest(kind=kind):self.exercise_events(cascade=False,operation_kind=kind)

    def test_two_operations_retain_complete_contributor_union(self):
        self.exercise_events(cascade=False,multiple=True)

    def test_object_to_edge_equal_id_touches_two_distinct_owners(self):
        self.exercise_events(cascade=False,ownership=True)

    def test_second_owner_reservation_failure_preserves_first_owner(self):
        self.exercise_events(cascade=False,ownership=True,owner_capacity_failure=True)

    def test_after_trigger_operation_rewrite_refuses_atomically(self):
        self.exercise_events(cascade=False,rewrite_operation=True)

    def test_historical_actor_survives_actual_role_change(self):
        self.exercise_events(cascade=False,multiple=True,switched_role=True)

    def exercise_events(self,*,cascade,exhausted=False,late_phase=None,rejected_node=False,wrong_event=False,suppress_touch=None,overflow=None,operation_kind='mutation',multiple=False,switched_role=False,rewrite_operation=False,ownership=False,owner_capacity_failure=False):
        import base64,hashlib
        def wire(value):return json.dumps(value,separators=(',',':'),ensure_ascii=False).encode()
        def artifact(name,value):return dict(identity=name,bytesBase64=base64.b64encode(value).decode(),sha256=hashlib.sha256(value).hexdigest())
        c=self.connection;c.run('BEGIN')
        try:
            c.run("SET LOCAL session_replication_role='replica'")
            c.run('INSERT INTO truss.schema_rev(rev) VALUES(0) ON CONFLICT DO NOTHING')
            c.run('INSERT INTO truss.schema_head VALUES(1,0) ON CONFLICT DO NOTHING')
            c.run("INSERT INTO truss.row_home_capacity VALUES(1,0,0,0,0,decode('01','hex'),decode('02','hex'))")
            xid,session,actor,database,pid,actor_oid,session_oid=c.run("SELECT pg_current_xact_id()::text,session_user::text,current_user::text,current_database(),pg_backend_pid()::text,(SELECT oid::text FROM pg_roles WHERE rolname=current_user),(SELECT oid::text FROM pg_roles WHERE rolname=session_user)")[0]
            profile=dict(identity='administrative-component-fixture',version='0.1',sha256='0'*64)
            execution=wire(dict(interfaceVersion='truss-native-operation-context/0.2',xid=xid,ordinal='0',sessionUser=session,actingUser=actor,database=database,backendPid=pid,actorRoleOid=actor_oid,sessionRoleOid=session_oid))
            address=wire(['truss-row-operation-address/0.1.0','fixture',xid,'0']).decode()
            admission=artifact('admission',b'fixture-not-installed-authority')
            member=dict(ownerKind='object',ownerId='-7',discriminatorId='-2',propertyOwnerTypeId='-2',propertyId='-3',originalHome=artifact('home',b'\x02'),originalOwnerProperty=artifact('property',b'original-fixture-property'))
            context=dict(interfaceVersion='truss-row-operation-context/0.1.0',profile=profile,installationIdentity='fixture',originalWriterXid=xid,operationOrdinal='0',addressDomain='truss-row-operation-address/0.1.0',authority='actual-protected-native-registry-correspondence',durability='transaction-local-until-original-commit-observation',originalGroupAdmission=admission)
            union_members=[member]
            if ownership:
                edge_member=dict(member);edge_member['ownerKind']='edge'
                union_members.append(edge_member)
            for name,value in dict(originalInstallation=b'fixture',originalLayout=b'\x01',originalResourceProfile=b'\x02',originalOperationDefinition=b'definition',originalExecutionContext=execution,originalActingRoleContext=execution,originalCatalogAuthorityCut=b'fixture-cut',originalOwnerUnion=wire(dict(interfaceVersion='truss-row-owner-property-union/0.1',members=union_members))).items():context[name]=artifact(name,value)
            group=wire(dict(interfaceVersion='truss-row-group-custody/0.1.0',profile=profile,addressDomain='truss-row-operation-address/0.1.0',operationIdentity=address,operationKind=operation_kind,originalGroupAdmission=admission,authority='actual-original-operation-admission-not-caller-address',completionEvidence='resolved-independently-not-embedded-future-digest'))
            state=self.state();node=self.node()
            scalar_values=dict(state_id=1,node_id=10,scalar_kind='string',text_value='exact',codec_definition_bytes='\\x01',original_source_bytes='\\x02')
            scalar=self.image('scalar',scalar_values)
            full=[('state',state),('node',node),('scalar',scalar)]
            before_sides=[[],full[:1],full[:2],full,full,full,full,full[:2],full[:1]]
            after_sides=[full[:1],full[:2],full,full,full,full,full[:2],full[:1],[]]
            if cascade:
                before_sides=before_sides[:6]+[full,full,full]
                after_sides=after_sides[:6]+[[],[],[]]
            descriptors=[]
            for kind,opcode,image in [('state','INSERT',state),('node','INSERT',node),('scalar','INSERT',scalar),('scalar','UPDATE',scalar),('node','UPDATE',node),('state','UPDATE',state),('scalar','DELETE',scalar),('node','DELETE',node),('state','DELETE',state)]:
                descriptors.append(dict(kind=kind,opcode=opcode,oldImageHex=None if opcode=='INSERT' else image.hex(),newImageHex=None if opcode=='DELETE' else image.hex()))
            if cascade:descriptors[6:]=list(reversed(descriptors[6:]))
            if ownership:
                edge_state=self.image('state',dict(state_id=1,owner_kind='edge',edge_id=-7,relationship_type_id=-2,property_owner_type_id=-2,property_id=-3,root_node_id=10,definition_bytes='\\x01',home_profile_bytes='\\x02',value_profile_bytes='\\x03',source_bytes='\\x04'))
                before_sides=[[],[('state',state)],[('state',edge_state)]]
                after_sides=[[('state',state)],[('state',edge_state)],[('state',state)]]
                descriptors=[dict(kind='state',opcode='INSERT',oldImageHex=None,newImageHex=state.hex()),dict(kind='state',opcode='UPDATE',oldImageHex=state.hex(),newImageHex=edge_state.hex()),dict(kind='state',opcode='UPDATE',oldImageHex=edge_state.hex(),newImageHex=state.hex())]
            def frames(sides):
                entries=[]
                for generation,images in enumerate(sides):
                    scope=wire(dict(interfaceVersion='truss-native-row-image-scope/0.1',images=[dict(kind=k,imageHex=v.hex()) for k,v in images]))
                    entries.append(dict(effectGeneration=str(generation),scope=artifact('scope/'+str(generation),scope),event=descriptors[generation]))
                return wire(dict(interfaceVersion='truss-native-row-image-frames/0.1',frames=entries))
            before=frames(before_sides);after=frames(after_sides);original=wire(context)
            c.run('SELECT truss.capacity_reserve_original(0,:context,:plan,:rows,1000000,:layout,:resource)',rows=1 if exhausted else 2 if owner_capacity_failure else 10,context=original,plan=b'obligation',layout=b'\x01',resource=b'\x02')
            if rewrite_operation:
                    c.run("CREATE FUNCTION truss.fixture_rewrite_operation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF pg_trigger_depth()=2 THEN UPDATE truss.row_home_operation SET effect_generation=effect_generation+1 WHERE original_writer_xid=NEW.original_writer_xid AND operation_ordinal=NEW.operation_ordinal; END IF; RETURN NULL; END $$")
                    c.run('CREATE TRIGGER fixture_rewrite_operation AFTER UPDATE ON truss.row_home_operation FOR EACH ROW EXECUTE FUNCTION truss.fixture_rewrite_operation()')
                    c.run('ALTER TABLE truss.row_home_operation ENABLE ALWAYS TRIGGER fixture_rewrite_operation')
            c.run("INSERT INTO truss.row_home_operation(original_writer_xid,operation_ordinal,operation_kind,phase,effect_generation,original_context_bytes,original_definition_bytes,original_input_bytes,original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes) VALUES(:xid::xid8,0,:kind,'admitted',0,:context,:definition,:input,:before,:after,:plan,:group)",kind=operation_kind,xid=xid,context=original,definition=b'definition',input=b'input',before=before,after=after,plan=b'obligation',group=group)
            actions=[
                lambda:c.run("INSERT INTO truss.row_home_state SELECT (truss.row_touch_state_from_image_original(:image)).*",image=state),
                lambda:c.run("INSERT INTO truss.row_home_node SELECT (truss.row_touch_node_from_image_original(:image)).*",image=node),
                lambda:c.run("INSERT INTO truss.row_home_scalar SELECT (jsonb_populate_record(NULL::truss.row_home_scalar,:value::jsonb)).*",value=json.dumps(scalar_values)),
                lambda:c.run("UPDATE truss.row_home_scalar SET text_value=text_value WHERE state_id=1"),
                lambda:c.run("UPDATE truss.row_home_node SET source_bytes=source_bytes WHERE state_id=1"),
                lambda:c.run("UPDATE truss.row_home_state SET source_bytes=source_bytes WHERE state_id=1"),
                lambda:c.run("DELETE FROM truss.row_home_scalar WHERE state_id=1"),
                lambda:c.run("DELETE FROM truss.row_home_node WHERE state_id=1"),
                lambda:c.run("DELETE FROM truss.row_home_state WHERE state_id=1")]
            if ownership:
                actions=actions[:1]+[
                    lambda:c.run("UPDATE truss.row_home_state SET owner_kind='edge',object_id=NULL,object_type_id=NULL,edge_id=-7,relationship_type_id=-2 WHERE state_id=1"),
                    lambda:c.run("UPDATE truss.row_home_state SET owner_kind='object',object_id=-7,object_type_id=-2,edge_id=NULL,relationship_type_id=NULL WHERE state_id=1")]
            if late_phase:
                c.run('UPDATE truss.row_home_operation SET phase=:phase,readiness_generation=0,sealed_generation=:sealed',phase=late_phase,sealed=0 if late_phase=='row_sealed' else None)
            if exhausted:
                from pg8000.exceptions import DatabaseError
                c.run('CREATE TEMP TABLE caller_work(value text) ON COMMIT DROP')
                c.run("INSERT INTO caller_work VALUES('keep')")
                ledger_before=c.run('SELECT * FROM truss.row_home_capacity')
                c.run('SAVEPOINT exhausted_event')
                with self.assertRaises(DatabaseError) as caught:actions[0]()
                self.assertEqual(caught.exception.args[0]['C'],'54000')
                c.run('ROLLBACK TO SAVEPOINT exhausted_event')
                self.assertEqual(c.run('SELECT * FROM truss.row_home_capacity'),ledger_before)
                self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_state'),[[0]])
                self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_touch'),[[0]])
                self.assertEqual(c.run('SELECT effect_generation FROM truss.row_home_operation'),[[0]])
                self.assertEqual(c.run('SELECT value FROM caller_work'),[['keep']])
                return
            if cascade:actions=actions[:6]
            for generation,action in enumerate(actions,1):
                if owner_capacity_failure and generation==2:
                    from pg8000.exceptions import DatabaseError
                    snapshots={table:c.run(f'SELECT * FROM truss.{table}') for table in ('row_home_operation','row_home_touch','row_home_capacity','row_home_state')}
                    c.run('SAVEPOINT second_owner')
                    with self.assertRaises(DatabaseError) as caught:action()
                    self.assertEqual(caught.exception.args[0]['C'],'54000')
                    c.run('ROLLBACK TO SAVEPOINT second_owner')
                    for table,rows in snapshots.items():self.assertEqual(c.run(f'SELECT * FROM truss.{table}'),rows)
                    return
                if rewrite_operation and generation==1:
                    from pg8000.exceptions import DatabaseError
                    snapshots={table:c.run(f'SELECT * FROM truss.{table}') for table in ('row_home_operation','row_home_touch','row_home_capacity')}
                    c.run('SAVEPOINT rewritten_operation')
                    with self.assertRaises(DatabaseError) as caught:action()
                    self.assertEqual(caught.exception.args[0]['C'],'55000')
                    c.run('ROLLBACK TO SAVEPOINT rewritten_operation')
                    for table,rows in snapshots.items():self.assertEqual(c.run(f'SELECT * FROM truss.{table}'),rows)
                    self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_state'),[[0]])
                    return
                if overflow and generation==(1 if overflow=='operation' else 2):
                    from pg8000.exceptions import DatabaseError
                    if overflow=='operation':c.run('UPDATE truss.row_home_operation SET effect_generation=9223372036854775807')
                    else:c.run('UPDATE truss.row_home_touch SET dirty_generation=9223372036854775807')
                    snapshots={table:c.run(f'SELECT * FROM truss.{table}') for table in ('row_home_operation','row_home_touch','row_home_capacity')}
                    c.run('SAVEPOINT overflowing_event')
                    with self.assertRaises(DatabaseError) as caught:action()
                    self.assertEqual(caught.exception.args[0]['C'],'55000')
                    c.run('ROLLBACK TO SAVEPOINT overflowing_event')
                    for table,rows in snapshots.items():self.assertEqual(c.run(f'SELECT * FROM truss.{table}'),rows)
                    self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_node'),[[0]])
                    return
                if wrong_event and generation==3:
                    from pg8000.exceptions import DatabaseError
                    snapshots={table:c.run(f'SELECT * FROM truss.{table}') for table in ('row_home_operation','row_home_touch','row_home_capacity')}
                    c.run('SAVEPOINT wrong_event')
                    with self.assertRaises(DatabaseError) as caught:c.run('UPDATE truss.row_home_node SET source_bytes=source_bytes WHERE state_id=1')
                    self.assertEqual(caught.exception.args[0]['C'],'55000')
                    c.run('ROLLBACK TO SAVEPOINT wrong_event')
                    for table,rows in snapshots.items():self.assertEqual(c.run(f'SELECT * FROM truss.{table}'),rows)
                if suppress_touch and generation==(1 if suppress_touch=='INSERT' else 2):
                    from pg8000.exceptions import DatabaseError
                    snapshots={table:c.run(f'SELECT * FROM truss.{table}') for table in ('row_home_operation','row_home_touch','row_home_capacity')}
                    c.run("CREATE FUNCTION truss.fixture_suppress_touch() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END $$")
                    c.run(f'CREATE TRIGGER fixture_suppress_touch BEFORE {suppress_touch} ON truss.row_home_touch FOR EACH ROW EXECUTE FUNCTION truss.fixture_suppress_touch()')
                    c.run('ALTER TABLE truss.row_home_touch ENABLE ALWAYS TRIGGER fixture_suppress_touch')
                    c.run('SAVEPOINT suppressed_event')
                    with self.assertRaises(DatabaseError) as caught:action()
                    self.assertEqual(caught.exception.args[0]['C'],'55000')
                    c.run('ROLLBACK TO SAVEPOINT suppressed_event')
                    for table,rows in snapshots.items():self.assertEqual(c.run(f'SELECT * FROM truss.{table}'),rows)
                    c.run('DROP TRIGGER fixture_suppress_touch ON truss.row_home_touch')
                    c.run('DROP FUNCTION truss.fixture_suppress_touch()')
                if rejected_node and generation==2:
                    from pg8000.exceptions import DatabaseError
                    snapshots={table:c.run(f'SELECT * FROM truss.{table}') for table in ('row_home_operation','row_home_touch','row_home_capacity')}
                    c.run('SAVEPOINT substituted_event')
                    with self.assertRaises(DatabaseError) as caught:
                        c.run("INSERT INTO truss.row_home_node SELECT (jsonb_populate_record(NULL::truss.row_home_node,:value::jsonb)).*",value=json.dumps(dict(state_id=1,node_id=10,slot_kind='root',value_kind='scalar',definition_bytes='\\x01',source_bytes='\\x03')))
                    self.assertEqual(caught.exception.args[0]['C'],'55000')
                    c.run('ROLLBACK TO SAVEPOINT substituted_event')
                    for table,rows in snapshots.items():self.assertEqual(c.run(f'SELECT * FROM truss.{table}'),rows)
                    self.assertEqual(c.run('SELECT count(*) FROM truss.row_home_node'),[[0]])
                action()
                self.assert_capacity_matches_original_rows()
                if ownership:
                    expected=[[ 'object',-7,1 ]] if generation==1 else [['edge',-7,generation-1],['object',-7,generation]]
                    self.assertEqual(c.run('SELECT owner_kind,owner_id,dirty_generation FROM truss.row_home_touch ORDER BY owner_kind'),expected)
                else:self.assertEqual(c.run('SELECT dirty_generation,sealed_generation,owner_id FROM truss.row_home_touch'),[[generation,None,-7]])
                self.assertEqual(c.run('SELECT effect_generation,phase,readiness_generation,sealed_generation,application_generation,application_result_bytes FROM truss.row_home_operation'),[[generation,'admitted',None,None,None,None]])
                manifest_bytes=bytes(c.run('SELECT original_operation_bytes FROM truss.row_home_touch')[0][0])
                from truss._row_operation_custody import decode_row_operation_custody
                from truss._row_operation_context import decode_row_operation_context,check_context_group_manifest
                from truss._row_group_custody import decode_row_group_custody
                decoded=decode_row_operation_custody(manifest_bytes)
                check_context_group_manifest(decode_row_operation_context(original),decode_row_group_custody(group),decoded,0)
                self.assertEqual(decoded.operations[0].prestate.original,before)
                self.assertEqual(decoded.operations[0].candidate.original,after)
                manifest=json.loads(manifest_bytes)
                self.assertEqual(len(manifest['operations']),1)
                self.assertEqual(base64.b64decode(manifest['operations'][0]['originalInput']['bytesBase64']),b'input')
            if cascade:
                c.run("SET LOCAL session_replication_role='origin'")
                c.run('DELETE FROM truss.row_home_state WHERE state_id=1')
                for table in ('state','node','scalar'):
                    self.assertEqual(c.run(f'SELECT count(*) FROM truss.row_home_{table}'),[[0]])
                self.assertEqual(c.run('SELECT dirty_generation FROM truss.row_home_touch'),[[9]])
                self.assertEqual(c.run('SELECT effect_generation FROM truss.row_home_operation'),[[9]])
            if multiple:
                # Administrative phase fixture permits the next original
                # operation; the unconditional deferred barrier still refuses
                # commit and these flags establish no installed finalization.
                c.run("UPDATE truss.row_home_operation SET phase='application_finalized',readiness_generation=9,sealed_generation=9,application_generation=9,application_result_bytes=:result",result=b'administrative-fixture-only')
                c.run('SELECT truss.capacity_release_original(:context,:plan)',context=original,plan=b'obligation')
                if switched_role:
                    # Actual administrative role switch, not authenticated-person
                    # authority or an ordinary-role installation qualification.
                    c.run('CREATE ROLE truss_fixture_actor SUPERUSER')
                    c.run('SET LOCAL ROLE truss_fixture_actor')
                second_context=json.loads(wire(context));second_context['operationOrdinal']='1'
                second_execution=json.loads(execution);second_execution['ordinal']='1'
                if switched_role:
                    acting,role_oid=c.run("SELECT current_user::text,(SELECT oid::text FROM pg_roles WHERE rolname=current_user)")[0]
                    second_execution['actingUser']=acting;second_execution['actorRoleOid']=role_oid
                second_capture=wire(second_execution)
                second_context['originalExecutionContext']=artifact('originalExecutionContext/1',second_capture)
                second_context['originalActingRoleContext']=artifact('originalActingRoleContext/1',second_capture)
                second_original=wire(second_context)
                second_group=json.loads(group);second_group['operationIdentity']=wire(['truss-row-operation-address/0.1.0','fixture',xid,'1']).decode()
                second_group_bytes=wire(second_group)
                second_before=frames([[]]);second_after=frames([[('state',state)]])
                c.run('SELECT truss.capacity_reserve_original(1,:context,:plan,10,1000000,:layout,:resource)',context=second_original,plan=b'second-obligation',layout=b'\x01',resource=b'\x02')
                c.run("INSERT INTO truss.row_home_operation(original_writer_xid,operation_ordinal,operation_kind,phase,effect_generation,original_context_bytes,original_definition_bytes,original_input_bytes,original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes) VALUES(:xid::xid8,1,:kind,'admitted',0,:context,:definition,:input,:before,:after,:plan,:group)",kind=operation_kind,xid=xid,context=second_original,definition=b'definition',input=b'second-input',before=second_before,after=second_after,plan=b'second-obligation',group=second_group_bytes)
                c.run("INSERT INTO truss.row_home_state SELECT (truss.row_touch_state_from_image_original(:image)).*",image=state)
                self.assertEqual(c.run('SELECT dirty_generation FROM truss.row_home_touch'),[[10]])
                self.assertEqual(c.run('SELECT operation_ordinal,effect_generation FROM truss.row_home_operation ORDER BY operation_ordinal'),[[0,9],[1,1]])
                retained=decode_row_operation_custody(bytes(c.run('SELECT original_operation_bytes FROM truss.row_home_touch')[0][0]))
                self.assertEqual([operation.input.original for operation in retained.operations],[b'input',b'second-input'])
                check_context_group_manifest(decode_row_operation_context(original),decode_row_group_custody(group),retained,0)
                check_context_group_manifest(decode_row_operation_context(second_original),decode_row_group_custody(second_group_bytes),retained,1)
            from pg8000.exceptions import DatabaseError
            with self.assertRaises(DatabaseError) as caught:c.run('SET CONSTRAINTS ALL IMMEDIATE')
            self.assertEqual(caught.exception.args[0]['C'],'55000')
        finally:c.run('ROLLBACK')
