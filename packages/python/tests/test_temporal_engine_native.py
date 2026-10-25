# SPDX-License-Identifier: MIT OR Apache-2.0
"""End-to-end .4 temporal engine reads/pages against the disposable native Truss fixture."""
from contextlib import contextmanager
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
import os

from pydantic import ConfigDict, create_model

from umf_access.engine_catalog import EngineRead
from umf_access.types import MISSING, StrictModel
from truss import Ok
from truss._query_runtime import compiler
from truss.access import TrussTarget
from truss.contracts import LocalTimestampValue, NullValue, TextValue
from truss.contracts import MapValue
from truss.groups import AuthoredValue, GroupSuccess, RequestNone
from truss.query import QueryCatalogSources

import test_local_timestamp_query_native as carrier


class EmptyParameters(StrictModel):
    pass


class TemporalEngineNativeTests(carrier.LocalTimestampQueryTests):
    # The carrier setup is reused, but its focused tests belong to its own module.
    for _name in tuple(n for n in dir(carrier.LocalTimestampQueryTests) if n.startswith('test_')):
        locals()[_name] = None

    def _store_rows(self, assembly, tx, *, key_scalar='string'):
        rows = (
            # One repeated first key component, distinct second components, and
            # duplicate temporal values make the complete composite Key visible.
            ('alpha', '2024-02-29', '2024-11-03T01:30:00.000000', '1970-01-01T00:00:09Z'),
            ('beta',  '2024-02-29', '2024-11-03T01:30:00.000000', '1969-12-31T19:00:09-05:00'),
            ('gamma', '2025-01-01', '2024-11-04T00:00:00.000000', '1970-01-01T00:00:10Z'),
            ('delta', None,         None,                          '1969-12-31T23:59:50Z'),
            ('epsilon', MISSING,    MISSING,                       '1969-12-31T23:59:58Z'),
            ('zeta',   '2023-01-01','2024-01-01T00:00:00.000001','2024-01-01T00:00:00Z'),
        )
        operations=[]
        for label, day, wall, instant in rows:
            value = len(operations)+1 if key_scalar == 'integer' else 'shared'
            create=self.create(label=label,value=str(value),alias=label)
            if key_scalar == 'integer':
                create=replace(create,values=tuple(
                    AuthoredValue(name='A-value',value=TextValue(kind='integer',text=str(value)))
                    if item.name=='A-value' else item for item in create.values))
            fields=[AuthoredValue(name='A-at',value=TextValue(kind='timestamp',text=instant))]
            if day is not MISSING:
                fields.append(AuthoredValue(name='A-on',value=NullValue() if day is None else TextValue(kind='date',text=day)))
            if wall is not MISSING:
                fields.append(AuthoredValue(name='A-local',value=NullValue() if wall is None else LocalTimestampValue(text=wall)))
            operations.append(replace(create,values=create.values+tuple(fields)))
        context=assembly.group_context_in_transaction(tx)
        self.assertIsInstance(context,Ok,repr(context))
        applied=assembly.apply_in_transaction(tx,context.value.input(tuple(operations),MapValue(entries=())),RequestNone(),
            documents=self.documents,bun_executable=os.environ.get('TRUSS_BUN_EXECUTABLE','bun'))
        self.assertIsInstance(applied,Ok,repr(applied))
        self.assertIsInstance(applied.value,GroupSuccess,repr(applied.value))
        return rows

    def _capture_request(self, assembly, tx, sql):
        captured=assembly.query_temporal_catalog_sources_in_transaction(tx,sql=sql,document_ids=('adoc',))
        self.assertIsInstance(captured,Ok,repr(captured))
        self.assertIsInstance(captured.value,QueryCatalogSources,repr(captured.value))
        request=json.loads(captured.value.request_json)
        self.assertEqual(request.get('temporalProfile'),'umf.weft-binding-temporal/0.2')
        self.assertEqual(request.get('temporalParameters'),{})
        return request

    def _entry(self, request, *, kind, temporal_parameters, page_size=None, key_scalar='string'):
        import weft
        self.assertIsNotNone(compiler(engine_temporal=True))
        result_scalar={'date':date,'instant':datetime,'local':datetime}[kind]
        result_model=create_model(f'{kind.title()}FilteredResult',__config__=ConfigDict(strict=True,extra='forbid'),
            occurred_at=(result_scalar|None|MISSING,MISSING))
        if page_size is None:
            packet=EngineRead.compile_original(weft,request,method='truss-runtime-temporal',
                temporal_parameters=temporal_parameters,temporal_profile='umf.weft-binding-temporal/0.2')
            return EngineRead.from_original(packet,parameters=self._parameter_model(kind),result=result_model,
                temporal_outputs={'occurred_at':kind})
        page_result=create_model(f'{kind.title()}PageResult',__config__=ConfigDict(strict=True,extra='forbid'),
            occurred_at=(result_scalar|None|MISSING,MISSING),key_first=(int if key_scalar=='integer' else str,...),
            key_second=(str,...))
        packet=EngineRead.compile_original(weft,request,method='truss-runtime-temporal',
            page_size=page_size,selected_key={'module':'m','record':'A','key':'a-primary'},
            temporal_profile='umf.weft-binding-temporal/0.2')
        return EngineRead.from_original(packet,parameters=EmptyParameters,result=page_result,
            temporal_outputs={'occurred_at':kind})

    @staticmethod
    def _parameter_model(kind):
        parameter={'date':date,'instant':datetime,'local':datetime}[kind]
        return create_model(f'{kind.title()}Parameters',__config__=ConfigDict(strict=True,extra='forbid'),
                            boundary=(parameter,...))

    def _target(self, entry):
        request=entry.artifact()['request']
        target=request['target']
        @contextmanager
        def operation(timeout):
            connection,host,assembly,tx=self.consumer()
            try:
                yield assembly,tx
            except BaseException:
                host.detach();connection.rollback();raise
            else:
                host.detach();connection.commit()
        return TrussTarget(operation,binding_sha256=target['bindingSha256'],
            platform=(('postgresql','18.6'),),default_timeout=timedelta(seconds=20),
            catalog_entries=(entry,))

    @staticmethod
    def _boundary(kind):
        if kind=='date':return date(2024,2,29),{'boundary':{'kind':'date','value':'2024-02-29'}}
        if kind=='instant':return datetime(1970,1,1,0,0,9,tzinfo=timezone.utc),{'boundary':{'kind':'instant','value':'9000000'}}
        return datetime(2024,11,3,1,30),{'boundary':{'kind':'local','value':'2024-11-03T01:30:00.000000'}}

    def test_typed_temporal_model_read_filter_verify_and_full_ordered_pages(self):
        connection,host,assembly,tx=self.ready()
        self._store_rows(assembly,tx)
        entries={}
        for kind,field in (('date','A-on'),('instant','A-at'),('local','A-local')):
            boundary,temporal_parameters=self._boundary(kind)
            sql=f'SELECT a."{field}" AS occurred_at FROM "A" a WHERE a."{field}" = :boundary'
            request=self._capture_request(assembly,tx,sql)
            entry=self._entry(request,kind=kind,temporal_parameters=temporal_parameters)
            entries[kind]=(entry,boundary)
        host.detach();connection.commit()

        expected_filtered={'date':2,'instant':2,'local':2}
        for kind,(entry,boundary) in entries.items():
            with self.subTest(read_kind=kind):
                target=self._target(entry)
                params=entry.parameters.model_validate({'boundary':boundary},strict=True)
                rows=target.read_native_temporal(entry,params)
                self.assertEqual(len(rows),expected_filtered[kind])
                self.assertTrue(all(row.occurred_at==boundary for row in rows))
                target.verify()
                wrong={'date':datetime(2024,2,29),'instant':date(1970,1,1),
                       'local':datetime(2024,11,3,1,30,tzinfo=timezone.utc)}[kind]
                with self.assertRaises(Exception):
                    target.read_native_temporal(entry,entry.parameters.model_validate({'boundary':wrong},strict=True))

        # The page model emits the complete selected composite Key alongside
        # the temporal value so each traversal asserts every tuple, not a bag.
        expected_values={
            'date': {'asc':['zeta','alpha','beta','gamma','delta','epsilon'],
                     'desc':['gamma','alpha','beta','zeta','delta','epsilon']},
            'instant': {'asc':['delta','epsilon','alpha','beta','gamma','zeta'],
                        'desc':['zeta','gamma','alpha','beta','epsilon','delta']},
            'local': {'asc':['zeta','alpha','beta','gamma','delta','epsilon'],
                      'desc':['gamma','alpha','beta','zeta','delta','epsilon']},
        }
        row_values={
            'date':{
                'alpha':('value',date(2024,2,29)),'beta':('value',date(2024,2,29)),
                'gamma':('value',date(2025,1,1)),'delta':('null',None),
                'epsilon':('missing',MISSING),'zeta':('value',date(2023,1,1))},
            'instant':{
                'alpha':('value',datetime(1970,1,1,0,0,9,tzinfo=timezone.utc)),
                'beta':('value',datetime(1970,1,1,0,0,9,tzinfo=timezone.utc)),
                'gamma':('value',datetime(1970,1,1,0,0,10,tzinfo=timezone.utc)),
                'delta':('value',datetime(1969,12,31,23,59,50,tzinfo=timezone.utc)),
                'epsilon':('value',datetime(1969,12,31,23,59,58,tzinfo=timezone.utc)),
                'zeta':('value',datetime(2024,1,1,tzinfo=timezone.utc))},
            'local':{
                'alpha':('value',datetime(2024,11,3,1,30)),
                'beta':('value',datetime(2024,11,3,1,30)),
                'gamma':('value',datetime(2024,11,4,0,0)),
                'delta':('null',None),'epsilon':('missing',MISSING),
                'zeta':('value',datetime(2024,1,1,0,0,0,1))},
        }
        for kind,field in (('date','A-on'),('instant','A-at'),('local','A-local')):
            for direction in ('ASC','DESC'):
                for nulls in ('FIRST','LAST'):
                    with self.subTest(page_kind=kind,direction=direction,nulls=nulls):
                        page_sql=(f'SELECT a."{field}" AS occurred_at,a."A-value" AS key_first,'
                                  f'a."A-label" AS key_second FROM "A" a '
                                  f'ORDER BY a."{field}" {direction} NULLS {nulls}')
                        # The source capture is read-only and yields original bytes;
                        # the selected .4 compiler owns page lowering and cursor checks.
                        page_connection,page_host,page_assembly,page_tx=self.consumer()
                        request=self._capture_request(page_assembly,page_tx,page_sql)
                        page_entry=self._entry(request,kind=kind,temporal_parameters={},page_size=2)
                        page_host.detach();page_connection.commit()
                        target=self._target(page_entry)
                        params=EmptyParameters()
                        observed=[];continuation=None
                        for page_number in range(4):
                            page=target.page_native_temporal(page_entry,params,after=continuation)
                            observed.extend((item.key_first,item.key_second,
                                'missing' if item.occurred_at is MISSING else 'null' if item.occurred_at is None else 'value',
                                item.occurred_at) for item in page.items)
                            continuation=page.next_after
                            if continuation is None:
                                break
                        else:
                            self.fail('Temporal page cursor did not exhaust within four pages')
                        labels=[item[1] for item in observed]
                        present_order=expected_values[kind][direction.lower()]
                        if kind=='instant':
                            expected=present_order
                        elif nulls=='FIRST':
                            expected=['delta','epsilon',*present_order[:-2]]
                        else:
                            expected=[*present_order[:-2],'delta','epsilon']
                        self.assertEqual(labels,expected)
                        expected_full=[('shared',label,*row_values[kind][label]) for label in expected]
                        self.assertEqual(observed,expected_full)
                        state={label:state for _,label,state,_ in observed}
                        if kind in ('date','local'):
                            self.assertEqual(state['delta'],'null')
                            self.assertEqual(state['epsilon'],'missing')
                        else:
                            self.assertTrue(all(item[2]=='value' for item in observed))
                        self.assertEqual(len(observed),6)
                        self.assertEqual(len({(item[0],item[1]) for item in observed}),6)

    def test_native_temporal_numeric_selected_key_is_explicitly_refused(self):
        # This probe makes the current string-only typed-page subset explicit;
        # it is not a claim that integer Keys have native temporal paging.
        from umf_access.native_program import ProgramBuildError

        def numeric_key(source):
            module=source['modules'][0]
            field=next(item for item in module['elements'] if item.get('id')=='A-value')
            field['scalarType']='integer';field['facets']={'integerWidth':{'bits':64,'signed':True}}
        connection,host,assembly,tx=self.ready(numeric_key)
        self._store_rows(assembly,tx,key_scalar='integer')
        sql='SELECT a."A-on" AS occurred_at,a."A-value" AS key_first,a."A-label" AS key_second FROM "A" a ORDER BY a."A-on" ASC NULLS FIRST'
        request=self._capture_request(assembly,tx,sql)
        with self.assertRaises(ProgramBuildError) as raised:
            self._entry(request,kind='date',temporal_parameters={},page_size=2,key_scalar='integer')
        self.assertIn('WFT-CAPABILITY', repr(raised.exception))
        self.assertIn('Unique required string page key mapping required', repr(raised.exception))
        host.detach();connection.rollback()

if __name__=='__main__':
    import unittest
    unittest.main()
