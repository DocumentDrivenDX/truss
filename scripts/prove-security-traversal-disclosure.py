# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional public traversal/private witness laws; no backend refinement."""
from pathlib import Path
import hashlib,json,z3
out=Path('docs/helix/04-build/evidence/security-traversal-disclosure-formal-20261014');out.mkdir(exist_ok=True)
record=z3.DeclareSort('RecordIdentity')
s,t=z3.Consts('source target',record)
source_ok=z3.Function('source_eligible',record,z3.BoolSort())
target_ok=z3.Function('target_eligible',record,z3.BoolSort())
key=z3.Function('matches_original_target_key',record,z3.BoolSort())
edge1=z3.Function('relationship_world1',record,record,z3.BoolSort())
edge2=z3.Function('relationship_world2',record,record,z3.BoolSort())
edge_ok=z3.Function('relationship_disclosable',record,record,z3.BoolSort())
def visible(edge,a,b):return z3.And(source_ok(a),target_ok(b),edge_ok(a,b),edge(a,b))
def has(edge,a):return z3.Exists(t,z3.And(visible(edge,a,t),key(t)))
visible_equal=z3.ForAll([s,t],visible(edge1,s,t)==visible(edge2,s,t))
private_witness=z3.Exists(t,z3.And(edge1(s,t),key(t)))
count,hidden,bound=z3.Ints('eligible_related_occurrences hidden_related_occurrences requested_bound')
queries=[
 ('hidden-source-no-public-witness',z3.And(z3.Not(source_ok(s)),has(edge1,s)),'unsat'),
 ('hidden-target-cannot-witness',z3.And(z3.Not(target_ok(t)),visible(edge1,s,t)),'unsat'),
 ('undisclosed-relationship-cannot-witness',z3.And(z3.Not(edge_ok(s,t)),visible(edge1,s,t)),'unsat'),
 ('visible-projection-noninterference',z3.And(visible_equal,has(edge1,s)!=has(edge2,s)),'unsat'),
 ('private-witness-is-not-query-permission',z3.And(source_ok(s),private_witness,z3.ForAll(t,z3.Not(target_ok(t))),z3.Not(has(edge1,s))),'sat'),
 ('raw-lookahead-leaks-hidden-cardinality',z3.And(count>=0,hidden>0,bound>0,count<=bound,count+hidden>bound),'sat')]
results=[]
for name,formula,expected in queries:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(formula);raw=solver.to_smt2();(out/(name+'.smt2')).write_text(raw)
 observed=str(solver.check());assert observed==expected,(name,observed)
 replay=z3.Solver(ctx=z3.Context());replay.set(timeout=10000);replay.from_string(raw);assert str(replay.check())==expected
 results.append({'id':name,'expected':expected,'observed':observed,'model':str(solver.model()) if observed=='sat' else None,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest()})
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'queries':results,'scope':'Uninterpreted record identities and relationship relations; eligible/disclosable projection invariance for existential original-key traversal. Arbitrary nonnegative integer cardinalities demonstrate raw truncation leakage.','limitations':['Eligibility, original identity/key correspondence and relationship disclosure are assumed; no new policy permission is granted.','Private witness is modeled only as existence, not as a complete policy decision.','No compiler/native SQL/codec/authority/cut/publication refinement theorem.','No path/multiplicity/outer-join/order/cardinality reconstruction theorem or backend case promotion.']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'queries':len(results)}))
