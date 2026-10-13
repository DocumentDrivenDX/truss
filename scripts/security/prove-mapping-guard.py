"""Conditional source/profile-cell and one participating writer model; not refinement."""
import hashlib,json
from pathlib import Path
from z3 import String,Int,Bool,And,Not,If,Solver,sat,unsat,get_version_string
sources,original=String('supplied_source_signature'),String('original_source_signature')
profile,expected_profile=String('native_profile'),String('original_profile')
epoch,expected_epoch=Int('native_epoch'),Int('expected_epoch')
held,settled=Bool('original_share_held'),Bool('outer_settled')
bounded=And(epoch>=1,epoch<9223372036854775807,expected_epoch>=1,expected_epoch<=9223372036854775807)
compile_admitted=And(sources==original,profile==expected_profile,epoch==expected_epoch,held,Not(settled))
# Model premise: a participating competing writer cannot change this original
# row while SHARE remains held. This models neither own-transaction ABA nor
# other native mutation/source/fact/dependency routes.
next_epoch=If(Not(held),epoch+1,epoch)
queries=[
 ('changed-original-sources-cannot-compile',And(bounded,compile_admitted,sources!=original),unsat),
 ('mismatched-native-profile-cannot-compile',And(bounded,compile_admitted,profile!=expected_profile),unsat),
 ('participating-writer-cannot-advance-while-held',And(bounded,held,next_epoch!=epoch),unsat),
 ('settlement-allows-writer-then-old-epoch-refuses',And(bounded,settled,Not(held),epoch==expected_epoch,next_epoch!=expected_epoch),sat),
 ('source-profile-match-without-authenticity',And(bounded,compile_admitted,Not(Bool('issuer_authenticated'))),sat),
]
results=[]
for name,formula,expected in queries:
 solver=Solver();solver.add(formula);result=solver.check();assert result==expected
 results.append({'id':name,'result':str(result),'model':str(solver.model()) if result==sat else None})
paths=['packages/python/src/truss/_security_mapping.py','packages/python/tests/test_security_mapping_native.py','scripts/security/prove-mapping-guard.py']
print(json.dumps({'solver':get_version_string(),'queries':results,'sourceDigests':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in paths},
 'scope':'Unbounded symbolic exact source signatures/profile strings and bounded positive int8 epochs, under stated row-lock/participating-writer transition premises. No Python signature/SQL/driver/source/native lock refinement, identity/issuer authenticity, effect/role/private-fact permission, complete writer closure, own-transaction ABA, or native release proof.'},indent=2))
