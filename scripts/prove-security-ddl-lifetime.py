# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional source-byte lifetime model; no source/native refinement theorem."""
import hashlib,json,sys
from pathlib import Path
import z3
active,source,pinned,next_active,next_source,next_pinned=z3.Bools('active source_changed pinned_changed next_active next_source_changed next_pinned_changed')
restored=z3.Bool('restored_source_changed')
invariant=z3.Implies(active,source==pinned);after=z3.Implies(next_active,next_source==next_pinned)
begin=z3.And(z3.Not(active),next_active,next_source==source,next_pinned==source)
end=z3.And(active,z3.Not(next_active),next_source==source,next_pinned==pinned)
coordinated_ddl=z3.And(z3.Not(active),z3.Not(next_active),next_source==z3.Not(source),next_pinned==pinned)
bypass=z3.And(active,next_active,next_source==z3.Not(source),next_pinned==pinned)
checks=[('empty-initial-state-consistent',z3.And(z3.Not(active),z3.Not(invariant)),z3.unsat),('coordinated-transitions-preserve-pinned-source',z3.And(invariant,z3.Or(begin,end,coordinated_ddl),z3.Not(after)),z3.unsat),('uncoordinated-ddl-can-break-lifetime',z3.And(invariant,bypass,z3.Not(after)),z3.sat),('restored-endpoints-cannot-exclude-intermediate-change',z3.And(active,z3.Not(pinned),z3.Not(source),next_source,source==pinned,restored==pinned,next_source!=pinned),z3.sat),('same-owner-reentrant-ddl-breaks-lifetime',z3.And(invariant,active,next_active,next_source==z3.Not(source),next_pinned==pinned,z3.Not(after)),z3.sat),('nonempty-admitted-reader-is-consistent',z3.And(active,source==pinned,invariant),z3.sat)]
cases=[]
for name,formula,expected in checks:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(formula);smt=solver.sexpr();result=solver.check()
 if result!=expected:raise RuntimeError(name+': '+str(result))
 replay=z3.Solver();replay.from_string(smt)
 if replay.check()!=expected:raise RuntimeError('Retained formula replay failed')
 cases.append({'id':name,'result':str(result),'smt':smt,'witness':str(solver.model()) if result==z3.sat else None})
paths=[Path(__file__),Path('packages/python/tests/test_security_public_ontology_native.py'),Path('packages/python/src/truss/_security_data_writer.py'),Path('packages/python/src/truss/_security_authority_change.py')]
receipt={'status':'conditional-inductive-proof','solverVersion':z3.get_version_string(),'sourceDigests':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'cases':cases,'scope':'Abstract two-source-state exclusive guard model. Empty state and modeled coordinated transitions preserve active reader source equality to its pin. Premises: every source change occurs only while no protected operation is active; all source mutators acquire the same exclusive guard before effects, pinning occurs under that guard and it stays held through every protected use. Acquiring a native reentrant lock alone does not establish the inactive-only mutation premise. SAT bypass/endpoint controls show why complete mutator participation is required. Native paired test demonstrates source-byte ABA with a harmless comment, not changed authorization semantics. Does not prove Python/SQL refinement, native object locking, DDL/event coverage, handler/library closure, roles, crashes, liveness or backend admission.'}
Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'unsat':2,'sat':4}))
