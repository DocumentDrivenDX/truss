"""Scoped SQL three-valued profile-dispatch model, not a proof of the runtime."""
import json
from z3 import Int,Bool,And,Not,Or,Solver,sat,unsat
# SQL truth encoding: -1 NULL, 0 false, 1 true. exact legacy configuration
# and exact modern remainder equality are explicit trusted comparisons.
p=Int('profile_match'); legacy=Bool('legacy_exact'); remainder=Bool('remainder_exact')
modern=And(p==1,remainder)
accept=Or(legacy,modern)
s=Solver();s.add(p>=-1,p<=1,accept,Not(legacy),Not(modern));assert s.check()==unsat
s=Solver();s.add(p>=-1,p<=1,accept,Not(legacy),p!=1);assert s.check()==unsat
# Weakened original SQL predicate: NOT(NULL AND TRUE) is NULL; PL/pgSQL
# IF NULL does not raise. This demonstrates why an explicit total test matters.
s=Solver();s.add(Not(legacy),p==-1,remainder);assert s.check()==sat
print(json.dumps({'scope':'abstract total exact-profile dispatch only; native implementation separately tested','total_dispatch':'unsat','missing_profile_acceptance':'unsat','weakened_nullable_guard':'sat','not_proven':['whole SQL runtime','issuer authentication','protected backend enforcement','concurrent source closure']}))
