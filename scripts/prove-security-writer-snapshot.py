# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional ordering model; native snapshot semantics are a separate premise."""
import hashlib,json,sys
from pathlib import Path
import z3
snapshot,revocation,guard=z3.Ints('snapshot revocation_commit guard_acquired')
base=z3.And(snapshot>=0,revocation>=0,guard>=0,revocation<=guard)
checks=[('guard-inside-statement-can-retain-stale-snapshot',z3.And(base,snapshot<revocation),z3.sat),('separate-prelock-before-fresh-statement-excludes-stale-snapshot',z3.And(base,guard<=snapshot,snapshot<revocation),z3.unsat),('fresh-order-is-satisfiable',z3.And(base,guard<snapshot,revocation<guard),z3.sat)]
cases=[]
for name,formula,expected in checks:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(formula);smt=solver.sexpr();result=solver.check()
 if result!=expected:raise RuntimeError(name+': '+str(result))
 replay=z3.Solver();replay.from_string(smt)
 if replay.check()!=expected:raise RuntimeError('retained SMT replay failed')
 cases.append({'id':name,'result':str(result),'smt':smt,'witness':str(solver.model()) if result==z3.sat else None})
paths=[Path(__file__),Path('packages/python/tests/test_security_public_ontology_native.py'),Path('packages/postgresql/native/security-data-writer-guard-pg18.sql')]
receipt={'status':'conditional-ordering-proof','solverVersion':z3.get_version_string(),'sourceDigests':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'cases':cases,'scope':'Unbounded integer event ordering only. Premises: committed revocation precedes original guard acquisition, same guard remains held through fresh DML, and supported READ COMMITTED separate-command snapshot is taken after guard acquisition. Native paired race separately demonstrates the selected predicate behavior. No verification of SQL/Python refinement, snapshot implementation generally, logical authorization, all writers, admission, liveness or complete acceptance. SAT inside-statement control prevents treating native trigger guard as a freshness theorem.'}
Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'unsat':1,'sat':2}))
