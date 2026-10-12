"""Conditional original host/handle identity; authentication and native lease refinement remain independent."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-host-attachment-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-host-attachment.py','packages/python/src/truss/psycopg_host.py','scripts/security_owned_receiver.py','packages/python/src/truss/execution.py','packages/python/tests/test_psycopg_host_native.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
claimed_host,registered_host,claimed_handle,registered_handle=z3.Ints('claimed_host registered_host claimed_handle registered_handle')
metadata,allowed,before_usable,after_usable,authenticated=z3.Bools('metadata_matches allowed before_usable after_usable authenticated')
strong=allowed==z3.And(metadata,claimed_host==registered_host,claimed_handle==registered_handle)
weak=allowed==metadata
detach=after_usable==z3.If(claimed_host==registered_host,z3.BoolVal(False),before_usable)
queries=[
 ('copied_host_cannot_borrow_original_attachment','unsat',[strong,claimed_host!=registered_host,allowed]),
 ('copied_handle_cannot_borrow_original_registration','unsat',[strong,claimed_handle!=registered_handle,allowed]),
 ('copied_host_detach_preserves_original_handle','unsat',[detach,claimed_host!=registered_host,before_usable,z3.Not(after_usable)]),
 ('metadata_only_host_check_admits_copy','sat',[weak,metadata,claimed_host!=registered_host,allowed]),
 ('metadata_only_handle_check_admits_copy','sat',[weak,metadata,claimed_handle!=registered_handle,allowed]),
 ('original_object_identity_does_not_authenticate_subject','sat',[strong,allowed,z3.Not(authenticated)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract registered host/handle identity and detach guard. Metadata equality cannot replace original object registration. An unrelated detach preserves original usability. Original identity does not establish authenticated subject authority.','limitations':['Faithful registry/object identity and lease exclusion are premises; no Python weak-reference/native driver/thread refinement proof','Trusted host process and private registry are assumptions, not protection against arbitrary same-process mutation','No caller/issuer authentication, credential/channel/source/lifetime closure or admitted protected backend']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
