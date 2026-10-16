"""Synthetic invalidation controls; native custody is qualified separately."""
import unittest
from types import SimpleNamespace as S
from truss._native_epoch_acquisitions import NativeEpochAcquisitions,NativeEpochAcquisition
from truss._native_pg8000 import NativeBoundaryRefusal

def fixture():
 generation=object();parent=object();child=object();later=object()
 before=S(generation=generation,savepoints=(parent,child,later))
 owner=NativeEpochAcquisitions(S())
 record=NativeEpochAcquisition(owner,None,None,generation,(parent,child))
 owner.records=(record,)
 call=S(capture_complete=True,driver_raised=False,final_status=b'T')
 return owner,record,before,call,parent,child,later
class AcquisitionTests(unittest.TestCase):
 def test_unknown_or_failed_completion_closes_without_claiming_release(self):
  for change in ({'capture_complete':False},{'driver_raised':True},{'final_status':b'E'},{'final_status':b'I'}):
   owner,r,before,call,p,c,l=fixture()
   for key,value in change.items():setattr(call,key,value)
   owner.after(S(kind='release',savepoint=c,expected=before),call,before)
   self.assertFalse(r.valid);self.assertEqual(r.scopes,(p,c))
 def test_original_expected_state_is_required(self):
  owner,r,before,call,p,c,l=fixture()
  owner.after(S(kind='release',savepoint=c,expected=S()),call,before)
  self.assertFalse(r.valid)
 def test_release_reparents_then_rollback_parent_invalidates(self):
  owner,r,before,call,p,c,l=fixture()
  owner.after(S(kind='release',savepoint=c,expected=before),call,before)
  self.assertTrue(r.valid);self.assertEqual(r.scopes,(p,))
  owner.after(S(kind='rollback_to',savepoint=p,expected=before),call,before)
  self.assertFalse(r.valid)
 def test_rollback_later_preserves_but_recreation_cannot_revive(self):
  owner,r,before,call,p,c,l=fixture()
  owner.after(S(kind='rollback_to',savepoint=l,expected=before),call,before);self.assertTrue(r.valid)
  owner.after(S(kind='rollback_to',savepoint=c,expected=before),call,before);self.assertFalse(r.valid)
  owner.after(S(kind='savepoint',expected=before),call,before);self.assertFalse(r.valid)
 def test_generation_transition_and_unknown_target_close(self):
  for kind,target in (('commit',None),('rollback',None),('begin',None),('release',object())):
   owner,r,before,call,p,c,l=fixture()
   owner.after(S(kind=kind,savepoint=target,expected=before),call,before);self.assertFalse(r.valid)
 def test_unqualified_call_invalidates_before_effect_and_never_rewinds(self):
  owner,r,before,call,p,c,l=fixture();owner.before(None)
  self.assertFalse(r.valid);self.assertEqual(r.reason,'unqualified-ordinary-call')
  owner.invalidate('another');self.assertEqual(r.reason,'unqualified-ordinary-call')
 def test_capacity_selection_is_exact_and_bounded(self):
  for maximum in (True,0,4097):
   with self.assertRaises(ValueError):NativeEpochAcquisitions(S(),maximum)
