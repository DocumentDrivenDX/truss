"""Conditional caller-login gates, not native/semantic/issuer refinement."""
from pathlib import Path
import hashlib,json,sys,uuid,z3
root=Path.cwd();native=Path(sys.argv[1])
assert native.is_relative_to(Path('docs/helix/04-build/evidence/python-psycopg-epoch-cut'))
assert json.loads(native.read_text())['status']=='component-passed'
out=root/'docs/helix/04-build/evidence/security-authenticated-publication-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=[Path(__file__).relative_to(root),Path('packages/python/src/truss/_psycopg_dependency_fact_cut.py'),Path('scripts/security_owned_read.py'),Path('scripts/security_owned_receiver.py'),Path('packages/python/tests/test_psycopg_fact_cut_native.py'),native]
pins={}
for path in paths:
    raw=path.read_bytes();pins[str(path)]=hashlib.sha256(raw).hexdigest();target=out/'preimages'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
auth,before,after=z3.Strings('original_native_authentication login_name_at_admission login_name_at_publication')
present,entry_role,final_role,source_cut,semantic_permit,retained,execute,publish,other_routes,subject_bound=z3.Bools('native_authentication_present entry_role_oid_matches final_role_oid_matches original_source_cut original_semantic_permit original_guards_retained executor_invoked decision_published other_routes_authenticated ontology_subject_binding')
entry=z3.And(present,entry_role,auth==z3.Concat(z3.StringVal('scram-sha-256:'),before))
final=z3.And(present,final_role,auth==z3.Concat(z3.StringVal('scram-sha-256:'),after))
protocol=z3.And(execute==z3.And(source_cut,entry),publish==z3.And(execute,semantic_permit,retained,final))
queries=[
    ('trust_null_excludes_executor_and_publication','unsat',[protocol,z3.Not(present),z3.Or(execute,publish)]),
    ('unchanged_role_oid_does_not_bypass_changed_login_name','unsat',[protocol,entry_role,final_role,auth==z3.Concat(z3.StringVal('scram-sha-256:'),before),before!=after,publish]),
    ('caller_login_does_not_pin_other_routes','sat',[protocol,publish,z3.Not(other_routes)]),
    ('caller_login_does_not_authenticate_subject_mapping','sat',[protocol,publish,z3.Not(subject_bound)]),
]
results=[]
for name,expected,clauses in queries:
    solver=z3.Solver();solver.set(timeout=10000);solver.add(*clauses);smt=solver.to_smt2();(out/(name+'.smt2')).write_text(smt);observed=str(solver.check())
    ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(smt,ctx=ctx));again=str(replay.check())
    assert observed==expected and again==expected,name
    results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(smt.encode()).hexdigest(),'model':str(solver.model()) if observed=='sat' else None})
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest for path,digest in pins.items())
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'nativePacket':str(native),'scope':'Selected owned0.5 caller requires original native SCRAM/role correspondence before executor and before publication.','limitations':['Source cut, native role/OID observations, immutable original authentication and original guard custody are premises','No Python/SQL/driver parsing or native/semantic refinement proof','No production subject/target/executor/issuer/credential/routing/public-catalog admission'],'acceptancePrerequisites':['TD-056 C02/C04/C05','STP-056 B05/B11/B12','US-056 AC5/AC9/AC10']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'queries':len(results),'evidence':str(out)}))
