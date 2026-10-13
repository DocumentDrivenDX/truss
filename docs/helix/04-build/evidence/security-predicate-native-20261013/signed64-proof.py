"""Conditional decimal lexical bound lemma, not a SQL implementation proof."""
import json
import z3
checks=[]
for bound in ('9223372036854775807','9223372036854775808'):
 d=[z3.Int('d'+str(i)) for i in range(19)]
 domain=[x>=0 for x in d]+[x<=9 for x in d]+[d[0]>0]
 value=sum(x*10**(18-i) for i,x in enumerate(d))
 lexical=z3.Or(*[z3.And(*[d[j]==int(bound[j]) for j in range(i)],d[i]<int(bound[i])) for i in range(19)],z3.And(*[d[i]==int(bound[i]) for i in range(19)]))
 s=z3.Solver();s.set(timeout=10000);s.add(*domain,lexical!=(value<=int(bound)))
 result=str(s.check());checks.append({'bound':bound,'counterexample':result});assert result=='unsat',result
s=z3.Solver();s.add(z3.Int('value')==9223372036854775808,z3.Int('value')>9223372036854775807)
assert s.check()==z3.sat
print(json.dumps({'z3':z3.get_version_string(),'scope':'19 canonical ASCII digits only; original lexical grammar, SQL collation, custody and execution remain separate premises','checks':checks,'positive_overflow_witness':str(s.model())},indent=2))
