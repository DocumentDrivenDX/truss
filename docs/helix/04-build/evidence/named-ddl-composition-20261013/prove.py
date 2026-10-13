"""Conditional selected-tag mutex model; not SQL/Python refinement."""
from pathlib import Path
import json,hashlib,z3
root=Path(__file__).resolve().parents[5]
share,cooperates,hook_now,writer_lock,mutates=z3.Bools('share_held writer_cooperates hook_now writer_lock mutation')
# Participating selected DDL must acquire conflicting writer modes before effect.
laws=[z3.Implies(z3.And(cooperates,hook_now,mutates),writer_lock),z3.Not(z3.And(share,writer_lock))]
checks=[]
for name,extra,expected in [
 ('held_cut_excludes_participating_selected_ddl',[share,cooperates,hook_now,mutates],'unsat'),
 ('writer_can_mutate_after_cut_ends',[z3.Not(share),cooperates,hook_now,mutates],'sat'),
 ('disabling_hook_after_snapshot_allows_mutation',[share,cooperates,z3.Not(hook_now),mutates],'sat'),
 ('uncovered_writer_can_mutate_without_participation',[share,z3.Not(cooperates),hook_now,mutates],'sat')]:
 solver=z3.Solver();solver.add(*(laws+extra));observed=str(solver.check());assert observed==expected
 checks.append({'name':name,'expected':expected,'observed':observed,'smt2':solver.to_smt2(),'model':str(solver.model()) if observed=='sat' else None})
paths=['packages/postgresql/native/source-epoch-routine-ddl-barrier.sql','packages/postgresql/native/source-epoch-table-ddl-barrier.sql','packages/python/src/truss/_psycopg_epoch_cut.py','packages/python/src/truss/_psycopg_dependency_fact_cut.py','scripts/security_owned_read.py']
receipt={'solver':z3.get_version_string(),'scope':'Boolean transcription of participating selected-tag writer-before-effect and conflicting table modes. Current hook/participation and mutex correspondence are explicit premises; not source/native refinement, complete closure or liveness.','sourcePins':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths},'checks':checks}
Path(__file__).with_name('proof.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('1 UNSAT; 3 SAT; conditional selected-tag model only')
