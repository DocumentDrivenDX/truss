"""Conditional epoch-state event/order laws, not SQL or driver refinement."""
from pathlib import Path
import hashlib,json,uuid
import z3
root=Path.cwd();folder=root/'docs/helix/04-build/evidence/epoch-state-fence-formal'/str(uuid.uuid4())
folder.mkdir(parents=True)
paths=['scripts/prove-epoch-state-fence.py','packages/postgresql/native/source-epoch-read-fence.sql',
       'packages/postgresql/native/source-epoch-fenced-fresh-lock.sql','packages/postgresql/native/source-epoch-issue.sql',
       'packages/python/tests/test_epoch_state_fence_native.py','scripts/check-python-catalog-report-release-native.py']
pins={}
for name in paths:
    raw=(root/name).read_bytes();pins[name]=hashlib.sha256(raw).hexdigest()
    target=folder/'preimages'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
alive,issuer_guard,table_guard,write,foreign_reader=z3.Bools('alive issuer_guard table_guard write foreign_reader')
state,desired,mid,end=z3.Ints('state desired mid end')
issuer_allowed=z3.Not(z3.Or(z3.And(alive,issuer_guard),foreign_reader))
direct_allowed=z3.Not(z3.Or(z3.And(alive,table_guard),foreign_reader))
issuer_step=mid==z3.If(z3.And(write,issuer_allowed),desired,state)
direct_step=mid==z3.If(z3.And(write,direct_allowed),desired,state)
restore=end==z3.If(z3.And(write,direct_allowed),state,mid)
# Lock-order abstraction: strongest writer table mode is mutually exclusive
# with reader SHARE. Rows-first alone permits the reader's table mode while
# the writer owns its pointer row, creating the circular upgrade wait.
writer_row,reader_table,writer_table,writer_waits,reader_waits=z3.Bools(
    'writer_row reader_table writer_table writer_waits reader_waits')
wait_laws=[writer_waits==z3.And(writer_row,reader_table,z3.Not(writer_table)),
           reader_waits==z3.And(writer_row,reader_table)]
ordered=[z3.Implies(writer_row,writer_table),z3.Not(z3.And(writer_table,reader_table))]
queries=[
 ('issuer_entry_guard_preserves_state','unsat',[alive,issuer_guard,issuer_step,mid!=state]),
 ('reverse_overlap_effect_guard_preserves_state','unsat',[alive,table_guard,direct_step,mid!=state]),
 ('foreign_reader_excludes_participating_issuer','unsat',[foreign_reader,issuer_step,mid!=state]),
 ('complete_fence_excludes_two_step_aba','unsat',[alive,table_guard,write,direct_step,restore,mid!=state,end==state]),
 ('ordered_modes_exclude_row_upgrade_cycle','unsat',wait_laws+ordered+[writer_waits,reader_waits]),
 ('old_row_only_reader_allows_same_writer_change','sat',[alive,z3.Not(issuer_guard),z3.Not(foreign_reader),write,issuer_step,mid!=state]),
 ('omitted_effect_guard_allows_aba','sat',[alive,z3.Not(table_guard),z3.Not(foreign_reader),write,direct_step,restore,mid!=state,end==state]),
 ('released_cut_allows_issuance','sat',[z3.Not(alive),issuer_guard,z3.Not(foreign_reader),write,issuer_step,mid!=state]),
 ('rows_first_allows_upgrade_cycle','sat',wait_laws+[writer_row,reader_table,z3.Not(writer_table),writer_waits,reader_waits]),
 ('omitted_entry_guard_permits_later_issuer_phase','sat',[alive,z3.Not(issuer_guard),z3.Not(foreign_reader),issuer_allowed])]
results=[]
for name,expected,clauses in queries:
    solver=z3.Solver();solver.set(timeout=10000);solver.add(*clauses)
    original=solver.to_smt2();(folder/(name+'.smt2')).write_text(original)
    actual=str(solver.check())
    context=z3.Context();replay=z3.Solver(ctx=context);replay.set(timeout=10000)
    replay.add(z3.parse_smt2_string(original,ctx=context));replayed=str(replay.check())
    if actual!=expected or replayed!=expected:raise RuntimeError('Exact solver and fresh-context replay required')
    results.append({'id':name,'expected':expected,'observed':actual,'freshContextReplay':replayed,
                    'counterexample':str(solver.model()) if actual=='sat' else None,
                    'smt2Sha256':hashlib.sha256(original.encode()).hexdigest()})
if any(hashlib.sha256((root/p).read_bytes()).hexdigest()!=h for p,h in pins.items()):raise RuntimeError('Original source drift')
receipt={'status':'conditional-model-passed','solver':z3.get_version_string(),'sourceDigests':pins,'queries':results,
 'scope':'Opaque epoch-state conditional event preservation and stated finite-history induction while actual cut and complete installed effect-fence participation hold at every step. Native table-mode compatibility and strongest-mode-before-row ordering are premises of the cycle model. The later-issuer-phase witness models permission, not marker waiting, native timing or privileges. No SQL/trigger/pg_locks/native-lock/savepoint/host refinement, authenticated issuer, full routine/shared-role/configuration/authorization-data writer closure or final disclosure proof. Separate native tests and omissions qualify only the selected PostgreSQL16.15 component.'}
(folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'status':receipt['status'],'evidence':str(folder),'queries':len(results)}))
