# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic public registration → writes → Weft queries on real PostgreSQL18."""
from truss import Ok,QueryRows,QueryRefused,adopt_psycopg_host,create_reference_assembly,CatalogRuntimeConfiguration
from truss.capabilities import CapabilityAvailable
from truss.groups import GroupSuccess
import test_object_mutations_native as mutation_tests

class CompiledQueryTests(mutation_tests.ObjectMutationTests):
    for _name in tuple(n for n in dir(mutation_tests.ObjectMutationTests) if n.startswith('test_')):
        locals()[_name]=None

    def test_combined_catalog_source_query_uses_one_operation_and_current_visibility(self):
        from truss import QueryCatalogRead,ReaderCatalogSnapshot,ReaderCatalogUnchanged
        from hashlib import sha256
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        host.detach();connection.rollback();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        self.consumer_connections.append((connection,host))
        adopted=host.adopt_transaction(access_mode='read_only');self.assertIsInstance(adopted,Ok,repr(adopted))
        tx=adopted.value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        sql='SELECT COUNT(*) AS total FROM "A" a'
        first=assembly.query_with_catalog_in_transaction(tx,sql=sql,document_ids=('adoc',))
        self.assertIsInstance(first,Ok,repr(first));self.assertIsInstance(first.value,QueryCatalogRead)
        self.assertIsInstance(first.value.catalog,ReaderCatalogSnapshot)
        self.assertEqual(first.value.result.rows,((0,),))
        self.assertIsNotNone(first.value.result.as_of)
        self.assertEqual(first.value.documents[0].content,self.documents[0].content)
        self.assertEqual(first.value.documents[0].sha256,sha256(self.documents[0].content).hexdigest())
        self.assertEqual(first.value.result.catalog_revision,first.value.catalog.catalog.catalog_revision)
        second=assembly.query_with_catalog_in_transaction(tx,sql=sql,document_ids=('adoc',),catalog_validator=first.value.catalog.validator)
        self.assertIsInstance(second.value.catalog,ReaderCatalogUnchanged)
        self.assertEqual(second.value.documents,first.value.documents)
        self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0])
        self.admin.execute('REVOKE group_writer FROM consumer')
        denied=assembly.query_with_catalog_in_transaction(tx,sql=sql,document_ids=('adoc',),catalog_validator=first.value.catalog.validator)
        self.assertEqual(denied,Ok(QueryRefused(code='unauthorized')))


    def test_repeated_query_compiles_once_but_revoked_reader_still_refuses(self):
        from unittest.mock import Mock,patch
        from truss._query_runtime import compiler
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        self.assertIsInstance(self.run_group(assembly,tx,(self.create(),),'cache-create')[0],GroupSuccess)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        original=compiler();self.assertIsNotNone(original)
        counted=Mock(wraps=original)
        sql='SELECT a."A-label" FROM "A" a WHERE a."A-label"=:label'
        with patch('truss._query_runtime.compiler',return_value=counted):
            for _ in range(3):
                result=assembly.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters={'label':'one'})
                self.assertIsInstance(result,Ok,repr(result))
                self.assertEqual(result.value.rows,(('one',),))
            self.assertEqual(counted.call_count,1)
            other=assembly.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters={'label':'absent'})
            self.assertEqual(other.value.rows,())
            self.assertEqual(counted.call_count,2)
            self.admin.execute('REVOKE group_writer FROM consumer')
            denied=assembly.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters={'label':'one'})
            self.assertEqual(denied,Ok(QueryRefused(code='unauthorized')))

    def test_complete_entity_wildcard_names_include_relationship_outputs(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        duplicate=assembly.query_in_transaction(tx,sql='SELECT a.*, RELATED_KEYS(a."A-B",1) AS "A-B" FROM "A" a',document_ids=('adoc',),read_profile='complete-entity')
        self.assertIsInstance(duplicate.value,QueryRefused,repr(duplicate))
        self.assertIn('WFT-OUTPUT-NAME',[d.code for d in duplicate.value.diagnostics])
        distinct=assembly.query_in_transaction(tx,sql='SELECT a.*, RELATED_KEYS(a."A-B",1) AS explicit_keys FROM "A" a',document_ids=('adoc',),read_profile='complete-entity')
        self.assertIsInstance(distinct.value,QueryRows,repr(distinct))
        self.assertIn('A-B',distinct.value.columns)
        self.assertIn('explicit_keys',distinct.value.columns)

    def test_complete_entity_materializes_facts_and_retains_nested_proofs(self):
        import psycopg
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        created=self.run_group(assembly,tx,(self.create(label='one',alias='one'),self.create(label='two',alias='two')),'facts-create')[0]
        self.assertIsInstance(created,GroupSuccess)
        host.detach();connection.commit();connection,host,assembly,tx=self.consumer()
        originals={}
        helpers=('query_object_attribution','query_object_times','query_object_load_id')
        try:
            for index,name in enumerate(helpers):
                signature=f'truss.{name}(jsonb,int,bigint)'
                original=self.admin.execute('SELECT pg_get_functiondef(%s::regprocedure)',(signature,)).fetchone()[0]
                originals[name]=original
                sequence=f'public.facts_calls_{index}'
                self.admin.execute('CREATE SEQUENCE '+sequence)
                self.addCleanup(self.admin.execute,'DROP SEQUENCE '+sequence)
                self.admin.execute(psycopg.sql.SQL('GRANT USAGE ON SEQUENCE {} TO {}').format(psycopg.sql.Identifier('public',f'facts_calls_{index}'),psycopg.sql.Identifier(self.installation.owner_role)))
                self.admin.execute(original.replace('BEGIN',f"BEGIN\n PERFORM pg_catalog.nextval('{sequence}'::regclass);",1))
            result=assembly.query_in_transaction(tx,sql='SELECT a.* FROM "A" a WHERE a."A-label"=:label',document_ids=('adoc',),parameters={'label':'one'},read_profile='complete-entity')
            self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,QueryRows,repr(result))
            self.assertEqual(len(result.value.rows),1)
            values=dict(zip(result.value.columns,result.value.rows[0],strict=True))
            self.assertEqual(values['A-label'],'one');self.assertEqual(values['_version'],1)
            self.assertEqual(values['_created_by'],'consumer');self.assertEqual(values['_updated_by'],'consumer')
            for index in range(3):
                # The time/load helpers each retain their own original
                # attribution proof: one direct + two nested calls, not eight
                # repeated projection evaluations in the old emitted SQL.
                expected=3 if index==0 else 1
                self.assertEqual(self.admin.execute(f'SELECT last_value,is_called FROM public.facts_calls_{index}').fetchone(),(expected,True),helpers[index])
        finally:
            for source in originals.values():self.admin.execute(source)

    def test_indexed_equality_precedes_residual_limit_with_legacy_count_page_bounds(self):
        connection,host,assembly,tx=self.ready(document_ids=('adoc',))
        created=self.run_group(assembly,tx,(self.create(label='first',alias='first'),self.create(label='second',alias='second')),'source-bound-create')[0]
        self.assertIsInstance(created,GroupSuccess)
        for sql,profile in (
                ('SELECT a."A-label" FROM "A" a WHERE a."A-label"=:label LIMIT 1',None),
                ('SELECT COUNT(*) AS total FROM "A" a',None),
                ('SELECT a.* FROM "A" a ORDER BY a."A-value",a."A-label" LIMIT 1','entity-page')):
            with self.subTest(sql=sql):
                params={'label':'first'} if ':label' in sql else None
                result=assembly.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters=params,maximum_scan_rows=1,read_profile=profile)
                if ':label' in sql:
                    self.assertIsInstance(result,Ok,repr(result));self.assertIsInstance(result.value,QueryRows,repr(result));self.assertEqual(result.value.rows,(('first',),))
                else:self.assertEqual(result,Ok(QueryRefused(code='limits')))


    def test_wide_complete_entity_preserves_fields_with_explicit_byte_budget(self):
        from dataclasses import replace
        from truss.contracts import TextValue
        from truss.groups import AuthoredValue
        names=tuple('wide'+str(i) for i in range(126))
        def wide(source):
            module=source['modules'][0]
            for record in module['elements']:
                if record['kind']=='record':record['name']=record['id']
                if record['id']=='A':record['members'] += [{'module':'m','element':name} for name in names]
            module['elements'] += [dict(id=name,name=name,kind='field',scalarType='string',nullability='required',cardinality='one',extensions={}) for name in names]
        c,h,a,t=self.ready(wide,document_ids=('adoc',))
        for first in range(0,100,20):
            operations=tuple(replace(self.create(label=f'wide-{i:03}',value=f'value-{i}',alias=f'row-{i}'),
                values=self.create(label=f'wide-{i:03}',value=f'value-{i}').values+tuple(
                    AuthoredValue(name=name,value=TextValue(kind='string',text=f'{name}/{i}/'+'x'*80)) for name in names))
                for i in range(first,first+20))
            created,_,_=self.run_group(a,t,operations)
            self.assertIsInstance(created,GroupSuccess,repr(created)+' '+str(h._custody.last_attempt.error))
            h.detach();c.commit();c,h,a,t=self.consumer()
        sql='SELECT x.* FROM "A" x ORDER BY x."A-label" LIMIT 51'
        default=a.query_in_transaction(t,sql=sql,document_ids=('adoc',),maximum_rows=100,read_profile='complete-entity')
        self.assertIsInstance(default,Ok,repr(default));self.assertIsInstance(default.value,QueryRefused)
        self.assertEqual(default.value.code,'limits')
        selected=a.query_in_transaction(t,sql=sql,document_ids=('adoc',),maximum_rows=100,
            maximum_bytes=16777216,read_profile='complete-entity')
        self.assertIsInstance(selected,Ok,repr(selected)+' '+str(h._custody.last_attempt.error))
        self.assertIsInstance(selected.value,QueryRows,repr(selected.value))
        self.assertEqual(len(selected.value.rows),51)
        self.assertTrue({'_version','_created_by','_updated_by'}.issubset(selected.value.columns))
        self.assertTrue(set(names).issubset(selected.value.columns))
        for i,row in enumerate(selected.value.rows):
            values=dict(zip(selected.value.columns,row,strict=True))
            self.assertEqual(values['A-label'],f'wide-{i:03}')
            for name in names:self.assertEqual(values[name],f'{name}/{i}/'+'x'*80)

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

    def test_supported_projection_on_mixed_scalar_catalog(self):
        from dataclasses import replace
        from truss import ObjectFound
        from truss.contracts import TextValue,NullValue
        from truss import QueryAbsent
        from truss.groups import AuthoredValue
        def add_fields(source):
            module=source['modules'][0]
            for element in module['elements']:
                if element['kind']=='record':element['name']=element['id']
                if element['id']=='A':element['members'] += [{'module':'m','element':'A-'+name} for name in ('at','blob','optional_at','optional_blob')]
            for name,family in [('at','timestamp'),('blob','binary'),('optional_at','timestamp'),('optional_blob','binary')]:
                module['elements'].append(dict(id='A-'+name,name=name,kind='field',scalarType=family,
                    nullability='absent-allowed' if name.startswith('optional_') else 'required',cardinality='one',extensions={}))
        connection,host,assembly,tx=self.ready(add_fields)
        timestamp=TextValue(kind='timestamp',text='2024-02-29t23:59:59.12345678901234567890-00:00')
        binary=TextValue(kind='binary',text='AP8=')
        original=self.create(label='one',alias='first')
        original=replace(original,values=original.values+(AuthoredValue(name='at',value=timestamp),AuthoredValue(name='blob',value=binary)))
        original=replace(original,values=original.values+(AuthoredValue(name='optional_at',value=timestamp),AuthoredValue(name='optional_blob',value=binary)))
        null=replace(self.create(label='null',alias='null'),values=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='null')),AuthoredValue(name='A-value',value=TextValue(kind='string',text='value')),AuthoredValue(name='at',value=timestamp),AuthoredValue(name='blob',value=binary),AuthoredValue(name='optional_at',value=NullValue()),AuthoredValue(name='optional_blob',value=NullValue())))
        absent=replace(self.create(label='absent',alias='absent'),values=tuple(v for v in null.values if not v.name.startswith('optional_') and v.name!='A-label')+(AuthoredValue(name='A-label',value=TextValue(kind='string',text='absent')),))
        created,_,_=self.run_group(assembly,tx,(original,null,absent,self.create(label='other',record='B',alias='other')))
        self.assertIsInstance(created,GroupSuccess)
        identity=created.response.semantic.results[0].identity
        host.detach();connection.commit()
        connection.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000')
        host=adopt_psycopg_host(connection);self.addCleanup(host.detach)
        tx=host.adopt_transaction(access_mode='read_only').value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        read=assembly.get_object_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',object_id=int(identity.id))
        self.assertIsInstance(read.value,ObjectFound)
        self.assertEqual(dict(read.value.object.values)['at'],timestamp)
        self.assertEqual(dict(read.value.object.values)['blob'],binary)
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        projected=query.query_in_transaction(tx,sql='SELECT a."A-label" FROM "A" a WHERE a."A-label" = :label',
            document_ids=('adoc',),parameters={'label':'one'})
        if not isinstance(projected,Ok) or not isinstance(projected.value,QueryRows):self.fail(repr(projected)+' '+repr(host._custody.last_attempt.error))
        self.assertEqual(projected.value.rows,(('one',),))
        counted=query.query_in_transaction(tx,sql='SELECT COUNT(*) FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(counted.value,QueryRows);self.assertEqual(counted.value.rows,((3,),))
        unrelated=query.query_in_transaction(tx,sql='SELECT b."B-label" FROM "B" b',document_ids=('adoc',))
        self.assertIsInstance(unrelated.value,QueryRows);self.assertEqual(unrelated.value.rows,(('other',),))
        exact=query.query_in_transaction(tx,sql='SELECT a.at, a.blob FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        self.assertIsInstance(exact.value,QueryRows);self.assertEqual(exact.value.rows,((timestamp,binary),))
        entity=query.query_in_transaction(tx,sql='SELECT a.* FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':'one'})
        self.assertIsInstance(entity.value,QueryRows)
        self.assertEqual(dict(zip(entity.value.columns,entity.value.rows[0],strict=True)),{'A-label':'one','A-value':'value','at':timestamp,'blob':binary,'optional_at':timestamp,'optional_blob':binary})
        optional=query.query_in_transaction(tx,sql='SELECT a.optional_at, a.optional_blob FROM "A" a ORDER BY a."A-label"',document_ids=('adoc',))
        self.assertIsInstance(optional.value,QueryRows)
        self.assertEqual(optional.value.rows,((QueryAbsent(),QueryAbsent()),(None,None),(timestamp,binary)))
        refusals=(
            ('SELECT a.at FROM "A" a WHERE a.at = :at','invalid_query'),
            ('SELECT a.blob FROM "A" a ORDER BY a.blob ASC','unsupported_query'),
            ('SELECT a.at, COUNT(*) FROM "A" a GROUP BY a.at','unsupported_query'),
        )
        for sql,expected_code in refusals:
            refused=query.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters={'at':timestamp.text} if ':at' in sql else {})
            self.assertIsInstance(refused.value,QueryRefused);self.assertEqual(refused.value.code,expected_code)
        self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0])

    def test_grouped_count_preserves_string_boolean_bags(self):
        from dataclasses import replace
        from truss.contracts import BooleanValue
        from truss.groups import AuthoredValue
        def add_fields(source):
            module=source['modules'][0]
            for element in module['elements']:
                if element['kind']=='record':element['name']=element['id']
                if element['id']=='A':element['members'].append({'module':'m','element':'A-active'})
            module['elements'].append(dict(id='A-active',name='active',kind='field',scalarType='boolean',
                nullability='required',cardinality='one',extensions={}))
        connection,host,assembly,tx=self.ready(add_fields)
        operations=[]
        for label,value,active in [('one','shared',True),('two','shared',True),('three','shared',False),('four','other',True)]:
            created=self.create(label=label,value=value,alias=label)
            operations.append(replace(created,values=created.values+(AuthoredValue(name='active',value=BooleanValue(value=active)),)))
        self.assertIsInstance(self.run_group(assembly,tx,tuple(operations))[0],GroupSuccess)
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        result=query.query_in_transaction(tx,
            sql='SELECT a."A-value" AS category,a.active,COUNT(*) AS total FROM "A" a '
                'GROUP BY a."A-value",a.active ORDER BY a."A-value",a.active LIMIT 10',
            document_ids=('adoc',),read_profile='count-summary')
        if not isinstance(result,Ok) or not isinstance(result.value,QueryRows):self.fail(repr(result)+' '+repr(host._custody.last_attempt.error))
        self.assertEqual(result.value.rows,(('other',True,1),('shared',False,1),('shared',True,2)))

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
        refused=query.query_in_transaction(tx,sql='SELECT a.note,COUNT(*) FROM "A" a GROUP BY a.note ORDER BY a.note LIMIT 10',
            document_ids=('adoc',),read_profile='count-summary')
        self.assertIsInstance(refused.value,QueryRefused);self.assertEqual(refused.value.code,'unsupported_query')

    def test_exact_integer_decimal_projection_and_parameters(self):
        from dataclasses import replace
        from decimal import Decimal
        from truss.contracts import TextValue
        from truss.groups import AuthoredValue
        def numeric_fields(source):
            module=source['modules'][0]
            for element in module['elements']:
                if element['kind']=='record':element['name']=element['id']
                if element['id']=='A':element['members'] += [{'module':'m','element':'A-units'},{'module':'m','element':'A-amount'},{'module':'m','element':'A-optional'}]
            module['elements'] += [dict(id='A-units',name='units',kind='field',scalarType='integer',nullability='required',cardinality='one',extensions={}),
                dict(id='A-amount',name='amount',kind='field',scalarType='decimal',nullability='required',cardinality='one',extensions={}),
                dict(id='A-optional',name='optional_amount',kind='field',scalarType='decimal',nullability='absent-allowed',cardinality='one',extensions={})]
        connection,host,assembly,tx=self.ready(numeric_fields)
        integer=900719925474099312345678901234567890
        decimal_token='9007199254740993.1234567890123456789000'
        exponent_token='1.23456789012345678900e-20'
        created=self.create()
        values=created.values+(AuthoredValue(name='units',value=TextValue(kind='integer',text=str(integer))),
            AuthoredValue(name='amount',value=TextValue(kind='decimal',text=decimal_token)),
            AuthoredValue(name='optional_amount',value=TextValue(kind='decimal',text=exponent_token)))
        self.assertIsInstance(self.run_group(assembly,tx,(replace(created,values=values),))[0],GroupSuccess)
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        result=query.query_in_transaction(tx,sql='SELECT a.units,a.amount,a.optional_amount FROM "A" a WHERE a.units = :units AND a.amount = :amount',document_ids=('adoc',),parameters={'units':integer,'amount':Decimal(decimal_token)})
        if not isinstance(result,Ok) or not isinstance(result.value,QueryRows):self.fail(repr(result)+' '+repr(host._custody.last_attempt.error))
        self.assertEqual(result.value.rows,((integer,Decimal(decimal_token),Decimal(exponent_token)),))
        self.assertEqual(result.value.rows[0][1].as_tuple(),Decimal(decimal_token).as_tuple())
        self.assertEqual(result.value.rows[0][2].as_tuple(),Decimal(exponent_token).as_tuple())
        expanded=query.query_in_transaction(tx,sql='SELECT a.* FROM "A" a',document_ids=('adoc',))
        self.assertIsInstance(expanded.value,QueryRows)
        row=dict(zip(expanded.value.columns,expanded.value.rows[0],strict=True))
        self.assertEqual(row['units'],integer);self.assertEqual(row['amount'].as_tuple(),Decimal(decimal_token).as_tuple())
        refused=query.query_in_transaction(tx,sql='SELECT a.amount FROM "A" a WHERE a.amount = :amount',document_ids=('adoc',),parameters={'amount':Decimal('1e-20000')})
        self.assertIsInstance(refused.value,QueryRefused);self.assertEqual(refused.value.code,'native_domain')

        grouped=query.query_in_transaction(tx,sql='SELECT a.amount,COUNT(*) FROM "A" a GROUP BY a.amount ORDER BY a.amount LIMIT 10',
            document_ids=('adoc',),read_profile='count-summary')
        self.assertIsInstance(grouped.value,QueryRefused);self.assertEqual(grouped.value.code,'unsupported_query')

        nonfinite=query.query_in_transaction(tx,sql='SELECT a.amount FROM "A" a WHERE a.amount = :amount',document_ids=('adoc',),parameters={'amount':Decimal('NaN')})
        self.assertIsInstance(nonfinite.value,QueryRefused);self.assertEqual(nonfinite.value.code,'invalid_query')
        expansion=query.query_in_transaction(tx,sql='SELECT a.amount FROM "A" a WHERE a.amount = :amount',document_ids=('adoc',),parameters={'amount':Decimal('1e-100000000')})
        self.assertIsInstance(expansion.value,QueryRefused);self.assertEqual(expansion.value.code,'limits')

    def test_public_links_forward_inverse_bounded_keys_readonly_and_unlink(self):
        from truss import QueryRelatedKeys
        from truss.groups import CreateEdge,AliasObjectReference,NullOrderKey,Delete,StoredObjectReference
        def named_relationship(source):
            for element in source['modules'][0]['elements']:
                if element['kind']=='record':element['name']=element['id']
            source['modules'][0]['relationships'][0]['inverse']='B-A'
        connection,host,assembly,tx=self.ready(named_relationship)
        pin=assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id='A-B').value.definition_pin
        def link(target,alias):
            return CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias='first'),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey(),alias=alias)
        created,_,_=self.run_group(assembly,tx,(self.create('one',alias='first'),self.create('two',alias='second',record='B'),self.create('three',alias='third',record='B'),link('second','edge1'),link('third','edge2')))
        self.assertIsInstance(created,GroupSuccess)
        edge=created.response.semantic.results[3].identity
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        def run(sql,parameters=None):
            result=query.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters={} if parameters is None else parameters)
            if not isinstance(result,Ok) or not isinstance(result.value,QueryRows):self.fail(repr(result)+' '+repr(host._custody.last_attempt.error))
            return result.value
        self.assertEqual(run("SELECT a.\"A-label\" FROM \"A\" a WHERE a.\"A-label\" = 'one'").rows,(('one',),))
        shorthand=query.query_in_transaction(tx,sql='SELECT a."A-label" FROM "A" a WHERE a."A-B" = :key',document_ids=('adoc',),parameters={'key':'two'})
        self.assertIsInstance(shorthand.value,QueryRefused)
        self.assertTrue(any('single-component key' in d.message for d in shorthand.value.diagnostics))
        forward='SELECT a."A-label" FROM "A" a WHERE HAS_RELATED(a."A-B",KEY(:value,:label))'
        self.assertEqual(run(forward,{'value':'value','label':'two'}).rows,(('one',),))
        self.assertEqual(run('SELECT b."B-label" FROM "B" b WHERE HAS_RELATED(b."B-A",KEY(:value,:label)) ORDER BY b."B-label"',{'value':'value','label':'one'}).rows,(('three',),('two',)))
        bounded='SELECT RELATED_KEYS(a."A-B",1) AS related FROM "A" a'
        self.assertEqual(run(bounded).rows,((QueryRelatedKeys(items=(('value','three'),),truncated=True),),))
        related=query.query_in_transaction(tx,sql='SELECT a.* FROM "A" a WHERE HAS_RELATED(a."A-B",KEY(:value,:label)) ORDER BY a."A-value",a."A-label" LIMIT 1',document_ids=('adoc',),parameters={'value':'value','label':'two'},read_profile='related-entity-page')
        self.assertIsInstance(related.value,QueryRows);self.assertEqual(len(related.value.rows),1)
        self.assertEqual(run('SELECT b."B-label",RELATED_KEYS(b."B-A",2) AS related FROM "B" b ORDER BY b."B-label"').rows,(('three',QueryRelatedKeys(items=(('value','one'),),truncated=False)),('two',QueryRelatedKeys(items=(('value','one'),),truncated=False))))
        host.detach();connection.commit();connection.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000')
        host=adopt_psycopg_host(connection);tx=host.adopt_transaction(access_mode='read_only').value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value;query=assembly.compiled_execution(assembly.compiled_selection).capability
        self.assertEqual(run(bounded).rows,((QueryRelatedKeys(items=(('value','three'),),truncated=True),),))
        self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0])
        host.detach();connection.rollback();connection,host,assembly,tx=self.consumer();query=assembly.compiled_execution(assembly.compiled_selection).capability
        deleted,_,_=self.run_group(assembly,tx,(Delete(operation='delete_edge',target=StoredObjectReference(identity=edge)),))
        self.assertIsInstance(deleted,GroupSuccess)
        self.assertEqual(run(forward,{'value':'value','label':'two'}).rows,())
        self.assertEqual(run(bounded).rows,((QueryRelatedKeys(items=(('value','three'),),truncated=False),),))

    def test_authored_composite_key_pages_and_count_profile(self):
        def names(source):
            for element in source['modules'][0]['elements']:
                if element['kind']=='record':element['name']=element['id']
        connection,host,assembly,tx=self.ready(names)
        created,_,_=self.run_group(assembly,tx,tuple(self.create(label,alias=label) for label in ('gamma','alpha','beta')))
        self.assertIsInstance(created,GroupSuccess)
        host.detach();connection.commit();connection.execute('BEGIN READ ONLY;SET LOCAL statement_timeout=10000')
        host=adopt_psycopg_host(connection);tx=host.adopt_transaction(access_mode='read_only').value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        query=assembly.compiled_execution(assembly.compiled_selection).capability
        def page(sql,parameters=None,profile='entity-page'):
            result=query.query_in_transaction(tx,sql=sql,document_ids=('adoc',),parameters={} if parameters is None else parameters,read_profile=profile)
            if not isinstance(result,Ok) or not isinstance(result.value,QueryRows):self.fail(repr(result)+' '+repr(host._custody.last_attempt.error))
            return result.value
        first=page('SELECT a.* FROM "A" a ORDER BY a."A-value",a."A-label" LIMIT 2')
        self.assertEqual(tuple(dict(zip(first.columns,row))['A-label'] for row in first.rows),('alpha','beta'))
        continuation='SELECT a.* FROM "A" a WHERE (a."A-value",a."A-label") > (:value,:label) ORDER BY a."A-value",a."A-label" LIMIT 2'
        second=page(continuation,{'value':'value','label':'beta'})
        self.assertEqual(tuple(dict(zip(second.columns,row))['A-label'] for row in second.rows),('gamma',))
        self.assertEqual(page(continuation,{'value':'value','label':'gamma'}).rows,())
        self.assertEqual(page('SELECT COUNT(*) AS total FROM "A" a',profile='count-summary').rows,((3,),))
        self.assertEqual(first.catalog_revision,second.catalog_revision)
        self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0])

    def test_complete_entity_pending_update_import_and_readonly(self):
        from truss.imports import ImportReported
        from truss.contracts import MapValue,MapEntry,TextValue
        from truss.groups import UpdateObject,StoredObjectReference,AuthoredValue
        def names(source):
            for element in source['modules'][0]['elements']:
                if element['kind']=='record':element['name']=element['id']
        connection,host,assembly,tx=self.ready(names)
        def entity(label):
            result=assembly.query_in_transaction(tx,sql='SELECT a.* FROM "A" a WHERE a."A-label" = :label',document_ids=('adoc',),parameters={'label':label},read_profile='complete-entity')
            if not isinstance(result,Ok) or not isinstance(result.value,QueryRows):self.fail(repr(result)+' '+str(host._custody.last_attempt.error))
            self.assertIsNotNone(result.value.as_of)
            self.assertEqual(result.value.as_of.semantics,'committed-lower-bound')
            self.assertIsNotNone(result.value.as_of.at.utcoffset())
            self.assertEqual(result.value.as_of.caller_xid_assigned,connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0] is not None)
            self.assertEqual(len(result.value.rows),1)
            return dict(zip(result.value.columns,result.value.rows[0],strict=True))
        created,_,_=self.run_group(assembly,tx,(self.create('one'),))
        identity=created.response.semantic.results[0].identity
        first=entity('one');self.assertEqual((first['_version'],first['_created_by'],first['_updated_by'],first['_original_author']),(1,'consumer','consumer',None))
        direct=self.read(assembly,tx,identity).object
        self.assertEqual((first['_created_at'],first['_updated_at']),(direct.created_at,direct.updated_at))
        changed,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='changed')),),unset=()),))
        self.assertIsInstance(changed,GroupSuccess)
        current=entity('changed');self.assertEqual(current['_version'],2)
        direct=self.read(assembly,tx,identity).object
        self.assertEqual((current['_created_at'],current['_updated_at']),(direct.created_at,direct.updated_at))
        self.assertEqual(current['_created_at'],first['_created_at'])
        noop,_,_=self.run_group(assembly,tx,(UpdateObject(target=StoredObjectReference(identity=identity),set=(AuthoredValue(name='A-label',value=TextValue(kind='string',text='changed')),),unset=()),))
        self.assertIsInstance(noop,GroupSuccess)
        self.assertEqual(entity('changed'),current)
        source=MapValue(entries=(MapEntry(key='author',value=TextValue(kind='string',text='historical')),MapEntry(key='at',value=TextValue(kind='string',text='2020-01-01'))))
        record=assembly.object_import_record_in_transaction(tx,document_id='adoc',module_id='m',record_id='A',values=self.create('imported',value='imported').values,source=source).value
        context=assembly.import_context_in_transaction(tx).value
        report=assembly.import_in_transaction(tx,context.input((record,),load_id='entity-import',asserted_origin=MapValue(entries=())),documents=self.documents,bun_executable='/opt/homebrew/bin/bun')
        self.assertIsInstance(report,ImportReported)
        imported=entity('imported');self.assertEqual((imported['_created_by'],imported['_original_author'],imported['_original_at']),('consumer','historical','2020-01-01'))
        host.detach();connection.commit();connection.execute('BEGIN READ ONLY')
        host=adopt_psycopg_host(connection);tx=host.adopt_transaction(access_mode='read_only').value
        assembly=create_reference_assembly(CatalogRuntimeConfiguration(),host).value
        self.assertEqual(entity('changed')['_version'],2)
        self.assertEqual(entity('imported')['_original_author'],'historical')
        host.detach();self.assertIsNone(connection.execute('SELECT pg_current_xact_id_if_assigned()').fetchone()[0]);connection.rollback()
