# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fresh-baseline assembly refusal controls; no native profile is issued."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('temporal_baseline_assembler',ROOT/'scripts/assemble-temporal-native-baseline.py')
assembler=importlib.util.module_from_spec(spec);spec.loader.exec_module(assembler)


class TemporalBaselineStagingTests(unittest.TestCase):
    def inventory(self):
        return {'relations':[['journal_runtime_horizon','r','p',False,False,None,True,'native-bound-A','heap',None,None]],
            'routines':[['original-name','original-arguments','original-native-definition']]}

    def test_only_exact_observed_native_horizon_bounds_may_differ(self):
        left=self.inventory();right=copy.deepcopy(left)
        self.assertEqual(assembler.initialization_rules(left,right),[])
        right['relations'][0][7]='native-bound-B'
        rules=assembler.initialization_rules(left,right)
        self.assertEqual(len(rules),1)
        self.assertEqual(rules[0]['rows'],[left['relations'][0],right['relations'][0]])
        self.assertEqual(left,self.inventory(),'Original native observation is never rewritten')

    def test_definition_acl_membership_or_nonbound_relation_differences_refuse(self):
        for fault in ('definition','category','relation','membership','nonbound'):
            left=self.inventory();right=copy.deepcopy(left)
            if fault=='definition':right['routines'][0][-1]='altered'
            if fault=='category':right['unexpected']=[]
            if fault=='relation':right['relations'][0][0]='different_table'
            if fault=='membership':right['relations'].append(copy.deepcopy(right['relations'][0]))
            if fault=='nonbound':right['relations'][0][3]=True
            with self.subTest(fault=fault),self.assertRaises(ValueError):assembler.initialization_rules(left,right)

    def test_no_profile_without_two_genuine_capture_pins_or_over_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'new'
            with self.assertRaises(ValueError):assembler.assemble([],target)
            self.assertFalse(target.exists())
            target.mkdir();(target/'preserved').write_bytes(b'original')
            with self.assertRaisesRegex(ValueError,'existing'):assembler.assemble([{},{}],target)
            self.assertEqual((target/'preserved').read_bytes(),b'original')
