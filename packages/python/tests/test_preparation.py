# SPDX-License-Identifier: MIT OR Apache-2.0
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
            self.assertNotIn('bytesBase64',carrier['artifact'])
            self.assertEqual(observed.document.content,original.content)
            self.assertEqual(carrier['artifact']['sha256'],hashlib.sha256(original.content).hexdigest())
            self.assertEqual(observed.document,original)
            self.assertEqual(observed.observation()['target']['umf'],'0.7.0')
            self.assertIsNone(observed.observation()['transition'])
        copy=result.input();copy['documents'].clear()
        self.assertEqual(len(result.input()['documents']),2)
        self.assertNotIn('acceptedIds',result.input())
        from jsonschema import Draft202012Validator
        schema=json.loads((ROOT/'docs/helix/02-design/contracts/acceptance-input-v0.2.schema.json').read_bytes())
        Draft202012Validator(schema).validate(result.input())

    def test_unavailable_registration_report_is_rejected_during_preparation(self):
        original = _capture
        for reason, code, limit in (
            ('report_evidence_resource', 'evidence_too_large', 16777216),
            ('report_evidence_unavailable', 'evidence_unavailable', None),
        ):
            def unavailable(command, **kwargs):
                completed = original(command, **kwargs)
                if command[-1].endswith('bridge.js'):
                    reply = json.loads(completed.stdout)
                    reply['reportEvidence'] = {
                        'scope': 'original_owner_report_preparation_only',
                        'ingress': {'state': 'unavailable', 'reason': reason},
                    }
                    return subprocess.CompletedProcess(command, completed.returncode,
                        json.dumps(reply).encode(), completed.stderr)
                return completed
            with self.subTest(reason=reason), patch('truss.preparation._capture', unavailable):
                with self.assertRaises(PreparationRejected) as raised:
                    prepare((document('ordinary'),))
                self.assertEqual(raised.exception.reason, 'producer_unavailable')
                self.assertIsNone(raised.exception.limit_bytes)
                self.assertIsNone(raised.exception.produced_bytes)

    def test_all_entrypoints_share_the_same_summary(self):
        from truss import prepare_catalog
        from truss.preparation import prepare_core08_acceptance
        from truss.catalog_preparation import _configuration
        from truss._catalog_report_semantics import canonical_numeric_free
        for version in ('0.7.0','0.8.0'):
            source=json.loads(document('same').content);source['umf']=version
            original=CatalogDocument('same','r1',json.dumps(source).encode())
            configuration=canonical_numeric_free(_configuration(version))
            methods=(prepare_acceptance,prepare_core08_acceptance)
            for method in methods:
                with self.subTest(version=version),patch.object(subprocess,'Popen',side_effect=AssertionError('No external process')):
                    legacy=method((original,),configuration,bun_executable='/missing/bun')
                    catalog=prepare_catalog((original,),source_version=version,bun_executable='/missing/bun')
                    self.assertEqual(legacy.input_bytes,catalog.input_bytes)
                    self.assertEqual(legacy.declarations_bytes,catalog.declarations_bytes)
                    self.assertEqual(legacy.report_evidence_bytes,catalog.report_evidence_bytes)
                    summary=json.loads(legacy.report_evidence_bytes)
                    self.assertEqual(set(summary),{'interfaceVersion','documents'})
                    self.assertEqual(summary['interfaceVersion'],'truss-registration-preparation/2.0')
                    self.assertEqual(summary['documents'][0]['contentSha256'],hashlib.sha256(original.content).hexdigest())
                    self.assertLess(len(legacy.report_evidence_bytes),4096)

    def test_substituted_summary_refuses_preparation(self):
        original=_capture
        for mutation in ('missing','digest','validation','duplicate'):
            def altered(command,**kwargs):
                completed=original(command,**kwargs);reply=json.loads(completed.stdout)
                summary=reply['reportEvidence']
                if mutation=='missing':summary['documents']=[]
                elif mutation=='digest':summary['documents'][0]['contentSha256']='0'*64
                elif mutation=='validation':summary['documents'][0]['validation']['valid']=False
                else:summary['documents'].append(summary['documents'][0])
                return subprocess.CompletedProcess(command,completed.returncode,json.dumps(reply).encode(),completed.stderr)
            with self.subTest(mutation=mutation),patch('truss.preparation._capture',altered):
                with self.assertRaises(PreparationRejected) as refused:prepare((document('dropped'),))
                self.assertEqual(refused.exception.reason,'producer_unavailable')

    def test_summary_executes_from_copied_package_outside_checkout(self):
        import os,shutil,tempfile
        with tempfile.TemporaryDirectory(prefix='truss-summary-package-') as directory:
            shutil.copytree(ROOT/'packages/python/src/truss',Path(directory)/'truss',ignore=shutil.ignore_patterns('__pycache__'))
            request={'documents':[{'identity':'outside','content':base64.b64encode(document('outside').content).decode()}],'configuration':CONFIG}
            code="""import sys,json,base64
from truss import CatalogDocument,prepare_acceptance
request=json.load(sys.stdin)
prepared=prepare_acceptance(tuple(CatalogDocument(d['identity'],'r1',base64.b64decode(d['content'])) for d in request['documents']),json.dumps(request['configuration']).encode(),bun_executable='/missing/bun')
print(json.loads(prepared.report_evidence_bytes)['interfaceVersion'])
"""
            environment=dict(os.environ,PYTHONPATH=directory)
            result=subprocess.run([sys.executable,'-c',code],input=json.dumps(request).encode(),stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=directory,env=environment,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            self.assertEqual(result.stdout.strip(),b'truss-registration-preparation/2.0')

    def test_unknown_extension_original_is_preserved(self):
        source=document('future')
        value=json.loads(source.content)
        value['vocabularies']={'future.vendor':{'version':'99.0.0'}}
        value['extensions']={'future.vendor':{'opaque':['keep',{'text':'雪'}]}}
        raw=json.dumps(value,ensure_ascii=False).encode()
        result=prepare((CatalogDocument('future','r1',raw),))
        self.assertNotIn('bytesBase64',result.input()['documents'][0]['artifact'])
        self.assertEqual(result.documents[0].document.content,raw)
        archived=json.loads(result.archive_documents_bytes)[0]
        self.assertEqual(archived['originalText'],raw.decode())
        self.assertEqual(result.documents[0].observation()['source']['extensions'],value['extensions'])

    def test_inspector_unavailability_does_not_prevent_preparation(self):
        value=json.loads(document('ext').content)
        value['vocabularies']={f'vendor{i}':{'version':'99.0.0'} for i in range(70)}
        value['extensions']={f'vendor{i}':{'opaque':True} for i in range(70)}
        value['future_padding']='x'*60000
        raw=json.dumps(value).encode()
        prepared=prepare((CatalogDocument('ext','r1',raw),))
        self.assertEqual(prepared.documents[0].document.content,raw)
        self.assertEqual(set(json.loads(prepared.report_evidence_bytes)),{'interfaceVersion','documents'})

    def test_inspector_expansion_cannot_refuse_valid_source(self):
        value=json.loads(document('ext').content)
        value['vocabularies']={f'vendor{i}':{'version':'99.0.0'} for i in range(40)}
        value['extensions']={f'vendor{i}':{'opaque':True} for i in range(40)}
        value['future_padding']='x'*60000
        value.update({f'future_extra_{i}':True for i in range(20)})
        raw=json.dumps(value).encode()
        prepared=prepare((CatalogDocument('ext','r1',raw),))
        self.assertEqual(prepared.documents[0].document.content,raw)
        self.assertEqual(set(json.loads(prepared.report_evidence_bytes)),{'interfaceVersion','documents'})

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
        with self.assertRaises(PreparationRejected) as raised:prepare((CatalogDocument('bad','r1',b'{"umf":"0.7.0"}'),))
        self.assertEqual(raised.exception.reason,'invalid_document')
        self.assertTrue(raised.exception.diagnostics)
        self.assertFalse(json.loads(raised.exception.diagnostics[0])['validation']['valid'])

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
            wire=value['input']
            wire['policy']['unknownEndpoint']='skip'
        def numeric(value):
            wire=value['input']
            wire['policy']['loss']=1
        def archive(value):value['documents'][0]['revision']='foreign'
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
