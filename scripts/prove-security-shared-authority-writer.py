"""Conditional participating-writer interval model; no native whole-authority theorem."""
from pathlib import Path
import hashlib,json,uuid,z3
root=Path.cwd();out=root/'docs/helix/04-build/evidence/security-shared-authority-writer-formal'/str(uuid.uuid4());out.mkdir(parents=True)
paths=['scripts/prove-security-shared-authority-writer.py','packages/postgresql/native/source-epoch-shared-authority-writer.sql','packages/python/tests/test_psycopg_fact_cut_native.py']
pins={}
for n in paths:
 raw=(root/n).read_bytes();pins[n]=hashlib.sha256(raw).hexdigest();p=out/'preimages'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
rs,re,ws,we,effect=z3.Reals('reader_start reader_end writer_start writer_end role_effect')
valid=z3.And(rs<re,ws<we)
inside_reader=z3.And(rs<=effect,effect<re)
participates=z3.And(ws<=effect,effect<we)
external_exclusion=z3.Or(re<=ws,we<=rs)
own_reader,writer_admitted=z3.Bools('same_backend_retained_reader writer_admitted')
protocol=writer_admitted==z3.Not(own_reader)
queries=[
 ('participating_external_writer_cannot_change_role_inside_reader','unsat',[valid,participates,external_exclusion,inside_reader]),
 ('uncoordinated_role_effect_can_overlap_retained_reader','sat',[valid,external_exclusion,inside_reader]),
 ('pending_participant_excludes_new_reader','unsat',[valid,external_exclusion,ws<=rs,rs<we]),
 ('same_backend_guard_refuses_writer_upgrade','unsat',[protocol,own_reader,writer_admitted]),
 ('omitted_same_backend_guard_permits_upgrade','sat',[own_reader,writer_admitted])]
results=[]
for name,expected,clauses in queries:
 s=z3.Solver();s.set(timeout=10000);s.add(*clauses);raw=s.to_smt2();(out/(name+'.smt2')).write_text(raw);observed=str(s.check());ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.set(timeout=10000);replay.add(z3.parse_smt2_string(raw,ctx=ctx));again=str(replay.check())
 if observed!=expected or again!=expected:raise RuntimeError((name,observed,again))
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':again,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest(),'model':str(s.model()) if observed=='sat' else None})
assert all(hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in pins.items())
r={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Unbounded real-time half-open reader/writer intervals under faithful external native exclusion and role effects confined to a participating writer interval. Such effects cannot overlap a reader, and pending writers exclude admission. Same-backend participation separately refuses upgrade; omitted participation or upgrade guards have countermodels.','limitations':['No native lock/catalog/SQL or role-change interception refinement proof','Participation is a premise, not proof all administrators comply; no cluster-wide/multi-database coordination or epoch transition','No authenticated caller/issuer, original writer installation/ACL closure, full authority admission or protected final release proof']}
(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'queries':len(results),'evidence':str(out)}))
