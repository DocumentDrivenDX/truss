# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional original-request identity and closed-family laws; no Python refinement."""
from pathlib import Path
import hashlib,json,uuid
import z3
repo=Path.cwd();folder=repo/'docs/helix/04-build/evidence/epoch-request-custody-formal'/str(uuid.uuid4());folder.mkdir(parents=True)
paths=['scripts/prove-epoch-request-custody.py','packages/python/src/truss/_native_fresh_epoch_capture.py','packages/python/src/truss/_native_epoch_acquisitions.py','packages/python/src/truss/_native_arbitration.py','packages/python/tests/test_native_fresh_epoch_capture.py','scripts/python-fresh-epoch-worker.py']
pins={}
for name in paths:
 raw=(repo/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest();p=folder/'preimages'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
gate,owner,session,request_session,root,request,sql,original_sql,comparison,original_comparison,family,response,lifecycle=z3.Ints('gate owner session request_session root request sql original_sql comparison original_comparison family response lifecycle')
exact=z3.Bool('exact_primitive_types')
identity=[gate==owner,session==request_session,root==request]
recipe=[exact,sql==original_sql,comparison==original_comparison]
closed=[z3.Or(family==0,family==1),response==family,lifecycle==family]
valid=z3.And(*(identity+recipe+closed))
queries=[('accepted_request_excludes_owner_session_root_substitution','unsat',[valid,z3.Or(gate!=owner,session!=request_session,root!=request)]),('accepted_request_excludes_recipe_substitution','unsat',[valid,z3.Or(sql!=original_sql,comparison!=original_comparison,z3.Not(exact))]),('accepted_closed_family_excludes_scope_crossover','unsat',[valid,response!=lifecycle]),('omitted_owner_check_allows_copied_gate','sat',[*identity[1:],*recipe,*closed,gate!=owner]),('omitted_root_check_allows_copied_request','sat',[*identity[:2],*recipe,*closed,root!=request]),('omitted_recipe_check_allows_substitution','sat',[*identity,*closed,sql!=original_sql]),('omitted_scope_correspondence_allows_crossover','sat',[*identity,*recipe,family==1,response==0,lifecycle==1])]
results=[]
for name,expected,clauses in queries:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(*clauses);raw=solver.to_smt2();(folder/(name+'.smt2')).write_text(raw);observed=str(solver.check())
 ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.add(z3.parse_smt2_string(raw,ctx=ctx));replayed=str(replay.check())
 if observed!=expected or replayed!=expected:raise RuntimeError(name)
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':replayed,'counterexample':str(solver.model()) if observed=='sat' else None,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest()})
if any(hashlib.sha256((repo/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise RuntimeError('Source drift')
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Identity-sensitive fixed-request and closed-family constraints under trusted original implementation/module/session custody and immutable request premises. Integers model distinct original identities and opaque recipe values. This proves constraint consistency and detects omitted premises; it is not a Python runtime refinement, arbitrary monkeypatch resistance, native SQL/trigger proof, continuous held protected-use capability, authenticated source/issuer, full source/authority/data cut or final-disclosure proof. Separate native captures and pre-SQL controls qualify the selected administrative component.'}
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'evidence':str(folder),'queries':len(results)}))
