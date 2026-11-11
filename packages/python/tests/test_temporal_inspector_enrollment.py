# SPDX-License-Identifier: MIT OR Apache-2.0
"""PR95 consumer enrollment controls using pure public-API fixtures.

UNIT file fingerprints are deliberately not compiled/public proof. No Core
implementation or JavaScript inspector is copied into the consumer.
"""
import copy
from hashlib import sha256
import json
from pathlib import Path
import shutil
import sys
import tempfile
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import patch

from truss import CatalogDocument,PreparationRejected
from truss.catalog_runtime import _release
from truss._temporal_owner import _inspector,_source_resources,prepare_temporal_catalog

ROOT=Path(__file__).resolve().parents[3]


class TemporalInspectorEnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.package=self.root/'truss';self.bundle=self.package/'_temporal_owner'
        shutil.copytree(ROOT/'packages/python/src/truss/_temporal_owner',self.bundle)
        self.owner=self.root/'umf';self.owner.mkdir()
        entries={}
        for name in ('__init__.py','rust_codegen.py','_rust.py','_rust_core.unit.so'):
            raw=('UNIT fingerprint fixture ONLY: '+name).encode();(self.owner/name).write_bytes(raw)
            entries[name]=sha256(raw).hexdigest()
        source=self.bundle.joinpath('source.json').read_bytes();source_value=json.loads(source)
        self.manifest={'distribution':'umf-core','version':'UNIT-not-a-release','sourceSha256':sha256(source).hexdigest(),
                       'sourceCommit':source_value['sourceCommit'],'installedFiles':entries,'maximumWork':1000000}
        self.write_manifest()
        self.module=ModuleType('umf');self.module.__file__=str(self.owner/'__init__.py');self.module.__path__=[str(self.owner)]
        self.module.__version__='UNIT-not-a-release'
        self.codegen=ModuleType('umf.rust_codegen');self.bridge=ModuleType('umf._rust')
        self.bridge._rust_core=SimpleNamespace(__file__=str(self.owner/'_rust_core.unit.so'));self.module._rust=self.bridge
        self.modules={'umf':self.module,'umf.rust_codegen':self.codegen,'umf._rust':self.bridge}

    def write_manifest(self):
        raw=json.dumps(self.manifest,separators=(',',':')).encode();(self.bundle/'manifest.json').write_bytes(raw)
        if not hasattr(self,'native'):self.native=copy.deepcopy(_release()[0])
        self.native['files']['../_temporal_owner/source.json']=sha256((self.bundle/'source.json').read_bytes()).hexdigest()
        self.native['files']['../_temporal_owner/manifest.json']=sha256(raw).hexdigest()

    def install_fixture(self,engine_type):
        from importlib import metadata
        original_version=metadata.version
        self.codegen.CodegenEngine=engine_type
        patches=(patch.dict(sys.modules,self.modules),
            patch('truss._temporal_owner.files',side_effect=lambda name:self.package if name=='truss' else self.owner),
            patch('truss._temporal_owner.metadata.version',side_effect=lambda name:
                'UNIT-not-a-release' if name=='umf-core' else original_version(name)),
            patch('truss.catalog_runtime._release',return_value=(self.native,'UNIT-source-not-native',())))
        for item in patches:item.start();self.addCleanup(item.stop)

    def engine_type(self,*,unknown=False):
        path=ROOT/'packages/python/tests/fixtures/temporal/native-guard-owner-inspection.json'
        golden=json.loads(path.read_bytes());self.golden=golden;calls=self.calls=[];constructed=self.constructed=[]
        class Engine:
            def __init__(self,resources,*,max_work):constructed.append((resources,max_work))
            def call(self,operation,request):
                calls.append((operation,copy.deepcopy(request)))
                if unknown:raise ValueError('UNKNOWN_OPERATION')
                result=copy.deepcopy(golden['result']);result['opaqueFuture']={'preserved':['whole','result']}
                result['diagnostics'].append({'code':'UNIT-NOTE','severity':'info','message':'retained diagnostic','future':True})
                return {'ok':True,'result':result}
            def inspect_access_views(self,document,selected,bindings=(),source_id='logical'):
                return self.call('inspectAccessViews',{'document':document,'selected':selected,'bindings':bindings,'sourceId':source_id})['result']
        return Engine

    def test_original_pr95_source_resources_and_actual_public_api_shape_are_enrolled(self):
        self.install_fixture(self.engine_type())
        engine,pin=_inspector()
        self.assertEqual(pin,{'identity':'umf-core','version':'UNIT-not-a-release',
                             'sha256':sha256((self.bundle/'manifest.json').read_bytes()).hexdigest()})
        resources,maximum=self.constructed[0]
        self.assertEqual(maximum,1000000);self.assertEqual(len(resources),9)
        self.assertTrue(callable(engine.inspect_access_views));self.assertTrue(callable(engine.call))
        self.assertEqual(json.loads((self.bundle/'source.json').read_bytes())['sourceCommit'],
                         'e3f38ef6f05ae636d2837f9d69f8d6805222664b')

    def test_public_preparation_retains_whole_owner_result_and_original_noncompact_source(self):
        self.install_fixture(self.engine_type())
        document=CatalogDocument('adoc','unit-r1',json.dumps(self.golden['request']['document'],ensure_ascii=True,indent=2).encode()+b'\n')
        prepared=prepare_temporal_catalog((document,))
        self.assertEqual(len(self.calls),1)
        operation,request=self.calls[0]
        self.assertEqual(operation,'inspectAccessViews');self.assertEqual(request['sourceId'],'logical')
        self.assertEqual(request['bindings'],());self.assertEqual(request['document'],self.golden['request']['document'])
        self.assertEqual(request['selected'],self.golden['request']['selected'])
        summary=json.loads(prepared.report_evidence_bytes);packet=summary['documents'][0]['inspection']
        self.assertEqual(packet['contentSha256'],sha256(document.content).hexdigest())
        retained=json.loads(packet['resultJson'])
        self.assertEqual(retained['opaqueFuture'],{'preserved':['whole','result']})
        self.assertEqual(retained['diagnostics'][-1]['future'],True)
        self.assertEqual(json.loads(prepared.archive_documents_bytes)[0]['originalText'].encode(),document.content)
        declarations=json.loads(prepared.declarations_bytes)
        local=next(f for r in declarations[0]['records'] for f in r['fields'] if 'nativeDescriptor' in f)
        self.assertEqual(local['declaration']['scalarType'],'timestamp')
        self.assertEqual(local['nativeDescriptor']['nativeScalarType'],'localTimestamp')

    def test_old_binding_without_public_inspection_never_uses_generic_call_as_fallback(self):
        calls=[]
        class OldEngine:
            def __init__(self,resources,*,max_work):pass
            def call(self,*args):calls.append(args);raise ValueError('UNKNOWN_OPERATION')
        self.install_fixture(OldEngine)
        with self.assertRaises(PreparationRejected) as caught:_inspector()
        self.assertEqual(caught.exception.reason,'producer_unavailable')
        self.assertEqual(calls,[])

    def test_unknown_operation_from_compiled_owner_explicitly_refuses_without_packet(self):
        self.install_fixture(self.engine_type(unknown=True))
        document=CatalogDocument('adoc','unit-r1',json.dumps(self.golden['request']['document']).encode())
        with patch('truss._temporal_owner.inspection_packet',side_effect=AssertionError('fabricated inspection packet')):
            with self.assertRaises(PreparationRejected) as caught:prepare_temporal_catalog((document,))
        self.assertEqual(caught.exception.reason,'producer_unavailable')
        self.assertEqual(len(self.calls),1)

    def test_semantic_refusal_preserves_all_ordered_diagnostics_and_whole_result(self):
        original_type=self.engine_type()
        class DiagnosticEngine(original_type):
            def call(self,*args):
                response=super().call(*args)
                response['result']['diagnostics'] += [
                    {'code':'UNIT-ERROR','severity':'error','message':'first','opaque':[2,1]},
                    {'code':'UNIT-FATAL','severity':'fatal','message':'second','future':{'kept':True}}]
                return response
        self.install_fixture(DiagnosticEngine)
        document=CatalogDocument('adoc','unit-r1',json.dumps(self.golden['request']['document']).encode())
        with self.assertRaises(PreparationRejected) as caught:prepare_temporal_catalog((document,))
        rejection=caught.exception
        self.assertEqual(rejection.reason,'unsupported_profile')
        diagnostics=[json.loads(raw) for raw in rejection.diagnostics]
        self.assertEqual([d['code'] for d in diagnostics],['UNIT-NOTE','UNIT-ERROR','UNIT-FATAL'])
        self.assertEqual(diagnostics[1]['opaque'],[2,1])
        whole=json.loads(rejection.__cause__.original_result_json)
        self.assertEqual(whole['diagnostics'],diagnostics)
        self.assertEqual(whole['opaqueFuture'],{'preserved':['whole','result']})

    def test_source_binary_resource_and_budget_drift_refuse_before_engine_construction(self):
        self.install_fixture(self.engine_type())
        for fault in ('binary','resource','source','budget','runtime-version','unloaded-native'):
            with self.subTest(fault=fault):
                if fault=='binary':target=self.owner/'rust_codegen.py';old=target.read_bytes();target.write_bytes(old+b' changed')
                elif fault=='resource':target=self.bundle/'resources/coreSchema.json';old=target.read_bytes();target.write_bytes(old+b' ')
                elif fault=='source':target=self.bundle/'source.json';old=target.read_bytes();target.write_bytes(old+b' ')
                elif fault=='budget':self.manifest['maximumWork']=True;self.write_manifest()
                elif fault=='runtime-version':self.module.__version__='UNIT-different-runtime'
                else:self.bridge._rust_core.__file__=str(self.root/'not-enrolled.so')
                try:
                    with self.assertRaises(PreparationRejected):_inspector()
                    self.assertEqual(self.constructed,[])
                finally:
                    if fault in ('binary','resource','source'):target.write_bytes(old)
                    elif fault=='budget':self.manifest['maximumWork']=1000000;self.write_manifest()
                    elif fault=='runtime-version':self.module.__version__='UNIT-not-a-release'
                    else:self.bridge._rust_core.__file__=str(self.owner/'_rust_core.unit.so')

    def test_source_resources_alone_never_claim_compiled_capability(self):
        self.install_fixture(self.engine_type());(self.bundle/'manifest.json').unlink()
        with self.assertRaises(PreparationRejected):_inspector()
        self.assertEqual(self.constructed,[])

    def test_composed_binary_source_can_keep_exact_original_resource_pins(self):
        self.install_fixture(self.engine_type())
        original=(self.bundle/'source.json').read_bytes()
        self.manifest['sourceCommit']='8305b11b031b90c4bcdb5a29e100074ef7499042'
        self.write_manifest()
        engine,pin=_inspector()
        self.assertTrue(callable(engine.inspect_access_views))
        self.assertEqual((self.bundle/'source.json').read_bytes(),original)
        self.assertEqual(self.manifest['sourceSha256'],sha256(original).hexdigest())
        self.assertEqual(pin['version'],'UNIT-not-a-release')

    def test_archived_pr95_resource_bytes_refuse_in_canonical_S_bundle_before_engine(self):
        self.install_fixture(self.engine_type())
        archived=ROOT/'docs/helix/04-build/evidence/temporal-native/canonical-S-resource-adoption-source/original-pr95'
        original=json.loads((archived/'source.json').read_bytes())
        self.assertEqual(original['sourceCommit'],'f629cda829223fb889d1faf25a2543e40689146d')
        selected=json.loads((self.bundle/'source.json').read_bytes())
        changed=[]
        for name,entry in selected['resources'].items():
            old=(archived/entry['file']).read_bytes();target=self.bundle/entry['file'];current=target.read_bytes()
            self.assertEqual(sha256(old).hexdigest(),original['resources'][name]['sha256'])
            self.assertEqual(sha256(current).hexdigest(),entry['sha256'])
            if old==current:continue
            changed.append(name)
            with self.subTest(resource=name):
                target.write_bytes(old)
                try:
                    with self.assertRaises(PreparationRejected):_inspector()
                    self.assertEqual(self.constructed,[])
                finally:target.write_bytes(current)
        self.assertEqual(set(changed),{'coreSchema','referenceSchema','packageSchema','constraints','domainPolicy'})
