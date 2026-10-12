"""Finite event-order proof; no native/driver refinement or lease authenticity."""
import itertools,json
from pathlib import Path
import z3
root=Path(__file__).parent
names=['acquire','probe','loss','ack','release']
t={n:z3.Int(n) for n in names}
base=[z3.Distinct(*t.values()),*[z3.And(v>=0,v<5) for v in t.values()],t['acquire']<t['probe'],t['probe']<t['release'],t['probe']<t['loss'],t['loss']<t['ack']]
# A participating revoker acknowledges only after original exclusion is lost.
# Stale protected disclosure means release after that acknowledgment.
stale=t['ack']<t['release']
queries={'probe-only-counterexample':base+[stale], 'retained-exclusion-no-stale-release':base+[t['release']<t['loss'],stale], 'successful-release-before-loss':base+[t['release']<t['loss']]}
results={}
for name,clauses in queries.items():
 s=z3.Solver();s.add(*clauses);(root/(name+'.smt2')).write_text(s.to_smt2());r=s.check();expected=z3.unsat if name=='retained-exclusion-no-stale-release' else z3.sat
 assert r==expected
 results[name]={'result':str(r),'witness':{n:s.model().eval(t[n]).as_long() for n in names} if r==z3.sat else None}
# Independently enumerate all 120 total event orders without solver expressions.
counts={'orders':0,'base':0,'probeOnlyStale':0,'retainedStale':0,'successfulRetained':0}
for order in itertools.permutations(names):
 counts['orders']+=1;p={n:order.index(n) for n in names}
 if not(p['acquire']<p['probe']<p['release'] and p['probe']<p['loss']<p['ack']):continue
 counts['base']+=1;st=p['ack']<p['release'];held=p['release']<p['loss']
 counts['probeOnlyStale']+=int(st);counts['retainedStale']+=int(st and held);counts['successfulRetained']+=int(held)
assert counts['probeOnlyStale']>0 and counts['retainedStale']==0 and counts['successfulRetained']>0
print(json.dumps({'solver':z3.get_version_string(),'queries':results,'independentEnumeration':counts,'scope':'Exactly five distinct events, one participating revoker, one buffered release. Required exclusion through release is a premise; not proved by a positive probe. No time, simultaneous events, arbitrary executions, source/caller authenticity or native refinement.'},indent=2))
