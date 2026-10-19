# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional closed receiver dispatch; authentication and channel closure remain independent."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-owned-receiver-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-owned-receiver.py','scripts/security_owned_receiver.py','scripts/security_owned_read.py','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
version,operation=z3.Strings('wire_version wire_operation')
exact_keys,duplicates,valid_utf8,bounded,dispatch,authenticated,channels_closed=z3.Bools('exact_keys duplicate_members valid_utf8 bounded_bytes dispatch authenticated_subject channels_closed')
closed=z3.And(version=='truss-owned-decision-request/0.1',operation=='read',exact_keys,z3.Not(duplicates),valid_utf8,bounded)
captured_valid,delegated,constructed=z3.Bools('captured_valid delegated_profile receiver_constructed')
construction=constructed==z3.And(captured_valid,delegated)
protocol=z3.And(construction,dispatch==z3.And(closed,constructed))
before,after,captured,selected=z3.Strings('original_source_before original_source_after captured_source selected_source')
snapshot=z3.And(captured==before,selected==captured)
queries=[
 ('invalid_server_source_prevents_dispatch','unsat',[protocol,z3.Not(captured_valid),dispatch]),
 ('carrier_mutation_cannot_change_captured_selection','unsat',[snapshot,before!=after,selected==after]),
 ('alias_selection_without_snapshot_follows_mutation','sat',[captured==before,selected==after,before!=after,selected!=captured]),
 ('extra_wire_fields_prevent_dispatch','unsat',[protocol,z3.Not(exact_keys),dispatch]),
 ('duplicate_members_prevent_dispatch','unsat',[protocol,duplicates,dispatch]),
 ('explain_operation_prevents_dispatch','unsat',[protocol,operation=='explain',dispatch]),
 ('unbounded_carrier_prevents_dispatch','unsat',[protocol,z3.Not(bounded),dispatch]),
 ('closed_grammar_does_not_authenticate_subject','sat',[protocol,dispatch,z3.Not(authenticated)]),
 ('closed_grammar_does_not_prove_other_channels_closed','sat',[protocol,dispatch,z3.Not(channels_closed)])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Abstract exact wire grammar to fixed read dispatch. Extra/duplicate members, wrong operation and oversize prevent dispatch. Matching grammar does not authenticate the subject or close other channels.','limitations':['Faithful JSON/UTF-8 parsing and exact dispatch mapping are premises; no Python/native driver refinement proof','Private server context is a trusted application premise, not an authenticated principal or capability','No credential/routing/native source/lifetime/diagnostic closure or admitted protected backend']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
