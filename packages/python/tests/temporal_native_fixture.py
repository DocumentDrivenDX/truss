# SPDX-License-Identifier: MIT OR Apache-2.0
"""Tiny authentic DEV-owner native fixture; no released cohort claim."""
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import psycopg
from truss import CatalogDocument, LocalPostgres, ModuleAccessGrant, Ok, adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
from truss.contracts import TextValue
from truss.groups import AuthoredValue, CreateObject, RootlessOwnership, GroupSuccess
from truss.catalog_runtime import _release,_pin_cursor
import test_object_mutations_native as ordinary_fixture
import test_temporal_canonical_text_native as scalar_fixture


class TemporalNativeFixture(ordinary_fixture.ObjectMutationTests):
    for _name in tuple(n for n in dir(ordinary_fixture.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name] = None
    cleanup_owned_runtime = classmethod(scalar_fixture.TemporalCanonicalTextNativeTests.cleanup_owned_runtime.__func__)

    @classmethod
    def setUpClass(cls):
        worker = os.environ.get('TRUSS_NATIVE_WORKER')
        if worker:
            from native_fixture import DatabaseFixture
            cls.worker_fixture = DatabaseFixture(Path(worker))
            cls.addClassCleanup(cls.worker_fixture.cleanup)
            cls.info = SimpleNamespace(connection_uri=cls.worker_fixture.get_uri())
        else:
            cls.root = Path(tempfile.mkdtemp(prefix='truss-temporal-guard-'))
            cls.runtime = LocalPostgres(cls.root / 'data')
            cls.addClassCleanup(cls.cleanup_owned_runtime)
            cls.runtime.__enter__()
            cls.original_pid = int((cls.runtime.directory / 'postmaster.pid').read_text().splitlines()[0])
            cls.info = cls.runtime.info

    def ready_temporal(self, mutate_source=None):
        self.install()
        fixture_path = Path(__file__).parent / 'fixtures/temporal/native-guard-owner-inspection.json'
        raw = fixture_path.read_bytes()
        provenance = json.loads(fixture_path.with_name('native-guard-owner-provenance.json').read_bytes())
        self.assertEqual(sha256(raw).hexdigest(), provenance['sha256'])
        fixture = json.loads(raw)
        request = fixture['request']
        if mutate_source is not None:
            mutate_source(request['document'])
        self.document = CatalogDocument('adoc', 'r1', json.dumps(request['document'], ensure_ascii=True).encode())
        connection, host, assembly, transaction = self.consumer()
        temporal = assembly.temporal_values()
        self.prepared = temporal.prepare_catalog((self.document,))
        self.documents = (self.document,)
        accepted = temporal.accept_in_transaction(transaction, self.prepared, request_key='temporal-model')
        self.assertIsInstance(accepted, Ok, repr(accepted))
        self.assertEqual(accepted.value.revision, 1)
        host.detach(); connection.commit()
        for role in ('group_reader', 'group_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute, psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        try:
            admin_tx = admin_host.adopt_transaction().value
            admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
            configured = admin_assembly.configure_module_access_in_transaction(admin_tx,
                (ModuleAccessGrant('adoc', 'm', 'group_reader', 'group_writer'),))
            self.assertIsInstance(configured, Ok, repr(configured))
        finally:
            admin_host.detach()
        self.admin.commit()
        self.admin.execute('GRANT group_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection, host, assembly, transaction = self.consumer()
        reference = assembly.get_type_reference_in_transaction(transaction, document_id='adoc', module_id='m', record_id='A')
        self.assertIsInstance(reference, Ok)
        self.type_reference = reference.value
        instants = ('1969-12-31T23:59:59.999999Z', '1970-01-01T00:00:00Z',
                    '1970-01-01T00:00:09Z', '1970-01-01T00:00:10Z',
                    '2024-01-01T01:00:00+01:00', '2023-12-31T19:00:00-05:00')
        operations = []
        for index, instant in enumerate(instants):
            values = tuple(AuthoredValue(name=name, value=TextValue(kind=kind, text=text)) for name, kind, text in (
                ('A-label', 'string', f'row-{index}'), ('A-value', 'string', 'shared-key'),
                ('A-date', 'date', f'2024-01-{index+1:02}'), ('A-instant', 'timestamp', instant),
                ('A-payload', 'string', 'p' * 4096)))
            operations.append(CreateObject(type_definition_pin=self.type_reference.definition_pin,
                values=values, ownership=RootlessOwnership(), alias=f'row{index}'))
        applied, _, _ = self.run_group(assembly.temporal_values(), transaction, tuple(operations), 'temporal-six-rows')
        self.assertIsInstance(applied, GroupSuccess, repr(applied))
        self.identities = tuple(sorted((item.identity for item in applied.response.semantic.results),key=lambda identity:int(identity.id)))
        host.detach(); connection.commit()
        self.selected_type = int(self.identities[0].type_id)
        self.property_ids = dict(self.admin.execute('SELECT element,prop_id FROM truss.prop_def WHERE type_id=%s AND retired_rev IS NULL', (self.selected_type,)).fetchall())
        self.owner_record = next(r for r in fixture['result']['records'] if r['ref']['element']=='A')
        self.assertEqual(len(self.identities), 6)
        return self.consumer()

    def capture(self, connection, scan=10000, maximum_bytes=1048576):
        manifest, digest, _ = _release()
        with connection.cursor() as pinned:
            _pin_cursor(pinned)
        raw = connection.execute('SELECT truss.person_query_temporal_binding(%s::jsonb,%s,1000,%s,%s,%s)',
            ('["adoc"]', scan, maximum_bytes, manifest['releaseId'], digest)).fetchone()[0]
        bundle = json.loads(bytes(raw))
        binding = json.loads(bundle['bindingJson'])
        self.assertEqual(binding['queryAbi']['version'], '1.3')
        self.assertEqual(binding, bundle['binding'])
        record = next(r for r in binding['records'] if r['typeId']==str(self.selected_type))
        fields = []
        for field in self.owner_record['fields']:
            kind = 'date' if field['scalarType']=='date' else field.get('temporal')
            if kind in ('date', 'instant', 'local'):
                fields.append({'field': {**record['identity'], **field['ref']}, 'kind': kind, 'presence': field['row']})
        return bundle['bindingJson'], {'version': 'truss.temporal-source-guard/0.2', 'record': record['identity'], 'fields': fields}

    def source(self, page=False, binding_expression='%s::jsonb'):
        if page:
            return f'truss.person_query_temporal_page_objects({binding_expression},%s,%s,%s::jsonb)'
        return f'truss.person_query_temporal_objects({binding_expression},%s,%s::jsonb)'

    def source_arguments(self, binding, requirements, page=False):
        return (binding, self.selected_type, 'a-primary', json.dumps(requirements)) if page else (binding, self.selected_type, json.dumps(requirements))

    def fault(self, identity, property_name, cell):
        """Named administrative corruption only; baseline rows came from public writes."""
        self.admin.execute('ALTER TABLE truss.object DISABLE TRIGGER USER')
        try:
            self.admin.execute('UPDATE truss.object SET props=jsonb_set(props,%s,%s::jsonb,true) WHERE id=%s AND type_id=%s',
                ([str(self.property_ids[property_name])], json.dumps(cell), int(identity.id), self.selected_type))
        finally:
            self.admin.execute('ALTER TABLE truss.object ENABLE TRIGGER USER')
        self.assertEqual(self.admin.execute('SELECT props->%s FROM truss.object WHERE id=%s AND type_id=%s',
            (str(self.property_ids[property_name]), int(identity.id), self.selected_type)).fetchone()[0], cell)

    def restore_props(self, identity, props):
        self.admin.execute('ALTER TABLE truss.object DISABLE TRIGGER USER')
        try:
            self.admin.execute('UPDATE truss.object SET props=%s::jsonb WHERE id=%s AND type_id=%s',
                               (json.dumps(props), int(identity.id), self.selected_type))
        finally:
            self.admin.execute('ALTER TABLE truss.object ENABLE TRIGGER USER')
