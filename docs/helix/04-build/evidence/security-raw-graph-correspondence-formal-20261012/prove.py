"""Bounded two-instance typed raw/graph correspondence; no SQL refinement."""
from pathlib import Path
import json,z3
out=Path(__file__).parent
# Four disjoint typed key spaces each have exactly two logical/native instances.
key={kind:[z3.Int(kind+'_native_key_'+str(i)) for i in range(2)] for kind in ['staff','assignment','project','resource']}
raw={name:[[z3.Bool('raw_'+name+'_'+str(i)+'_'+str(j)) for j in range(2)] for i in range(2)] for name in ['sa','ap','rp']}
graph={name:[[z3.Bool('graph_'+name+'_'+str(i)+'_'+str(j)) for j in range(2)] for i in range(2)] for name in ['sa','ap','rp']}
active=[z3.Bool('raw_active_'+str(i)) for i in range(2)];native_active=[z3.Bool('native_active_'+str(i)) for i in range(2)]
def lookup(matrix,i,j):return z3.Or(*[z3.And(i==a,j==b,matrix[a][b]) for a in range(2) for b in range(2)])
def bit_lookup(bits,i):return z3.Or(*[z3.And(i==a,bits[a]) for a in range(2)])
bounds=z3.And(*[z3.And(value>=0,value<2) for values in key.values() for value in values])
bijection=z3.And(*[values[0]!=values[1] for values in key.values()])
incidence=[]
for name,left,right in [('sa','staff','assignment'),('ap','assignment','project'),('rp','resource','project')]:
 for i in range(2):
  for j in range(2):incidence.append(graph[name][i][j]==lookup(raw[name],key[left][i],key[right][j]))
attributes=z3.And(*[native_active[i]==bit_lookup(active,key['assignment'][i]) for i in range(2)])
def eligible_raw(s,r):return z3.Or(*[z3.And(raw['sa'][s][a],active[a],raw['ap'][a][p],raw['rp'][r][p]) for a in range(2) for p in range(2)])
def eligible_graph(s,r):return z3.Or(*[z3.And(key['staff'][ns]==s,key['resource'][nr]==r,graph['sa'][ns][a],native_active[a],graph['ap'][a][p],graph['rp'][nr][p]) for ns in range(2) for nr in range(2) for a in range(2) for p in range(2)])
difference=z3.Or(*[eligible_raw(s,r)!=eligible_graph(s,r) for s in range(2) for r in range(2)])
exact=z3.And(*incidence)
# Omit only resource-owner correspondence; all other premises remain.
no_owner=z3.And(*incidence[:8])
cases=[('exact-typed-correspondence-preserves-membership',[bounds,bijection,exact,attributes,difference],'unsat'),('missing-owner-incidence-can-change-membership',[bounds,bijection,no_owner,attributes,difference],'sat'),('missing-active-attribute-can-change-membership',[bounds,bijection,exact,difference],'sat'),('nonbijective-key-projection-can-lose-membership',[bounds,exact,attributes,difference],'sat'),('nonvacuous-authorized-population',[bounds,bijection,exact,attributes,eligible_raw(0,0),eligible_graph(0,0)],'sat')]
observations=[]
for name,premises,expected in cases:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(*premises);(out/(name+'.smt2')).write_text(solver.to_smt2());observed=str(solver.check());assert observed==expected,(name,observed)
 replay=z3.Solver();replay.set(timeout=10000);replay.from_file(str(out/(name+'.smt2')));assert str(replay.check())==expected
 observations.append({'id':name,'expected':expected,'observed':observed,'formula':name+'.smt2','model':str(solver.model()) if observed=='sat' else None})
(out/'formal.json').write_text(json.dumps({'solver':z3.get_version_string(),'bound':'Exactly two instances in each of four disjoint typed key spaces; arbitrary Boolean incidences/active flags and independent native key permutations.','assumptions':'Decoded native keys are bounded typed bijections; complete incidence and active values correspond exactly. No unknown-value/codec, SQL/TS refinement, authentic population, caller, cut or authority proof.','observations':observations,'replays':5},indent=2)+'\n')
