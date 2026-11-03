# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN09/10 authentic installed owner -> generated model -> Truss execution.

No fixture compiler, owner manifest, generated source identity or native
binding is invented. Missing actual enrollments fail; collection is not proof.
"""
from contextlib import contextmanager
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
from hashlib import sha256
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import ClassVar,Annotated
from uuid import uuid4
import psycopg

from truss import Ok,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly
from truss import temporal
from truss.contracts import LocalTimestampValue,NullValue
from truss.groups import StoredObjectReference,GroupSuccess
from truss.query import QueryRefused
from truss._temporal_owner import _inspector
from truss._temporal_compiler import compiler
from truss._temporal_query_execution import _original
from truss._temporal_program_custody import check_shape
import temporal_native_fixture as fixture


def quoted(value):return '"'+value.replace('"','""')+'"'


class TemporalEngineNativeTests(fixture.TemporalNativeFixture):
    def test_actual_sdk_wrapper_preserves_whole_generation_and_inner_program_string(self):
        from umf_access.engine_catalog import EngineRead
        row=self.ready_engine()
        sql='SELECT '+','.join(quoted(element)+' AS '+quoted(name) for module,element,name in row.UMF_FIELDS)+' FROM "A"'
        entry,parameters=self.entry(row,sql)
        # Rewrap authentic compiled bytes with deliberate outer whitespace.
        # SDK custody must retain that exact inner string, not serialize it.
        inner='\n '+entry.originals()+'\n'
        wrapped=EngineRead.from_original(inner,parameters=entry.parameters,result=row)
        original,program=_original(wrapped.artifact_json)
        self.assertEqual(original,inner);self.assertEqual(program,wrapped.artifact())
        owner=compiler();self.assertIsNotNone(owner)
        self.assertEqual(check_shape(owner,original,json.dumps(program['request'],ensure_ascii=False,separators=(',',':')),page=False),program)
        with self.assertRaises(ValueError):_original(wrapped.originals())
        damaged=json.loads(wrapped.artifact_json);damaged['stageOne']={'changed':'generation'}
        with self.assertRaises(ValueError):_original(json.dumps(damaged))
        actual=self.target(wrapped).read(wrapped,parameters);expected=self.target(entry).read(entry,parameters)
        self.assertEqual(len(actual),6);self.assertEqual(len(expected),6);self.assertEqual(actual,expected)
        print('temporal-actual-sdk-wrapper-custody '+json.dumps({'wrapperSha256':sha256(wrapped.artifact_json.encode()).hexdigest(),
            'innerProgramSha256':sha256(inner.encode()).hexdigest(),'nativeReadRows':len(actual),'wholeGenerationRetained':True},sort_keys=True))

    def generated_row(self,record='A'):
        owner,owner_pin=_inspector()
        package='temporal_native_'+uuid4().hex
        generated=owner.generate_python_client({'text':self.document.content.decode(),'package':package})
        self.assertTrue(generated['files'])
        from native_fixture import evidence_directory
        evidence_directory().joinpath(package+'-original-generation.json').write_text(json.dumps({
            'request':{'text':self.document.content.decode(),'package':package},'owner':owner_pin,'response':generated},
            ensure_ascii=True,separators=(',',':'),allow_nan=False)+'\n')
        root=Path(tempfile.mkdtemp(prefix='truss-temporal-generated-'))
        self.addCleanup(shutil.rmtree,root)
        manifest=[]
        for entry in generated['files']:
            path=Path(entry['path']);self.assertFalse(path.is_absolute());self.assertNotIn('..',path.parts)
            self.assertEqual(path.parts[0],package)
            destination=root/path;destination.parent.mkdir(parents=True,exist_ok=True)
            raw=entry['text'].encode();destination.write_bytes(raw)
            manifest.append({'path':entry['path'],'sha256':sha256(raw).hexdigest()})
        sys.path.insert(0,str(root))
        def forget():
            sys.path.remove(str(root))
            for name in tuple(sys.modules):
                if name==package or name.startswith(package+'.'):del sys.modules[name]
        self.addCleanup(forget)
        models=importlib.import_module(package+'.models')
        source=json.loads(self.document.content)
        declared=next(e for m in source['modules'] if m['id']=='m' for e in m['elements'] if e['id']==record and e['kind']=='record')
        required={member['element'] for member in declared['members']}
        rows=[value for value in vars(models).values() if isinstance(value,type) and hasattr(value,'objects')
              and {element for module,element,name in getattr(value,'UMF_FIELDS',()) if module=='m'}==required]
        self.assertEqual(len(rows),1,'One actual owner-generated row model required for '+record)
        row=rows[0]
        self.assertEqual(row.UMF_SOURCE.document_sha256,sha256(self.document.content).hexdigest())
        print('temporal-native-generated-model '+json.dumps({'owner':owner_pin,'files':manifest,
            'documentSha256':sha256(self.document.content).hexdigest(),'inputDigest':row.UMF_SOURCE.input_digest},sort_keys=True))
        return row

    def ready_engine(self):
        c,h,a,tx=self.ready_temporal();selected=a.temporal_values()
        values=((0,LocalTimestampValue(text='2000-02-29T12:34:56.000001')),(1,NullValue()),
                (2,LocalTimestampValue(text='2024-01-01T00:00:00.000001')),
                (4,LocalTimestampValue(text='2000-02-29T12:34:56.000001')))
        updates=tuple(temporal.UpdateObject(target=StoredObjectReference(identity=identity),expected_version='1',unset=(),
            set=(temporal.AuthoredValue(name='A-local',value=value),)) for index,value in values for identity in (self.identities[index],))
        applied,_,_=self.run_group(selected,tx,updates,'engine-public-local-values')
        self.assertIsInstance(applied,GroupSuccess,repr(applied));h.detach();c.commit()
        return self.generated_row()

    def projection(self,row,elements):
        from umf_access.types import StrictModel
        fields=tuple(f for f in row.UMF_FIELDS if f[1] in elements)
        namespace={'__module__':__name__,'UMF_SOURCE':row.UMF_SOURCE,'UMF_FIELDS':fields,
            '__annotations__':{'UMF_SOURCE':ClassVar[type(row.UMF_SOURCE)],'UMF_FIELDS':ClassVar[tuple],
                **{name:row.model_fields[name].rebuild_annotation() for module,element,name in fields}}}
        for module,element,name in fields:
            if not row.model_fields[name].is_required():namespace[name]=row.model_fields[name].default
        return type('NativeTemporalProjection_'+uuid4().hex,(StrictModel,),namespace)

    def entry(self,result,sql,*,page=False,key='a-primary',record='A',parameters_type=None,parameters=None,temporal_parameters=None):
        from umf_access.engine_catalog import EngineRead
        from umf_access.types import StrictModel
        class Parameters(StrictModel):pass
        if parameters_type is not None:Parameters=parameters_type
        c,h,a,tx=self.consumer()
        captured=a.query_temporal_catalog_sources_in_transaction(tx,sql=sql,document_ids=('adoc',),temporal_parameters=temporal_parameters)
        self.assertIsInstance(captured,Ok,repr(captured));h.detach();c.rollback()
        owner=compiler();self.assertIsNotNone(owner,'Actual enrolled compiled Weft is mandatory')
        options={'method':'truss-runtime-temporal','temporal_profile':'umf.weft-binding-temporal/0.2'}
        if page:options.update(page_size=2,selected_key={'module':'m','record':record,'key':key})
        original=json.loads(captured.value.request_json)
        entry=EngineRead.build(owner,original,parameters=Parameters,result=result,**options)
        self.assertEqual(entry.artifact()['request'],original)
        return entry,Parameters() if parameters is None else parameters

    def target(self,entry,*,user='consumer'):
        from truss.access import TrussTarget
        @contextmanager
        def operation(budget):
            milliseconds=max(1,int(budget.total_seconds()*1000))
            params={**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),'user':user}
            with psycopg.connect(**params,autocommit=True,options=f'-c statement_timeout={milliseconds}') as c:
                c.execute('BEGIN READ ONLY')
                h=adopt_psycopg_host(c,statement_timeout_ms=milliseconds,operation_timeout_ms=milliseconds)
                try:
                    adopted=h.adopt_transaction(access_mode='read_only');self.assertIsInstance(adopted,Ok,repr(adopted))
                    assembly=create_reference_assembly(CatalogRuntimeConfiguration(),h)
                    self.assertIsInstance(assembly,Ok,repr(assembly))
                    yield assembly.value,adopted.value
                except BaseException:
                    h.detach();c.rollback();raise
                else:
                    self.assertTrue(h.detach());c.commit()
        return TrussTarget(operation,binding_sha256=entry.artifact()['request']['target']['bindingSha256'],
            platform=(('postgresql','18.6'),),default_timeout=timedelta(seconds=10),catalog_entries=(entry,))

    def test_typed_temporal_model_read_verify_and_complete_pages(self):
        from umf_access.types import MISSING
        row=self.ready_engine();names={element:name for module,element,name in row.UMF_FIELDS}
        sql='SELECT '+','.join(quoted(element)+' AS '+quoted(name) for module,element,name in row.UMF_FIELDS)+ \
            ' FROM "A" ORDER BY "A-instant" ASC,"A-label" ASC'
        read,parameters=self.entry(row,sql);target=self.target(read);target.verify()
        whole=target.read(read,parameters)
        self.assertEqual([getattr(v,names['A-label']) for v in whole],[f'row-{i}' for i in range(6)])
        self.assertEqual([getattr(v,names['A-date']) for v in whole],[date(2024,1,i+1) for i in range(6)])
        self.assertEqual([getattr(v,names['A-instant']).astimezone(timezone.utc) for v in whole],
            [datetime(1969,12,31,23,59,59,999999,tzinfo=timezone.utc),datetime(1970,1,1,tzinfo=timezone.utc),
             datetime(1970,1,1,0,0,9,tzinfo=timezone.utc),datetime(1970,1,1,0,0,10,tzinfo=timezone.utc),
             datetime(2024,1,1,tzinfo=timezone.utc),datetime(2024,1,1,tzinfo=timezone.utc)])
        self.assertEqual(getattr(whole[0],names['A-local']),datetime(2000,2,29,12,34,56,1))
        self.assertIsNone(getattr(whole[1],names['A-local']));self.assertIs(getattr(whole[3],names['A-local']),MISSING)
        page,parameters=self.entry(row,sql,page=True);target=self.target(page);actual=[];after=None
        for index in range(4):
            batch=target.page(page,parameters,after=after);actual.extend(batch.items);after=batch.next_after
            if after is None:break
        self.assertIsNone(after);self.assertEqual(actual,whole)

    def test_hidden_full_composite_key_pages_preserve_repeated_prefixes(self):
        row=self.ready_engine();names={element:name for module,element,name in row.UMF_FIELDS};name=names['A-instant']
        # Projection annotations and source identity come from actual generated
        # owner output, never a handwritten temporal validator or fake digest.
        projection=self.projection(row,{'A-instant'})
        sql='SELECT "A-instant" AS '+quoted(name)+' FROM "A" ORDER BY "A-instant" ASC'
        read,parameters=self.entry(projection,sql);expected=self.target(read).read(read,parameters)
        page,parameters=self.entry(projection,sql,page=True);metadata=page.artifact()['page']
        self.assertEqual(len(metadata['keyOutputPositions']),2)
        self.assertTrue(set(metadata['keyOutputPositions'])-set(metadata['visibleOutputPositions']))
        target=self.target(page);actual=[];after=None;tokens=[]
        for index in range(4):
            result=target.page(page,parameters,after=after);actual.extend(result.items);after=result.next_after
            if after is None:break
            self.assertIs(type(after.owner_cursor),bytes);tokens.append(after.owner_cursor)
        self.assertIsNone(after);self.assertEqual(actual,expected);self.assertEqual(len(actual),6)
        self.assertEqual(len(tokens),len(set(tokens)))

    def test_temporal_filter_parameters_use_all_three_explicit_kinds(self):
        from pydantic import BeforeValidator
        from umf_access.types import StrictModel
        from umf_access.values import FieldValidator
        class Parameters(StrictModel):
            minimum_day:Annotated[date,BeforeValidator(FieldValidator(kind='date'))]
            since:Annotated[datetime,BeforeValidator(FieldValidator(kind='instant'))]
            wall:Annotated[datetime,BeforeValidator(FieldValidator(kind='local'))]
        row=self.ready_engine();names={element:name for module,element,name in row.UMF_FIELDS}
        sql='SELECT '+','.join(quoted(element)+' AS '+quoted(name) for module,element,name in row.UMF_FIELDS)+ \
            ' FROM "A" WHERE "A-date">=:minimum_day AND "A-instant">=:since AND "A-local">=:wall ORDER BY "A-label" ASC'
        values=Parameters(minimum_day=date(2024,1,3),since=datetime(1970,1,1,tzinfo=timezone.utc),
                          wall=datetime(2000,2,29,12,34,56,1))
        entry,parameters=self.entry(row,sql,parameters_type=Parameters,parameters=values,temporal_parameters={
            'minimum_day':{'kind':'date','value':'2024-01-03'},'since':{'kind':'instant','value':'1970-01-01T00:00:00Z'},
            'wall':{'kind':'local','value':'2000-02-29T12:34:56.000001'}})
        target=self.target(entry);original=entry.artifact_json
        actual=target.read(entry,parameters)
        self.assertEqual([getattr(v,names['A-label']) for v in actual],['row-2','row-4'])
        # Reuse this exact compiled entry: changing only runtime parameters
        # must change results without recapturing or rebuilding its program.
        changed=Parameters(minimum_day=date(2024,1,5),since=datetime(2024,1,1,tzinfo=timezone.utc),
                           wall=datetime(2000,2,29,12,34,56,1))
        self.assertEqual([getattr(v,names['A-label']) for v in target.read(entry,changed)],['row-4'])
        self.assertEqual(entry.artifact_json,original)
        self.assertEqual([getattr(v,names['A-label']) for v in target.read(entry,parameters)],['row-2','row-4'])
        self.assertEqual(set(entry.artifact()['request']['temporalParameters']),{'minimum_day','since','wall'})
        self.assertEqual(entry.artifact_json,original)
        print('temporal-native-parameter-reuse '+json.dumps({'wholeWrapperSha256':sha256(original.encode()).hexdigest(),
            'compiledEntries':1,'runtimeReads':3,'expectedLabels':[['row-2','row-4'],['row-4'],['row-2','row-4']]},sort_keys=True))

    def test_full_pages_match_independent_native_order_oracle_all_directions_and_null_orders(self):
        from umf_access.types import MISSING
        row=self.ready_engine();projection=self.projection(row,{'A-label','A-local'})
        names={element:name for module,element,name in row.UMF_FIELDS}
        known_local=(datetime(2000,2,29,12,34,56,1),None,datetime(2024,1,1,0,0,0,1),None,
                     datetime(2000,2,29,12,34,56,1),None)
        oracle_values=tuple(v for index,wall in enumerate(known_local) for v in (f'row-{index}','shared-key',wall))
        # Values are already known-admitted canonical fixture tokens. Native
        # SQL typed ordering is an independent test oracle, never admission.
        oracle='SELECT label FROM (VALUES '+','.join(['(%s::text,%s::text,%s::timestamp)']*6)+') v(label,prefix,wall)'
        for direction in ('ASC','DESC'):
            for nulls in ('FIRST','LAST'):
                for key in ('a-primary','z-alt'):
                    with self.subTest(direction=direction,nulls=nulls,key=key):
                        order=f' ORDER BY "A-local" {direction} NULLS {nulls},"A-local" ASC NULLS LAST'
                        sql='SELECT '+','.join(quoted(e)+' AS '+quoted(n) for m,e,n in projection.UMF_FIELDS)+' FROM "A"'+order
                        page,parameters=self.entry(projection,sql,page=True,key=key)
                        metadata=page.artifact()['page'];self.assertEqual(len(metadata['sort']),2+(2 if key=='a-primary' else 1))
                        self.assertEqual(metadata['sort'][0]['field'],metadata['sort'][1]['field'])
                        expected=[v[0] for v in self.admin.execute(oracle+f' ORDER BY wall {direction} NULLS {nulls},wall ASC NULLS LAST,prefix ASC,label ASC',oracle_values).fetchall()]
                        actual=[];after=None;target=self.target(page)
                        for index in range(4):
                            batch=target.page(page,parameters,after=after);actual.extend(batch.items);after=batch.next_after
                            if after is None:break
                        self.assertIsNone(after);self.assertEqual([getattr(v,names['A-label']) for v in actual],expected)
                        by_label={getattr(v,names['A-label']):getattr(v,names['A-local']) for v in actual}
                        self.assertIsNone(by_label['row-1']);self.assertIs(by_label['row-3'],MISSING)
                        self.assertIs(by_label['row-5'],MISSING)

    def test_date_and_instant_pages_match_independent_native_order_permutations(self):
        row=self.ready_engine();names={element:name for module,element,name in row.UMF_FIELDS}
        known_dates=tuple(date(2024,1,index+1) for index in range(6))
        known_instants=(datetime(1969,12,31,23,59,59,999999,tzinfo=timezone.utc),
            datetime(1970,1,1,tzinfo=timezone.utc),datetime(1970,1,1,0,0,9,tzinfo=timezone.utc),
            datetime(1970,1,1,0,0,10,tzinfo=timezone.utc),datetime(2024,1,1,tzinfo=timezone.utc),
            datetime(2024,1,1,tzinfo=timezone.utc))
        for element,pg_type,values in (('A-date','date',known_dates),('A-instant','timestamptz',known_instants)):
            projection=self.projection(row,{'A-label',element})
            oracle_values=tuple(v for index,value in enumerate(values) for v in (f'row-{index}','shared-key',value))
            oracle='SELECT label FROM (VALUES '+','.join([f'(%s::text,%s::text,%s::{pg_type})']*6)+') v(label,prefix,value)'
            for direction in ('ASC','DESC'):
                for nulls in ('FIRST','LAST'):
                    for key in ('a-primary','z-alt'):
                        with self.subTest(element=element,direction=direction,nulls=nulls,key=key):
                            sql='SELECT '+','.join(quoted(e)+' AS '+quoted(n) for m,e,n in projection.UMF_FIELDS)+ \
                                ' FROM "A" ORDER BY '+quoted(element)+f' {direction} NULLS {nulls}'
                            page,parameters=self.entry(projection,sql,page=True,key=key)
                            expected=[v[0] for v in self.admin.execute(oracle+
                                f' ORDER BY value {direction} NULLS {nulls},prefix ASC,label ASC',oracle_values).fetchall()]
                            target=self.target(page);actual=[];after=None
                            for index in range(4):
                                batch=target.page(page,parameters,after=after);actual.extend(batch.items);after=batch.next_after
                                if after is None:break
                            self.assertIsNone(after);self.assertEqual(len(actual),6)
                            self.assertEqual([getattr(v,names['A-label']) for v in actual],expected)

    def test_actual_sdk_page_refuses_tuple_token_context_and_other_actor_before_data_sql(self):
        from unittest.mock import patch
        from truss import _temporal_query_execution as execution
        from truss.access import TrussReadRefused
        from umf_access.pages import StaleContinuation
        row=self.ready_engine();projection=self.projection(row,{'A-instant'})
        name=next(n for m,e,n in projection.UMF_FIELDS if e=='A-instant')
        sql='SELECT "A-instant" AS '+quoted(name)+' FROM "A" ORDER BY "A-instant" ASC'
        entry,parameters=self.entry(projection,sql,page=True);target=self.target(entry)
        first=target.page(entry,parameters);self.assertEqual(len(first.items),2)
        after=first.next_after;self.assertIsNotNone(after)
        for fault,changed in (('arity',replace(after,values=())),
                ('tuple',replace(after,values=after.values[::-1])),
                ('token',replace(after,owner_cursor=b'not-an-issued-native-cursor'))):
            with self.subTest(fault=fault),patch.object(execution,'_artifact',wraps=execution._artifact) as data_gate:
                with self.assertRaises(TrussReadRefused):target.page(entry,parameters,after=changed)
                data_gate.assert_not_called()
        with self.assertRaises(StaleContinuation):
            target.page(entry,parameters,after=replace(after,identity_digest='0'*64))
        different,other_parameters=self.entry(projection,sql.replace(' ASC',' DESC'),page=True)
        other_target=self.target(different);different_first=other_target.page(different,other_parameters)
        self.assertIsNotNone(different_first.next_after)
        # Give the old native bytes the other honest SDK context identity. The
        # actual native token must still refuse cross-query reuse independently.
        changed=replace(after,identity_digest=different_first.next_after.identity_digest)
        with patch.object(execution,'_artifact',wraps=execution._artifact) as data_gate:
            with self.assertRaises(TrussReadRefused) as refused:other_target.page(different,other_parameters,after=changed)
            self.assertEqual(refused.exception.original,Ok(QueryRefused(code='stale_context')))
            data_gate.assert_not_called()
        role='engine_page_reader_'+uuid4().hex[:8]
        self.admin.execute(psycopg.sql.SQL('CREATE ROLE {} LOGIN').format(psycopg.sql.Identifier(role)))
        self.addCleanup(self.admin.execute,psycopg.sql.SQL('DROP ROLE {}').format(psycopg.sql.Identifier(role)))
        self.admin.execute(psycopg.sql.SQL('GRANT group_reader TO {} WITH SET FALSE').format(psycopg.sql.Identifier(role)))
        other_actor=self.target(entry,user=role)
        self.assertEqual(len(other_actor.page(entry,parameters).items),2,'Actual second actor must be authorized for its own first page')
        with patch.object(execution,'_artifact',wraps=execution._artifact) as data_gate:
            with self.assertRaises(TrussReadRefused) as refused:other_actor.page(entry,parameters,after=after)
            self.assertEqual(refused.exception.original,Ok(QueryRefused(code='stale_context')))
            data_gate.assert_not_called()

    def test_actual_compiled_program_tamper_refuses_before_data_artifact_dispatch(self):
        from unittest.mock import patch
        from truss import _temporal_query_execution as execution
        from truss.access import TrussReadRefused
        from umf_access.engine_catalog import EngineRead
        from umf_access.reviewed import ReadBuildError
        from umf_access.native_program import canonical_json
        row=self.ready_engine()
        sql='SELECT '+','.join(quoted(e)+' AS '+quoted(n) for m,e,n in row.UMF_FIELDS)+' FROM "A"'
        entry,parameters=self.entry(row,sql);self.assertEqual(len(self.target(entry).read(entry,parameters)),6)
        refusals=[]
        for fault in ('sql','requirements','caps','abi','origin','column','module'):
            program=entry.artifact();artifact=program['artifact'];source=artifact['sourceDomainChecks']['sources'][0]
            if fault=='sql':artifact['sql']+=' /* unauthorized artifact edit */'
            elif fault=='requirements':
                slot=artifact['parameters'][source['requirementsParameter']-1]
                value=json.loads(slot['value']);value['fields'].pop();slot['value']=json.dumps(value)
            elif fault=='caps':artifact['sourceDomainChecks']['maxScanRows']+=1
            elif fault=='abi':artifact['sourceDomainChecks']['queryAbi']['sha256']='0'*64
            elif fault=='origin':artifact['parameters'][source['bindingParameter']-1]['origin']={'kind':'forged-origin'}
            elif fault=='column':artifact['columns'][0]['sourceIdentities'][0]['element']='foreign'
            else:program['request']['modules'][0]['documentJson']+='\n'
            # Public checksums confer no authority. Reseal the tampered genuine
            # program to force semantic/custody checks beyond a checksum test.
            program.pop('structuralDigest')
            program['structuralDigest']={'owner':'weft-runtime-engine-read','version':'0.4',
                'sha256':sha256(canonical_json(program).encode()).hexdigest()}
            try:
                altered=EngineRead.from_original(json.dumps(program),parameters=entry.parameters,result=row)
                target=self.target(altered)
            except ReadBuildError:
                refusals.append({'fault':fault,'stage':'original-sdk-custody'});continue
            with patch.object(execution,'_artifact',wraps=execution._artifact) as data_gate:
                with self.assertRaises(TrussReadRefused) as refused:target.read(altered,parameters)
                data_gate.assert_not_called()
                self.assertIsInstance(refused.exception.original,dict)
                self.assertEqual(refused.exception.original['status'],'blocked')
                self.assertTrue(refused.exception.original['diagnostics'])
                self.assertIs(type(refused.exception.__cause__.original),str)
                refusals.append({'fault':fault,'stage':'actual-owner-checker','original':refused.exception.__cause__.original})
        self.assertEqual(len(refusals),7)
        self.assertTrue(any(v['fault']=='sql' and v['stage']=='actual-owner-checker' for v in refusals))
        print('temporal-actual-program-tamper-refusals '+json.dumps(refusals,ensure_ascii=True,sort_keys=True))

    def test_native_and_actual_owner_refuse_numeric_selected_key_even_for_empty_source(self):
        from umf_access.native_program import ProgramBuildError
        def numeric_record(source):
            module=source['modules'][0]
            module['elements'].extend(({'id':'C','name':'C','kind':'record',
                'members':[{'module':'m','element':'C-id'},{'module':'m','element':'C-day'}],
                'keys':[{'id':'c-primary','name':'primary','primary':True,'fields':[{'module':'m','element':'C-id'}]}]},
                {'id':'C-id','name':'C-id','kind':'field','scalarType':'integer','cardinality':'one','nullability':'required',
                 'facets':{'integerWidth':{'bits':64,'signed':True}}},
                {'id':'C-day','name':'C-day','kind':'field','scalarType':'date','cardinality':'one','nullability':'required'}))
            module['extensions']['umf.access']['views'].append({'record':{'module':'m','element':'C'},
                'selectedKey':{'module':'m','element':'C','key':'c-primary'},'fields':[
                    {'field':{'module':'m','element':name},'row':{'missing':False,'null':False},
                     'create':{'missing':False,'null':False},'mutable':name!='C-id','generated':False}
                    for name in ('C-id','C-day')]})
        c,h,a,tx=self.ready_temporal(numeric_record)
        binding,_=self.capture(c);parsed=json.loads(binding)
        record=next(r for r in parsed['records'] if r['identity']['element']=='C')
        field=next(f['identity'] for f in record['fields'] if f['identity']['element']=='C-day')
        requirements={'version':'truss.temporal-source-guard/0.2','record':record['identity'],
                      'fields':[{'field':field,'kind':'date','presence':{'missing':False,'null':False}}]}
        with self.assertRaises(psycopg.Error) as refused:
            with c.transaction():
                with c.cursor(name='native_numeric_temporal_key') as cursor:
                    cursor.execute('SELECT id FROM truss.person_query_temporal_page_objects(%s::jsonb,%s,%s,%s::jsonb) LIMIT 1',
                        (binding,int(record['typeId']),'c-primary',json.dumps(requirements)))
                    self.fail('Numeric temporal page Key accepted an empty source: '+repr(cursor.fetchone()))
        self.assertEqual(refused.exception.sqlstate,'0A000');h.detach();c.rollback()
        model=self.generated_row('C')
        sql='SELECT '+','.join(quoted(e)+' AS '+quoted(n) for m,e,n in model.UMF_FIELDS)+' FROM "C" ORDER BY "C-day" ASC'
        with self.assertRaises(ProgramBuildError) as blocked:self.entry(model,sql,page=True,key='c-primary',record='C')
        original=json.loads(blocked.exception.original_json)
        self.assertEqual(original['status'],'blocked');self.assertTrue(original['diagnostics'])
        self.assertTrue(any('string' in d['message'].lower() for d in original['diagnostics']))
