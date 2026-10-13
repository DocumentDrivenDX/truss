"""Conditional event-order model, not Rust/TypeScript/native refinement."""
import argparse,hashlib,json
from pathlib import Path
import z3

def scenario(final_guard=True,atomic=True):
 pre,reset,gate,publish,close=z3.Ints('initial_gate reset_complete final_gate publish closure')
 reset_ok=z3.Bool('reset_ok')
 schedule=[pre>=0,reset>pre,gate>=reset,close>=0,publish==gate if atomic else publish>gate]
 # Closure is monotone; an event sees closed iff closure occurred by that event.
 lease=z3.And(reset_ok,pre<close,gate<close if final_guard else z3.BoolVal(True))
 quarantine=z3.And(reset_ok,pre<close,close<=gate) if final_guard else z3.BoolVal(False)
 return schedule,lease,quarantine,(pre,reset,gate,publish,close,reset_ok)

def prove():
 results=[]
 def query(name,expected,guard=True,atomic=True,extra=lambda v,lease,q:[]):
  constraints,lease,q,v=scenario(guard,atomic);pre,reset,gate,publish,close,ok=v
  solver=z3.Solver();solver.add(*constraints,*extra(v,lease,q));status=str(solver.check())
  if status!=expected:raise RuntimeError(name+': '+status)
  result={'query':name,'expected':expected,'observed':status,'constraints':[str(x) for x in solver.assertions()]}
  if status=='sat':result['witness']={str(x):str(solver.model().eval(x,model_completion=True)) for x in (*v,lease,q)}
  results.append(result)
 query('pre-await-check-only-can-publish-after-closure','sat',guard=False,extra=lambda v,l,q:[l,v[4]<=v[3]])
 query('final-check-synchronous-publication-prevents-escape','unsat',extra=lambda v,l,q:[l,v[4]<=v[3]])
 query('yield-after-final-check-reopens-race','sat',atomic=False,extra=lambda v,l,q:[l,v[4]<=v[3]])
 query('closure-during-successful-reset-refuses-publication','unsat',extra=lambda v,l,q:[v[5],v[0]<v[4],v[4]<=v[1],l])
 query('pending-checkout-is-quarantined-after-closure','unsat',extra=lambda v,l,q:[v[5],v[0]<v[4],v[4]<=v[1],z3.Not(q)])
 query('failed-reset-never-publishes','unsat',extra=lambda v,l,q:[z3.Not(v[5]),l])
 query('future-acquisition-after-monotone-closure-refuses','unsat',extra=lambda v,l,q:[v[4]<=v[0],l])
 query('open-successful-source-can-publish','sat',extra=lambda v,l,q:[l,v[3]<v[4]])
 return results

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 root=Path(__file__).resolve().parents[2];source=root/'packages/pg-runtime/src/index.ts'
 result={'format':'truss.principal-acquisition-order-proof/0.1','solver':z3.get_version_string(),
  'scope':'One pending ordinaryPrincipal-configured acquisition and one monotone source closure in a single JavaScript isolate. Abstract event order only; no general native/driver/helper refinement or protected release proof.',
  'premises':['closure does not reopen','no await or reentrant external call between final check and lease publication','successful original reset is required to reach publication','original executed runtime is trusted'],
  'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modelSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'queries':prove(),
  'excluded':['closure revocation of previously published leases','native or authenticated helper semantics','complete role/subject/writer authority','process/crash recovery','quarantine shutdown proves native outcome settlement','full security backend acceptance']}
 Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'queries':len(result['queries']),'unsat':sum(q['observed']=='unsat' for q in result['queries']),'sat':sum(q['observed']=='sat' for q in result['queries']),'solver':result['solver']}))
if __name__=='__main__':main()
