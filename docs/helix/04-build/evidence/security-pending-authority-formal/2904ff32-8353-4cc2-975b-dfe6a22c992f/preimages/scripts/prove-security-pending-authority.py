"""Conditional committed-pending authority transition; issuer and native distributed refinement remain unproved."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-pending-authority-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-pending-authority.py','scripts/security_authority_transition.py','packages/postgresql/native/source-epoch-issue.sql','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
drained,pending_committed,remote_committed,remote_known,requalified,successor,admit,native_image_matches,fresh=z3.Bools('readers_drained pending_committed remote_committed remote_outcome_known requalified successor_committed admit native_image_matches fresh_post_barrier_snapshot')
ordering=z3.And(z3.Implies(pending_committed,z3.And(drained,fresh)),z3.Implies(remote_committed,pending_committed),z3.Implies(successor,z3.And(pending_committed,remote_known,requalified,native_image_matches,fresh)))
publication=admit==z3.Or(z3.Not(pending_committed),successor)
already_pending,begin_transition=z3.Bools('already_pending begin_transition')
single_transition=z3.Implies(begin_transition,z3.Not(already_pending))
queries=[
 ('active_pending_prevents_second_begin','unsat',[single_transition,already_pending,begin_transition]),
 ('omitted_overlap_guard_allows_second_begin','sat',[already_pending,begin_transition]),
 ('inherited_old_snapshot_prevents_pending_publication','unsat',[ordering,z3.Not(fresh),pending_committed]),
 ('changed_native_image_prevents_successor','unsat',[ordering,z3.Not(native_image_matches),successor]),
 ('self_asserted_pending_kind_without_image_guard_allows_successor','sat',[publication,pending_committed,successor,z3.Not(native_image_matches),admit]),
 ('pending_without_successor_prevents_admission','unsat',[ordering,publication,pending_committed,z3.Not(successor),admit]),
 ('undrained_readers_prevent_pending_publication','unsat',[ordering,z3.Not(drained),pending_committed]),
 ('unknown_remote_outcome_prevents_successor_admission','unsat',[ordering,publication,pending_committed,z3.Not(remote_known),admit]),
 ('remote_change_without_committed_pending_allows_old_admission','sat',[publication,remote_committed,z3.Not(pending_committed),z3.Not(successor),admit]),
 ('unqualified_successor_without_completion_guard_allows_admission','sat',[publication,pending_committed,z3.Not(remote_known),z3.Not(requalified),successor,admit])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract drain, committed pending marker, remote mutation, exact native-image correspondence and qualified successor ordering. Pending excludes admission; undrained readers exclude pending publication; unknown remote outcome excludes successor admission. Omitted pending or qualification guards admit countermodels.','limitations':['No PostgreSQL commit/WAL/SQL, multi-database driver or concrete distributed state-machine refinement proof','Durable pending, complete writer routing and authenticated requalification are premises; native fixture only observes successful commits and writer disconnect','No automatic cross-database role interception, authenticated issuer/mapping/target, complete recovery/commit-unknown or admitted protected backend']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
