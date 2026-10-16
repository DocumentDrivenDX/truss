"""Exact framing/transport profile only; no UMF permission or native campaign."""
import unittest,json,struct,sys
from hashlib import sha256
from decimal import Decimal
from truss._current_disclosure_wire import object_members,disclosure_initializer,frame_digest
from truss._current_disclosure_pipe import CurrentDisclosurePipe,VERSION
from truss._current_query_pipe import CurrentQueryPipe,CurrentQueryPipeError

PEER=r'''import json,struct,sys
b=sys.stdin.buffer;n=struct.unpack('>I',b.read(4))[0];r=json.loads(b.read(n));out=json.dumps({'requestId':r['requestId'],'sourceReceipt':'a'*64,'kind':'fixture-echo'},separators=(',',':')).encode();sys.stdout.buffer.write(struct.pack('>I',len(out))+out);sys.stdout.buffer.flush()
'''

def request(kind,padding=0):
 return json.dumps({'version':VERSION,'kind':kind,'requestId':'r','padding':'x'*padding},separators=(',',':')).encode()

class CurrentDisclosureWireTests(unittest.TestCase):
 def test_raw_values_and_distinct_original_receipts_are_retained(self):
  policy=b'{"id":"p","revision":"r","unknown":{"n":1.2300e-999999,"big":9007199254740993,"escaped":"\\u0061"}}'
  initial=(b'{"kind":"initialize","requestId":"old_init","sources":{"policy":'+policy+b',"catalog":{},"closure":{"documents":[],"pins":[]},"ontology":{},"associationBindings":[],"extensionSelection":{"unknown":-0.00}}}')
  owner=b' {"id":"owner","revision":"r","opaque":2.500e+1000000} '
  selection={'type':{'documentId':'d','moduleId':'m','elementId':'R'},'fields':[]}
  raw,registered,child=disclosure_initializer(initial,owner,selection)
  self.assertEqual(registered,sha256(struct.pack('>I',len(initial))+initial).hexdigest());self.assertEqual(child,frame_digest(raw));self.assertNotEqual(registered,child)
  outer=object_members(raw);sources=object_members(outer['sources']);self.assertEqual(sources['policy'],policy);self.assertNotIn('extensionSelection',sources);self.assertEqual(outer['owner'].strip(),owner.strip())
  decoded=json.loads(raw,parse_float=Decimal);self.assertEqual(decoded['sources']['policy']['unknown']['n'].as_tuple(),Decimal('1.2300e-999999').as_tuple());self.assertEqual(decoded['sources']['policy']['unknown']['big'],9007199254740993)
  self.assertIn(b'"escaped":"\\u0061"',sources['policy']);self.assertEqual(decoded['version'],VERSION)
 def test_unknown_and_bad_original_structures_refuse_without_repair(self):
  for raw in [b'{"a":1,"a":2}',b'[]',b'{"a":NaN}',b'{"a":"\\ud800"}',b'{"a":'+b'1'*513+b'}']:
   with self.assertRaises(ValueError):object_members(raw)
  with self.assertRaises(ValueError):disclosure_initializer(b'{}',b'{}',{})
  with self.assertRaises(ValueError):frame_digest(b'')
  with self.assertRaises(ValueError):frame_digest('not bytes')
 def test_only_separate_inspection_transport_allows_larger_frames(self):
  large=request('inspect-native-disclosure',4*1024*1024)
  with CurrentDisclosurePipe((sys.executable,'-u','-c',PEER),timeout_seconds=10) as pipe:
   self.assertEqual(json.loads(pipe.exchange(large,source_receipt='a'*64))['kind'],'fixture-echo')
  self.assertTrue(pipe._cleanup_complete);self.assertIsNotNone(pipe._child.poll())
  for cls,raw in [(CurrentQueryPipe,large),(CurrentDisclosurePipe,request('initialize',4*1024*1024)),(CurrentDisclosurePipe,request('evaluate-disclosure',4*1024*1024)),(CurrentDisclosurePipe,request('unknown')),(CurrentDisclosurePipe,b'{}')]:
   with cls((sys.executable,'-u','-c',PEER),timeout_seconds=10) as pipe:
    with self.assertRaises(CurrentQueryPipeError):pipe.exchange(raw,source_receipt='a'*64)
   self.assertTrue(pipe._cleanup_complete);self.assertIsNotNone(pipe._child.poll())
 def test_inspection_wire_maximum_and_old_version_stay_closed(self):
  maximum=16*1024*1024;base=request('inspect-native-disclosure');exact=request('inspect-native-disclosure',maximum-len(base));self.assertEqual(len(exact),maximum)
  with CurrentDisclosurePipe((sys.executable,'-u','-c',PEER),timeout_seconds=10) as pipe:self.assertEqual(json.loads(pipe.exchange(exact,source_receipt='a'*64))['kind'],'fixture-echo')
  for raw in [exact+b' ',request('inspect-native-disclosure').replace(b'/0.2-candidate',b'/0.1-candidate')]:
   with CurrentDisclosurePipe((sys.executable,'-u','-c',PEER),timeout_seconds=10) as pipe:
    with self.assertRaises(CurrentQueryPipeError):pipe.exchange(raw,source_receipt='a'*64)
   self.assertTrue(pipe._cleanup_complete)

if __name__=='__main__':unittest.main()
