"""Conditional authority-generation atomicity model; no native issuer/refinement theorem."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-authority-generation-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-authority-generation.py','packages/postgresql/native/source-epoch-authority-issue.sql','packages/postgresql/native/source-epoch-authority-reason-storage.sql','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
old_role,new_role=z3.Ints('old_role_state new_role_state');old_gen,new_gen=z3.Strings('old_generation new_generation');commit=z3.Bool('whole_transaction_committed')
role=z3.If(commit,new_role,old_role);generation=z3.If(commit,new_gen,old_gen)
accept_old=generation==old_gen
captured=z3.String('captured_generation');weak_admitted=z3.Bool('weak_admitted');weak_rule=weak_admitted==(captured==old_gen)
role_commit,generation_commit=z3.Bools('separate_role_commit separate_generation_commit')
split_role=z3.If(role_commit,new_role,old_role);split_generation=z3.If(generation_commit,new_gen,old_gen)
original_target,selected_target=z3.Strings('original_target_incarnation selected_target_incarnation');issuer_admitted=z3.Bool('authority_issuer_admitted');preserves=issuer_admitted==(selected_target==original_target)
queries=[
 ('committed_successor_excludes_old_generation','unsat',[old_gen!=new_gen,commit,accept_old]),
 ('aborted_atomic_update_preserves_both_original_states','unsat',[z3.Not(commit),z3.Or(role!=old_role,generation!=old_gen)]),
 ('split_transactions_can_publish_role_without_generation','sat',[old_role!=new_role,old_gen!=new_gen,role_commit,z3.Not(generation_commit),split_role==new_role,split_generation==old_gen]),
 ('omitted_fresh_generation_comparison_accepts_stale_capture','sat',[old_gen!=new_gen,commit,captured==old_gen,weak_rule,weak_admitted,generation!=captured]),
 ('authority_issuer_cannot_change_target_incarnation','unsat',[preserves,issuer_admitted,selected_target!=original_target])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded role states and generation/incarnation strings under an atomic transaction visibility projection and distinct successor generation. Commit excludes old generation; abort preserves both states. Split commits and omitted fresh comparison have countermodels. Selected authority issuance preserves the target incarnation.','limitations':['No PostgreSQL transaction/catalog/SQL/UUID issuer refinement proof','Atomicity, successor distinctness and fresh comparison are premises; no automatic administration interception or cluster-wide coordination','No authenticated caller/issuer, original writer installation/ACL closure, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
