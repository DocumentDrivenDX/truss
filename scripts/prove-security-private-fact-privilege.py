# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional private-fact privilege exclusion; native callable closure and lifetime remain unproved."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-private-fact-privilege-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-private-fact-privilege.py','scripts/security_owned_read.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
table,column,definer,admin,callback=z3.Bools('table_privilege column_privilege definer_execute privileged_role callback')
protocol=callback==z3.Not(z3.Or(table,column,definer,admin))
queries=[
 ('private_table_privilege_excludes_callback','unsat',[protocol,table,callback]),
 ('private_column_privilege_excludes_callback','unsat',[protocol,column,callback]),
 ('reachable_definer_excludes_callback','unsat',[protocol,definer,callback]),
 ('table_only_filter_misses_column_privilege','sat',[callback==z3.Not(table),z3.Not(table),column,callback]),
 ('excluded_privileges_absent_allows_callback_in_this_dimension','sat',[protocol,z3.Not(table),z3.Not(column),z3.Not(definer),z3.Not(admin),callback])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract active table/column/definer/administration privilege exclusion. A table-only filter admits a column-only bypass. Absence of these excluded paths is compatible with callback in this dimension.','limitations':['No native privilege-function, role-path, SQL, callable closure or host refinement proof','These checks are snapshots and do not prove role/grant/routine lifetime','No original caller/issuer/mapping authentication, complete private-fact isolation or protected backend admission']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
