# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original-owner comparison for the bounded required set-value consumer."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from truss.weft import _decode
from truss._bulk_set_values import check_set_literal,SetValueRefusal


def field(family,facets=None):
    return {'id':'value','name':'value','kind':'field','scalarType':family,'cardinality':'one','nullability':'required','extensions':{},'facets':facets or {}}


def cases():
    values=[]
    def add(f,l):values.append({'field':f,'literal':l})
    integer=field('integer',{'integerWidth':{'bits':64,'signed':False}})
    for token in ['0','-0','0e9999999999999999999999999999999999999999999','9007199254740993','18446744073709551615','18446744073709551616','-1','1.0','10e-1','1e-1','NaN','01','1\n','1e10000000']:
        add(integer,{'integerToken':token})
    for bits in (1,8,64,9007199254740991):
        f=field('integer',{'integerWidth':{'bits':bits,'signed':True}})
        for token in ['-128','127','128','-129','0','1']:
            add(f,{'integerToken':token})
    ranged=field('integer',{'range':{'min':{'integerToken':'1'},'max':{'integerToken':'3'},'minInclusive':False}})
    for token in ['1','2','3','4','2.0','20e-1']:add(ranged,{'integerToken':token})
    for text in ['','a','😀','e\u0301','é','a\x00','\ud800']:
        add(field('string',{'length':{'min':1,'max':1,'unit':'unicode-scalar'}}),{'string':text})
    for value in [True,False,0,'true',None]:add(field('boolean'),{'boolean':value})
    allowed=field('integer');allowed['allowedValues']=[{'integerToken':'10e-1'}]
    for token in ['1','1.0','2']:add(allowed,{'integerToken':token})
    for family,literal in [('boolean',None),('integer',{'string':'1'}),('string',{'string':'x','other':True})]:add(field(family),literal)
    return values


class SetValueTests(unittest.TestCase):
    def test_agrees_with_original_umf_evaluator(self):
        corpus=cases();oracle=Path(__file__).with_name('owner_set_values.ts')
        run=subprocess.run(['bun',str(oracle)],input=json.dumps(corpus),capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr)
        expected=json.loads(run.stdout);actual=[]
        for case in corpus:
            before=copy.deepcopy(case)
            try:check_set_literal(case['field'],case['literal']);actual.append(True)
            except SetValueRefusal:actual.append(False)
            self.assertEqual(case,before)
        self.assertEqual(actual,expected)
        self.assertTrue(any(actual));self.assertTrue(any(not value for value in actual))

    def test_original_numeric_metadata_spellings_are_exact(self):
        for spelling in ['8.0','8e0','8','9007199254740991.0']:
            raw=(' {"kind":"field","scalarType":"integer","cardinality":"one","nullability":"required","extensions":{},"facets":{"integerWidth":{"bits":'+spelling+',"signed":true}}}').encode()
            _,f=_decode(raw,1048576,'fixture')
            check_set_literal(f,{'integerToken':'127'})
        for spelling in ['8.1','true','9007199254740992.0','1e1000000000','1e-1000000000']:
            raw=('{"kind":"field","scalarType":"integer","cardinality":"one","nullability":"required","facets":{"integerWidth":{"bits":'+spelling+',"signed":true}}}').encode()
            _,f=_decode(raw,1048576,'fixture')
            with self.assertRaises(SetValueRefusal):check_set_literal(f,{'integerToken':'127'})

    def test_unknown_and_unsupported_domains_refuse(self):
        for f in [field('decimal'),field('integer',{'future':{}}),{**field('string'),'extensions':{'future':{}}},{**field('string'),'nullability':'absent-allowed'}]:
            with self.assertRaises(SetValueRefusal):check_set_literal(f,{'string':'x'})

    def test_large_compact_exponent_and_original_expansion_boundary(self):
        # Independent subprocess deadline catches the prior >55-second ratio
        # conversion without claiming a universal native-operation time bound.
        program='''
from truss._bulk_set_values import check_set_literal, SetValueRefusal
base={'kind':'field','scalarType':'integer','cardinality':'one','nullability':'required'}
check_set_literal(base,{'integerToken':'1e3999999'})
for token in ('1e4000000','1e-1'):
 try:check_set_literal(base,{'integerToken':token})
 except SetValueRefusal:pass
 else:raise AssertionError('out-of-domain integer accepted')
small={**base,'facets':{'integerWidth':{'bits':8,'signed':True}}}
try:check_set_literal(small,{'integerToken':'1e3999999'})
except SetValueRefusal:pass
else:raise AssertionError('huge integer accepted by signed8')
'''
        run=subprocess.run([sys.executable,'-c',program],capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)
