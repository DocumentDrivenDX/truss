"""Conditional semantic dependency/provider cut model; no native refinement."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-field-cuts-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-field-cuts.py','packages/python/src/truss/_security_fact_coverage.py','packages/python/src/truss/_psycopg_fact_cut.py','docs/helix/04-build/evidence/security-fact-requirements/requirements.json','docs/helix/04-build/evidence/security-fact-requirements/policy.json','docs/helix/04-build/evidence/security-fact-requirements/resolution.json']
pins={}
for name in paths:
 raw=(root/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
artifact=json.loads((root/paths[3]).read_bytes())
for key,path in [('policySha256',paths[4]),('resolutionSha256',paths[5])]:assert artifact[key]==pins[path]
refs=[(kind,tuple(r[k] for k in ('documentId','moduleId','elementId'))) for category,kind in [('fields','field'),('associations','association')] for r in artifact['dependencies'][category]]
assert len(refs)==10 and refs[0]==('field',('domain','m','active'))
I=z3.IntSort();R=z3.Array('required',I,z3.BoolSort());M=z3.Array('declared_members',I,z3.BoolSort());C=z3.Array('held_provider_cuts',I,z3.BoolSort())
actual=z3.Array('actual_provider',I,I);declared=z3.Array('declared_provider',I,I)
A=z3.Array('before_provider_state',I,I);B=z3.Array('after_provider_state',I,I)
decode=z3.Function('original_decoder',I,I,I);later=z3.Function('later_decoder',I,I,I)
f,p,w=z3.Ints('fact provider witness')
coverage=z3.ForAll([f],z3.Implies(z3.Select(R,f),z3.Select(M,f)))
correspondence=z3.ForAll([f],z3.Implies(z3.Select(R,f),z3.Select(actual,f)==z3.Select(declared,f)))
cut_coverage=z3.ForAll([f],z3.Implies(z3.And(z3.Select(R,f),z3.Select(M,f)),z3.Select(C,z3.Select(declared,f))))
preservation=z3.ForAll([p],z3.Implies(z3.Select(C,p),z3.Select(A,p)==z3.Select(B,p)))
stable=z3.ForAll([f,p],later(f,p)==decode(f,p))
value=lambda decoder,state:decoder(w,z3.Select(state,z3.Select(actual,w)))
changed=z3.And(z3.Select(R,w),value(later,B)!=value(decode,A))
full=[coverage,correspondence,cut_coverage,preservation,stable]
fixture=[R==z3.Lambda(f,z3.And(f>=0,f<len(refs))),w==0]
queries=[
 ('complete_corresponding_stable_cuts_preserve_facts','unsat',full+[changed]),
 ('fixture_complete_cuts_preserve_active','unsat',full+fixture+[changed]),
 ('missing_active_dependency_changes_fact','sat',[correspondence,cut_coverage,preservation,stable,*fixture,z3.Not(z3.Select(M,0)),changed]),
 ('wrong_provider_mapping_changes_fact','sat',[coverage,cut_coverage,preservation,stable,*fixture,z3.Select(actual,0)!=z3.Select(declared,0),changed]),
 ('missing_provider_cut_changes_fact','sat',[coverage,correspondence,preservation,stable,*fixture,z3.Not(z3.Select(C,z3.Select(actual,0))),changed]),
 ('released_or_bypassed_cut_changes_fact','sat',[coverage,correspondence,cut_coverage,stable,*fixture,changed]),
 ('changed_decoder_changes_fact_under_all_data_cuts','sat',[coverage,correspondence,cut_coverage,preservation,*fixture,changed]),
 ('unrelated_uncut_provider_can_change','sat',full+[z3.Not(z3.Select(C,999)),z3.Select(A,999)!=z3.Select(B,999)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check())
 ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'fixtureReferences':refs,'queries':results,'scope':'Unbounded symbolic facts/providers and opaque provider states. Complete original dependency membership, corresponding actual/declared providers, continuously effective provider cuts and stable deterministic decoding imply one-step fact preservation. Fixture instantiation uses the ten original UMF dependency identities, not inferred physical bindings. Finite-history induction requires premises at every step.','limitations':['Opaque state equality abstracts all rows, presence, nulls and column values; no PostgreSQL SQL, trigger, driver or semantic decoder refinement','Source/role/config cuts, authenticated issuer and actual mapping provenance are premises, not established by hashes','No authorization, mutation atomicity, disclosure, browser/package qualification or backend acceptance promotion']}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'queries':len(results),'evidence':str(out)}))
