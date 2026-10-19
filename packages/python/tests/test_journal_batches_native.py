"""Bounded journal batches retain complete ordered history and atomicity."""
import base64
import hashlib
import json

from truss import Ok, Error
from truss.contracts import MapValue, TextValue
from truss.groups import RequestNone, UpdateObject, AuthoredValue, StoredObjectReference, GroupSuccess
from test_bulk_create_sql_native import BulkUpdateSqlTests


class JournalBatchTests(BulkUpdateSqlTests):
    for _name in tuple(n for n in dir(BulkUpdateSqlTests) if n.startswith('test_')):
        locals()[_name] = None

    def expected_history_record(self, image, identity):
        type_id = int(image['type_id'])
        revision = int(image['rev'])
        type_pin = self.admin.execute('''SELECT definition_pin
            FROM truss.runtime_owned_definition_metadata('type',%s,NULL,%s)''',
            (type_id, revision)).fetchone()[0]
        property_rows = self.admin.execute('''SELECT prop_id
            FROM truss.prop_def WHERE type_id=%s ORDER BY prop_id''', (type_id,)).fetchall()
        property_ids = [int(row[0]) for row in property_rows]
        pins = {}
        for prop_id in property_ids:
            pins[str(prop_id)] = self.admin.execute('''SELECT definition_pin
                FROM truss.runtime_owned_definition_metadata('property',%s,%s,%s)''',
                (type_id, prop_id, revision)).fetchone()[0]
        metadata = {'typeId': str(type_id), 'revision': str(revision), 'typePin': type_pin,
                    'propertyOrder': [str(prop_id) for prop_id in property_ids], 'propertyPins': pins}
        return self.admin.execute('''SELECT truss.runtime_owned_history_record_in_metadata(%s,%s,%s)''',
                                  (json.dumps(image), json.dumps(identity), json.dumps(metadata))).fetchone()[0]

    def assert_boundary(self, count):
        connection, host, assembly, tx, identities = self.initialized_updates(count)
        # Native transition images use the runtime's fixed UTC serialization.
        self.admin.execute("SET TimeZone='UTC'")
        changed_ids = {int(identity.id) for i, identity in enumerate(identities) if i % 2 == 0}
        original_identities = {int(identity.id): {
            'id': identity.id, 'typeId': identity.type_id,
            'definitionPin': identity.definition_pin,
            'owner': {'documentId': identity.owner.document_id, 'moduleId': identity.owner.module_id}
        } for identity in identities}
        before_images = dict(self.admin.execute(
            'SELECT id,to_jsonb(o) FROM truss.object o ORDER BY id').fetchall())
        before_journals = self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()[0]
        before_transitions = self.admin.execute(
            'SELECT count(*) FROM truss.runtime_object_transition').fetchone()[0]
        operations = tuple(
            UpdateObject(
                target=StoredObjectReference(identity=identity),
                set=(AuthoredValue(name='A-value', value=TextValue(
                    kind='string', text=(f'after-{i}' if i % 2 == 0 else f'before-{i}'))),),
                unset=(), expected_version='1')
            for i, identity in enumerate(identities))
        context = assembly.group_context_in_transaction(tx).value
        result = assembly.apply_in_transaction(
            tx, context.input(operations, MapValue(entries=())), RequestNone(), documents=self.documents)
        self.assertIsInstance(result, Ok, f'n={count}: {result!r} {host._custody.last_attempt.error}')
        self.assertIsInstance(result.value, GroupSuccess)
        outcomes = [r.outcome for r in result.value.response.semantic.results]
        self.assertEqual(outcomes, ['changed' if i % 2 == 0 else 'unchanged' for i in range(count)])
        self.assertEqual(sum(o == 'changed' for o in outcomes), len(changed_ids))
        host.detach()
        connection.commit()

        all_ids = [int(identity.id) for identity in identities]
        physical = self.admin.execute('''SELECT seq,entity_id,ver,op,prop_id,new_value,origin
            FROM truss.journal WHERE entity_kind='o' AND entity_id=ANY(%s) AND ver=2
            ORDER BY entity_id,seq''', (all_ids,)).fetchall()
        self.assertEqual(len(physical), 2 * len(changed_ids), f'n={count}')
        self.assertEqual({row[1] for row in physical}, changed_ids)
        ordered_events = self.admin.execute('''SELECT entity_id,op FROM truss.journal
            WHERE entity_kind='o' AND entity_id=ANY(%s) AND ver=2 ORDER BY seq''',
            (all_ids,)).fetchall()
        self.assertEqual(ordered_events, [event for identity in identities
            if int(identity.id) in changed_ids
            for event in ((int(identity.id), 'update'), (int(identity.id), 'metadata'))])
        by_id = {}
        for row in physical:
            by_id.setdefault(row[1], []).append(row)
        transition_rows = self.admin.execute('''SELECT object_id,journal,before_object,after_object
            FROM truss.runtime_object_transition WHERE object_id=ANY(%s)
                AND after_object->>'ver'='2' ORDER BY transition_id''', (all_ids,)).fetchall()
        refs_by_id = {row[0]: row[1] for row in transition_rows}
        self.assertEqual(set(refs_by_id), changed_ids)
        self.assertEqual(len(transition_rows), len(changed_ids))
        for object_id in sorted(changed_ids):
            rows = by_id[object_id]
            self.assertEqual([r[3] for r in rows].count('update'), 1)
            self.assertEqual([r[3] for r in rows].count('metadata'), 1)
            self.assertEqual(len([r[4] for r in rows if r[3] == 'update']), 1)
            self.assertEqual(len(refs_by_id[object_id]), 2)
            self.assertEqual([int(ref['seq']) for ref in refs_by_id[object_id]], [r[0] for r in rows])
            for ref, row in zip(refs_by_id[object_id], rows):
                new_value = row[5]
                origin = row[6]
                payload = base64.b64decode(new_value['bytesBase64'])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), new_value['bytesSha256'])
                self.assertEqual(ref['eventSha256'], new_value['bytesSha256'])
                self.assertEqual(ref['originSha256'], origin['bytesSha256'])
                self.assertEqual(hashlib.sha256(base64.b64decode(origin['bytesBase64'])).hexdigest(),
                                 origin['bytesSha256'])
            decoded = [json.loads(base64.b64decode(row[5]['bytesBase64'])) for row in rows]
            metadata_events = [event for event in decoded if event.get('operation') == 'metadata']
            self.assertEqual(len(metadata_events), 1)
            metadata_event = metadata_events[0]
            self.assertEqual(metadata_event['identity'], original_identities[object_id])
            transition = next(row for row in transition_rows if row[0] == object_id)
            self.assertEqual(transition[2], before_images[object_id])
            self.assertEqual(metadata_event['before'],
                self.expected_history_record(transition[2], original_identities[object_id]))
            self.assertEqual(metadata_event['after'],
                self.expected_history_record(transition[3], original_identities[object_id]))
            group = metadata_event['mutationGroup']
            self.assertEqual(group['profile'], 'truss-history-group/0.1.0')
            self.assertEqual(group['eventCount'], '2')
            digest = self.admin.execute('''SELECT encode(sha256(convert_to(
                jsonb_agg(convert_from(decode(new_value->>'bytesBase64','base64'),'UTF8')::jsonb
                    - 'mutationGroup' ORDER BY seq)::text,'UTF8')),'hex')
                FROM truss.journal WHERE entity_kind='o' AND entity_id=%s AND ver=2''',
                (object_id,)).fetchone()[0]
            self.assertEqual(group['orderedEventDigest'], digest)
            self.assertTrue(all(event['mutationGroup'] == group for event in decoded))
        object_states = self.admin.execute('''SELECT o.id,o.ver,cell.value->>'text'
            FROM truss.object o CROSS JOIN LATERAL jsonb_each(o.props) cell
            JOIN truss.prop_def p ON p.type_id=o.type_id AND p.prop_id=cell.key::int
            WHERE o.id=ANY(%s) AND p.name='A-value' ORDER BY o.id''',
            ([int(identity.id) for identity in identities],)).fetchall()
        expected = [(int(identity.id), 2 if i % 2 == 0 else 1,
                     f'after-{i}' if i % 2 == 0 else f'before-{i}')
                    for i, identity in enumerate(identities)]
        self.assertEqual(object_states, sorted(expected))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()[0],
                         before_journals + 2 * len(changed_ids))
        self.assertEqual(self.admin.execute(
            'SELECT count(*) FROM truss.runtime_object_transition').fetchone()[0],
            before_transitions + len(changed_ids))

    def test_63_mixed_changed_noop_history_order_and_refs(self):
        self.assert_boundary(63)

    def test_64_mixed_changed_noop_history_order_and_refs(self):
        self.assert_boundary(64)

    def test_65_mixed_changed_noop_history_order_and_refs(self):
        self.assert_boundary(65)

    def test_65_all_noop_group_emits_no_journal_or_transition(self):
        connection, host, assembly, tx, identities = self.initialized_updates(65)
        before_objects = self.admin.execute(
            'SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        before_journal = self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()
        before_transitions = self.admin.execute('SELECT count(*) FROM truss.runtime_object_transition').fetchone()
        context = assembly.group_context_in_transaction(tx).value
        result = assembly.apply_in_transaction(
            tx, context.input(self.updates(identities, unchanged=True), MapValue(entries=())),
            RequestNone(), documents=self.documents)
        self.assertIsInstance(result, Ok, repr(result) + ' ' + str(host._custody.last_attempt.error))
        self.assertEqual([r.outcome for r in result.value.response.semantic.results], ['unchanged'] * 65)
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(), before_objects)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), before_journal)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_object_transition').fetchone(), before_transitions)

    def test_late_chunk_suppressed_journal_insert_rolls_back_all_chunks(self):
        connection, host, assembly, tx, identities = self.initialized_updates(65)
        ids = [int(identity.id) for identity in identities]
        before_objects = self.admin.execute(
            'SELECT to_jsonb(o) FROM truss.object o WHERE id=ANY(%s) ORDER BY id', (ids,)).fetchall()
        before_keys = self.admin.execute(
            'SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall()
        before_journal = self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()
        before_transitions = self.admin.execute('SELECT count(*) FROM truss.runtime_object_transition').fetchone()
        before_reservations = self.admin.execute('SELECT count(*) FROM truss.object_key_reservation_bucket').fetchone()
        connection.execute('CREATE TEMP TABLE chunk_prior_work(value text)')
        connection.execute("INSERT INTO chunk_prior_work VALUES ('kept')")
        self.admin.execute('''CREATE FUNCTION public.suppress_late_chunk_metadata() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
            BEGIN
              IF NEW.entity_kind='o' AND NEW.entity_id=TG_ARGV[0]::bigint AND NEW.op='metadata' THEN RETURN NULL; END IF;
              RETURN NEW;
            END; $$''')
        self.addCleanup(self.admin.execute,
            'DROP FUNCTION IF EXISTS public.suppress_late_chunk_metadata() CASCADE')
        from psycopg import sql
        self.admin.execute(sql.SQL('''CREATE TRIGGER suppress_late_chunk_metadata BEFORE INSERT ON truss.journal
            FOR EACH ROW EXECUTE FUNCTION public.suppress_late_chunk_metadata({})''').format(sql.Literal(ids[-1])))
        try:
            context = assembly.group_context_in_transaction(tx).value
            result = assembly.apply_in_transaction(
                tx, context.input(self.updates(identities), MapValue(entries=())),
                RequestNone(), documents=self.documents)
            self.assertIsInstance(result, Error, repr(result))
            self.assertEqual(result.error.sql_state, '55000', repr(result))
            self.assertEqual(host._custody.last_attempt.phase, 'contained')
            self.assertEqual(connection.execute('TABLE chunk_prior_work').fetchall(), [('kept',)])
            self.assertEqual(self.admin.execute(
                'SELECT to_jsonb(o) FROM truss.object o WHERE id=ANY(%s) ORDER BY id', (ids,)).fetchall(),
                before_objects)
            self.assertEqual(self.admin.execute(
                'SELECT to_jsonb(k) FROM truss.object_key_bucket k ORDER BY storage_row_id').fetchall(),
                before_keys)
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), before_journal)
            self.assertEqual(self.admin.execute(
                'SELECT count(*) FROM truss.runtime_object_transition').fetchone(), before_transitions)
            self.assertEqual(self.admin.execute(
                'SELECT count(*) FROM truss.object_key_reservation_bucket').fetchone(), before_reservations)
        finally:
            self.admin.execute('DROP TRIGGER suppress_late_chunk_metadata ON truss.journal')
        host.detach()
        connection.commit()
        self.assertEqual(connection.execute('TABLE chunk_prior_work').fetchall(), [('kept',)])
        self.assertEqual(self.admin.execute(
            'SELECT to_jsonb(o) FROM truss.object o WHERE id=ANY(%s) ORDER BY id', (ids,)).fetchall(),
            before_objects)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), before_journal)
