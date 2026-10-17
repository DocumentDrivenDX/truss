"""Installed owner execution with JavaScript process launch forbidden."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import struct
import time
import unittest
from unittest.mock import patch

from truss._embedded import OwnerVM, capture
from truss._current_query_pipe import CurrentQueryPipeError
from truss._current_query_computation import open_current_query_computation
frame_digest=lambda raw:sha256(struct.pack('>I',len(raw))+raw).hexdigest()
from truss._umf_key_tuples import KeyTupleRequest, encode_string_key_tuples
from truss._core08_catalog_source import prepare_core08_catalog_source
from test_preparation import prepare, document

FIXTURES=Path(__file__).with_name('fixtures')
wire=lambda value:json.dumps(value,ensure_ascii=True,separators=(',',':')).encode()

class EmbeddedOwnerTests(unittest.TestCase):
    def test_acceptance_catalog_and_exact_keys_without_any_subprocess(self):
        with patch.object(subprocess,'Popen',side_effect=AssertionError('No external owner process')):
            prepared=prepare((document('embedded'),))
            self.assertEqual(prepared.documents[0].document.content,document('embedded').content)
            self.assertEqual(prepared.provenance.runtime_version,'mini-racer==0.14.1/V8 14.4.258.23')
            original=json.loads((FIXTURES/'security-mapping-request.json').read_bytes())['modules'][0]['documentJson'].encode()
            observed=prepare_core08_catalog_source(original,document_id='domain',document_revision='r1',bun_executable='/missing/bun')
            self.assertEqual(observed.original_document,original)
            from truss.catalog_preparation import prepare_catalog
            from truss import CatalogDocument
            current=prepare_catalog((CatalogDocument('domain','r1',original),),source_version='0.8.0',bun_executable='/missing/bun')
            self.assertEqual(current.documents[0].document.content,original)
            from test_umf_key_tuples import OriginalUmfKeyTupleTests
            raw=OriginalUmfKeyTupleTests().source()
            request=KeyTupleRequest('m','A','a-primary',('9007199254740993.0001','e\u0301'))
            keys=encode_string_key_tuples(raw,(request,),bun_executable='/missing/bun')
            self.assertEqual(keys[0].document_sha256,sha256(raw).hexdigest())
            self.assertEqual(json.loads(keys[0].original_receipt_bytes)['values'],[{'string':v} for v in request.values])

    def test_held_query_original_frames_and_fencing_without_subprocess(self):
        initial=wire(json.loads((FIXTURES/'current-query-initialize.json').read_bytes()))
        receipt=frame_digest(initial)
        with patch.object(subprocess,'Popen',side_effect=AssertionError('No external owner process')):
            with open_current_query_computation(bun_executable='/missing/bun',timeout_seconds=10) as owner:
                response=json.loads(owner.exchange(initial,source_receipt=receipt))
                self.assertEqual(response['kind'],'initialized')
                with self.assertRaises(CurrentQueryPipeError):
                    owner.exchange(initial,source_receipt=receipt)
                self.assertTrue(owner._closed)
                self.assertTrue(owner._cleanup_complete)
                with self.assertRaises(CurrentQueryPipeError):
                    owner.exchange(initial,source_receipt=receipt)

    def test_owner_engine_failure_preserves_public_preparation_refusal(self):
        from truss import PreparationRejected
        with patch('truss._embedded.capture',side_effect=ValueError('owner heap/output refused')):
            with self.assertRaises(PreparationRejected) as raised:
                prepare((document('embedded'),))
            self.assertEqual(raised.exception.reason,'producer_unavailable')

    def test_owner_refusal_is_a_fenced_transport_error(self):
        with open_current_query_computation(timeout_seconds=5) as owner:
            with self.assertRaises(CurrentQueryPipeError):
                owner.exchange(wire({'kind':'initialize','requestId':'invalid','sources':{}}),source_receipt='a'*64)
            self.assertTrue(owner._cleanup_complete)

    def test_isolate_deadline_interrupts_nonterminating_code(self):
        start=time.monotonic()
        with OwnerVM('_umf_keys08/bridge.mjs',input_bytes=b'{}',timeout=1) as owner:
            with self.assertRaises(TimeoutError):
                owner.eval('for(;;){}')
        self.assertLess(time.monotonic()-start,4)
        self.assertIsNone(owner.vm)

    def test_virtual_host_refuses_unbundled_files_and_modules(self):
        with OwnerVM('_umf_keys08/bridge.mjs',input_bytes=b'{}',timeout=5) as owner:
            self.assertEqual(owner.eval('typeof require'), 'undefined')
            self.assertEqual(owner.eval('JSON.stringify(Object.keys(process.env))'),'[]')
            self.assertEqual(owner.eval('typeof process.spawn'),'undefined')
            with self.assertRaises(Exception):
                owner.promise('Bun.file("/etc/passwd").text()')
            self.assertIsNone(owner.vm)

if __name__=='__main__':unittest.main()
