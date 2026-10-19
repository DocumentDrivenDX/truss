# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional typed graph IDs/business-key membership correspondence.

Original UMF string-key equality, complete faithful selected edge projection,
unique typed node identities and key injectivity on each compared pair are
premises. IDs and key values are symbolic and unbounded. This
is not native SQL/codec/evaluator refinement or authenticated policy authority.
"""
import json,hashlib
from pathlib import Path
import z3
root=Path(__file__).resolve().parent.parent
out=root/'docs/helix/04-build/evidence/graph-policy-read-20261013/formal';out.mkdir(parents=True,exist_ok=True)
s,a,p,q,r,o=z3.Ints('caller_node assignment_staff assignment_project ownership_project resource_node ownership_resource')
staff=z3.Function('staff_key',z3.IntSort(),z3.StringSort())
project=z3.Function('project_key',z3.IntSort(),z3.StringSort())
resource=z3.Function('resource_key',z3.IntSort(),z3.StringSort())
injective=[z3.Implies(f(left)==f(right),left==right) for f,left,right in ((staff,s,a),(project,p,q),(resource,r,o))]
graph=z3.And(s==a,p==q,r==o)
semantic=z3.And(staff(s)==staff(a),project(p)==project(q),resource(r)==resource(o))
cases=[('injective_typed_keys_preserve_membership',injective+[graph!=semantic],'unsat'),
       ('duplicate_staff_key_breaks_native_id_correspondence',injective[1:]+[s!=a,staff(s)==staff(a),p==q,r==o,graph!=semantic],'sat'),
       ('omitted_project_join_changes_membership',injective+[z3.And(staff(s)==staff(a),resource(r)==resource(o)),z3.Not(semantic)],'sat')]
rows=[]
for name,premises,expected in cases:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(*premises);actual=str(solver.check())
 (out/(name+'.smt2')).write_text(solver.to_smt2())
 rows.append({'id':name,'expected':expected,'observed':actual,'model':str(solver.model()) if actual=='sat' else None})
 if actual!=expected:raise RuntimeError(name+': '+actual)
receipt={'solver':z3.get_version_string(),'queries':rows,'scope':__doc__,'sources':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in ('scripts/security_graph_read.py','scripts/evaluate-security-captured-identity-fixture.ts','scripts/prove-graph-semantic-membership.py')}}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'queries':len(rows),'status':'conditional-model-passed'}))
