"""Two-row conditional model; no SQL/TS refinement or native guard proof."""
import json
from pathlib import Path
import z3
out=Path(__file__).parent
valid0=[z3.Bool('valid_cut0_'+str(i)) for i in range(2)]
valid1=[z3.Bool('valid_cut1_'+str(i)) for i in range(2)]
active=[z3.Bool('active_'+str(i)) for i in range(2)]
visible=[z3.And(valid1[i],active[i]) for i in range(2)]
complete0=z3.And(*valid0);complete1=z3.And(*valid1)
filtered=z3.Or(*visible)
coherent=z3.And(*[valid0[i]==valid1[i] for i in range(2)])
cases=[
 ('complete-current-gate-rejects-malformation',z3.And(complete1,filtered,z3.Not(complete1)),'unsat'),
 ('filtered-success-does-not-imply-completeness',z3.And(filtered,z3.Not(complete1)),'sat'),
 ('old-preflight-does-not-establish-current-completeness',z3.And(complete0,filtered,z3.Not(complete1)),'sat'),
 ('coherent-preflight-rejects-malformation',z3.And(complete0,coherent,filtered,z3.Not(complete1)),'unsat'),
 ('valid-eligible-positive',z3.And(complete0,coherent,filtered),'sat')]
observations=[]
for name,formula,expected in cases:
 solver=z3.Solver();solver.add(formula);path=out/(name+'.smt2');path.write_text(solver.to_smt2());observed=str(solver.check());assert observed==expected
 observations.append({'id':name,'expected':expected,'observed':observed,'formula':path.name,'model':str(solver.model()) if observed=='sat' else None})
(out/'formal.json').write_text(json.dumps({'solver':z3.get_version_string(),'bound':'Exactly two abstract rows and two validity cuts; Boolean eligibility requires validity.','assumptions':'Complete preflight covers both rows; coherent means unchanged per-row validity across cuts. No implementation refinement, complete population authentication or held native authority proof.','observations':observations},indent=2)+'\n')
