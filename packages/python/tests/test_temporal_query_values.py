# SPDX-License-Identifier: MIT OR Apache-2.0
"""Property-envelope decoder controls only; no native/owner binding is simulated."""
import copy
from decimal import Decimal
import json
import unittest
from unittest.mock import patch
from hashlib import sha256

from truss import LocalTimestampValue
from truss.contracts import TextValue
from truss.query import QueryAbsent,QueryRefused
from truss._temporal_query_values import decode_rows
from truss._temporal_compiler import compiler


class TemporalQueryValueTests(unittest.TestCase):
    def program(self):
        outputs=[];columns=[]
        for index,(name,kind,missing,nullable) in enumerate((
                ('local','local',False,False),('instant','instant',False,False),('date','date',False,False),
                ('optional','local',True,True),('number','integer',False,False),('flag','boolean',False,False)),1):
            identity={'documentId':'component','revision':'r1','module':'m','element':name}
            representation=({'kind':'value','descriptor':identity,'nativeNull':True} if kind in ('date','instant','local')
                else {'kind':'scalar','logicalType':{'family':kind,'facets':{},'nullable':False},'carrier':'text','decoder':kind})
            output={'name':name,'carrier':kind,'nullable':nullable,'missing':missing,'source':identity,
                    'representation':representation,'modelPins':[]}
            if kind in ('date','instant','local'):
                output['decoder']={'profile':'truss-temporal/0.2','kind':kind,'temporalProfile':'umf.weft-binding-temporal/0.2'}
            outputs.append(output)
            columns.append({'position':index,'outputName':name,'nullable':missing or nullable,
                            'sourceIdentities':[identity],'representation':copy.deepcopy(representation)})
        return {'outputs':outputs,'artifact':{'columns':columns,'modelPins':[]}}

    def row(self,optional=None):
        return (json.dumps('2024-02-29T12:34:56.123456'),json.dumps('2024-01-01T01:00:00.123456+01:00'),
                json.dumps('2000-02-29'),json.dumps({'state':'absent'} if optional is None else optional),
                '9007199254740993','true')

    def decode(self,rows,program=None,**limits):
        return decode_rows(rows,self.program() if program is None else program,
                           maximum_rows=limits.get('maximum_rows',10),maximum_bytes=limits.get('maximum_bytes',4096),catalog_revision=3)

    def test_raw_spelling_presence_exact_numbers_and_full_metadata_preserved(self):
        program=self.program();result=self.decode((self.row(),self.row({'state':'null'}),
            self.row({'state':'value','value':'2000-02-29T00:00:00.000000'})),program)
        local,instant,date,absent,number,flag=result.rows[0]
        self.assertEqual(local,LocalTimestampValue(text='2024-02-29T12:34:56.123456'))
        self.assertEqual(instant,TextValue(kind='timestamp',text='2024-01-01T01:00:00.123456+01:00'))
        self.assertEqual(date,TextValue(kind='date',text='2000-02-29'))
        self.assertIsInstance(absent,QueryAbsent);self.assertEqual(number,9007199254740993);self.assertIs(flag,True)
        self.assertIsNone(result.rows[1][3]);self.assertIsInstance(result.rows[2][3],LocalTimestampValue)
        self.assertEqual(result.column_descriptors[0].value_descriptor['decoder']['profile'],'truss-temporal/0.2')
        with self.assertRaises(TypeError):result.column_descriptors[0].original['position']=2

    def test_changed_decoder_source_column_and_presence_refuse(self):
        for fault in ('decoder','source','column','nullable','duplicate'):
            program=self.program()
            if fault=='decoder':program['outputs'][0]['decoder']['kind']='instant'
            elif fault=='source':program['outputs'][0]['representation']['descriptor']={'foreign':True}
            elif fault=='column':program['artifact']['columns'][0]['position']=2
            elif fault=='nullable':program['artifact']['columns'][0]['nullable']=True
            else:program['outputs'][1]['name']='local'
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.decode((self.row(),),program)
        for state in ({'state':'null','extra':True},{'state':'absent','value':'discarded'},{'state':'present','value':'x'}):
            with self.subTest(state=state),self.assertRaises(ValueError):self.decode((self.row(state),))
        row=list(self.row());row[0]=json.dumps({'state':'null'})
        with self.assertRaises(ValueError):self.decode((tuple(row),))

    def test_whole_result_caps_and_nontext_native_carriers_refuse(self):
        self.assertEqual(self.decode((self.row(),),maximum_rows=0),QueryRefused(code='limits'))
        self.assertEqual(self.decode((self.row(),),maximum_bytes=1),QueryRefused(code='limits'))
        row=list(self.row());row[-1]=True
        with self.assertRaises(ValueError):self.decode((tuple(row),))

    def test_unenrolled_compiler_never_adopts_ambient_version(self):
        class Missing:
            def joinpath(self,*args):return self
            def read_bytes(self):raise FileNotFoundError('deliberate absent enrollment')
        with patch('truss._temporal_compiler.files',return_value=Missing()), \
             patch('truss._temporal_compiler.metadata.version',side_effect=AssertionError('ambient version considered')):
            self.assertIsNone(compiler())

    def test_selected_compiler_refuses_dual_weft_distribution_before_import(self):
        from truss._temporal_compiler import CHECKERS
        import builtins
        # Deliberately UNIT metadata only: this exercises refusal before any
        # compiler import, never a synthetic successful owner enrollment.
        raw=json.dumps({'distribution':'umf-weft','version':'UNIT','sourceCommit':'0'*40,
            'installedFiles':{},'checkers':CHECKERS}).encode()
        class UnitFile:
            def joinpath(self,*args):return self
            def read_bytes(self):return raw
        original_import=builtins.__import__
        def no_compiler_import(name,*args,**kwargs):
            if name=='weft':raise AssertionError('Co-installed compiler must refuse before import')
            return original_import(name,*args,**kwargs)
        with patch('truss._temporal_compiler.files',return_value=UnitFile()), \
             patch('truss.catalog_runtime._release',return_value=({'files':{'../_temporal_owner/compiler.json':sha256(raw).hexdigest()}},'UNIT',())), \
             patch('truss._temporal_compiler.metadata.version',return_value='UNIT'), \
             patch('truss._temporal_compiler.metadata.distribution',return_value=object()) as legacy, \
             patch('builtins.__import__',side_effect=no_compiler_import):
            self.assertIsNone(compiler())
        legacy.assert_called_once_with('weft-sql')

    def test_ordinary_read_and_page_never_retry_explicit_engine04(self):
        from truss._query_runtime import run_query
        from truss.execution import Ok
        class NoIO:
            def _run_operation(self,*args,**kwargs):raise AssertionError('ordinary native fallback')
        for page in (None,2):
            with self.subTest(page=page),patch('truss._query_runtime.compiler',side_effect=AssertionError('ordinary compiler fallback')):
                result=run_query(NoIO(),object(),sql='SELECT 1',document_ids=('component',),parameters={},
                    maximum_rows=10,maximum_scan_rows=10,maximum_bytes=1024,manifest={},digest='',pin_cursor=None,
                    read_profile=None,page_size=page,engine_program=json.dumps({'version':'umf.engine-catalog/0.4'}))
                self.assertEqual(result,Ok(QueryRefused(code='unsupported_query')))
