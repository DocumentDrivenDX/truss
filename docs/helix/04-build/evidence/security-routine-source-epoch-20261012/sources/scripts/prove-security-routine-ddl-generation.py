"""Conditional generation arithmetic, not SQL/Python or DDL-route refinement."""
import hashlib,json,sys
from pathlib import Path
import z3
original,data,expected,ddl,next_generation=z3.Ints('original data_events expected_data_events ddl_events next_generation')
source_original,source_next=z3.Ints('source_original source_next')
maximum=9223372036854775807
base=z3.And(original>=1,data>=1,expected>=1,ddl>=0,next_generation==original+data+ddl,next_generation<=maximum)
checks=[('distinct-source-epoch-cannot-hide-ddl-with-any-data-inventory',z3.And(base,source_original>=0,source_next==source_original+ddl,source_next<=maximum,ddl>0,source_next==source_original),z3.unsat),('correct-data-inventory-cannot-hide-any-ddl',z3.And(base,data==expected,ddl>0,next_generation==original+expected),z3.unsat),('bounded-ddl-successor-never-wraps',z3.And(original>=1,original<maximum,next_generation==original+1,next_generation<=original),z3.unsat),('no-ddl-correct-data-inventory-can-pass',z3.And(base,ddl==0,data==expected,next_generation==original+expected),z3.sat),('wrong-data-inventory-can-hide-ddl',z3.And(base,data==1,ddl==1,expected==2,next_generation==original+expected),z3.sat)]
cases=[]
for name,formula,expected_result in checks:
 solver=z3.Solver();solver.set(timeout=10000);solver.add(formula);smt=solver.sexpr();result=solver.check()
 if result!=expected_result:raise RuntimeError(name+': '+str(result))
 replay=z3.Solver();replay.set(timeout=10000);replay.from_string(smt)
 if replay.check()!=expected_result:raise RuntimeError('Retained SMT replay failed')
 cases.append({'id':name,'result':str(result),'smt':smt,'witness':str(solver.model()) if result==z3.sat else None})
paths=[Path(__file__),Path('packages/postgresql/native/security-routine-ddl-guard-pg18.sql'),Path('packages/python/tests/test_security_public_ontology_native.py'),Path('packages/python/src/truss/_security_data_writer.py'),Path('packages/postgresql/native/security-data-writer-guard-pg18.sql')]
receipt={'status':'conditional-generation-proof','solverVersion':z3.get_version_string(),'sourceDigests':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'cases':cases,'scope':'Exact bounded integer model. A distinct monotonic source epoch cannot remain equal after any positive participating DDL count, independently of declared data-event inventory. The separate shared-generation check alone still needs correct independently qualified data-event inventory: under that premise, each selected DDL advances once and no generation decreases/reset/overflow, nonzero DDL cannot pass the original data-only final delta. SAT wrong-inventory control demonstrates this is not proof that each effect participated. Original guard serialization, fresh claim refusal and rollback are native exercising observations, not established by arithmetic. No SQL/Python refinement, complete DDL/role/routine/procedure/extension/source route closure, trusted installer or sink/admission theorem.'}
Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':receipt['status'],'unsat':3,'sat':2}))
