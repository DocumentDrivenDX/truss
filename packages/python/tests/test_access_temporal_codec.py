# SPDX-License-Identifier: MIT OR Apache-2.0
from datetime import date, datetime, timedelta, timezone
import json
import unittest
from pathlib import Path

from pydantic import BaseModel

from truss.access import _typed_rows
from umf_access.engine_catalog import _engine_parameter_fields
from truss.access import _engine_verification_sample
from truss._query_runtime import (_checked_temporal_engine_program, _temporal_parameter_value,
                                 _temporal_cursor_envelope, _temporal_cursor_result_value,
                                 _temporal_cursor_typed_value, _temporal_page_result,
                                 _decode_rows, _validate_temporal_cursor_value)
from truss.contracts import LocalTimestampValue, TextValue
from truss.query import QueryRows, QueryAbsent
from truss.access import _typed_rows


class TemporalResult(BaseModel):
    day: date
    instant: datetime
    local: datetime


class TemporalEntry:
    result = TemporalResult


def output(name: str, carrier: str, kind: str) -> dict:
    return {"name": name, "carrier": carrier, "nullable": False, "missing": False,
            "decoder": {"profile": "truss-temporal/0.1", "kind": kind}}


class NativeTemporalCodecTests(unittest.TestCase):
    def test_explicit_native_engine_version_gate_is_closed(self):
        request = {"interfaceVersion": "weft-compile/0.2.10",
                   "temporalProfile": "umf.weft-binding-temporal/0.2",
                   "target": {"backendVersion": "0.4.47",
                              "targetProfile": "truss-runtime-pg18.6/0.7-temporal-candidate"},
                   "temporalParameters": {}}
        program = {"version": "weft.engine-read/0.4", "status": "compiled",
                   "compiler": "truss-runtime-temporal",
                   "temporalProfile": "umf.weft-binding-temporal/0.2", "request": request}
        self.assertEqual(_checked_temporal_engine_program(json.dumps(program)), program)
        legacy = dict(program, version="weft.engine-read/0.1", compiler="truss-runtime")
        legacy.pop("temporalProfile")
        self.assertIsNone(_checked_temporal_engine_program(json.dumps(legacy)))
        for bad in (dict(program, version="weft.engine-read/0.3"),
                    dict(program, temporalProfile="umf.weft-binding-temporal/0.1"),
                    dict(program, compiler="truss-runtime")):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                _checked_temporal_engine_program(json.dumps(bad))

    def test_temporal_parameter_conversion_uses_the_selected_kind(self):
        self.assertEqual(_temporal_parameter_value("date", date(2000, 2, 29)), "2000-02-29")
        self.assertEqual(_temporal_parameter_value("instant", datetime(1970, 1, 1, 1, tzinfo=timezone.utc)), "3600000000")
        self.assertEqual(_temporal_parameter_value("instant", datetime(1969, 12, 31, 19, 0, 0, 1, tzinfo=timezone(-timedelta(hours=5)))), "1")
        self.assertEqual(_temporal_parameter_value("local", datetime(2024, 11, 3, 1, 30)), "2024-11-03T01:30:00.000000")
        with self.assertRaises(ValueError):
            _temporal_parameter_value("date", datetime(2000, 2, 29))
        with self.assertRaises(ValueError):
            _temporal_parameter_value("instant", datetime(2024, 1, 1))
        with self.assertRaises(ValueError):
            _temporal_parameter_value("local", datetime(2024, 1, 1, tzinfo=timezone.utc))

    def test_target_verification_sample_uses_original_temporal_kind(self):
        program={'compiler':'truss-runtime-temporal','temporalProfile':'umf.weft-binding-temporal/0.2',
                 'request':{'parameters':{'label':{'family':'string','value':'x'}},
                            'temporalParameters':{'day':{'kind':'date','value':'2000-02-29'},
                                                  'instant':{'kind':'instant','value':'-1'},
                                                  'wall':{'kind':'local','value':'2024-11-03T01:30:00.000000'}}}}
        sample=_engine_verification_sample(program)
        self.assertEqual(sample['label'],'x')
        self.assertEqual(sample['day'],date(2000,2,29))
        self.assertEqual(sample['instant'],datetime(1969,12,31,23,59,59,999999,tzinfo=timezone.utc))
        self.assertEqual(sample['wall'],datetime(2024,11,3,1,30))
        class Parameters(BaseModel):
            day:date
            instant:datetime
            wall:datetime
            label:str
        typed=Parameters.model_validate(sample)
        self.assertIsNone(typed.wall.tzinfo)
        self.assertIsNotNone(typed.instant.tzinfo)
        for bad in ({'kind':'date','value':'20000229'},
                    {'kind':'instant','value':'-0'},
                    {'kind':'local','value':'2024-11-03T01:30:00-04:00'}):
            forged={**program,'request':{**program['request'],'temporalParameters':{'x':bad}}}
            with self.subTest(bad=bad),self.assertRaises(ValueError):_engine_verification_sample(forged)

    def test_native_temporal_parameter_signature_uses_owner_selected_kind(self):
        class DateParameters(BaseModel):
            model_config={'strict':True,'extra':'forbid'}
            boundary:date
        class InstantParameters(BaseModel):
            model_config={'strict':True,'extra':'forbid'}
            boundary:datetime
        for model,kind,carrier in ((DateParameters,'date','date'),
                                   (InstantParameters,'instant','timestamp'),
                                   (InstantParameters,'local','timestamp')):
            self.assertEqual(_engine_parameter_fields(model,{
                'boundary':{'kind':kind,'value':'selected-by-original-program'}}),
                [{'name':'boundary','carrier':carrier,'nullable':False}])
        with self.assertRaises(ValueError):
            _engine_parameter_fields(DateParameters,{'boundary':{'kind':'instant','value':'1'}})
        with self.assertRaises(ValueError):
            _engine_parameter_fields(InstantParameters,{})

    def test_temporal_page_cursor_preserves_full_tagged_tuple_and_closed_states(self):
        row=(TextValue(kind="date",text="2024-02-29"), TextValue(kind="timestamp",text="1969-12-31T19:00:00.000001-05:00"), LocalTimestampValue(text="2024-11-03T01:30:00.123456"),
             "A", 7, True, "present", "null", "missing", "present")
        slots=(
            {"valueOutput":0,"stateOutput":6,"carrier":"date","temporal":"date"},
            {"valueOutput":1,"stateOutput":6,"carrier":"timestamp","temporal":"instant"},
            {"valueOutput":2,"stateOutput":6,"carrier":"localTimestamp","temporal":"local"},
            {"valueOutput":3,"stateOutput":6,"carrier":"string","temporal":None},
            {"valueOutput":4,"stateOutput":6,"carrier":"integer","temporal":None},
            {"valueOutput":5,"stateOutput":6,"carrier":"boolean","temporal":None},
        )
        values=[_temporal_cursor_envelope(row,slot) for slot in slots]
        self.assertEqual(values[:3], [
            {"state":"temporal","kind":"date","value":"2024-02-29"},
            {"state":"temporal","kind":"instant","value":"1"},
            {"state":"temporal","kind":"local","value":"2024-11-03T01:30:00.123456"},
        ])
        self.assertEqual(values[3:], [
            {"state":"present","carrier":"string","value":"A"},
            {"state":"present","carrier":"integer","value":"7"},
            {"state":"present","carrier":"boolean","value":"true"},
        ])
        self.assertTrue(all(_validate_temporal_cursor_value(value) for value in values))
        self.assertTrue(_validate_temporal_cursor_value({"state":"null"}))
        self.assertTrue(_validate_temporal_cursor_value({"state":"missing"}))
        self.assertTrue(_validate_temporal_cursor_value({"state":"temporal","kind":"instant","value":"-1"}))
        self.assertEqual(_temporal_cursor_typed_value(row[0],slots[0]),values[0])
        self.assertEqual(_temporal_cursor_typed_value(row[1],slots[1]),values[1])
        self.assertEqual(_temporal_cursor_typed_value(row[2],slots[2]),values[2])
        self.assertEqual(_temporal_cursor_result_value((row[0],"present"),dict(slots[0],valueOutput=0,stateOutput=1)),row[0])
        self.assertIsInstance(_temporal_cursor_result_value((QueryAbsent(),"missing"),dict(slots[0],valueOutput=0,stateOutput=1)),QueryAbsent)
        for inconsistent in ((None,"present"),(TextValue(kind="date",text="2024-02-29"),"null"),
                             ("2024-02-29","missing")):
            with self.subTest(inconsistent=inconsistent), self.assertRaises(ValueError):
                _temporal_cursor_envelope(inconsistent,dict(slots[0],valueOutput=0,stateOutput=1))
            with self.subTest(result_inconsistent=inconsistent), self.assertRaises(ValueError):
                _temporal_cursor_result_value(inconsistent,dict(slots[0],valueOutput=0,stateOutput=1))
        for forged in ({"state":"null","value":None},
                       {"state":"temporal","kind":"local","value":"2024-11-03 01:30:00.123456"},
                       {"state":"temporal","kind":"instant","value":"1970-01-01T00:00:00Z"},
                       {"state":"temporal","kind":"instant","value":"01"},
                       {"state":"present","carrier":"integer","value":"01"}):
            with self.subTest(forged=forged):
                self.assertFalse(_validate_temporal_cursor_value(forged))

    def test_owner_value_json_transport_decodes_through_typed_page_and_next_cursor(self):
        fixtures=json.loads((Path(__file__).parent/'fixtures'/'pws03-temporal-page-metadata.json').read_text())['cases']
        cases={'date':('2000-02-29',date(2000,2,29)),
               'instant':('1969-12-31T19:00:00.000001-05:00',datetime(1970,1,1,0,0,0,1,tzinfo=timezone.utc)),
               'local':('2024-11-03T01:30:00.123456',datetime(2024,11,3,1,30,0,123456))}
        for kind,(token,expected) in cases.items():
            with self.subTest(kind=kind):
                case=fixtures[kind];columns=case['columns'];page_meta=case['page']
                slots=page_meta['sortSlots'];visible=page_meta['visibleOutputs'];raw=[]
                for suffix in ('a','b','c','d'):
                    row=[None]*len(columns)
                    for column in columns[:visible]:
                        row[column['position']-1]=json.dumps({'state':'value','value':token})
                    for index,slot in enumerate(slots):
                        field=slot['field']['element']
                        value=token if slot['temporal'] is not None else 'group' if field=='A-value' else suffix
                        envelope={'state':'value','value':value} if slot.get('nullable') or slot.get('missing') else value
                        row[slot['valueOutput']]=json.dumps(envelope)
                        row[slot['stateOutput']]='present'
                    raw.append(tuple(row))
                artifact={'columns':columns,'logicalPlan':{'base':{'typeGraph':case['typeGraph']}}}
                decoded=_decode_rows(raw,artifact,10,10000)
                temporal_output=case['outputs'][0]
                model_field={'date':date,'instant':datetime,'local':datetime}[kind]
                model=__import__('pydantic').create_model(f'Result_{kind}',occurred_at=(model_field,...))
                entry=type('Entry',(),{'result':model})()
                program={'version':'weft.engine-page/0.4','compiler':'truss-runtime-temporal',
                         'temporalProfile':'umf.weft-binding-temporal/0.2','outputs':case['outputs']}
                page=_temporal_page_result(decoded,page_meta,page_meta['pageSize'],'fixture-context',7,None)
                typed=_typed_rows(entry,program,page)
                self.assertEqual(type(decoded.rows[0][0]),TextValue if kind!='local' else LocalTimestampValue)
                self.assertEqual(typed[0].occurred_at,expected)
                self.assertEqual(page.next_sort_values,('group','c'))
                cursor=json.loads(page.next_cursor.original_bytes)
                self.assertEqual(cursor['profile'],'truss-engine-page/0.4')
                self.assertEqual(cursor['after']['key'],[
                    {'state':'present','carrier':'string','value':'group'},
                    {'state':'present','carrier':'string','value':'c'}])
                if kind=='instant':
                    self.assertEqual(cursor['after']['sortValues'][0],{'state':'temporal','kind':'instant','value':'1'})
                elif kind=='date':
                    self.assertEqual(cursor['after']['sortValues'][0],{'state':'temporal','kind':'date','value':'2000-02-29'})
                else:
                    self.assertEqual(cursor['after']['sortValues'][0],{'state':'temporal','kind':'local','value':'2024-11-03T01:30:00.123456'})

    def test_native_engine_temporal_envelopes_compose_with_umf_exact_result_decoder(self):
        outputs = [output("day", "date", "date"), output("instant", "timestamp", "instant"),
                   output("local", "localTimestamp", "local")]
        program = {"version": "weft.engine-read/0.4", "compiler": "truss-runtime-temporal",
                   "temporalProfile": "umf.weft-binding-temporal/0.2", "outputs": outputs}
        native = QueryRows(columns=("day", "instant", "local"), rows=((
            TextValue(kind="date", text="2000-02-29"),
            TextValue(kind="timestamp", text="1969-12-31T19:00:00.000001-05:00"),
            LocalTimestampValue(text="2024-11-03T01:30:00.123456"),
        ),), catalog_revision=1)
        rows = _typed_rows(TemporalEntry(), program, native)
        self.assertEqual(rows, [TemporalResult(day=date(2000, 2, 29),
                                               instant=datetime(1970, 1, 1, 0, 0, 0, 1, tzinfo=timezone.utc),
                                               local=datetime(2024, 11, 3, 1, 30, 0, 123456))])

    def test_native_engine_temporal_output_kind_mismatch_refuses(self):
        outputs = [output("day", "date", "date"), output("instant", "timestamp", "instant"),
                   output("local", "localTimestamp", "local")]
        program = {"version": "weft.engine-read/0.4", "compiler": "truss-runtime-temporal",
                   "temporalProfile": "umf.weft-binding-temporal/0.2", "outputs": outputs}
        rest = (TextValue(kind="timestamp", text="2000-02-29T00:00:00Z"),
                LocalTimestampValue(text="2000-02-29T00:00:00.000000"))
        for wrong in (TextValue(kind="timestamp", text="2000-02-29T00:00:00Z"),
                      LocalTimestampValue(text="2000-02-29T00:00:00.000000"), "2000-02-29"):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                native = QueryRows(columns=("day", "instant", "local"), rows=((wrong, *rest),), catalog_revision=1)
                _typed_rows(TemporalEntry(), program, native)
