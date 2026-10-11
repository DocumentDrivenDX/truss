"""Conditional graph-fact projection preservation; not native-trigger refinement."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/graph-fact-projection-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-graph-fact-projection.py','packages/postgresql/native/authorization-graph-fact-scope.sql','packages/postgresql/native/authorization-graph-fact-scope-storage.sql','packages/postgresql/native/authorization-fact-write-fence.sql','packages/python/tests/test_psycopg_graph_projection_native.py','docs/helix/04-build/evidence/authorization-graph-fact-scope.owner-export.sql']
pins={}
for name in paths:
 raw=(root/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
Row=z3.Datatype('Row');Row.declare('absent');Row.declare('edge',('rel',z3.IntSort()),('source',z3.IntSort()),('target',z3.IntSort()),('payload',z3.IntSort()));Row=Row.create()
A=z3.Array('before',z3.IntSort(),Row);B=z3.Array('after',z3.IntSort(),Row)
S=z3.Array('native_scope',z3.IntSort(),z3.BoolSort());R=z3.Array('required_scope',z3.IntSort(),z3.BoolSort());T=z3.Array('later_scope',z3.IntSort(),z3.BoolSort())
key,witness,op,rel=z3.Ints('key witness op rel');new=z3.Const('new',Row);old=z3.Select(A,key)
held,known,old_guard,new_guard,write=z3.Bools('held known old_guard new_guard write')
selected=lambda row,scope:z3.And(Row.is_edge(row),z3.Select(scope,Row.rel(row)))
project=lambda row:z3.If(selected(row,R),row,Row.absent)
valid=z3.Or(z3.And(op==0,Row.is_absent(old),Row.is_edge(new)),z3.And(op==1,Row.is_edge(old),Row.is_edge(new)),z3.And(op==2,Row.is_edge(old),Row.is_absent(new)))
allowed=z3.Not(z3.And(held,z3.Or(z3.Not(known),z3.And(old_guard,selected(old,S)),z3.And(new_guard,selected(new,S)))))
step=B==z3.If(z3.And(write,allowed),z3.Store(A,key,new),A)
complete=z3.ForAll([rel],z3.Implies(z3.Select(R,rel),z3.Select(S,rel)))
changed=project(z3.Select(B,witness))!=project(z3.Select(A,witness))
base=[held,known,write,valid,step]
truncate_guard=z3.Bool('truncate_guard');truncate_allowed=z3.Not(z3.And(held,truncate_guard));truncated=z3.Array('truncated',z3.IntSort(),Row)
truncate_step=truncated==z3.If(truncate_allowed,z3.K(z3.IntSort(),Row.absent),A)
queries=[
 ('complete_row_guards_preserve_required_projection','unsat',[*base,old_guard,new_guard,complete,changed]),
 ('unrelated_business_row_can_change','sat',[*base,old_guard,new_guard,complete,op==0,new==Row.edge(101,1,1,7),z3.Select(S,101)==False,z3.Select(R,100),witness==key,z3.Select(B,key)!=z3.Select(A,key)]),
 ('omitted_old_guard_allows_selected_delete','sat',[*base,z3.Not(old_guard),new_guard,op==2,selected(old,R),complete,witness==key,changed]),
 ('omitted_old_guard_allows_reclassification_out','sat',[*base,z3.Not(old_guard),new_guard,op==1,selected(old,R),z3.Not(selected(new,S)),complete,witness==key,changed]),
 ('omitted_new_guard_allows_reclassification_in','sat',[*base,old_guard,z3.Not(new_guard),op==1,z3.Not(selected(old,S)),selected(new,R),complete,witness==key,changed]),
 ('omitted_required_association_allows_fact_change','sat',[*base,old_guard,new_guard,op==2,selected(old,R),z3.Not(selected(old,S)),witness==key,changed]),
 ('missing_original_scope_refuses_write','unsat',[held,z3.Not(known),allowed]),
 ('selected_truncate_guard_preserves_projection','unsat',[held,truncate_guard,truncate_step,project(z3.Select(truncated,witness))!=project(z3.Select(A,witness))]),
 ('omitted_truncate_guard_changes_projection','sat',[held,z3.Not(truncate_guard),truncate_step,project(z3.Select(truncated,witness))!=project(z3.Select(A,witness))]),
 ('monotonic_scope_extension_preserves_required_coverage','unsat',[complete,z3.ForAll([rel],z3.Implies(z3.Select(S,rel),z3.Select(T,rel))),z3.Select(R,witness),z3.Not(z3.Select(T,witness))]),
 ('shrunk_scope_loses_required_coverage','sat',[complete,z3.Select(R,witness),z3.Not(z3.Select(T,witness))])]
results=[]
for name,expected,clauses in queries:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(*clauses);raw=solver.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(solver.check())
 ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));replayed=str(replay.check())
 if observed!=expected or replayed!=expected:raise RuntimeError((name,observed,replayed))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':replayed,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(solver.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded symbolic edge IDs/typed rows and required/native relation-type sets. Complete native scope superset, actual old/new-row correspondence, continuously held cut and faithful one-row transitions imply arbitrary one-step required-projection preservation; stable-scope finite-history induction assumes those premises at every step. Monotonic extension preserves earlier required coverage, not earlier baseline equality for newly added facts. Truncate has a separate statement guard. Does not derive SQL/trigger/savepoint/driver refinement, original authenticated dependency membership, installed source/ACL closure, whole authorization, business-write authorization, complete atomic effects or final disclosure.'}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
