# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional native caller-binding model; issuer/mapping authority is a separate premise."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-caller-binding-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-caller-binding.py','packages/python/src/truss/_security_fact_coverage.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py','scripts/security_owned_read.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
actual_session,actual_effective,mapped_session,mapped_effective,claimed_session=z3.Ints('actual_session actual_effective mapped_session mapped_effective claimed_session')
native_subject,selected_subject,authorized_subject=z3.Strings('native_mapped_subject selected_subject independently_authorized_subject')
strong=z3.And(actual_session==mapped_session,actual_effective==mapped_effective,selected_subject==native_subject)
weak=z3.And(claimed_session==mapped_session,actual_effective==mapped_effective)
hint_effective=z3.Int('role_setting_name_resolution_oid')
queries=[
 ('cached_hint_replacement_cannot_match_original_native_role','unsat',[strong,mapped_effective==hint_effective,hint_effective!=actual_effective]),
 ('live_native_match_does_not_require_cached_hint_match','sat',[strong,hint_effective!=actual_effective]),
 ('hint_only_mapping_can_borrow_replacement_identity','sat',[actual_session==mapped_session,mapped_effective==hint_effective,hint_effective!=actual_effective]),
 ('native_session_mismatch_refuses','unsat',[strong,actual_session!=mapped_session]),
 ('native_effective_role_mismatch_refuses','unsat',[strong,actual_effective!=mapped_effective]),
 ('caller_claim_without_native_capture_can_impersonate','sat',[weak,claimed_session!=actual_session]),
 ('retained_mapping_prevents_caller_subject_substitution','unsat',[strong,selected_subject!=native_subject]),
 ('native_role_match_does_not_authenticate_semantic_mapping','sat',[strong,native_subject!=authorized_subject])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded native role identities and abstract canonical subject keys under faithful native capture and retained-profile key selection. Session/effective mismatches and subject replacement refuse. Live role identity remains independent of cached name-hint resolution; hint-only mapping admits replacement identity. Caller claims and unauthenticated semantic mappings have countermodels.','limitations':['No database authentication, JSON/Python/PostgreSQL or original Core key-encoding refinement proof','Native capture and retained mapping are premises; semantic mapping authorization and source/role lifetime remain unqualified','No authenticated caller/issuer, original writer installation/ACL closure, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
