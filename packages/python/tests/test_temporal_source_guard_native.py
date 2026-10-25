# SPDX-License-Identifier: MIT OR Apache-2.0
"""Native whole-source temporal guard, resource and snapshot checks."""
from concurrent.futures import ThreadPoolExecutor
import json
import time

import psycopg

from test_temporal_engine_native import TemporalEngineNativeTests


class TemporalSourceGuardNativeTests(TemporalEngineNativeTests):
    # This module owns focused guard cases; do not rerun the engine suite here.
    for _name in tuple(n for n in dir(TemporalEngineNativeTests) if n.startswith('test_')):
        locals()[_name] = None

    def _accepted_source(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        self._store_rows(assembly, tx)
        host.detach()
        connection.commit()

        connection, host, assembly, tx = self.consumer()
        import truss.catalog_runtime as catalog_runtime
        manifest, digest, _ = catalog_runtime._release()
        raw = connection.execute(
            'SELECT truss.person_query_temporal_binding(%s::jsonb,10000,1000,1048576,%s,%s)',
            ('["adoc"]', manifest['releaseId'], digest),
        ).fetchone()[0]
        envelope = json.loads(bytes(raw))
        binding = json.loads(envelope['bindingJson'])
        record = next(item for item in binding['records'] if item['identity']['element'] == 'A')
        elements = {field['identity']['element']: field['identity'] for field in record['fields']}
        requirements = {
            'version': 'truss.temporal-source-guard/0.1',
            'record': record['identity'],
            'fields': [
                {'field': elements['A-on'], 'kind': 'date', 'presence': {'missing': True, 'null': True}},
                {'field': elements['A-at'], 'kind': 'instant', 'presence': {'missing': False, 'null': False}},
                {'field': elements['A-local'], 'kind': 'local', 'presence': {'missing': True, 'null': True}},
            ],
        }
        return connection, host, binding, record['typeId'], requirements

    def _property_id(self, type_id, element):
        return self.admin.execute(
            'SELECT prop_id FROM truss.prop_def WHERE type_id=%s AND element=%s AND retired_rev IS NULL',
            (type_id, element),
        ).fetchone()[0]

    def _corrupt_instant(self, type_id, label, token):
        instant_id = self._property_id(type_id, 'A-at')
        label_id = self._property_id(type_id, 'A-label')
        self.admin.execute(
            "UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s],%s::jsonb) "
            "WHERE type_id=%s AND props->%s->>'text'=%s",
            (str(instant_id), json.dumps({'kind': 'timestamp', 'text': token}), type_id, str(label_id), label),
        )
        observed = self.admin.execute(
            'SELECT props->%s FROM truss.object WHERE type_id=%s AND props->%s->>\'text\'=%s',
            (str(instant_id), type_id, str(label_id), label),
        ).fetchone()
        self.assertEqual(observed, ({'kind': 'timestamp', 'text': token},))

    def _guard_sql(self, *, binding=None, requirements=None, type_id=None):
        return (
            'SELECT s.id,s.props FROM truss.person_query_temporal_objects(%s::jsonb,%s,%s::jsonb) s',
            (json.dumps(binding, separators=(',', ':')), int(type_id),
             json.dumps(requirements, separators=(',', ':'))),
        )

    def _assert_guard_refusal(self, connection, sql, params, *, state, diagnostic):
        with self.assertRaises(psycopg.Error) as raised:
            with connection.transaction():
                # A named cursor makes the first-row publication boundary
                # observable: the guarded SRF must fail before yielding even
                # one row from a source containing any invalid selected cell.
                with connection.cursor(name='truss_temporal_guard_refusal') as cursor:
                    cursor.execute(sql, params)
                    cursor.fetchone()
        self.assertEqual(raised.exception.sqlstate, state, str(raised.exception))
        self.assertIn(diagnostic, str(raised.exception))

    def test_invalid_source_is_not_hidden_by_outer_filter_or_limit(self):
        connection, host, binding, type_id, requirements = self._accepted_source()
        label_id = self._property_id(type_id, 'A-label')
        base, params = self._guard_sql(binding=binding, requirements=requirements, type_id=type_id)
        # The first invalid token is outside the business predicate. The full
        # source must still refuse before the selected public row is returned.
        self._corrupt_instant(type_id, 'alpha', 'not-an-instant')
        sql = base + f" WHERE s.props->'{label_id}'->>'text'=%s LIMIT 1"
        self._assert_guard_refusal(connection, sql, params + ('zeta',),
                                   state='22023', diagnostic='instant')

        # A later invalid row must also defeat LIMIT 1 when an earlier row
        # satisfies the outer predicate. No partial page may escape.
        self._corrupt_instant(type_id, 'alpha', '1970-01-01T00:00:09Z')
        self._corrupt_instant(type_id, 'zeta', 'not-an-instant')
        self._assert_guard_refusal(connection, base + f" WHERE s.props->'{label_id}'->>'text'=%s LIMIT 1",
                                   params + ('alpha',), state='22023', diagnostic='instant')
        host.detach()
        connection.rollback()

    def test_scan_and_byte_caps_refuse_complete_source(self):
        connection, host, binding, type_id, requirements = self._accepted_source()
        sql, params = self._guard_sql(binding=binding, requirements=requirements, type_id=type_id)
        scan_limited = dict(binding, maximumScanRows=5)
        scan_sql, scan_params = self._guard_sql(binding=scan_limited, requirements=requirements, type_id=type_id)
        self._assert_guard_refusal(connection, scan_sql, scan_params,
                                   state='54000', diagnostic='bounded complete temporal source required')
        byte_limited = dict(binding, maximumBytes=1)
        byte_sql, byte_params = self._guard_sql(binding=byte_limited, requirements=requirements, type_id=type_id)
        self._assert_guard_refusal(connection, byte_sql, byte_params, state='54000',
                                   diagnostic='bounded complete temporal source required')
        host.detach()
        connection.rollback()

    def test_wrong_provenance_kind_and_presence_requirements_refuse(self):
        connection, host, binding, type_id, valid = self._accepted_source()
        sql, params = self._guard_sql(binding=binding, requirements=valid, type_id=type_id)
        mutations = []
        wrong_source = json.loads(json.dumps(valid))
        wrong_source['record']['documentId'] = 'foreign-document'
        mutations.append(wrong_source)
        wrong_kind = json.loads(json.dumps(valid))
        wrong_kind['fields'][1]['kind'] = 'local'
        mutations.append(wrong_kind)
        wrong_presence = json.loads(json.dumps(valid))
        wrong_presence['fields'][0]['presence']['missing'] = False
        mutations.append(wrong_presence)
        for requirements in mutations:
            with self.subTest(requirements=requirements):
                tampered_sql, tampered_params = self._guard_sql(
                    binding=binding, requirements=requirements, type_id=type_id)
                self._assert_guard_refusal(connection, tampered_sql, tampered_params,
                                           state='22023',
                                           diagnostic='selected temporal source requirements required')
        host.detach()
        connection.rollback()

    def test_buffered_source_uses_statement_snapshot_before_outer_gate(self):
        connection, host, binding, type_id, requirements = self._accepted_source()
        label_id = self._property_id(type_id, 'A-label')
        sql, params = self._guard_sql(binding=binding, requirements=requirements, type_id=type_id)
        gate_key = (83017, 3)
        reader_pid = connection.execute('SELECT pg_catalog.pg_backend_pid()').fetchone()[0]
        connection.execute("SET application_name='truss-temporal-source-guard-snapshot'")
        self.admin.execute('SELECT pg_catalog.pg_advisory_lock(%s,%s)', gate_key)
        guarded_cte = (
            'WITH guarded AS MATERIALIZED (' + sql + '), '
            'gate AS MATERIALIZED (SELECT pg_catalog.pg_advisory_xact_lock(%s,%s) '
            'FROM (SELECT count(*) AS row_count FROM guarded) complete_source '
            'WHERE complete_source.row_count=6) '
            f"SELECT guarded.id,guarded.props FROM guarded CROSS JOIN gate "
            f"WHERE guarded.props->'{label_id}'->>'text'=%s LIMIT 1"
        )
        future = None
        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(lambda: connection.execute(guarded_cte, params + gate_key + ('alpha',)).fetchall())
                try:
                    deadline = time.monotonic() + 10
                    waiting = False
                    while time.monotonic() < deadline:
                        row = self.admin.execute(
                            "SELECT wait_event_type,wait_event FROM pg_catalog.pg_stat_activity WHERE pid=%s",
                            (reader_pid,),
                        ).fetchone()
                        if row == ('Lock', 'advisory'):
                            waiting = True
                            break
                        time.sleep(0.025)
                    if not waiting:
                        self.admin.execute('SELECT pg_catalog.pg_advisory_unlock(%s,%s)', gate_key)
                    self.assertTrue(waiting, 'reader did not reach the post-source advisory gate')
                    # This later source row becomes invalid after the reader has
                    # materialized its full source, but before the outer predicate.
                    self._corrupt_instant(type_id, 'zeta', 'not-an-instant')
                    self.admin.commit()
                finally:
                    # Release before executor shutdown so an assertion or writer
                    # failure cannot strand its worker behind this test's gate.
                    self.admin.execute('SELECT pg_catalog.pg_advisory_unlock(%s,%s)', gate_key)
                rows = future.result(timeout=10)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1][str(label_id)]['text'], 'alpha')
            # The writer's new value is visible to a later READ COMMITTED
            # statement, confirming the earlier success used its old snapshot.
            verify_connection, verify_host, _, _ = self.consumer()
            try:
                verify_sql, verify_params = self._guard_sql(
                    binding=binding, requirements=requirements, type_id=type_id)
                self._assert_guard_refusal(verify_connection, verify_sql, verify_params,
                                           state='22023', diagnostic='instant')
            finally:
                verify_host.detach()
                verify_connection.rollback()
        finally:
            self.admin.execute('SELECT pg_catalog.pg_advisory_unlock(%s,%s)', gate_key)
            host.detach()
            connection.rollback()


if __name__ == '__main__':
    import unittest
    unittest.main()
