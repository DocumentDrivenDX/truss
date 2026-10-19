# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional bounded-query sentinel algebra, not SQL/driver refinement."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-capture-cardinality-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-capture-cardinality.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
source,quota,received=z3.Ints('complete_source_rows quota received_native_rows');bounded=received==z3.If(source<=quota+1,source,quota+1);accept=received<=quota
base=[source>=0,quota>=0,bounded]
queries=[('sentinel_acceptance_cannot_hide_over_quota_source','unsat',base+[accept,source>quota]),('sentinel_accepted_capture_is_count_complete','unsat',base+[accept,received!=source]),('sentinel_native_result_is_bounded','unsat',base+[received>quota+1]),('omitted_limit_can_receive_unbounded_source','sat',[source>=0,quota>=0,received==source,received>quota+1]),('limit_at_quota_silently_accepts_incomplete_source','sat',[source>=0,quota>=0,received==z3.If(source<=quota,source,quota),accept,source>quota])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded nonnegative source cardinality and quota. A faithful query result min(source,quota+1) plus refusal above quota guarantees native row bound and count-complete acceptance.','limitations':['Does not derive SQL LIMIT semantics, driver PGresult origin or semantic row correspondence from implementation','Requires original complete visible source population; no RLS/role/source/authority visibility qualification','Count completeness is not field/identity completeness, strict byte/allocator transport budget, protected policy execution or final disclosure']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
