# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exact integer codec laws, not a PostgreSQL arithmetic refinement theorem."""
from pathlib import Path
import json,hashlib
import z3

out=Path('docs/helix/04-build/evidence/security-preparation-integer-xid-formal-20261014')
out.mkdir(exist_ok=True)
x,y=z3.Ints('original_xid supplied_xid')
base=2**32
valid=lambda value:z3.And(value>=1,value<2**64)
signed=lambda value:z3.If(value>=2**31,value-base,value)
oid=lambda value:z3.If(value<0,value+base,value)
low=lambda value:value%base
high=lambda value:value/base
encoded=lambda value:(signed(low(value)),signed(high(value)))
xl,xh=encoded(x);yl,yh=encoded(y)
queries=[
 ('exact-integer-quotient-reconstructs-full-xid',z3.And(valid(x),high(x)*base+low(x)!=x),'unsat'),
 ('encoded-pieces-fit-native-int32',z3.And(valid(x),z3.Or(xl<-(2**31),xl>=2**31,xh<-(2**31),xh>=2**31)),'unsat'),
 ('signed-int32-to-oid-roundtrip',z3.And(valid(x),z3.Or(oid(xl)!=low(x),oid(xh)!=high(x))),'unsat'),
 ('complete-native-marker-tuple-injective',z3.And(valid(x),valid(y),oid(xl)==oid(yl),oid(xh)==oid(yh),x!=y),'unsat'),
 ('discarded-high-marker-allows-foreign-xid',z3.And(valid(x),valid(y),oid(xl)==oid(yl),x!=y),'sat'),
]
results=[]
for name,formula,expected in queries:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(formula)
 text=solver.to_smt2();(out/(name+'.smt2')).write_text(text)
 result=str(solver.check());assert result==expected,(name,result)
 replay=z3.Solver(ctx=z3.Context());replay.set(timeout=10000);replay.from_string(text)
 assert str(replay.check())==expected
 results.append(dict(id=name,result=result,expected=expected,model=str(solver.model()) if result=='sat' else None,sha256=hashlib.sha256(text.encode()).hexdigest()))
receipt=dict(status='conditional-integer-codec-passed',solver=z3.get_version_string(),queries=results,sourceSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='All nonzero unsigned64 xids under exact integer Euclidean quotient/modulo, signed32 encoding and unsigned OID reconstruction.',limits=['Models exact integer quotient; PostgreSQL NUMERIC / rounding is deliberately not this operation.','Native div/mod implementation and lock representation are premises, not refined by these SMT formulas.','Native maximum-xid failing division control and repaired div boundary vectors are retained separately.','No anchor, peer, authority, guarded issuer, selector/seal or backend admission theorem.'])
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'queries':len(results)}))
