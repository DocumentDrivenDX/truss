"""Conditional direct ACL equality proof, not PostgreSQL/effective-role refinement."""
import json
import z3

def prove():
 owner,caller=z3.Ints('owner caller');g,r,p=z3.Ints('grantee grantor privilege');d=z3.Bool('delegable')
 acl=z3.Function('acl',z3.IntSort(),z3.IntSort(),z3.IntSort(),z3.BoolSort(),z3.BoolSort())
 shape=z3.And(z3.Or(g==owner,g==caller),r==owner,p==0,z3.Not(d))
 exact=z3.ForAll([g,r,p,d],acl(g,r,p,d)==shape)
 premises=[owner>0,caller>0,owner!=caller,exact]
 cases={
  'unexpected_direct_acl_row':(premises+[z3.Exists([g,r,p,d],z3.And(acl(g,r,p,d),z3.Not(shape)))],'unsat'),
  'missing_caller_execute':(premises+[z3.Not(acl(caller,owner,0,False))],'unsat'),
  'public_execute':(premises+[z3.Exists([r,d],acl(0,r,0,d))],'unsat'),
  'positive_exact_two_direct_grants':(premises,'sat'),
  'uncompared_public_grant_counterexample':([owner>0,caller>0,owner!=caller,acl(owner,owner,0,False),acl(caller,owner,0,False),acl(0,owner,0,False)],'sat'),
 }
 results={}
 for name,(constraints,expected) in cases.items():
  solver=z3.Solver();solver.set(timeout=5000);solver.add(*constraints);actual=str(solver.check())
  if actual!=expected:raise RuntimeError('Original direct ACL proof result refused')
  results[name]={'expected':expected,'actual':actual}
 return {'scope':'Conditional exact direct ACL set equality only; no SQL/catalog/role-membership/continuous-lifetime/native refinement proof','z3Version':z3.get_version_string(),'cases':results}

if __name__=='__main__':print(json.dumps(prove(),indent=2))
