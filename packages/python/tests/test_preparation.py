"""Public preparation with original owner assets; no native acceptance claims."""
import base64
import hashlib
import json
from pathlib import Path
import unittest
import sys
import subprocess
from truss.preparation import _capture
from unittest.mock import patch
from truss import CatalogDocument, PreparationRejected, prepare_acceptance

ROOT=Path(__file__).resolve().parents[3]
CONFIG=json.loads((ROOT/'docs/helix/02-design/contracts/bindings/acceptance-input-capacity-v0.1.fixture.json').read_text())['input']
CONFIG={k:v for k,v in CONFIG.items() if k not in ('interfaceVersion','documents')}
CONFIG['binding']={'state':'absent'}
CONFIG['transforms']=[]

def document(identity):
    value={'umf':'0.7.0','id':identity,'vocabularies':{},'extensions':{},'modules':[{'id':'m','namespace':'m','elements':[
        {'id':'Item','kind':'record','members':[{'module':'m','element':'label'}],'extensions':{}},
        {'id':'label','kind':'field','scalarType':'string','nullability':'required','cardinality':'one','extensions':{}}]}]}
    return CatalogDocument(identity,'r1',(' \n'+json.dumps(value)+'\n').encode())

def prepare(documents,configuration=None):
    return prepare_acceptance(documents,json.dumps(CONFIG if configuration is None else configuration).encode(),bun_executable='/opt/homebrew/bin/bun')

class PreparationTests(unittest.TestCase):
    def test_public_original_documents_and_qualified_declarations(self):
        documents=(document('first'),document('second'))
        result=prepare(documents)
        self.assertFalse(result.provenance.installation_profiles_verified)
        self.assertEqual(result.provenance.scope,'original_umf_preparation_only')
        self.assertEqual([d['records'][0]['documentId'] for d in json.loads(result.declarations_bytes)],['first','second'])
        for original,carrier,observed in zip(documents,result.input()['documents'],result.documents):
            self.assertEqual(base64.b64decode(carrier['artifact']['bytesBase64']),original.content)
            self.assertEqual(carrier['artifact']['sha256'],hashlib.sha256(original.content).hexdigest())
            self.assertEqual(observed.document,original)
            self.assertEqual(observed.observation()['target']['umf'],'0.8.0')
        copy=result.input();copy['documents'].clear()
        self.assertEqual(len(result.input()['documents']),2)
        self.assertNotIn('acceptedIds',result.input())

    def test_complete_owner_observations_retain_separate_pins_and_sources(self):
        from truss._catalog_owner_evidence import require_catalog_owner_evidence
        result=prepare((document('first'),document('second')))
        evidence=json.loads(result.report_evidence_bytes)
        observations,coverage,core=require_catalog_owner_evidence(result,evidence)
        self.assertGreater(int(coverage['observationsRequired']),0)
        self.assertFalse(core['complete'])
        self.assertEqual(observations['profile']['version'],observations['fieldProfile']['version'])
        self.assertNotEqual(observations['profile']['version'],observations['scalarProfile']['version'])
        self.assertNotEqual(observations['scalarProfile']['version'],observations['membersProfile']['version'])
        self.assertTrue(any(o['operation']=='scalarType' for o in observations['observations']))
        for mutation in ('missing','digest','profile','coverage'):
            changed=json.loads(result.report_evidence_bytes)
            if mutation=='missing':del changed['ownerObservations']
            elif mutation=='digest':changed['ownerObservations']['observations'][0]['evidence']['sha256']='0'*64
            elif mutation=='profile':changed['ownerObservations']['scalarProfile']['version']='substitute'
            else:changed['observationCoverage']['observationsRequired']='0'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                require_catalog_owner_evidence(result,changed)

    def test_adjusted_empty_bridge_observation_inventory_refuses_report_use(self):
        from truss._catalog_owner_evidence import require_catalog_owner_evidence
        original=_capture
        def altered(command,**kwargs):
            completed=original(command,**kwargs)
            if command[-1].endswith('bridge.js'):
                reply=json.loads(completed.stdout)
                reply['reportEvidence']['ownerObservations']['observations']=[]
                coverage=reply['reportEvidence']['observationCoverage']
                coverage.update(observationsRequired='0',observationsAvailable='0',unavailable=[],availability='available')
                return subprocess.CompletedProcess(command,completed.returncode,json.dumps(reply).encode(),completed.stderr)
            return completed
        with patch('truss.preparation._capture',altered):
            result=prepare((document('dropped'),))
        with self.assertRaises(ValueError):
            require_catalog_owner_evidence(result,json.loads(result.report_evidence_bytes))

    def test_unavailable_version_specific_owner_operations_are_retained(self):
        from truss._catalog_owner_evidence import require_catalog_owner_evidence
        value=json.loads(document('current').content)
        value['umf']='0.8.0'
        result=prepare((CatalogDocument('current','r1',json.dumps(value).encode()),))
        evidence=json.loads(result.report_evidence_bytes)
        observations,coverage,core=require_catalog_owner_evidence(result,evidence)
        self.assertEqual(coverage['availability'],'incomplete')
        self.assertGreater(len(coverage['unavailable']),0)
        self.assertTrue(any(o['operation']=='scalarType' and o['code']=='CORE_SCALAR_TYPE_VERSION' for o in coverage['unavailable']))
        self.assertTrue(any(o['result']['state']=='unavailable' for o in observations['observations']))
        self.assertGreater(len(core['deferred']),0)
        self.assertFalse(core['complete'])

    def test_owner_observations_execute_from_copied_package_outside_checkout(self):
        import os
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory(prefix='truss-owner-package-') as directory:
            shutil.copytree(ROOT/'packages/python/src/truss',Path(directory)/'truss',ignore=shutil.ignore_patterns('__pycache__'))
            request={'documents':[{'identity':'outside','content':base64.b64encode(document('outside').content).decode()}],'configuration':CONFIG}
            code="""import sys,json,base64
from truss import CatalogDocument,prepare_acceptance
from truss._catalog_owner_evidence import require_catalog_owner_evidence
request=json.load(sys.stdin)
prepared=prepare_acceptance(tuple(CatalogDocument(d['identity'],'r1',base64.b64decode(d['content'])) for d in request['documents']),json.dumps(request['configuration']).encode(),bun_executable='/opt/homebrew/bin/bun')
_,coverage,_=require_catalog_owner_evidence(prepared,json.loads(prepared.report_evidence_bytes))
print(coverage['observationsRequired'])
"""
            environment=dict(os.environ, PYTHONPATH=directory)
            result=subprocess.run([sys.executable,'-c',code],input=json.dumps(request).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=directory,env=environment,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            self.assertGreater(int(result.stdout),0)

    def test_unknown_extension_original_is_preserved(self):
        source=document('future')
        value=json.loads(source.content)
        value['vocabularies']={'future.vendor':{'version':'99.0.0'}}
        value['extensions']={'future.vendor':{'opaque':['keep',{'text':'雪'}]}}
        raw=json.dumps(value,ensure_ascii=False).encode()
        result=prepare((CatalogDocument('future','r1',raw),))
        self.assertEqual(base64.b64decode(result.input()['documents'][0]['artifact']['bytesBase64']),raw)
        archived=json.loads(result.archive_documents_bytes)[0]
        self.assertEqual(archived['originalText'],raw.decode())
        self.assertEqual(result.documents[0].observation()['source']['extensions'],value['extensions'])

    def test_report_capacity_does_not_reject_valid_preparation(self):
        value=json.loads(document('ext').content)
        value['vocabularies']={f'vendor{i}':{'version':'99.0.0'} for i in range(70)}
        value['extensions']={f'vendor{i}':{'opaque':True} for i in range(70)}
        value['future_padding']='x'*60000
        raw=json.dumps(value).encode()
        result=prepare((CatalogDocument('ext','r1',raw),))
        self.assertEqual(result.documents[0].document.content,raw)
        evidence=json.loads(result.report_evidence_bytes)
        self.assertEqual(evidence['ingress']['state'],'unavailable')

    def test_combined_report_output_capacity_preserves_preparation(self):
        value=json.loads(document('ext').content)
        value['vocabularies']={f'vendor{i}':{'version':'99.0.0'} for i in range(40)}
        value['extensions']={f'vendor{i}':{'opaque':True} for i in range(40)}
        value['future_padding']='x'*60000
        value.update({f'future_extra_{i}':True for i in range(20)})
        result=prepare((CatalogDocument('ext','r1',json.dumps(value).encode()),))
        self.assertEqual(json.loads(result.report_evidence_bytes)['ingress']['state'],'unavailable')

    def test_duplicate_json_key_cannot_be_silently_overwritten(self):
        with self.assertRaises(PreparationRejected):
            prepare_acceptance((document('first'),),b'{"binding":{"state":"absent"},"binding":{"state":"absent"}}',bun_executable='/opt/homebrew/bin/bun')

    def test_unsafe_numeric_source_is_not_rounded(self):
        source=document('number')
        raw=source.content.replace(b'"extensions": {}',b'"extensions": {"future": {"n": 9007199254740993}}',1)
        with self.assertRaises(PreparationRejected):
            prepare((CatalogDocument('number','r1',raw),))

    def test_unsupported_version_refuses(self):
        source=document('future');value=json.loads(source.content);value['umf']='99.0.0'
        with self.assertRaises(PreparationRejected):
            prepare((CatalogDocument('future','r1',json.dumps(value).encode()),))

    def test_duplicate_document_identity_refuses(self):
        with self.assertRaises(PreparationRejected) as raised:prepare((document('same'),document('same')))
        self.assertEqual(raised.exception.reason,'invalid_input')

    def test_invalid_document_refuses(self):
        with self.assertRaises(PreparationRejected) as raised:prepare((CatalogDocument('bad','r1',b'{}'),))
        self.assertEqual(raised.exception.reason,'invalid_document')
        self.assertTrue(raised.exception.diagnostics)
        self.assertIn('originalError',json.loads(raised.exception.diagnostics[0]))

    def test_invalid_utf8_refuses(self):
        with self.assertRaises(PreparationRejected):prepare((CatalogDocument('bad','r1',b'\xff'),))

    def test_source_identity_mismatch_refuses(self):
        source=document('original')
        with self.assertRaises(PreparationRejected):prepare((CatalogDocument('other','r1',source.content),))

    def test_missing_configuration_refuses(self):
        with self.assertRaises(PreparationRejected):prepare((document('first'),),{})

    def test_external_runtime_is_unnecessary(self):
        result=prepare_acceptance((document('first'),),json.dumps(CONFIG).encode(),bun_executable='/missing/truss-bun')
        self.assertEqual(result.documents[0].document.content,document('first').content)

    def test_corrupted_bridge_outputs_refuse(self):
        original=_capture
        def fault(mutator):
            def capture(command,**options):
                result=original(command,**options)
                if command[-1]!='--version':
                    value=json.loads(result.stdout);mutator(value)
                    result.stdout=json.dumps(value).encode()
                return result
            return capture
        def policy(value):
            wire=json.loads(bytes.fromhex(value['inputHex']))
            wire['policy']['unknownEndpoint']='skip'
            value['inputHex']=json.dumps(wire).encode().hex()
        def numeric(value):
            wire=json.loads(bytes.fromhex(value['inputHex']))
            wire['policy']['loss']=1
            value['inputHex']=json.dumps(wire).encode().hex()
        def archive(value):value['archiveDocuments'][0]['revision']='foreign'
        def observation(value):value['documents'][0]['documentId']='foreign'
        def pin(value):value['provenance']['umfProfile']['identity']='foreign'
        for mutate in (policy,numeric,archive,observation,pin):
            with self.subTest(mutate=mutate.__name__),patch('truss.preparation._capture',fault(mutate)):
                with self.assertRaises(PreparationRejected) as raised:prepare((document('first'),))
                self.assertEqual(raised.exception.reason,'producer_unavailable')
        def list_reply(command,**options):
            if command[-1]=='--version':return original(command,**options)
            return subprocess.CompletedProcess(command,0,b'[]',b'')
        with patch('truss.preparation._capture',list_reply):
            with self.assertRaises(PreparationRejected):prepare((document('first'),))
        def null_diagnostics(command,**options):
            if command[-1]=='--version':return original(command,**options)
            return subprocess.CompletedProcess(command,0,b'{"status":"refused","reason":"invalid_document","diagnostics":null}',b'')
        with patch('truss.preparation._capture',null_diagnostics):
            with self.assertRaises(PreparationRejected):prepare((document('first'),))

    def test_transport_combined_output_cap(self):
        command=[sys.executable,'-c',"import sys;sys.stdout.write('x'*600);sys.stdout.flush();sys.stderr.write('y'*600);sys.stderr.flush()"]
        with self.assertRaises(PreparationRejected):_capture(command,limit=1024,timeout=5)

    def test_transport_deadline_reaps_child(self):
        with self.assertRaises(subprocess.TimeoutExpired):
            _capture([sys.executable,'-c','import time;time.sleep(10)'],limit=1024,timeout=.1)

    def test_altered_asset_refuses(self):
        original=Path.read_bytes
        def read(path):
            value=original(path)
            return value+b'altered' if str(path).endswith('/owner/producer.js') else value
        with patch.object(Path,'read_bytes',read):
            with self.assertRaises(PreparationRejected) as raised:prepare((document('first'),))
        self.assertEqual(raised.exception.reason,'producer_unavailable')

if __name__=='__main__':unittest.main()
