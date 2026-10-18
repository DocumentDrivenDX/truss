"""Bulk update transition rows retain the exact journal projection."""
import base64
import json
import re
from truss import Error
from truss import (Ok, ModuleAccessGrant, CatalogRuntimeConfiguration,
    adopt_psycopg_host, create_reference_assembly, HistoryEntity,
    HistoricalRecord, QueryRows, FeedPage)
from truss.contracts import MapValue
from truss.groups import RequestNone
from test_bulk_create_sql_native import BulkUpdateSqlTests


class BulkUpdateTransitionGuardTests(BulkUpdateSqlTests):
    for _name in tuple(n for n in dir(BulkUpdateSqlTests) if n.startswith('test_')):
        locals()[_name] = None

    def enrolled_for_compact_journal_test(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        host.detach(); connection.rollback()
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        self.addCleanup(admin_host.detach)
        admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
        admin_tx = admin_host.adopt_transaction().value
        configured = admin_assembly.configure_module_access_in_transaction(admin_tx,
            (ModuleAccessGrant('adoc', 'm', 'group_reader', 'group_writer'),))
        self.assertIsInstance(configured, Ok)
        enrolled = admin_assembly.register_feed_consumer_in_transaction(admin_tx,
            consumer_id='compact-update', reader_role='group_reader')
        self.assertIsInstance(enrolled, Ok)
        admin_host.detach(); self.admin.commit()
        self.admin.execute('GRANT group_reader TO consumer WITH SET FALSE')
        return self.consumer()

    def test_independent_update_uses_compact_transition_refs_and_keeps_public_reads(self):
        connection, host, assembly, tx = self.enrolled_for_compact_journal_test()
        context = assembly.group_context_in_transaction(tx).value
        created = assembly.apply_in_transaction(tx,
            context.input((self.create(value='before'),), MapValue(entries=())),
            context.request('compact-update-create'), documents=self.documents)
        self.assertIsInstance(created, Ok, repr(created) + ' ' + str(host._custody.last_attempt.error))
        identity = created.value.response.semantic.results[0].identity
        host.detach(); connection.commit()

        # Consume the create transaction so the next feed page qualifies the update.
        connection, host, assembly, tx = self.consumer()
        first_page = assembly.read_feed_in_transaction(tx, consumer_id='compact-update')
        self.assertIsInstance(first_page, Ok, repr(first_page))
        self.assertIsInstance(first_page.value, FeedPage)
        first_changes = json.loads(first_page.value.content)['changes']
        if not first_changes:
            # Feed enrollment itself can be the first complete committed
            # transaction in the source interval. Acknowledge that empty
            # change page before reading the later object create.
            self.assertEqual(first_page.value.outcome, 'transaction')
            acknowledged = assembly.acknowledge_feed_in_transaction(tx, first_page.value)
            self.assertIsInstance(acknowledged, Ok, repr(acknowledged))
            host.detach(); connection.commit()
            connection, host, assembly, tx = self.consumer()
            first_page = assembly.read_feed_in_transaction(tx, consumer_id='compact-update')
            self.assertIsInstance(first_page, Ok, repr(first_page))
            self.assertIsInstance(first_page.value, FeedPage)
            first_changes = json.loads(first_page.value.content)['changes']
        self.assertIn('create', [change['op'] for change in first_changes])
        acknowledged = assembly.acknowledge_feed_in_transaction(tx, first_page.value)
        self.assertIsInstance(acknowledged, Ok, repr(acknowledged))
        host.detach(); connection.commit()

        connection, host, assembly, tx = self.consumer()
        context = assembly.group_context_in_transaction(tx).value
        updated = assembly.apply_in_transaction(tx,
            context.input(self.updates((identity,)), MapValue(entries=())),
            context.request('compact-update-value'), documents=self.documents)
        self.assertIsInstance(updated, Ok, repr(updated) + ' ' + str(host._custody.last_attempt.error))
        self.assertEqual(updated.value.response.semantic.results[0].outcome, 'changed')
        host.detach(); connection.commit()

        transition = self.admin.execute('''SELECT journal FROM truss.runtime_object_transition
            WHERE object_id=%s ORDER BY transition_id DESC LIMIT 1''', (int(identity.id),)).fetchone()[0]
        self.assertIsInstance(transition, list)
        self.assertTrue(transition)
        required = {'referenceProfile', 'seq', 'at', 'xid', 'entity_kind', 'entity_id',
            'entity_type', 'ver', 'op', 'prop_id', 'old_value', 'rev',
            'eventSha256', 'originSha256'}
        for reference in transition:
            self.assertTrue(required.issubset(reference), reference)
            self.assertEqual(reference['referenceProfile'], 'truss-native-journal-reference/0.1')
            self.assertNotIn('new_value', reference)
            self.assertNotIn('origin', reference)
            self.assertRegex(reference['eventSha256'], re.compile(r'^[0-9a-f]{64}$'))
            self.assertRegex(reference['originSha256'], re.compile(r'^[0-9a-f]{64}$'))

        physical = self.admin.execute('''SELECT seq,op,prop_id,new_value,origin FROM truss.journal
            WHERE entity_kind='o' AND entity_id=%s AND ver=2 ORDER BY seq''', (int(identity.id),)).fetchall()
        self.assertEqual(len(physical), len(transition))
        self.assertTrue(any(row[1] == 'update' and row[3] is not None and row[4] is not None for row in physical))
        self.assertTrue(any(row[1] == 'metadata' for row in physical))

        connection, host, assembly, tx = self.consumer()
        entity = HistoryEntity(kind='object', document_id='adoc', module_id='m', definition_id='A', id=int(identity.id))
        history = assembly.page_history_in_transaction(tx, entity=entity)
        self.assertIsInstance(history, Ok, repr(history))
        history_events = list(history.value.events)
        cursor = history.value.continuation
        while cursor is not None and not any(event.version == 2 for event in history_events):
            next_page = assembly.page_history_in_transaction(tx, entity=entity, cursor=cursor)
            self.assertIsInstance(next_page, Ok, repr(next_page))
            history_events.extend(next_page.value.events)
            cursor = next_page.value.continuation
        self.assertTrue(any(event.version == 2 for event in history_events))
        reconstructed = assembly.reconstruct_in_transaction(tx, entity=entity, version=2)
        self.assertIsInstance(reconstructed, Ok, repr(reconstructed))
        self.assertIsInstance(reconstructed.value, HistoricalRecord)
        self.assertIn('after-0', reconstructed.value.record.decode('utf8'))
        query = assembly.query_in_transaction(tx, sql='SELECT a."A-value" FROM "A" a', document_ids=('adoc',))
        self.assertIsInstance(query, Ok, repr(query))
        self.assertIsInstance(query.value, QueryRows)
        self.assertEqual(query.value.rows[0][0], 'after-0')

        update_page = assembly.read_feed_in_transaction(tx, consumer_id='compact-update')
        self.assertIsInstance(update_page, Ok, repr(update_page))
        self.assertIsInstance(update_page.value, FeedPage)
        changes = json.loads(update_page.value.content)['changes']
        self.assertIn('update', [change['op'] for change in changes])
        events = [json.loads(base64.b64decode(change['new_value']['bytesBase64']))
            for change in changes if change.get('new_value', {}).get('bytesBase64')]
        self.assertTrue(any('after-0' in json.dumps(event) for event in events), repr(changes))
        host.detach(); connection.rollback()

    def test_before_insert_journal_tamper_refuses_and_keeps_caller_work(self):
        connection, host, assembly, tx, identities = self.initialized_updates(2)
        before_objects = self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall()
        before_journal_count = self.admin.execute('SELECT count(*) FROM truss.journal').fetchone()
        before_transition_count = self.admin.execute('SELECT count(*) FROM truss.runtime_object_transition').fetchone()
        connection.execute('CREATE TEMP TABLE transition_guard_caller_work(value text)')
        connection.execute("INSERT INTO transition_guard_caller_work VALUES ('keep')")

        self.admin.execute("""CREATE FUNCTION public.tamper_bulk_transition_journal() RETURNS trigger
            LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN
              NEW.journal:=jsonb_set(NEW.journal,'{0,eventSha256}','\"0000000000000000000000000000000000000000000000000000000000000000\"'::jsonb);
              NEW.journal:=jsonb_set(NEW.journal,'{0,new_value}','\"forged\"'::jsonb);
              NEW.journal:=jsonb_set(NEW.journal,'{0,origin}','{\"actor\":\"forged\"}'::jsonb);
              RETURN NEW;
            END $$""")
        self.addCleanup(self.admin.execute, 'DROP FUNCTION IF EXISTS public.tamper_bulk_transition_journal() CASCADE')
        self.admin.execute('''CREATE TRIGGER tamper_bulk_transition_journal
            BEFORE INSERT ON truss.runtime_object_transition FOR EACH ROW
            EXECUTE FUNCTION public.tamper_bulk_transition_journal()''')
        try:
            context = assembly.group_context_in_transaction(tx).value
            result = assembly.apply_in_transaction(tx,
                context.input(self.updates(identities), MapValue(entries=())),
                RequestNone(), documents=self.documents)
            self.assertIsInstance(result, Error, repr(result))
            self.assertEqual(result.error.sql_state, '55000', repr(result))
            self.assertEqual(host._custody.last_attempt.phase, 'contained')
            self.assertEqual(connection.execute('TABLE transition_guard_caller_work').fetchall(), [('keep',)])
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_object_transition').fetchone(), before_transition_count)
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), before_journal_count)
            self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(), before_objects)
        finally:
            self.admin.execute('DROP TRIGGER tamper_bulk_transition_journal ON truss.runtime_object_transition')

        host.detach()
        connection.commit()
        self.assertEqual(connection.execute('TABLE transition_guard_caller_work').fetchall(), [('keep',)])
        self.assertEqual(self.admin.execute('SELECT to_jsonb(o) FROM truss.object o ORDER BY id').fetchall(), before_objects)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.journal').fetchone(), before_journal_count)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.runtime_object_transition').fetchone(), before_transition_count)
