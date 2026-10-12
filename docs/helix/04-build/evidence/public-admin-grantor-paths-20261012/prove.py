"""Conditional three-role linear delegation model; not general native refinement."""
from pathlib import Path
from itertools import product
import json,z3
root=Path(__file__).parent
flags=z3.Bools('i0 s0 a0 i1 s1 a1')
def exposure(bits,compressed):
 edges=[(0,1,*bits[:3]),(1,2,*bits[3:])];states={(0,0)}
 while True:
  next_states=set(states)
  for active,privilege in states:
   for source,target,inherit,sets,admin in edges:
    if source!=privilege:continue
    switch=admin or (sets and active==privilege)
    if switch:next_states.add((target,target))
    if inherit and (not compressed or not switch):next_states.add((active,target))
  if next_states==states:break
  states=next_states
 return any(active==2 or active==1 and bits[3] or active==0 and bits[0] and bits[3] for active,_ in states)
def formula(compressed):
 return z3.Or(*[z3.And(*[f if b else z3.Not(f) for f,b in zip(flags,bits)]) for bits in product([False,True],repeat=6) if exposure(bits,compressed)])
full,compact=formula(False),formula(True)
i0,s0,a0,i1,s1,a1=flags
old=z3.Or(z3.And(i0,i1),z3.And(z3.Or(s0,a0),z3.Or(i1,s1,a1)))
queries=[('compressed-active-state-equivalence',full!=compact,'unsat'),('inherited-admin-missing-from-old-closure',z3.And(i0,z3.Not(s0),z3.Not(a0),z3.Not(i1),z3.Not(s1),a1,full,z3.Not(old)),'sat')]
out={}
for name,query,expected in queries:
 s=z3.Solver();s.add(query);p=root/(name+'.smt2');p.write_text(s.to_smt2());assert str(s.check())==expected
 replay=z3.Solver(ctx=z3.Context());replay.add(z3.parse_smt2_file(str(p),ctx=replay.ctx));assert str(replay.check())==expected
 out[name]=expected
print(json.dumps({'z3':z3.get_version_string(),'linear_graph_assignments':64,'queries':out,'fresh_replays':2,'limits':'Three-role linear model with native effective inherited ACLs and inherited ADMIN grantor behavior as premises. No arbitrary/cyclic graph, SQL/driver/source-currentness/delegation/lifetime refinement or backend qualification.'},indent=2))
