"""Synthetic PG17 static role graph experiment; not native authorization."""
from pathlib import Path
import hashlib,json
path=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/observer-role-reachability-pg17-v0.1.vectors.json'
raw=path.read_bytes()
if len(raw)>16384:raise ValueError('experiment fixture bound')
f=json.loads(raw)
def observe(edges):
 roles=set(f['roles']);adj={r:[] for r in roles}
 if len(roles)>64 or len(edges)>128:raise ValueError('experiment bound')
 seen=set()
 for e in edges:
  if e['member'] not in roles or e['role'] not in roles or any(type(e[x]) is not bool for x in ['inherit','set','admin']):raise ValueError('original endpoint/options')
  key=(e['member'],e['role'])
  if key in seen:raise ValueError('experiment duplicate edge')
  seen.add(key);adj[e['member']].append(e)
 # Reject any membership cycle independent of options via finite topological elimination.
 degree={r:0 for r in roles}
 for e in edges:degree[e['role']]+=1
 ready=[r for r in roles if degree[r]==0];count=0
 while ready:
  r=ready.pop();count+=1
  for e in adj[r]:
   degree[e['role']]-=1
   if degree[e['role']]==0:ready.append(e['role'])
 if count!=len(roles):raise ValueError('PG17 cycle')
 def closure(initial,option):
  found=set(initial);pending=list(initial)
  while pending:
   r=pending.pop()
   for e in adj[r]:
    if e[option] and e['role'] not in found:found.add(e['role']);pending.append(e['role'])
  return found
 switchable=closure([f['sessionRole']],'set')
 if f['activeRole'] not in switchable:raise ValueError('active role correspondence not admitted')
 effective=closure(switchable,'inherit')
 return {'outcome':'exposed' if f['observerRole'] in effective else 'not_exposed','switchable':sorted(switchable),'effectivePrivilegeRoles':sorted(effective)}
ids=set()
for c in f['cases']:
 if c['id'] in ids:raise ValueError('duplicate fixture identity')
 ids.add(c['id'])
 try:outcome=observe(c['edges'])
 except ValueError:outcome={'outcome':'refused','switchable':None,'effectivePrivilegeRoles':None}
 if outcome!=c['expected']:raise ValueError(c['id'])
if path.read_bytes()!=raw:raise ValueError('fixture changed')
result={'status':'pass','cases':len(ids),'fixtureSha256':hashlib.sha256(raw).hexdigest(),'scope':f['scope'],'nativeExecuted':False,'profileAdopted':False}
Path(__file__).with_name('observer-role-reachability-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'pass','cases':len(ids)}))
