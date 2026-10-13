"""Exact current guard compatibility; not implementation refinement or authority."""
from pathlib import Path
from hashlib import sha256
import json,sys
import z3
ROOT=Path(__file__).resolve().parents[2]
iso=z3.Int('isolation');readonly=z3.Bool('read_only')
domain=z3.Or(iso==0,iso==1,iso==2) # read committed, repeatable read, serializable
subject=z3.And(z3.Or(iso==1,iso==2),readonly)
fresh=z3.And(iso==0,z3.Not(readonly))
def check(name,constraint,expected):
 solver=z3.Solver();solver.add(domain,constraint);actual=solver.check()
 if str(actual)!=expected:raise AssertionError(name)
 result={'name':name,'expected':expected,'actual':str(actual),'smt2':solver.to_smt2()}
 if actual==z3.sat:
  model=solver.model();result['witness']={'isolation':['read_committed','repeatable_read','serializable'][model.eval(iso).as_long()],'readOnly':z3.is_true(model.eval(readonly))}
 return result
results=[check('current original guards have no shared native transaction profile',z3.And(subject,fresh),'unsat'),
 check('subject repeatable-read read-only is independently feasible',z3.And(subject,iso==1),'sat'),
 check('subject serializable read-only is independently feasible',z3.And(subject,iso==2),'sat'),
 check('fresh fenced source read-committed read-write is independently feasible',fresh,'sat'),
 check('changing only access mode cannot compose repeatable-read with fresh source',z3.And(fresh,iso==1),'unsat'),
 check('changing only isolation cannot compose read-only with fresh source',z3.And(fresh,readonly),'unsat')]
paths=['packages/python/src/truss/_psycopg_subject_observation.py','packages/postgresql/native/source-epoch-fresh-lock.sql','packages/postgresql/native/source-epoch-fenced-fresh-lock.sql','tools/security/prove-subject-source-profile-compatibility.py']
output={'z3Version':z3.get_version_string(),'scope':'Finite current isolation/access guard predicates; three UNSAT compatibility controls and three SAT nonvacuity witnesses. Guards are transcribed/reviewed premises, not Python/SQL source refinement or proof of native installation/authority.','sourceSha256':{p:sha256((ROOT/p).read_bytes()).hexdigest()for p in paths},'results':results,'conclusion':'Current profiles cannot compose in one transaction. Existing native component passes do not establish protected caller/source integration. A new admitted fresh fenced read profile or independently qualified fresh stronger-isolation source producer is required; no current guard is relaxed.'}
Path(sys.argv[1]).write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'checks':len(results),'unsat':3,'sat':3,'composable':False}))
