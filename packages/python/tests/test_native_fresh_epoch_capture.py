# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure/frame controls; no native lock or authority qualification."""
import hashlib,struct,unittest
from types import SimpleNamespace
from pg8000.converters import string_in
from truss._native_fresh_epoch_capture import NativeFreshEpochCapture,FRESH_EPOCH_LIMITS,validate_epoch_row,_literal
from truss._native_result_custody import NativeTextLimits
from truss._native_pg8000 import NativeBoundaryRefusal


EXPECTED=('installation','epoch','incarnation')
ROW=(*EXPECTED,'01','0203',hashlib.sha256(b'\x02\x03').hexdigest(),'123','5','345','actor','actor','transaction_source_epoch_lock_only')
def gate():
 g=object.__new__(NativeFreshEpochCapture)
 g.boundary=SimpleNamespace(_connection=SimpleNamespace(_client_encoding='utf8'),_active_control=None)
 g.session=SimpleNamespace(cleanup_calls=())
 g.frames=[];g.limits=FRESH_EPOCH_LIMITS;g.rows_seen=0;g.bytes_seen=0;g.cleanup_rows_seen=0;g.cleanup_bytes_seen=0
 g.response_stage=0;g.expected_command='SELECT';g.admission_context=SimpleNamespace(input_funcs=[string_in]*12)
 return g
def descriptor(oid=25,names=None):
 names=names or NativeFreshEpochCapture.NAMES
 return struct.pack('!H',len(names))+b''.join(n+b'\0'+struct.pack('!IhIhih',0,0,oid,-1,-1,0) for n in names)
def feed(g,code,data):g._validate(code,data,g.admission_context)
class NativeFreshEpochTests(unittest.TestCase):
 def test_valid_and_forged_shapes_are_not_authority(self):
  self.assertEqual(validate_epoch_row(ROW,EXPECTED),ROW)
  self.assertEqual(validate_epoch_row((*ROW[:6],'987',*ROW[7:]),EXPECTED)[6],'987')
 def test_comparison_scope_and_closed_tuple(self):
  for row in (list(ROW),ROW[:-1],(*ROW[:-1],'trusted'),('wrong',*ROW[1:]),(*ROW[:4],None,*ROW[5:])):
   with self.subTest(row=row),self.assertRaises(NativeBoundaryRefusal):validate_epoch_row(row,EXPECTED)
 def test_exact_hex_and_evidence_digest(self):
  for index,value in ((3,'0'),(3,'GG'),(3,'a'*131074),(4,'a'*2097154),(5,'0'*64)):
   changed=list(ROW);changed[index]=value
   with self.subTest(index=index),self.assertRaises(NativeBoundaryRefusal):validate_epoch_row(tuple(changed),EXPECTED)
 def test_native_identity_bounds(self):
  for index,value in ((6,'0'),(6,'01'),(6,'18446744073709551616'),(7,'4294967296'),(8,'2147483648'),(9,''),(10,'x'*64),(9,'\ud800')):
   changed=list(ROW);changed[index]=value
   with self.subTest(index=index,value=value),self.assertRaises(NativeBoundaryRefusal):validate_epoch_row(tuple(changed),EXPECTED)
 def test_bounded_lossless_sql_literal(self):
  self.assertNotIn("'unsafe",_literal("'unsafe",20))
  for text in ('','x'*1025,'\0','\ud800','🙂'*257):
   with self.subTest(text=text),self.assertRaises(NativeBoundaryRefusal):_literal(text,1024)
 def test_default_profiles_unchanged(self):
  self.assertEqual(NativeTextLimits().wire_bytes,1048576)
  self.assertEqual(FRESH_EPOCH_LIMITS.columns,12)
  self.assertEqual(FRESH_EPOCH_LIMITS.rows,1)
 def test_descriptor_order_types_and_count(self):
  for data in (descriptor(23),descriptor(names=NativeFreshEpochCapture.NAMES[::-1]),descriptor(names=NativeFreshEpochCapture.NAMES[:-1])):
   with self.subTest(data=data[:20]),self.assertRaises(NativeBoundaryRefusal):feed(gate(),b'T',data)
 def test_singleton_active_response(self):
  g=gate();feed(g,b'T',descriptor())
  cells=[x.encode() for x in ROW];data=struct.pack('!H',12)+b''.join(struct.pack('!i',len(x))+x for x in cells)
  feed(g,b'D',data);feed(g,b'C',b'SELECT 1\0');feed(g,b'Z',b'T');self.assertEqual(g.response_stage,4);self.assertEqual(tuple(e.code for e in g.frames),(b'T',b'D',b'C',b'Z'))
  with self.assertRaises(NativeBoundaryRefusal):feed(g,b'Z',b'T')
 def test_prefix_wrong_completion_and_idle_refuse(self):
  for stage,code,data in ((0,b'Z',b'T'),(2,b'C',b'SELECT 2\0'),(3,b'Z',b'I')):
   g=gate();g.response_stage=stage
   with self.subTest(stage=stage),self.assertRaises(NativeBoundaryRefusal):feed(g,code,data)

class OriginalEpochRequestTests(unittest.TestCase):
 def recipe(self,cls=None):
  from truss._native_fresh_epoch_capture import NativeFencedFreshEpochCapture,_capture_profile,_EpochRequest
  from truss._native_arbitration import NativeOperationSession
  g=object.__new__(cls or NativeFencedFreshEpochCapture);s=object.__new__(NativeOperationSession)
  g.session=s;g.sql='SELECT original';g.expected=EXPECTED;g._request_profile=_capture_profile(g)
  g._request=_EpochRequest(g,s,g._request_profile,g.expected,g.sql);s._epoch_request=g._request
  return g
 def test_scopes_are_disjoint(self):
  from truss._native_fresh_epoch_capture import validate_fenced_epoch_row
  fenced=(*ROW[:-1],'transaction_epoch_state_fence_only')
  self.assertEqual(validate_fenced_epoch_row(fenced,EXPECTED),fenced)
  for validator,row in ((validate_epoch_row,fenced),(validate_fenced_epoch_row,ROW)):
   with self.assertRaises(NativeBoundaryRefusal):validator(row,EXPECTED)
 def test_frozen_owner_bound_request(self):
  import copy
  from dataclasses import FrozenInstanceError
  g=self.recipe();self.assertIs(g._check_recipe(),g._request)
  with self.assertRaises(FrozenInstanceError):g._request.sql='SELECT substituted'
  with self.assertRaises(NativeBoundaryRefusal):copy.copy(g)._check_recipe()
  original=g._request;g._request=copy.copy(original)
  with self.assertRaises(NativeBoundaryRefusal):g._check_recipe()
 def test_altered_crossed_and_nonprimitive_recipes_refuse(self):
  class Text(str):pass
  class Values(tuple):pass
  for field,value in (('sql','SELECT altered'),('sql',Text('SELECT original')),('expected',('other',*EXPECTED[1:])),('expected',Values(EXPECTED)),('expected',(Text(EXPECTED[0]),*EXPECTED[1:])),('_request',self.recipe()._request),('session',self.recipe().session)):
   g=self.recipe();setattr(g,field,value)
   with self.subTest(field=field),self.assertRaises(NativeBoundaryRefusal):g._check_recipe()
 def test_only_closed_concrete_classes(self):
  from truss._native_fresh_epoch_capture import NativeFencedFreshEpochCapture,_capture_profile
  class Derived(NativeFencedFreshEpochCapture):pass
  with self.assertRaises(NativeBoundaryRefusal):_capture_profile(object.__new__(Derived))
  self.assertNotEqual(self.recipe(NativeFreshEpochCapture)._request.profile,self.recipe()._request.profile)
