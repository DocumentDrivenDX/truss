# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional selected-fact stability, not SQL/trigger/native refinement.

Reader continuously holds a conflicting table cut, foreign writes participate,
and an exact installed before-effect guard excludes same-backend writes. Other
source/caller/context inputs stay fixed. DML transitions are faithful and atomic.
"""
from pathlib import Path
import hashlib,json,z3
root=Path(__file__).resolve().parent.parent
out=root/'docs/helix/04-build/evidence/accepted-catalog-fact-guard-20261013/formal';out.mkdir(parents=True,exist_ok=True)
row=z3.DeclareSort('SelectedFactRow');array=z3.ArraySort(z3.IntSort(),row)
before=z3.Const('before',array);value=z3.Const('value',row);absent=z3.Const('absent',row);key=z3.Int('key');op=z3.Int('operation')
cut,same,guard=z3.Bools('continuously_held_cut same_backend installed_before_effect_guard')
allowed=z3.Or(z3.Not(cut),z3.And(same,z3.Not(guard)))
changed=z3.If(op==3,z3.K(z3.IntSort(),absent),z3.Store(before,key,z3.If(op==2,absent,value)))
after=z3.If(allowed,changed,before)
policy=z3.Function('fixed_source_caller_context_pure_policy',array,z3.BoolSort())
cases=[('selected_guard_preserves_all_rows_and_pure_decision','unsat',[cut,guard,z3.Or(after!=before,policy(after)!=policy(before))]),
       ('foreign_writer_conflict_preserves_rows_without_own_guard','unsat',[cut,z3.Not(same),after!=before]),
       ('missing_same_backend_guard_allows_fact_and_decision_change','sat',[cut,same,z3.Not(guard),op==1,after!=before,policy(after)!=policy(before)]),
       ('released_cut_allows_foreign_fact_change','sat',[z3.Not(cut),z3.Not(same),op==1,after!=before])]
results=[]
for name,expected,clauses in cases:
 s=z3.Solver();s.add(op>=0,op<=3,*clauses);actual=str(s.check());raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw)
 replay=z3.Solver();replay.add(z3.parse_smt2_string(raw));again=str(replay.check())
 if (actual,again)!=(expected,expected):raise RuntimeError(name)
 results.append({'id':name,'expected':expected,'observed':actual,'replay':again,'model':str(s.model()) if actual=='sat' else None})
paths=['scripts/prove-selected-fact-write-exclusion.py','packages/postgresql/native/authorization-fact-write-fence.sql','packages/python/src/truss/_psycopg_fact_cut.py','scripts/security_catalog_read.py']
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'queries':results,'scope':__doc__,'limits':['No source/native/trigger/savepoint/driver refinement or complete statement effect inventory proof.','No source/caller/issuer authenticity, RLS/role/ACL/DDL lifetime or protected final release theorem.','Pure policy is uninterpreted with fixed non-fact inputs; no original evaluator implementation theorem.'],'sourceDigests':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'queries':len(results),'status':r['status']}))
