"""Conditional negative-existence visibility model; no RLS implementation theorem."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-fact-visibility-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-fact-visibility.py','packages/python/src/truss/_psycopg_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
I=z3.IntSort();bad=z3.Array('complete_relevant_forbidden_facts',I,z3.BoolSort());visible=z3.Array('original_visibility',I,z3.BoolSort());later=z3.Array('later_visibility',I,z3.BoolSort());i=z3.Int('fact')
full_bad=z3.Exists([i],z3.Select(bad,i));seen=lambda v:z3.Exists([i],z3.And(z3.Select(bad,i),z3.Select(v,i)))
complete=z3.ForAll([i],z3.Implies(z3.Select(bad,i),z3.Select(visible,i)))
enabled,forced,admitted,admin=z3.Bools('row_security_enabled force_row_security admitted_plain_profile admin_observes_all_rows');profile=admitted==z3.And(z3.Not(enabled),z3.Not(forced))
queries=[('hidden_forbidden_fact_can_falsely_permit','sat',[full_bad,z3.Not(seen(visible))]),('complete_relevant_visibility_prevents_false_permit','unsat',[complete,full_bad,z3.Not(seen(visible))]),('visibility_change_can_flip_decision_under_unchanged_facts','sat',[seen(visible),z3.Not(seen(later))]),('enabled_rls_refuses_plain_profile','unsat',[profile,enabled,admitted]),('force_flag_refuses_plain_profile_even_disabled','unsat',[profile,z3.Not(enabled),forced,admitted]),('admin_current_visibility_does_not_override_profile_refusal','unsat',[profile,admin,enabled,admitted])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded relevant forbidden-fact and visibility sets. A no-visible-forbidden-fact decision needs complete relevant visibility; fixed facts alone do not stabilize it. Plain-profile admission excludes both native RLS flags regardless of current administrative visibility.','limitations':['No SQL policy, role/BYPASSRLS/config/ACL visibility refinement or whole-source lifetime proof','Native metadata refusal is an installed fixture control; no full RLS-aware provider qualification','Does not prove all policy predicates, authenticated issuer/caller, protected evaluation or final disclosure']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
