"""Basic public whole-object import load provenance, pending and committed."""
from truss import Ok,QueryRows,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.contracts import MapValue,MapEntry,TextValue
from truss.imports import ImportReported,ImportCreated
import test_object_mutations_native as mutation_tests

class ImportLoadQueryTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_import_load_and_ordinary_creation_in_public_sql(self):
        def named(source):
            for element in source['modules'][0]['elements']:
                if element['kind']=='record':element['name']=element['id']
        connection,host,assembly,tx=self.ready(named)
        ordinary,_,_=self.run_group(assembly,tx,(self.create(label='ordinary',value='ordinary'),))
        context=assembly.import_context_in_transaction(tx).value
        imported=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',values=self.create(label='imported',value='imported').values,
            source=MapValue(entries=(MapEntry(key='author',value=TextValue(kind='string',text='ann')),)))
        self.assertIsInstance(imported,Ok)
        load='L1:é/ exact load'
        report=assembly.import_in_transaction(tx,context.input((imported.value,),load_id=load,asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(report,ImportReported);self.assertIsInstance(report.report.outcomes[0],ImportCreated)
        def rows():
            result=assembly.query_in_transaction(tx,sql='SELECT a.* FROM "A" a ORDER BY a."A-label"',document_ids=('adoc',),read_profile='complete-entity')
            if not isinstance(result,Ok):self.fail(repr(result)+' '+str(host._custody.last_attempt.error))
            self.assertIsInstance(result.value,QueryRows)
            return [dict(zip(result.value.columns,row,strict=True)) for row in result.value.rows]
        pending=rows();self.assertEqual([r['_load_id'] for r in pending],[load,None])
        self.assertEqual([r['_original_author'] for r in pending],['ann',None])
        self.assertEqual([r['_created_by'] for r in pending],['consumer','consumer'])
        host.detach();connection.commit()
        connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        tx=host.adopt_transaction(access_mode='read_only').value
        self.assertEqual(rows(),pending)
        host.detach();self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);connection.rollback()
