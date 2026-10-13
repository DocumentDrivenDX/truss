"""Conditional endpoint/source correspondence; deliberately excludes ABA."""
import json
from z3 import Bool,And,Not,Solver,unsat,sat
release,receipt,source,inventory,endpoints=[Bool(k) for k in ('release','receipt','source','inventory','endpoints')]
admit=And(release,receipt,source,inventory,endpoints)
s=Solver();s.add(admit,Not(source));assert s.check()==unsat
s=Solver();s.add(admit,Not(inventory));assert s.check()==unsat
changed_between=Bool('changed_between');s=Solver();s.add(admit,changed_between);assert s.check()==sat
print(json.dumps({'scope':'abstract conjunctive gates under truthful native equality checks only','source_substitution':'unsat','definition_substitution':'unsat','endpoint_equal_with_intermediate_change':'sat','unproven':['native gate implementation equivalence','concurrent source/write closure','same-transaction ABA','issuer/caller authentication','physical policy lowering','protected execution']}))
