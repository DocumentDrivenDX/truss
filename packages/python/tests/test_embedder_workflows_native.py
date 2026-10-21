# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit named revisions of frozen embedder samples: list, open and modify."""
import gzip, hashlib, json
from pathlib import Path
import psycopg
from truss import CatalogDocument, Ok, ModuleAccessGrant, QueryRows, QueryRefused, ObjectFound
from truss.contracts import MapValue, TextValue
from truss.groups import (CreateObject, RootlessOwnership, AuthoredValue, CreateEdge,
    AliasObjectReference, NullOrderKey, GroupSuccess, RequestNone, UpdateObject,
    StoredObjectReference)
import test_catalog_runtime_native as base
from embedder_fixture_sources import named_revision

CORPUS = json.loads(gzip.decompress((Path(__file__).with_name('fixtures')/'hohfeld/originals.json.gz').read_bytes()))
quote = lambda text: '"'+text.replace('"', '""')+'"'

class EmbedderWorkflowTests(base.PublicCatalogRuntimeTests):
    for name in tuple(n for n in dir(base.PublicCatalogRuntimeTests) if n.startswith('test_')):
        locals()[name] = None

def workflow(fixture):
    def run(self):
        raw = fixture['sourceText'].encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), fixture['sha256'])
        revised,missing = named_revision(fixture)
        self.assertTrue(missing)
        source = json.loads(revised.content); module = source['modules'][0]
        document = source['id']; module_id = module['id']
        elements = {e['id']: e for e in module['elements']}
        records = [e for e in module['elements'] if e['kind']=='record']
        documents = (revised,)
        self.install(); c, h, a, t = self.consumer()
        registered = a.accept_in_transaction(t, a.prepare_catalog(documents), request_key='real-schema')
        self.assertIsInstance(registered, Ok, repr(registered)+' '+str(h._custody.last_attempt.error))
        view = a.catalog_view_in_transaction(t, a.catalog_view_request()).value.view
        references = {d.reference.authored_identity: d.reference for d in view.definitions if d.reference.kind=='type'}
        h.detach(); c.commit()
        for role in ('embedder_reader', 'embedder_writer'):
            self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} NOLOGIN').format(psycopg.sql.Identifier(role)))
            self.addCleanup(self.admin.execute, psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        from truss import adopt_psycopg_host, create_reference_assembly, CatalogRuntimeConfiguration
        self.admin.execute('BEGIN'); host = adopt_psycopg_host(self.admin)
        tx = host.adopt_transaction().value
        assembly = create_reference_assembly(CatalogRuntimeConfiguration(), host).value
        self.assertIsInstance(assembly.configure_module_access_in_transaction(tx,
            (ModuleAccessGrant(document, module_id, 'embedder_reader', 'embedder_writer'),)), Ok)
        host.detach(); self.admin.commit()
        self.admin.execute('GRANT embedder_writer TO consumer WITH SET FALSE')
        self.admin.execute(psycopg.sql.SQL('REVOKE {} FROM consumer').format(psycopg.sql.Identifier(self.installation.registrar_role)))
        c, h, a, t = self.consumer()
        def apply(operations):
            context = a.group_context_in_transaction(t).value
            result = a.apply_in_transaction(t, context.input(tuple(operations), MapValue(entries=())), RequestNone(), documents=documents)
            self.assertIsInstance(result, Ok, repr(result)+' '+str(h._custody.last_attempt.error))
            self.assertIsInstance(result.value, GroupSuccess, repr(result))
            return result.value.response.semantic.results
        def values(record, suffix=''):
            return tuple(AuthoredValue(name=field.get('name', field['id']), value=TextValue(kind=field['scalarType'],
                text=('1.25' if field['scalarType']=='decimal' else '1' if field['scalarType']=='integer' else field['id']+suffix)))
                for member in record['members'] for field in (elements[member['element']],) if field['nullability']=='required')
        creates = [CreateObject(type_definition_pin=references[r['id']].definition_pin, values=values(r), ownership=RootlessOwnership(), alias=r['id']) for r in records]
        for relation in module.get('relationships', []):
            pin = a.get_relationship_reference_in_transaction(t, document_id=document, module_id=module_id, relationship_id=relation['id']).value.definition_pin
            creates.append(CreateEdge(relationship_definition_pin=pin, source=AliasObjectReference(alias=relation['source'][0]['element']),
                target=AliasObjectReference(alias=relation['target'][0]['element']), values=(), order_key=NullOrderKey()))
        results = apply(creates)
        identities = {record['id']: result.identity for record, result in zip(records, results)}
        first = records[0]
        apply(CreateObject(type_definition_pin=references[first['id']].definition_pin, values=values(first, '-'+str(i)),
            ownership=RootlessOwnership(), alias='list-'+str(i)) for i in range(50))
        h.detach(); c.commit(); c, h, a, t = self.consumer()
        for record in records:
            with self.subTest(record=record['id']):
                qualified = quote(module.get('namespace', module_id))+'.'+quote(record.get('name', record['id']))
                key_field = elements[record['keys'][0]['fields'][0]['element']]
                sql = 'SELECT x.* FROM '+qualified+' x ORDER BY x.'+quote(key_field.get('name', key_field['id']))+' LIMIT 51'
                selected = a.query_in_transaction(t, sql=sql, document_ids=(document,), parameters=None, maximum_rows=100, read_profile='complete-entity')
                self.assertIsInstance(selected, Ok, repr(selected)+' '+str(h._custody.last_attempt.error))
                self.assertIsInstance(selected.value, QueryRows, repr(selected.value))
                self.assertEqual(len(selected.value.rows), 51 if record is first else 1)
                self.assertTrue({'_version', '_created_by', '_updated_by'}.issubset(selected.value.columns))
                identity = identities[record['id']]
                opened = a.get_object_in_transaction(t, document_id=document, module_id=module_id, record_id=record['id'], object_id=int(identity.id))
                self.assertIsInstance(opened, Ok); self.assertIsInstance(opened.value, ObjectFound)
                field = next((elements[m['element']] for m in record['members'] if elements[m['element']]['scalarType']=='string' and elements[m['element']]['id']!=key_field['id']), key_field)
                changed = AuthoredValue(name=field.get('name', field['id']), value=TextValue(kind='string', text='modified-'+record['id']))
                apply((UpdateObject(target=StoredObjectReference(identity=identity), set=(changed,), unset=()),))
                # Updated attribution must also survive complete entity projection.
                selected = a.query_in_transaction(t, sql=sql, document_ids=(document,), maximum_rows=100, read_profile='complete-entity')
                self.assertIsInstance(selected, Ok, repr(selected)+' '+str(h._custody.last_attempt.error)); self.assertIsInstance(selected.value, QueryRows, repr(selected.value))
        # The host's repeated whole-entity relationship aliases are explicit refusals.
        relation = module.get('relationships', [None])[0]
        if relation:
            record = elements[relation['source'][0]['element']]
            sql = 'SELECT x.*, RELATED_KEYS(x.'+quote(relation.get('name', relation['id']))+',100) AS '+quote(relation.get('name', relation['id']))+' FROM '+quote(module.get('namespace', module_id))+'.'+quote(record.get('name', record['id']))+' x LIMIT 51'
            refused = a.query_in_transaction(t, sql=sql, document_ids=(document,), maximum_rows=100, read_profile='complete-entity')
            self.assertIsInstance(refused, Ok); self.assertIsInstance(refused.value, QueryRefused)
            self.assertIn('WFT-OUTPUT-NAME', [d.code for d in refused.value.diagnostics])
        h.detach(); c.commit(); c, h, a, t = self.consumer()
        for record in records:
            opened = a.get_object_in_transaction(t, document_id=document, module_id=module_id, record_id=record['id'], object_id=int(identities[record['id']].id))
            self.assertIsInstance(opened, Ok); self.assertEqual(opened.value.object.version, 2)
        h.detach(); c.rollback()
    return run

for fixture in CORPUS['documents']:
    setattr(EmbedderWorkflowTests, 'test_'+fixture['sample'], workflow(fixture))
