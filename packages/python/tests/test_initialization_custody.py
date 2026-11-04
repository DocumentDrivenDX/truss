# SPDX-License-Identifier: MIT OR Apache-2.0
"""JH transport/order/refusal SOURCE controls; never native calendar evidence."""
from contextlib import contextmanager
from hashlib import sha256
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from truss import _initialization_custody as custody
from truss.catalog_runtime import _release
from truss._migration_verify import matches_inventory

ROOT=Path(__file__).resolve().parents[3]


class InitializationCustodyTests(unittest.TestCase):
    def setUp(self):
        self.manifest,self.digest,_=_release();self.policy=custody.source_policy(self.manifest)
        self.row=['journal_runtime_horizon','r','p',False,False,None,True,
                  "FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2027-12-01 00:00:00+00')",'heap',None,None]
        self.pair={'lowerUtc':'2026-10-01T00:00:00.000000Z','upperUtc':'2027-12-01T00:00:00.000000Z'}
        self.value={'profile':custody.PROFILE,'installationId':'12345678-1234-4234-8234-123456789abc',
            'runtimeManifestSha256':self.digest,'initializerSha256':custody.GROUPS_SHA,'installerSha256':self.policy['installerSha256'],
            'databaseOid':42,'ownerOid':43,'backendPid':44,'writerXid':'18446744073709551615','timeZone':'UTC',
            'clockBeforeUtc':'2026-11-03T17:00:00.000000Z','clockAfterUtc':'2026-11-03T17:00:01.000000Z',
            'candidateBoundPairs':[self.pair],'originalRelation':self.row}

    def validate(self,value):
        raw=custody.canonical(value)
        return custody.validate_bytes(raw,sha256(raw).hexdigest(),policy=self.policy,runtime_digest=self.digest)

    def test_original_initializer_schema_and_packaged_source_pins_are_exact(self):
        source=ROOT/'packages/python/src/truss/_catalog_runtime/groups.sql'
        self.assertEqual(sha256(source.read_bytes()).hexdigest(),custody.GROUPS_SHA)
        governed=(ROOT/'docs/helix/02-design/contracts/journal-horizon-initialization-custody-0.1.schema.json').read_bytes()
        self.assertEqual(sha256(governed).hexdigest(),custody.SCHEMA_SHA)
        self.assertEqual(governed,(ROOT/'packages/python/src/truss/_catalog_runtime/initialization-custody.schema.json').read_bytes())
        self.assertEqual(self.validate(self.value),self.value)

    def test_numeric_boolean_float_overflow_and_noncanonical_xid_refuse(self):
        for name in ('databaseOid','ownerOid','backendPid','writerXid'):
            for value in (True,False,0,-1,1.0,None):
                item={**self.value,name:value}
                with self.subTest(name=name,value=value),self.assertRaises((ValueError,ValidationError)):self.validate(item)
        for xid in ('01','+1',' 1','1.0','18446744073709551616'):
            with self.subTest(xid=xid),self.assertRaises((ValueError,ValidationError)):self.validate({**self.value,'writerXid':xid})

    def test_duplicate_extra_noncanonical_and_digest_corrupt_bytes_refuse(self):
        original=custody.canonical(self.value)
        for raw in (original+b' ',original.replace(b'"databaseOid":42',b'"databaseOid":42,"databaseOid":42'),custody.canonical({**self.value,'future':True}),b' '*16385):
            with self.subTest(raw=raw[:30]),self.assertRaises((ValueError,ValidationError)):
                custody.validate_bytes(raw,sha256(raw).hexdigest(),policy=self.policy,runtime_digest=self.digest)
        with self.assertRaises(ValueError):custody.validate_bytes(original,'0'*64,policy=self.policy,runtime_digest=self.digest)

    def test_source_profile_clock_shape_and_unknown_policy_fields_refuse(self):
        for name in ('runtimeManifestSha256','initializerSha256','installerSha256'):
            with self.subTest(name=name),self.assertRaises(ValueError):self.validate({**self.value,name:'0'*64})
        for value in ('infinity','0000-01-01T00:00:00.000000Z','2026-11-03T17:00:00Z','2026-11-03 17:00:00.000000Z','2026-11-03T17:00:00.0000000Z'):
            with self.subTest(value=value),self.assertRaises((ValueError,ValidationError)):self.validate({**self.value,'clockBeforeUtc':value})
        for change in ({'extra':False},{'boundIndex':True},{'maxWindowMicros':300000000},{'qualifiedTimeZones':['UTC']},{'installerSha256':'0'*64}):
            with self.subTest(change=change),self.assertRaises(ValueError):custody.validate_policy({**self.policy,**change},self.manifest)

    def test_unit_boundary_orders_one_exact_whole_groups_unit_between_observations(self):
        groups=(ROOT/'packages/python/src/truss/_catalog_runtime/groups.sql').read_text();events=[]
        before=(self.value['clockBeforeUtc'],'UTC',44,'42',42);after=(self.value['clockAfterUtc'],*before[1:])
        def observe(cursor):events.append('clock');return before if events.count('clock')==1 else after
        def execute(cursor,units):events.append(tuple(units))
        with patch.object(custody,'_zone',return_value='UTC'),patch.object(custody,'observe',side_effect=observe),patch.object(custody,'derive',return_value=([self.pair],[self.row[7]])):
            custody.bracket(object(),['prefix',groups,'suffix'],self.manifest,execute)
        self.assertEqual(events,[('prefix',),'clock',(groups,),'clock',('suffix',)])
        for sources in (['prefix',groups+' ','suffix'],[groups,groups]):
            with self.subTest(sources=len(sources)),self.assertRaises(ValueError):custody.bracket(object(),sources,self.manifest,execute)

    def test_zone_backend_transaction_database_drift_is_postddl_contained_refusal(self):
        groups=(ROOT/'packages/python/src/truss/_catalog_runtime/groups.sql').read_text()
        before=(self.value['clockBeforeUtc'],'UTC',44,'42',42)
        for index,replacement in ((1,'America/New_York'),(2,45),(3,'43'),(4,43)):
            after=list(before);after[0]=self.value['clockAfterUtc'];after[index]=replacement
            with self.subTest(index=index),patch.object(custody,'_zone',return_value='UTC'),patch.object(custody,'observe',side_effect=[before,tuple(after)]):
                with self.assertRaises(custody.InitializationCustodyRefused):custody.bracket(object(),[groups],self.manifest,lambda *_:None)

    def test_nested_rollback_restores_zone_and_preserves_original_error_identity(self):
        class NativeError(Exception):sqlstate='22008'
        error=NativeError('invalid native date')
        class Cursor:
            zone='Pacific/Auckland';row=None
            @property
            def connection(self):return self
            @contextmanager
            def transaction(self):
                previous=self.zone
                try:yield
                except BaseException:self.zone=previous;raise
            def execute(self,query,args=None,**kwargs):
                if query==custody._DERIVE:raise error
                if 'set_config' in query:self.zone=args[0]
                self.row=(self.zone,)
            def fetchone(self):return self.row
        c=Cursor()
        with self.assertRaises(NativeError) as caught:custody.derive(c,'2026-02-30T00:00:00.000000Z',self.value['clockAfterUtc'],'UTC')
        self.assertIs(caught.exception,error);self.assertEqual(c.zone,'Pacific/Auckland');self.assertEqual(caught.exception.sqlstate,'22008')
        self.assertIn('EXTRACT(YEAR FROM c.lo) NOT BETWEEN 1 AND 9999',custody._DERIVE)
        self.assertIn('NOT EXISTS (SELECT 1 FROM candidates',custody._DERIVE)

    def test_new_policy_needs_private_verification_and_defers_only_one_bound_cell(self):
        expected={'relations':[self.row],'routines':[['original','signature','exact definition']]}
        profile={'inventory':expected,'manifest':self.manifest,'initializationPolicies':[self.policy],'initializationAlternatives':[],'definitionAlternatives':[]}
        observed=copy.deepcopy(expected);observed['relations'][0][7]='another literal, not a timestamp-shaped capability'
        self.assertTrue(custody.static_inventory_matches(observed,profile),'Classification only')
        for caller in (None,True,False,{},self.value):self.assertFalse(matches_inventory(observed,profile,initialization_custody=caller))
        for fault in ('routine','othercell','membership'):
            actual=copy.deepcopy(observed)
            if fault=='routine':actual['routines'][0][-1]='changed'
            elif fault=='othercell':actual['relations'][0][3]=True
            else:actual['relations'].append(actual['relations'][0])
            with self.subTest(fault=fault):self.assertFalse(custody.static_inventory_matches(actual,profile))
        for missing in ({},{'initializationPolicies':[]},{'initializationPolicies':[self.policy,self.policy]}):
            self.assertFalse(matches_inventory(observed,{'manifest':self.manifest,'inventory':expected,**missing}))
        old={'inventory':expected,'initializationAlternatives':[{'surface':'relations','identity':['journal_runtime_horizon'],'rows':[self.row,observed['relations'][0]]}]}
        self.assertTrue(matches_inventory(observed,old),'Historical finite-row algorithm remains unchanged')

    def test_new_assembler_refuses_familiar_finite_rows_without_original_custody(self):
        spec=importlib.util.spec_from_file_location('jh_assembler',ROOT/'scripts/assemble-temporal-native-baseline.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        left={'relations':[self.row]};right=copy.deepcopy(left);right['relations'][0][7]='next calendar literal'
        for actual in (left,right):
            with self.subTest(actual=actual),self.assertRaisesRegex(ValueError,'custody'):module.initialization_rules(left,actual)

    def test_closed_jh_set_adds_cases_without_replacing_any_original119(self):
        previous=json.loads(subprocess.check_output(['git','show','4e0b1c32d8ca208d656609789c06c12bb5f06398:scripts/temporal-native-case-ledger.json'],cwd=ROOT))
        current=json.loads((ROOT/'scripts/temporal-native-case-ledger.json').read_bytes())
        for stage,rows in previous['stages'].items():self.assertEqual(rows,current['stages'][stage])
        self.assertEqual(sum(len(v) for v in previous['stages'].values()),119)
        self.assertEqual(len(current['stages']['journal']),10)
        self.assertEqual(len({row['test'] for row in current['stages']['journal']}),10)
