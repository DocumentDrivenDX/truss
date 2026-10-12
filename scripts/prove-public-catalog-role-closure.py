"""Finite membership-closure laws, not PostgreSQL protocol refinement."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/public-catalog-role-closure-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-public-catalog-role-closure.py','packages/python/src/truss/_catalog_runtime/runtime.sql','packages/python/src/truss/_catalog_runtime/manifest.json','packages/python/tests/test_catalog_runtime_native.py']
pins={}
for name in paths:
    raw=(root/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
# Actor0, registrar1, private owner2, bridge3, three server capabilities4..6.
count=7;edges=[[z3.Bool(f'member_{i}_of_{j}') for j in range(count)] for i in range(count)]
reach=[[z3.Or(i==j,edges[i][j]) for j in range(count)] for i in range(count)]
for k in range(count):
    reach=[[z3.Or(reach[i][j],z3.And(reach[i][k],reach[k][j])) for j in range(count)] for i in range(count)]
allowed=z3.And(reach[0][1],z3.Not(reach[0][2]),*[z3.Not(reach[0][j]) for j in (4,5,6)])
unknown_danger=z3.Bool('unmodeled_capability')
queries=[
 ('direct_server_capability_excludes_admission','unsat',[edges[0][4],allowed]),
 ('indirect_server_capability_excludes_admission','unsat',[edges[0][3],edges[3][6],allowed]),
 ('unrelated_membership_can_remain_admitted','sat',[edges[0][1],edges[0][3],allowed]),
 ('known_role_exclusion_does_not_close_all_capabilities','sat',[allowed,unknown_danger]),
]
results=[]
for name,expected,clauses in queries:
    s=z3.Solver();s.set(timeout=10000);s.add(*clauses);smt=s.to_smt2();(out/(name+'.smt2')).write_text(smt);observed=str(s.check())
    ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(smt,ctx=ctx));again=str(replay.check())
    assert observed==expected and again==expected,name
    results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(smt.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest for name,digest in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Seven-role conservative any-membership closure matching selected public actor owner/server-capability exclusion.','limitations':['Membership/current-snapshot/correspondence and complete relevant-role inventory are premises','Inheritance/SET/ADMIN flags are deliberately not used; dormant paths are conservatively excluded too','No PostgreSQL/Psycopg/SQL refinement, complete capability/diagnostic/writer closure or advanced backend admission'],'acceptancePrerequisites':['CONTRACT-005','STP-056 B05/B11/B12']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
