# SPDX-License-Identifier: MIT OR Apache-2.0
"""CREATE uses the exact immutable five-key schema basis compiled at head."""
import json
import os
import psycopg
from truss import (CatalogDocument, CatalogRegistration, Error, ModuleAccessGrant, Ok,
                   adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration)
from truss.groups import GroupFailed, GroupSuccess
import test_group_create_native as base


class CreateMetadataCacheTests(base.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def assert_current_basis(self, type_id, expected_properties):
        cached, manual = self.admin.execute('''
          WITH head AS (SELECT rev FROM truss.schema_head WHERE id=1),
          properties AS MATERIALIZED (
            SELECT p.prop_id,d.definition_pin
            FROM truss.prop_def p CROSS JOIN head
            CROSS JOIN LATERAL truss.runtime_owned_definition_metadata('property',p.type_id,p.prop_id) d
            WHERE p.type_id=%s AND p.since_rev<=head.rev AND (p.retired_rev IS NULL OR p.retired_rev>head.rev)
          ), basis AS (
            SELECT h.rev,t.type_id,pin.definition_pin type_pin,
             coalesce((SELECT jsonb_agg(p.prop_id::text ORDER BY p.prop_id) FROM properties p),'[]'::jsonb) property_order,
             coalesce((SELECT jsonb_object_agg(p.prop_id::text,p.definition_pin) FROM properties p),'{}'::jsonb) property_pins
            FROM head h JOIN truss.type_def t ON t.type_id=%s
            CROSS JOIN LATERAL truss.runtime_owned_definition_metadata('type',t.type_id) pin
          )
          SELECT jsonb_build_object('typeId',s.metadata->'typeId','revision',s.metadata->'revision',
             'typePin',s.metadata->'typePin','propertyOrder',s.metadata->'propertyOrder',
             'propertyPins',s.metadata->'propertyPins'),
           jsonb_build_object('typeId',b.type_id::text,'revision',b.rev::text,'typePin',b.type_pin,
             'propertyOrder',b.property_order,'propertyPins',b.property_pins)
          FROM basis b JOIN truss.runtime_type_schema s ON s.rev=b.rev AND s.type_id=b.type_id
        ''', (type_id, type_id)).fetchone()
        self.assertEqual(cached, manual)
        self.assertEqual(len(cached['propertyOrder']), expected_properties)
        return cached

    def test_create_matches_manual_basis_after_compatible_revision_and_refuses_retirement(self):
        connection, host, assembly, tx = self.ready(document_ids=('adoc',))
        self.admin.execute(psycopg.sql.SQL('GRANT {} TO consumer WITH SET FALSE').format(
            psycopg.sql.Identifier(self.installation.registrar_role)))

        source = json.loads(next(document.content for document in self.documents
                                 if document.document_id == 'adoc'))
        module = source['modules'][0]
        next(element for element in module['elements'] if element['id'] == 'A')['members'].append(
            {'module': 'm', 'element': 'A-note'})
        module['elements'].append({'id': 'A-note', 'name': 'A-note', 'kind': 'field',
            'scalarType': 'string', 'nullability': 'absent-allowed', 'cardinality': 'one', 'extensions': {}})
        document = CatalogDocument('adoc', 'r2', json.dumps(source, ensure_ascii=False).encode())
        prepared = assembly.prepare_catalog((document,), source_version=source['umf'],
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        accepted = assembly.accept_in_transaction(tx, prepared, request_key='create-schema-r2')
        self.assertIsInstance(accepted, Ok, repr(accepted))
        self.assertIsInstance(accepted.value, CatalogRegistration)
        host.detach()
        connection.commit()
        self.documents = (document,)
        connection, host, assembly, tx = self.consumer()
        reference = assembly.get_type_reference_in_transaction(
            tx, document_id='adoc', module_id='m', record_id='A')
        self.assertIsInstance(reference, Ok)
        self.types[('adoc', 'A')] = reference.value
        type_id = int(reference.value.type_id)
        self.assert_current_basis(type_id, 3)

        # A later accepted source retires the optional field. The current compiled
        # basis must follow the head rather than retaining the earlier property map.
        source['modules'][0]['elements'] = [element for element in source['modules'][0]['elements']
                                           if element['id'] != 'A-note']
        record = next(element for element in source['modules'][0]['elements'] if element['id'] == 'A')
        record['members'] = [member for member in record['members'] if member['element'] != 'A-note']
        retired_document = CatalogDocument('adoc', 'r3', json.dumps(source, ensure_ascii=False).encode())
        retired_prepared = assembly.prepare_catalog((retired_document,), source_version=source['umf'],
            bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        retired = assembly.accept_in_transaction(tx, retired_prepared, request_key='create-schema-r3')
        self.assertIsInstance(retired, Error, repr(retired))
        self.assertEqual(retired.error.sql_state, '0A000')
        self.assertEqual(retired.error.catalog_code, 'unsupported_profile')
        self.assertEqual(self.admin.execute('SELECT rev FROM truss.schema_head').fetchone(), (2,))
        self.assertEqual(self.admin.execute(
            "SELECT retired_rev IS NOT NULL FROM truss.prop_def WHERE type_id=%s AND element='A-note'",
            (type_id,)).fetchone(), (False,))
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (0,))
        self.assertEqual(connection.execute('SELECT 42').fetchone(), (42,))

        # The failed retirement attempt does not perturb accepted r2 metadata or
        # prevent an ordinary create using its exact compiled basis.
        self.documents = (document,)
        result = self.apply(assembly, tx, *self.input(assembly, tx, (self.create(alias='compiled'),)))
        self.assertIsInstance(result, GroupSuccess)
        host.detach()
        connection.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (1,))

    @staticmethod
    def separate_property_module(source):
        module = source['modules'][0]
        moved = next(element for element in module['elements'] if element['id'] == 'A-value')
        module['elements'].remove(moved)
        for record in (element for element in module['elements'] if element['kind'] == 'record'):
            for member in record['members']:
                if member['element'] == 'A-value':
                    member['module'] = 'fields'
            for key in record['keys']:
                for field in key['fields']:
                    if field['element'] == 'A-value':
                        field['module'] = 'fields'
        source['modules'].append({'id': 'fields', 'namespace': 'fields', 'elements': [moved],
                                  'relationships': [], 'extensions': {}})

    def test_create_rechecks_current_property_reader_permission(self):
        connection, host, assembly, tx = self.ready(self.separate_property_module, document_ids=('adoc',))
        for role in ('field_reader', 'field_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute,
                psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        try:
            admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
            configured = admin_assembly.configure_module_access_in_transaction(admin_host.adopt_transaction().value,
                (ModuleAccessGrant('adoc', 'fields', 'field_reader', 'field_writer'),))
            self.assertIsInstance(configured, Ok, repr(configured))
        finally:
            admin_host.detach()
        self.admin.commit()
        self.admin.execute('GRANT field_reader TO consumer WITH SET FALSE')
        type_id = int(self.types[('adoc', 'A')].type_id)
        self.assertTrue(self.admin.execute(
            'SELECT truss.runtime_object_values_readable_qualified(%s, (SELECT oid FROM pg_roles WHERE rolname=%s))',
            (type_id, 'consumer')).fetchone()[0])
        self.admin.execute('REVOKE field_reader FROM consumer')
        self.assertFalse(self.admin.execute(
            'SELECT truss.runtime_object_values_readable_qualified(%s, (SELECT oid FROM pg_roles WHERE rolname=%s))',
            (type_id, 'consumer')).fetchone()[0])
        result = assembly.apply_in_transaction(tx, *self.input(assembly, tx, (self.create(alias='denied'),)),
            documents=self.documents, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        if isinstance(result, Ok):
            self.assertIsInstance(result.value, GroupFailed)
            self.assertEqual(result.value.failure.code, 'unauthorized_person')
        else:
            self.assertIsInstance(result, Error)
            self.assertEqual(result.error.sql_state, '42501')
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(), (0,))
