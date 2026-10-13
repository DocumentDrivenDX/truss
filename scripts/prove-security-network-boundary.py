"""Conditional network membership model, not Docker/kernel refinement proof."""
import json
from z3 import Bool,And,Or,Not,Solver,sat,unsat,get_version_string
peer_front,peer_back,service_front,service_back,db_front,db_back,credential,forwarder=[Bool(n) for n in ('peer_front','peer_back','service_front','service_back','db_front','db_back','credential','arbitrary_private_fact_forwarder')]
base=[peer_front,Not(peer_back),service_front,service_back,Not(db_front),db_back]
direct=Or(And(peer_front,db_front),And(peer_back,db_back))
service_to_db=Or(And(service_front,db_front),And(service_back,db_back))
peer_to_service=Or(And(peer_front,service_front),And(peer_back,service_back))
relay=And(peer_to_service,service_to_db,forwarder)
cases=[('direct_private_sql_unreachable_even_with_credential',base+[credential,direct],unsat),('trusted_service_private_sql_reachable',base+[service_to_db],sat),('excluded_admin_membership_change_allows_direct_sql',[peer_front,peer_back,service_front,service_back,Not(db_front),db_back,credential,direct],sat),('unqualified_proxy_can_relay_private_facts_without_peer_sql_credential',base+[Not(credential),forwarder,relay],sat)]
results=[]
for name,assertions,expected in cases:
 s=Solver();s.add(*assertions);answer=s.check()
 if answer!=expected:raise RuntimeError('Original conditional network model result required')
 results.append({'name':name,'result':str(answer),'model':str(s.model()) if answer==sat else None})
print(json.dumps({'solver':get_version_string(),'scope':'Exact abstract network memberships and trusted service capability; native route/firewall/namespace/lifetime/credential/transport assumptions are not proven. Reachable application relay counterexample is abstract, not an observed service escape.','results':results},indent=2))
