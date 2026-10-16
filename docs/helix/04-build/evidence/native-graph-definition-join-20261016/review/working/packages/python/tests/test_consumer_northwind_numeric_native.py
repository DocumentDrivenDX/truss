"""Unmodified consumer schema: exact numeric create/read/update/query/reopen."""
from decimal import Decimal
from hashlib import sha256
import json
import os
from pathlib import Path
import psycopg
from truss import (Ok, ObjectFound, QueryRows, CatalogDocument, ModuleAccessGrant,
                   adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration)
from truss.contracts import TextValue, MapValue
from truss.groups import (AuthoredValue, CreateObject, RootlessOwnership, GroupSuccess,
                          UpdateObject, StoredObjectReference, RequestNone)
import test_catalog_runtime_native as catalog_tests

FIXTURE = Path(__file__).parent/'fixtures/consumer/northwind.umf.json'

class ConsumerNorthwindNumericTests(catalog_tests.PublicCatalogRuntimeTests):
    for _name in tuple(n for n in dir(catalog_tests.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_original_product_exact_numeric_workflow(self):
        self.install()
        raw = FIXTURE.read_bytes()
        source = json.loads(raw)
        document_id = source['id']
        module_id = source['modules'][0]['id']
        connection, host, assembly, tx = self.consumer()
        prepared = assembly.prepare_catalog((CatalogDocument(document_id, sha256(raw).hexdigest(), raw),),
            source_version=source['umf'], bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
        documents = tuple(item.document for item in prepared.documents)
        self.assertIsInstance(assembly.accept_in_transaction(tx, prepared, request_key='northwind-original'), Ok)
        view = assembly.catalog_view_in_transaction(tx, assembly.catalog_view_request()).value.view
        product = next(d.reference for d in view.definitions if d.reference.kind == 'type'
                       and d.reference.authored_identity == 'Product')
        host.detach(); connection.commit()
        self.admin.execute('BEGIN')
        admin_host = adopt_psycopg_host(self.admin)
        self.addCleanup(admin_host.detach)
        admin_tx = admin_host.adopt_transaction().value
        admin_assembly = create_reference_assembly(CatalogRuntimeConfiguration(), admin_host).value
        for role in ('northwind_reader', 'northwind_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute, psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        grant = ModuleAccessGrant(document_id, module_id, 'northwind_reader', 'northwind_writer')
        self.assertIsInstance(admin_assembly.configure_module_access_in_transaction(admin_tx, (grant,)), Ok)
        admin_host.detach(); self.admin.commit()
        self.admin.execute('GRANT northwind_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        connection, host, assembly, tx = self.consumer()
        values = tuple(AuthoredValue(name=name, value=TextValue(kind=kind, text=text)) for name,kind,text in (
            ('Product.code','string','exact-product'), ('Product.name','string','Exact price'),
            ('Product.unitPrice','decimal','9999999999.9900'),
            ('Product.unitsInStock','integer','9007199254740993')))
        create = CreateObject(type_definition_pin=product.definition_pin, values=values, ownership=RootlessOwnership())
        def apply(operation):
            context = assembly.group_context_in_transaction(tx).value
            result = assembly.apply_in_transaction(tx, context.input((operation,), MapValue(entries=())),
                RequestNone(), documents=documents, bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE', 'bun'))
            self.assertIsInstance(result, Ok, repr(result))
            self.assertIsInstance(result.value, GroupSuccess, repr(result.value))
            return result.value.response.semantic.results[0]
        identity = apply(create).identity
        apply(UpdateObject(target=StoredObjectReference(identity=identity), expected_version='1',
            set=(AuthoredValue(name='Product.unitPrice', value=TextValue(kind='decimal', text='1.2300')),), unset=()))
        host.detach(); connection.commit()
        connection, host, assembly, tx = self.consumer()
        found = assembly.get_object_in_transaction(tx, document_id=document_id, module_id=module_id,
            record_id='Product', object_id=int(identity.id))
        self.assertIsInstance(found.value, ObjectFound)
        self.assertEqual(dict(found.value.object.values)['Product.unitPrice'], TextValue(kind='decimal', text='1.2300'))
        self.assertEqual(dict(found.value.object.values)['Product.unitsInStock'], TextValue(kind='integer', text='9007199254740993'))
        rows = assembly.query_in_transaction(tx,
            sql='SELECT p."Product.unitPrice", p."Product.unitsInStock" FROM "Product" p WHERE p."Product.unitPrice" = :price',
            document_ids=(document_id,), parameters={'price': Decimal('1.23')})
        self.assertIsInstance(rows, Ok, repr(rows))
        self.assertIsInstance(rows.value, QueryRows, repr(rows.value))
        self.assertEqual(rows.value.rows, ((Decimal('1.2300'), 9007199254740993),))
        self.assertEqual(str(rows.value.rows[0][0]), '1.2300')
        host.detach(); connection.rollback()


import test_group_create_native as group_tests

class UnnamedSqlTests(group_tests.PublicCreateGroupTests):
    for _name in tuple(n for n in dir(group_tests.PublicCreateGroupTests) if n.startswith('test_')):
        locals()[_name] = None

    def test_default_compiler_uses_stable_ids_without_authored_names(self):
        def unnamed(source):
            for module in source['modules']:
                for element in module['elements']:
                    element.pop('name', None)
        connection, host, assembly, tx = self.ready(unnamed, document_ids=('adoc',))
        semantic, request = self.input(assembly, tx)
        self.assertIsInstance(self.apply(assembly, tx, semantic, request), GroupSuccess)
        host.detach(); connection.commit()
        connection, host, assembly, tx = self.consumer()
        rows = assembly.query_in_transaction(tx,
            sql='SELECT a."A-label" FROM "A" a WHERE a."A-label" = :label',
            document_ids=('adoc',), parameters={'label': 'one'})
        self.assertIsInstance(rows, Ok, repr(rows))
        self.assertIsInstance(rows.value, QueryRows, repr(rows.value))
        self.assertEqual(rows.value.rows, (('one',),))
        host.detach(); connection.rollback()
