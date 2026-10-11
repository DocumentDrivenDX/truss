"""Conditional exact-source comparison model; digests are not authenticated identity."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-source-profile-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-source-profile.py','packages/python/src/truss/_security_fact_coverage.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
original_policy,native_policy,selected_policy,original_resolution,native_resolution,selected_resolution=z3.Strings('original_policy native_policy selected_policy original_resolution native_resolution selected_resolution')
hash=z3.Function('abstract_digest',z3.StringSort(),z3.BitVecSort(256))
manifest=z3.BitVec('selected_manifest_policy_digest',256);weak_admitted=z3.Bool('weak_admitted');weak_rule=weak_admitted==(manifest==hash(selected_policy))
strong=z3.And(selected_policy==original_policy,selected_resolution==original_resolution,native_policy==selected_policy,native_resolution==selected_resolution)
queries=[
 ('digest_equality_alone_does_not_establish_byte_identity','sat',[hash(native_policy)==hash(original_policy),native_policy!=original_policy]),
 ('exact_policy_correspondence_excludes_changed_native_policy','unsat',[strong,native_policy!=original_policy]),
 ('exact_resolution_correspondence_excludes_changed_native_resolution','unsat',[strong,native_resolution!=original_resolution]),
 ('retained_native_source_excludes_replaced_caller_policy','unsat',[native_policy==original_policy,selected_policy!=original_policy,native_policy==selected_policy]),
 ('omitted_retained_native_comparison_accepts_replaced_bundle','sat',[native_policy==original_policy,selected_policy!=original_policy,manifest==hash(selected_policy),weak_rule,weak_admitted])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded source strings and abstract finite-width digests. Exact original/selected/native byte correspondence prevents source substitution. Digest equality alone and omitted retained native comparison have countermodels; no hash injectivity is assumed.','limitations':['No UTF8/JSON/Python/PostgreSQL/epoch-projection refinement or SHA256 implementation proof','Original source selection and faithful retained native comparison are premises, not authenticated issuer or mapping provenance','No authenticated caller/issuer, original writer installation/ACL closure, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
