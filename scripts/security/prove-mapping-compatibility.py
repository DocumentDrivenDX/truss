# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional producer intersection model, not implementation/native refinement."""
import json
from pathlib import Path
from hashlib import sha256
import z3

def check(name,assumptions,expected):
 solver=z3.Solver();solver.add(*assumptions);result=solver.check()
 if str(result)!=expected:raise AssertionError((name,result))
 return {'name':name,'result':str(result),'smt2':solver.to_smt2(),'model':str(solver.model()) if result==z3.sat else None}
source_version=z3.Int('original_source_version')
native_version=z3.Int('native_version');compiler_version=z3.Int('compiler_version')
superuser,createrole=z3.Bools('original_superuser original_createrole')
original_sha,rewritten_sha=z3.Strings('original_sha rewritten_sha')
results=[
 check('current_original_source_versions_have_no_intersection',[native_version==7,compiler_version==8,source_version==native_version,source_version==compiler_version],'unsat'),
 check('selected_original_actor_gates_have_no_intersection',[z3.Or(superuser,createrole),z3.Not(superuser),z3.Not(createrole)],'unsat'),
 check('dropping_source_correspondence_can_relabel',[source_version==7,compiler_version==8,original_sha!=rewritten_sha],'sat'),
 check('future_common_original08_version_is_logically_feasible',[native_version==8,compiler_version==8,source_version==native_version,source_version==compiler_version],'sat'),
 check('separate_producer_actors_are_logically_feasible',[z3.Or(superuser,createrole),z3.Not(z3.Bool('producer_superuser')),z3.Not(z3.Bool('producer_createrole'))],'sat')]
root=Path(__file__).resolve().parents[2]
print(json.dumps({'solver':z3.get_version_string(),'scope':'Conditional equality/Boolean gate intersection only. Integers7/8 are abstract version tags. Exact native producer version/actor premises come from separately retained source and native controls. No schema, SQL, driver, hash authentication, cross-context issuance, source cut, original0.8 native ingress or protected execution proof. SAT future controls establish logical possibility only.','results':results,'sourceDigests':{str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),root/'packages/python/src/truss/_installation_privileges.py',root/'packages/python/src/truss/_catalog_support.py',root/'packages/python/src/truss/_catalog_runtime/runtime.sql',root/'packages/python/tests/test_security_mapping_compatibility_native.py']}},indent=2))
