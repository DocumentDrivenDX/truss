"""Conditional bag join law; not SQL/native/compiler refinement evidence."""
from pathlib import Path
import hashlib,json,z3
out=Path('docs/helix/04-build/evidence/security-relational-join-formal-20261014');out.mkdir(exist_ok=True)
l,r=z3.Ints('left_occurrences right_occurrences')
el,er,on=z3.Bools('left_eligible right_eligible original_join_predicate')
premise=z3.And(l>=0,r>=0)
left=z3.If(el,l,0);right=z3.If(er,r,0)
joined=z3.If(on,left*right,0)
original=z3.If(z3.And(el,er,on),l*r,0)
queries=[('eligible-bag-join-law',z3.And(premise,joined!=original),'unsat'),
 ('hidden-left-contributes-zero',z3.And(premise,z3.Not(el),joined!=0),'unsat'),
 ('hidden-right-contributes-zero',z3.And(premise,z3.Not(er),joined!=0),'unsat'),
 ('filtering-only-left-leaks-right',z3.And(premise,l>0,r>0,el,z3.Not(er),on,z3.If(on,left*r,0)>0),'sat')]
results=[]
for name,formula,expected in queries:
 solver=z3.Solver();solver.add(formula);raw=solver.to_smt2();(out/(name+'.smt2')).write_text(raw)
 observed=str(solver.check());assert observed==expected,(name,observed)
 replay=z3.Solver(ctx=z3.Context());replay.from_string(raw);assert str(replay.check())==expected
 results.append({'id':name,'expected':expected,'observed':observed,'model':str(solver.model()) if observed=='sat' else None,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest()})
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'queries':results,'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Arbitrary nonnegative integer bag multiplicities for a fixed pair of native identities and original join predicate. Both input populations must apply original primary eligibility before the bag join.','limitations':['Eligibility and identity correspondence are assumed, not authenticated by the algebra.','No SQL optimizer/compiler/codec/native-role or release refinement is proved.','No NULL/absence predicate semantics, outer join, cursor or aggregate theorem.','Native self-join evidence is separate; no complete B03 promotion.']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'queries':len(results)}))
