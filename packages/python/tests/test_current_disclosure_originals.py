# SPDX-License-Identifier: MIT OR Apache-2.0
"""Distinct transport/source profiles, not owner semantics or native admission."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from hashlib import sha256
from truss._current_disclosure_originals import CurrentDisclosureOriginals,_check_disclosure_sources,check_disclosure_originals,prepare_current_disclosure_originals
from truss._current_query_originals import CurrentQueryOriginals,check_query_originals
from truss._current_query_evaluation import wire

class DisclosureOriginalTests(unittest.TestCase):
 def setUp(self):
  self.fixture=json.loads(Path(__file__).with_name('fixtures').joinpath('current-disclosure/source-correspondence.json').read_bytes())
  self.rows=self.fixture['opaqueSources'];self.initial=wire(self.fixture['initialize']);self.accepted=wire(self.fixture['acceptedRequest'])
 def test_exact_logical_sources_correspond_without_native_admission(self):
  rows,decoded=_check_disclosure_sources(wire(self.rows),self.initial,self.accepted)
  self.assertEqual(set(rows),{'policy','ontology','catalog','owner','native-binding','presence-designation'})
  self.assertEqual(decoded['presence-designation']['binding']['targetProfile'],'unadmitted-fixture')
 def test_old_and_new_registration_objects_remain_distinct(self):
  new=CurrentDisclosureOriginals(wire(self.rows),b'{}');old=CurrentQueryOriginals(wire(self.rows),b'{}')
  with self.assertRaises(ValueError):check_query_originals(new,self.initial,self.accepted)
  with self.assertRaises(ValueError):check_disclosure_originals(old,self.initial,self.accepted)
  with self.assertRaises(ValueError):check_query_originals(old,self.initial,self.accepted)
  rows=copy.deepcopy(self.rows);next(r for r in rows if r['role']=='presence-designation')['role']='query-designation'
  with self.assertRaises(ValueError):_check_disclosure_sources(wire(rows),self.initial,self.accepted)
 def test_source_pin_order_is_irrelevant_but_unique_exact_roles_are_required(self):
  for mutate,accepted in ((lambda p:p['sources'].reverse(),True),(lambda p:p['sources'].__setitem__(0,copy.deepcopy(p['sources'][1])),False),(lambda p:p['sources'][0].update(extra=True),False)):
   rows=copy.deepcopy(self.rows);row=next(r for r in rows if r['role']=='presence-designation');profile=json.loads(row['utf8']);mutate(profile);row['utf8']=wire(profile).decode();row['sha256']=sha256(row['utf8'].encode()).hexdigest()
   if accepted:_check_disclosure_sources(wire(rows),self.initial,self.accepted)
   else:
    with self.assertRaises(ValueError):_check_disclosure_sources(wire(rows),self.initial,self.accepted)
 def test_unenrolled_installed_consumer_cannot_activate(self):
  with patch('truss._current_disclosure_originals._CONSUMER_COHORTS',()):
   with self.assertRaises(ValueError):prepare_current_disclosure_originals(wire(self.rows))
  with self.assertRaises(ValueError):check_disclosure_originals(CurrentDisclosureOriginals(wire(self.rows),b'{}'),self.initial,self.accepted)
 def test_registration_dispatch_refuses_cross_profiles_before_any_database_use(self):
  from truss._current_query_sources import register_current_query_sources_in_transaction,register_current_disclosure_sources_in_transaction,_register_sources
  from truss.psycopg_host import PsycopgHost
  from truss.execution import Error
  # Deliberately uninitialized exact-type host: input refusal must not inspect
  # it or invoke native operations. This is no authenticated-host evidence.
  host=object.__new__(PsycopgHost);new=CurrentDisclosureOriginals(wire(self.rows),b'{}');old=CurrentQueryOriginals(wire(self.rows),b'{}')
  common=dict(initialize_bytes=self.initial,accepted_request_bytes=self.accepted)
  self.assertIsInstance(register_current_query_sources_in_transaction(host,None,query_originals=new,**common),Error)
  self.assertIsInstance(register_current_disclosure_sources_in_transaction(host,None,disclosure_originals=old,**common),Error)
  self.assertIsInstance(register_current_disclosure_sources_in_transaction(host,None,disclosure_originals=new,**common),Error)
  self.assertIsInstance(_register_sources(host,None,query_originals=old,disclosure_originals=new,**common),Error)
 def test_source_hash_role_identity_and_initializer_drift_refuse(self):
  for mutate in (lambda rows:rows.pop(),lambda rows:rows.append(copy.deepcopy(rows[0])),lambda rows:rows[0].update(sha256='0'*64),lambda rows:rows[0]['identity'].update(revision='different')):
   rows=copy.deepcopy(self.rows);mutate(rows)
   with self.assertRaises(ValueError):_check_disclosure_sources(wire(rows),self.initial,self.accepted)
  init=copy.deepcopy(self.fixture['initialize']);init['sources']['policy']['revision']='different'
  with self.assertRaises(ValueError):_check_disclosure_sources(wire(self.rows),wire(init),self.accepted)
 def test_profile_capability_binding_and_model_drift_refuse(self):
  for mutate in (lambda p:p.update(version='weft.current-query.designation-profile/0.1-candidate'),lambda p:p.update(capabilities=[]),lambda p:p['binding'].update(sha256='0'*64),lambda p:p['sources'].pop(),lambda p:p['modelPins'][0].update(revision='different')):
   rows=copy.deepcopy(self.rows);row=next(r for r in rows if r['role']=='presence-designation');profile=json.loads(row['utf8']);mutate(profile);row['utf8']=wire(profile).decode();row['sha256']=sha256(row['utf8'].encode()).hexdigest()
   with self.assertRaises(ValueError):_check_disclosure_sources(wire(rows),self.initial,self.accepted)

if __name__=='__main__':unittest.main()
