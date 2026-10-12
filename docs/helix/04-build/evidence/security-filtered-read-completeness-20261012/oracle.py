"""Exhaustive Boolean oracle independent of Z3 expressions (64 assignments)."""
import itertools,json
from pathlib import Path
counts=[0]*5
for bits in itertools.product([False,True],repeat=6):
 v0=bits[:2];v1=bits[2:4];active=bits[4:]
 c0=all(v0);c1=all(v1);visible=any(v1[i] and active[i] for i in range(2));coherent=v0==v1
 values=[c1 and visible and not c1,visible and not c1,c0 and visible and not c1,c0 and coherent and visible and not c1,c0 and coherent and visible]
 for i,value in enumerate(values):counts[i]+=int(value)
assert counts[0]==counts[3]==0 and all(counts[i]>0 for i in [1,2,4])
Path(__file__).with_name('oracle.json').write_text(json.dumps({'assignments':64,'satisfyingAssignmentCounts':counts,'scope':'Exactly the two-row Boolean model, not implementation refinement.'},indent=2)+'\n')
