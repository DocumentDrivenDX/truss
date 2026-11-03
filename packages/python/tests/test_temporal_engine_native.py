# SPDX-License-Identifier: MIT OR Apache-2.0
"""TN09/10 authentic installed owner -> generated model -> Truss execution.

No fixture compiler, owner manifest, generated source identity or native
binding is invented. Missing actual enrollments fail; collection is not proof.
"""
from contextlib import contextmanager
from datetime import date,datetime,timedelta,timezone
from hashlib import sha256
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import ClassVar
from uuid import uuid4
import psycopg

from truss import Ok,CatalogRuntimeConfiguration,adopt_psycopg_host,create_reference_assembly
from truss import temporal
from truss.contracts import LocalTimestampValue,NullValue
from truss.groups import StoredObjectReference,GroupSuccess
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

    def generated_row(self):
        owner,owner_pin=_inspector()
        package='temporal_native_'+uuid4().hex
        generated=owner.generate_python_client({'text':self.document.content.decode(),'package':package})
        self.assertTrue(generated['files'])
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
        required={'A-label','A-value','A-date','A-instant','A-local','A-payload'}
        rows=[value for value in vars(models).values() if isinstance(value,type) and hasattr(value,'objects')
              and {element for module,element,name in getattr(value,'UMF_FIELDS',()) if module=='m'}==required]
        self.assertEqual(len(rows),1,'One actual owner-generated A row model required')
        row=rows[0]
        self.assertEqual(row.UMF_SOURCE.document_sha256,sha256(self.document.content).hexdigest())
        print('temporal-native-generated-model '+json.dumps({'owner':owner_pin,'files':manifest,
            'documentSha256':sha256(self.document.content).hexdigest(),'inputDigest':row.UMF_SOURCE.input_digest},sort_keys=True))
        return row

    def ready_engine(self):
        c,h,a,tx=self.ready_temporal();selected=a.temporal_values()
        values=(LocalTimestampValue(text='2000-02-29T12:34:56.000001'),NullValue(),
                LocalTimestampValue(text='2000-02-29T12:34:56.000001'))
        updates=tuple(temporal.UpdateObject(target=StoredObjectReference(identity=identity),expected_version='1',unset=(),
            set=(temporal.AuthoredValue(name='A-local',value=value),)) for identity,value in zip(self.identities,values))
        applied,_,_=self.run_group(selected,tx,updates,'engine-public-local-values')
        self.assertIsInstance(applied,GroupSuccess,repr(applied));h.detach();c.commit()
        return self.generated_row()

    def entry(self,result,sql,*,page=False,key='a-primary'):
        from umf_access.engine_catalog import EngineRead
        from umf_access.types import StrictModel
        class Parameters(StrictModel):pass
        c,h,a,tx=self.consumer()
        captured=a.query_temporal_catalog_sources_in_transaction(tx,sql=sql,document_ids=('adoc',))
        self.assertIsInstance(captured,Ok,repr(captured));h.detach();c.rollback()
        owner=compiler();self.assertIsNotNone(owner,'Actual enrolled compiled Weft is mandatory')
        options={'method':'truss-runtime-temporal','temporal_profile':'umf.weft-binding-temporal/0.2'}
        if page:options.update(page_size=2,selected_key={'module':'m','record':'A','key':key})
        original=json.loads(captured.value.request_json)
        entry=EngineRead.build(owner,original,parameters=Parameters,result=result,**options)
        self.assertEqual(entry.artifact()['request'],original)
        return entry,Parameters()

    def target(self,entry):
        from truss.access import TrussTarget
        @contextmanager
        def operation(budget):
            milliseconds=max(1,int(budget.total_seconds()*1000))
            params={**psycopg.conninfo.conninfo_to_dict(self.info.connection_uri),'user':'consumer'}
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
        from umf_access.types import StrictModel
        row=self.ready_engine();names={element:name for module,element,name in row.UMF_FIELDS};name=names['A-instant']
        # Projection annotations and source identity come from actual generated
        # owner output, never a handwritten temporal validator or fake digest.
        projection=type('NativeInstantProjection',(StrictModel,),{'__module__':__name__,
            '__annotations__':{name:row.model_fields[name].rebuild_annotation(),
                'UMF_SOURCE':ClassVar[type(row.UMF_SOURCE)],'UMF_FIELDS':ClassVar[tuple]},
            'UMF_SOURCE':row.UMF_SOURCE,'UMF_FIELDS':tuple(f for f in row.UMF_FIELDS if f[1]=='A-instant')})
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
