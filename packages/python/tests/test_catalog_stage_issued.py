"""Native issued staging component; fixture artifacts do not grant authority."""
import json
import unittest
from test_catalog_staging import CatalogNativeFixture, ROOT


class NativeIssuedCatalogStageTests(CatalogNativeFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c = cls.Connection(**cls.kwargs)
        try:
            c.run((ROOT/'packages/postgresql/native/issued-operation-admission/operation-admission.sql').read_text())
            c.run((ROOT/'packages/postgresql/native/catalog-stage-issued.sql').read_text())
        finally:
            c.close()

    def setUp(self):
        super().setUp()
        self.connection.run('ROLLBACK')
        self.connection.run('BEGIN')

    def invoke(self, declarations=None):
        p = self.prepared
        declarations = p.declarations_bytes if declarations is None else declarations
        return self.connection.run("""SELECT * FROM truss.runtime_stage_catalog_issued(
          0,decode('01','hex'),decode(:input,'hex'),decode(:candidate,'hex'),
          decode('05','hex'),decode('06','hex'),decode(:documents,'hex'),
          decode(:declarations,'hex'),convert_to('{}','UTF8'))""",
          input=p.input_bytes.hex(), candidate=p.declarations_bytes.hex(),
          documents=p.archive_documents_bytes.hex(), declarations=declarations.hex())

    def test_original_prestate_staging_and_native_result(self):
        rows = self.invoke()
        self.assertEqual(len(rows), 1)
        writer, ordinal, context, result_hex = rows[0]
        result = json.loads(bytes.fromhex(result_hex))
        self.assertEqual((result['writerXid'], result['ordinal']), (writer, ordinal))
        self.assertEqual(result['counts']['types_added'], '1')
        self.assertEqual(result['counts']['properties_added'], '1')
        self.assertFalse(result['accepted'])
        self.assertEqual(self.connection.run('SELECT home FROM truss.prop_def'), [['json']])
        self.assertEqual(self.connection.run('SELECT rev FROM truss.schema_head'), [[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.catalog_acceptance_report'), [[0]])
        self.assertEqual(json.loads(bytes.fromhex(context))['xid'], writer)

    def test_substituted_plan_refuses_and_preserves_host_work(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run('CREATE TEMP TABLE catalog_host(value text)')
        self.connection.run("INSERT INTO catalog_host VALUES('preserve')")
        self.connection.run('SAVEPOINT stage')
        with self.assertRaises(DatabaseError):
            self.invoke(b'[]')
        self.connection.run('ROLLBACK TO SAVEPOINT stage')
        self.assertEqual(self.connection.run('SELECT value FROM catalog_host'), [['preserve']])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'), [[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.type_def'), [[0]])

    def test_commit_barrier_remains_closed(self):
        from pg8000.exceptions import DatabaseError
        self.invoke()
        with self.assertRaises(DatabaseError) as raised:
            self.connection.run('COMMIT')
        self.assertEqual(raised.exception.args[0]['C'], '55000')

    def test_real_consumer_record_and_key_inventory(self):
        from test_preparation import prepare
        from truss import CatalogDocument
        original=(ROOT/'packages/python/tests/fixtures/security-association-core.json').read_bytes()
        self.prepared=prepare((CatalogDocument('domain','schema-natural-1',original),))
        result=json.loads(bytes.fromhex(self.invoke()[0][3]))
        self.assertEqual(result['counts']['types_added'],'5')
        self.assertEqual(result['counts']['properties_added'],'9')
        self.assertEqual(result['counts']['keys_added'],'5')
        self.assertEqual(len(result['inventory']),19)

    def test_multiple_documents_keep_qualified_ids_and_original_order(self):
        from test_preparation import prepare
        from test_catalog_staging import native_document
        self.prepared=prepare((native_document('first'),native_document('second')))
        result=json.loads(bytes.fromhex(self.invoke()[0][3]))
        self.assertEqual([d['doc_id'] for d in result['documents']],['first','second'])
        self.assertEqual([d['ord'] for d in result['documents']],['0','1'])
        self.assertEqual(result['counts']['types_added'],'2')
        self.assertEqual(result['counts']['properties_added'],'2')
        self.assertEqual({i['identity'][1] for i in result['inventory'] if i['family']=='type'},
                         {'first','second'})

    def test_late_failure_contained_by_caller_savepoint(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run("""CREATE FUNCTION truss.fixture_late_stage_refuse() RETURNS trigger
          LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'late property failure'; END $$;
          CREATE TRIGGER fixture_late_stage AFTER INSERT ON truss.prop_def FOR EACH ROW
          EXECUTE FUNCTION truss.fixture_late_stage_refuse()""")
        self.connection.run('CREATE TEMP TABLE catalog_host(value text)')
        self.connection.run("INSERT INTO catalog_host VALUES('preserve')")
        self.connection.run('SAVEPOINT stage')
        with self.assertRaises(DatabaseError):self.invoke()
        self.connection.run('ROLLBACK TO SAVEPOINT stage')
        self.assertEqual(self.connection.run('SELECT value FROM catalog_host'),[['preserve']])
        for name in ('schema_doc','type_def','prop_def','row_home_operation'):
            self.assertEqual(self.connection.run('SELECT count(*) FROM truss.'+name),[[0]])

    def test_original_row_substitution_at_same_generation_refuses(self):
        from pg8000.exceptions import DatabaseError
        self.connection.run("""CREATE FUNCTION truss.fixture_substitute_stage() RETURNS trigger
          LANGUAGE plpgsql AS $$ BEGIN NEW.original_group_custody_bytes:='changed'::bytea; RETURN NEW; END $$;
          CREATE TRIGGER fixture_substitute_stage BEFORE INSERT ON truss.row_home_operation
          FOR EACH ROW EXECUTE FUNCTION truss.fixture_substitute_stage()""")
        self.connection.run('SAVEPOINT stage')
        with self.assertRaises(DatabaseError) as caught:self.invoke()
        self.assertEqual(caught.exception.args[0]['C'],'55000')
        self.connection.run('ROLLBACK TO SAVEPOINT stage')
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.row_home_operation'),[[0]])
        self.assertEqual(self.connection.run('SELECT count(*) FROM truss.schema_doc'),[[0]])

    def test_key_and_relationship_allocation_ignore_authored_order(self):
        from test_preparation import prepare
        from truss import CatalogDocument
        field=lambda name: {'id':name,'kind':'field','name':name,'scalarType':'string',
            'nullability':'required','cardinality':'one','extensions':{}}
        record=lambda name: {'id':name,'kind':'record','members':[
            {'module':'m','element':name+suffix} for suffix in ('Label','Tag')],
            'keys':[{'id':key,'name':key,'primary':key=='a',
                     'fields':[{'module':'m','element':name+('Label' if key=='a' else 'Tag')}]} for key in ('z','a')],
            'extensions':{}}
        relationship=lambda name: {'id':name,'name':name,'source':[{'module':'m','element':'A'}],
            'target':[{'module':'m','element':'B','key':'a'}],
            'sourceMultiplicity':{'min':0,'max':1},'targetMultiplicity':{'min':0,'max':2},
            'targetLifecycle':'independent','directed':True}
        source={'umf':'0.7.0','id':'ordered','vocabularies':{},'extensions':{},'modules':[{
            'id':'m','namespace':'m','elements':[record('A'),field('ALabel'),field('ATag'),
                                              record('B'),field('BLabel'),field('BTag')],
            'relationships':[relationship('z'),relationship('a')]}]}
        mappings=[]
        for reverse in (False,True):
            if reverse:
                source['modules'][0]['relationships'].reverse()
                for element in source['modules'][0]['elements']:
                    if element['kind']=='record':element['keys'].reverse()
            self.prepared=prepare((CatalogDocument('ordered','r1',json.dumps(source).encode()),))
            self.connection.run('SAVEPOINT stage')
            result=json.loads(bytes.fromhex(self.invoke()[0][3]))
            self.assertEqual(result['counts']['relationships_added'],'2')
            mappings.append(self.connection.run('SELECT key_id,key_num::text FROM truss.key_def ORDER BY type_id,key_id')+
                self.connection.run('SELECT rel_id,rel_type_id::text FROM truss.rel_def ORDER BY rel_id'))
            self.connection.run('ROLLBACK TO SAVEPOINT stage')
            self.connection.run('RELEASE SAVEPOINT stage')
        self.assertEqual(mappings[0],mappings[1])
