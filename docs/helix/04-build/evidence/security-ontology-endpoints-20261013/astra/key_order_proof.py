"""Scoped sequence-order lemma; not refinement of Python/native implementation."""
import json
from z3 import Array,IntSort,Int,Select,Solver,unsat,sat,Or
native=Array('native_key',IntSort(),IntSort());original=Array('original_key',IntSort(),IntSort());paired=Array('paired_target',IntSort(),IntSort());i=Int('i');n=Int('n')
s=Solver();s.add(n>0,i>=0,i<n,native==original,paired==native,Select(paired,i)!=Select(original,i));assert s.check()==unsat
# A weakened unordered two-component check accepts a swapped target sequence.
a=Int('a');b=Int('b');p0=Int('p0');p1=Int('p1')
s=Solver();s.add(a!=b,Or((p0==a)&(p1==b),(p0==b)&(p1==a)),p0!=a);assert s.check()==sat
print(json.dumps({'scope':'abstract ordered key/paired target sequence equality only, truthful native and original key sequences are premises','ordered_target_position_mismatch':'unsat','weakened_unordered_key_swap':'sat','not_proven':['native key encoding/equality-domain enforcement','ontology semantic closure refinement','issuer authenticity','row predicate lowering','complete writer/source and authority lifetime','protected SQL admission']}))
