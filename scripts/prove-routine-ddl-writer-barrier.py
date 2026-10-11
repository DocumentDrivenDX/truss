"""Conditional selected routine-DDL writer barrier, not native/SQL refinement."""
from pathlib import Path
import hashlib,json,uuid,z3
repo=Path.cwd();folder=repo/'docs/helix/04-build/evidence/routine-ddl-writer-barrier-formal'/str(uuid.uuid4());folder.mkdir(parents=True)
paths=['scripts/prove-routine-ddl-writer-barrier.py','packages/postgresql/native/source-epoch-routine-ddl-barrier.sql','packages/postgresql/native/source-epoch-fenced-fresh-lock.sql','packages/postgresql/native/source-epoch-read-fence.sql','packages/python/tests/test_routine_ddl_barrier_native.py','scripts/check-python-catalog-report-release-native.py']
pins={}
for name in paths:
 raw=(repo/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest();p=folder/'preimages'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
reader,tagged,own,own_guard,writer_modes,write=z3.Bools('reader tagged own own_guard writer_modes write')
retained_operation,operation_guard=z3.Bools('retained_operation operation_guard')
state,desired,successor,epoch_before,epoch_after=z3.Ints('state desired successor epoch_before epoch_after')
allowed=z3.And(z3.Not(z3.And(reader,tagged,z3.If(own,own_guard,writer_modes))),z3.Not(z3.And(tagged,own,retained_operation,operation_guard)))
step=successor==z3.If(z3.And(write,allowed),desired,state)
epoch=epoch_after==epoch_before
started,ended,writer_held,accepted=z3.Bools('started ended writer_held accepted')
lifetime=writer_held==z3.And(started,tagged,writer_modes,z3.Not(ended))
compatibility=z3.Not(z3.And(writer_held,accepted))
marker1,marker2,effect1,effect2=z3.Bools('marker1 marker2 effect1 effect2')
serial=[z3.Implies(effect1,marker1),z3.Implies(effect2,marker2),z3.Not(z3.And(marker1,marker2))]
queries=[
 ('selected_foreign_writer_cannot_change_held_source','unsat',[reader,tagged,z3.Not(own),writer_modes,step,successor!=state]),
 ('selected_own_writer_refuses_before_effect','unsat',[reader,tagged,own,own_guard,step,successor!=state]),
 ('pending_selected_writer_excludes_new_reader','unsat',[started,tagged,writer_modes,z3.Not(ended),lifetime,compatibility,accepted]),
 ('marker_serializes_participating_effects','unsat',[*serial,effect1,effect2]),
 ('complete_selected_barrier_preserves_one_step_source','unsat',[reader,tagged,own_guard,writer_modes,step,successor!=state]),
 ('omitted_own_guard_permits_same_backend_change','sat',[reader,tagged,own,z3.Not(own_guard),write,step,successor!=state,epoch]),
 ('omitted_writer_modes_permit_pending_writer_and_reader','sat',[started,tagged,z3.Not(writer_modes),z3.Not(ended),lifetime,compatibility,accepted]),
 ('uncovered_or_disabled_hook_allows_change','sat',[reader,z3.Not(tagged),write,step,successor!=state,epoch]),
 ('selected_committed_ddl_changes_source_without_epoch_issuance','sat',[z3.Not(reader),tagged,own_guard,writer_modes,write,step,successor!=state,epoch]),
 ('completed_writer_allows_new_reader','sat',[started,tagged,writer_modes,ended,lifetime,compatibility,accepted]),
 ('original_operation_excludes_selected_own_ddl_without_reader','unsat',[z3.Not(reader),tagged,own,retained_operation,operation_guard,step,successor!=state]),
 ('omitted_operation_guard_allows_source_change_behind_admission','sat',[z3.Not(reader),tagged,own,retained_operation,z3.Not(operation_guard),write,step,successor!=state,epoch])]
results=[]
for name,expected,clauses in queries:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(*clauses);raw=solver.to_smt2();(folder/(name+'.smt2')).write_text(raw);observed=str(solver.check())
 ctx=z3.Context();replay=z3.Solver(ctx=ctx);replay.add(z3.parse_smt2_string(raw,ctx=ctx));replayed=str(replay.check())
 if observed!=expected or replayed!=expected:raise RuntimeError(name)
 results.append({'id':name,'expected':expected,'observed':observed,'freshContextReplay':replayed,'counterexample':str(solver.model()) if observed=='sat' else None,'smt2Sha256':hashlib.sha256(raw.encode()).hexdigest()})
if any(hashlib.sha256((repo/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise RuntimeError('Source drift')
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,'scope':'Conditional arbitrary one-step source preservation for continuously held reader and complete selected-tag participation, own-backend entry guard and native mode compatibility. Finite-history induction assumes these laws at every step. Writer lifetime/marker exclusion are explicit abstract premises, not derived PostgreSQL lock/transaction/savepoint/SQL refinement. The completed-writer witness models reader permission after end, not a native timing trace. No snapshot freshness, whole-source/role/grant/cascade/authorization-data coverage, authenticated issuer, automatic source-epoch advancement, ordinary executor or final-disclosure qualification.'}
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'evidence':str(folder),'queries':len(results)}))
