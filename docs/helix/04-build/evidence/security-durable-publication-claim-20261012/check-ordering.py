"""Conditional finite durable-claim ordering; not native implementation proof."""
from pathlib import Path
import itertools,json,z3
root=Path(__file__).parent
names=['register','loss','release','settle','ack'];t={n:z3.Int(n) for n in names}
base=[z3.Distinct(*t.values()),*[z3.And(v>=0,v<5) for v in t.values()],t['register']<t['loss'],t['register']<t['release'],t['register']<t['settle'],t['settle']<t['ack']]
queries={'durable-claim-stale-release':(base+[t['release']<t['settle'],t['ack']<t['release']],'unsat'),'durable-claim-success-after-loss':(base+[t['loss']<t['release'],t['release']<t['settle']],'sat'),'auto-clear-on-loss-counterexample':(base+[t['loss']<t['settle'],t['ack']<t['release']],'sat')}
results={}
for name,(clauses,expected) in queries.items():
 s=z3.Solver();s.add(*clauses);(root/(name+'.smt2')).write_text(s.to_smt2());r=s.check();assert str(r)==expected
 results[name]={'result':str(r),'witness':{n:s.model().eval(t[n]).as_long() for n in names} if r==z3.sat else None}
counts={'orders':0,'base':0,'durableStale':0,'durableSuccessAfterLoss':0,'autoClearStale':0}
for order in itertools.permutations(names):
 counts['orders']+=1;p={n:order.index(n) for n in names}
 if not(p['register']<p['loss'] and p['register']<p['release'] and p['register']<p['settle']<p['ack']):continue
 counts['base']+=1;durable=p['release']<p['settle'];stale=p['ack']<p['release']
 counts['durableStale']+=int(durable and stale);counts['durableSuccessAfterLoss']+=int(durable and p['loss']<p['release']);counts['autoClearStale']+=int(p['loss']<p['settle'] and stale)
assert counts['durableStale']==0 and counts['durableSuccessAfterLoss']>0 and counts['autoClearStale']>0
print(json.dumps({'solver':z3.get_version_string(),'queries':results,'independentEnumeration':counts,'scope':'Five distinct events, one durable registered claim and one participating authority acknowledgment. Settlement only after final release and acknowledgment only after settlement are assumptions. No native SQL equivalence, multi-operation generalization, clock/TTL, source/issuer/sink authenticity, simultaneous events or driver refinement.'},indent=2))
