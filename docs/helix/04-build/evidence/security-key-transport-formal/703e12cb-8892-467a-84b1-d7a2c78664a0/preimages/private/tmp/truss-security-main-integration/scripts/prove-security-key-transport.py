"""Conditional ordered-key transport algebra, not encoder/native refinement."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();owner=Path('/Users/erik/.codex/worktrees/security-main-integration/umf');out=root/'docs/helix/04-build/evidence/security-key-transport-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=[root/p for p in ('scripts/prove-security-key-transport.py','scripts/evaluate-security-captured-identity-fixture.ts','scripts/produce-security-identity-requirements.ts','packages/python/src/truss/_psycopg_dependency_fact_cut.py','docs/helix/04-build/evidence/security-identity-requirements/transport.json','docs/helix/04-build/evidence/security-identity-requirements/requirements.json')]+[owner/'src/extensions/security/dependencies.ts',owner/'src/model/key-tuple.ts']
pins={}
for p in paths:
 raw=p.read_bytes();pins[str(p)]=hashlib.sha256(raw).hexdigest();dest=out/'preimages'/str(p).lstrip('/');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
I=z3.IntSort();A=z3.Array('original_field_values',I,I);B=z3.Array('later_field_values',I,I);K=z3.Array('original_ordered_components',I,I);L=z3.Array('later_ordered_components',I,I)
n,m,i,w=z3.Ints('original_width later_width index witness');t,k=z3.Ints('qualified_type stable_key_id')
vector=lambda values,order,width:z3.Lambda(i,z3.If(z3.And(i>=0,i<width),z3.Select(values,z3.Select(order,i)),0))
VA=vector(A,K,n);VB=vector(B,L,m)
stable=z3.ForAll([i],z3.Implies(z3.And(i>=0,i<n),z3.Select(A,z3.Select(K,i))==z3.Select(B,z3.Select(K,i))))
encode=z3.Function('stable_deterministic_encoder',I,I,I,z3.ArraySort(I,I),I)
frame=[n>0,n==m,K==L,stable]
queries=[
 ('complete_component_cuts_preserve_original_key_vector','unsat',frame+[VA!=VB]),
 ('complete_original_frame_preserves_deterministic_identity','unsat',frame+[encode(t,k,n,VA)!=encode(t,k,m,VB)]),
 ('changed_component_order_changes_key_despite_unchanged_data','sat',[n==2,m==2,A==B,z3.Select(K,0)==0,z3.Select(K,1)==1,z3.Select(L,0)==1,z3.Select(L,1)==0,z3.Select(A,0)!=z3.Select(A,1),VA!=VB]),
 ('changed_key_width_can_change_identity_despite_unchanged_data','sat',[n==1,m==2,A==B,K==L,encode(t,k,n,VA)!=encode(t,k,m,VB)]),
 ('row_ordinal_can_collide_for_distinct_original_keys','sat',[z3.Select(A,0)!=z3.Select(A,1),encode(t,k,1,z3.K(I,0))==encode(t,k,1,z3.K(I,0))])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded positive ordered-key widths, opaque qualified component references and typed canonical values. Stable original width/order/frame plus preserved selected values imply key-vector and stable deterministic encoder equality.','limitations':['Integer symbols abstract qualified references and full typed literals; no hash-collision or native domain inference','No injectivity/byte-format, original UMF encoder, JSON/Python/SQL capture or browser refinement theorem','Ordinal counter only demonstrates that replacing original key material by constant row position permits distinct-key collision; no SQL row-order theorem','No authenticated issuer/mapping, complete source/role/config cut, protected evaluation or final disclosure admission']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
