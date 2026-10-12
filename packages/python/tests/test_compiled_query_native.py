"""Basic public registration → writes → Weft queries on real PostgreSQL18."""
from truss import Ok,QueryRows,QueryRefused,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.capabilities import CapabilityAvailable
from truss.groups import GroupSuccess
import test_object_mutations_native as mutation_tests

class CompiledQueryTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_public_mutations_filter_count_complete_record_and_readonly_query(self):
        def name_records(source):
            for element in source['modules'][0]['elements']:
                if element['kind']=='record':element['name']=element['id']
        connection,host,assembly,tx=self.ready(name_records)
        created,_,_=self.run_group(assembly,tx,(self.create('one',alias='first'),self.create('two',alias='second'),self.create('three',alias='third',record='B')))
        self.assertIsInstance(created,GroupSuccess)
        selected=assembly.compiled_execution(assembly.compiled_selection)
        self.assertIsInstance(selected,CapabilityAvailable)
        query=selected.capability
        filtered=query.query_in_transaction(tx,sql='SELECT a."A-label" AS label FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        if not isinstance(filtered,Ok) or not isinstance(filtered.value,QueryRows):
            self.fail(repr(filtered)+' '+repr(host._custody.last_attempt.error))
        self.assertEqual(filtered.value.columns,('label',));self.assertEqual(filtered.value.rows,(('one',),))
        counted=query.query_in_transaction(tx,sql='SELECT COUNT(*) AS total FROM "A" a',document_ids=('adoc',))
        self.assertEqual(counted.value.rows,((2,),))
        joined=query.query_in_transaction(tx,sql='SELECT b."B-label" AS other FROM "A" a JOIN "B" b ON a."A-value" = b."B-value" WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        self.assertIsInstance(joined.value,QueryRows);self.assertEqual(joined.value.rows,(('three',),))
        complete=query.query_in_transaction(tx,sql='SELECT a.* FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        self.assertIsInstance(complete.value,QueryRows)
        self.assertEqual(dict(zip(complete.value.columns,complete.value.rows[0],strict=True)),{'A-label':'one','A-value':'value'})
        self.assertFalse(self.admin.execute("SELECT has_table_privilege('consumer','truss.object','SELECT')").fetchone()[0])
        host.detach();connection.commit()
        connection.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000')
        host=adopt_psycopg_host(connection);adopted=host.adopt_transaction(access_mode='read_only')
        self.assertIsInstance(adopted,Ok);tx=adopted.value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        counted=query.query_in_transaction(tx,sql='SELECT COUNT(*) AS total FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(counted,Ok);self.assertEqual(counted.value.rows,((2,),))
        self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0])
        refused=query.query_in_transaction(tx,sql='SELECT COUNT(*) AS total FROM "A" a',document_ids=('zdoc',))
        self.assertIsInstance(refused,Ok);self.assertIsInstance(refused.value,QueryRefused);self.assertEqual(refused.value.code,'unauthorized')

    def test_boolean_and_optional_values_remain_logical(self):
        from dataclasses import replace
        from truss import QueryAbsent
        from truss.contracts import BooleanValue,NullValue,TextValue
        from truss.groups import AuthoredValue
        def add_fields(source):
            module=source['modules'][0]
            for element in module['elements']:
                if element['kind']=='record':element['name']=element['id']
                if element['id']=='A':element['members'] += [{'module':'m','element':'A-active'},{'module':'m','element':'A-note'}]
            module['elements'] += [dict(id='A-active',name='active',kind='field',scalarType='boolean',nullability='required',cardinality='one',extensions={}),
                                   dict(id='A-note',name='note',kind='field',scalarType='string',nullability='absent-allowed',cardinality='one',extensions={})]
        connection,host,assembly,tx=self.ready(add_fields)
        operations=[]
        for label,note in [('absent',None),('null',NullValue()),('empty',TextValue(kind='string',text=''))]:
            created=self.create(label,alias=label)
            values=created.values+(AuthoredValue(name='active',value=BooleanValue(value=True)),)
            if note is not None:values+=(AuthoredValue(name='note',value=note),)
            operations.append(replace(created,values=values))
        self.assertIsInstance(self.run_group(assembly,tx,tuple(operations))[0],GroupSuccess)
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        result=query.query_in_transaction(tx,sql='SELECT a."A-label" AS label,a.active AS active,a.note AS note FROM "A" a WHERE a.active = :active ORDER BY a."A-label"',document_ids=('adoc',),parameters={'active':True})
        if not isinstance(result,Ok) or not isinstance(result.value,QueryRows):self.fail(repr(result)+' '+repr(host._custody.last_attempt.error))
        self.assertEqual(result.value.rows,(('absent',True,QueryAbsent()),('empty',True,''),('null',True,None)))
