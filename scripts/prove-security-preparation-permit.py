"""Conditional native-permit binding laws; no SQL/issuer/selection refinement."""
from pathlib import Path
import hashlib, json, z3

out = Path('docs/helix/04-build/evidence/security-preparation-permit-formal-20261014')
out.mkdir(exist_ok=True)
x, y = z3.BitVecs('original_data_xid8 supplied_data_xid8', 64)
same_low = z3.Extract(31, 0, x) == z3.Extract(31, 0, y)
same_high = z3.Extract(63, 32, x) == z3.Extract(63, 32, y)
old, current, source, held, issuer, live = z3.Bools(
    'old_permission current_permission original_source_match native_data_exclusion authentic_issuer original_coordinator_live')
permit = z3.And(current, source, held, issuer, live)
coordinator_lost, data_commit, change = z3.Bools('coordinator_lost data_commit_in_progress authority_changed')
data_fence = z3.Bool('original_data_transaction_holds_authority_exclusion')
writer_participation = z3.Implies(data_fence, z3.Not(change))
anchor_a, anchor_b, pid_a, pid_b = z3.Ints('anchor_a anchor_b pid_a pid_b')
lo_a, lo_b, hi_a, hi_b = z3.Ints('lo_a lo_b hi_a hi_b')
# One original issuer's complete tuple; no union of separately issued tuples.
candidate = z3.Ints('candidate_anchor candidate_pid candidate_lo candidate_hi')
a = (anchor_a, pid_a, lo_a, hi_a)
b = (anchor_b, pid_b, lo_b, hi_b)
same_tuple = lambda left, right: z3.And(*(u == v for u, v in zip(left, right)))
member_union = z3.And(*(z3.Or(v == av, v == bv) for v, av, bv in zip(candidate, a, b)))
one_lease = z3.Or(same_tuple(candidate, a), same_tuple(candidate, b))

queries = [
    ('full-xid8-pieces-injective', z3.And(same_low, same_high, x != y), 'unsat'),
    ('xid32-only-allows-foreign-cut', z3.And(same_low, x != y), 'sat'),
    ('fresh-authority-denies-stale-snapshot', z3.And(old, z3.Not(current), permit), 'unsat'),
    ('stale-snapshot-authority-control', z3.And(old, z3.Not(current), source, held, issuer, live), 'sat'),
    ('lost-coordinator-refuses-new-stage', z3.And(permit, z3.Not(live)), 'unsat'),
    ('data-held-fence-closes-commit-loss-window', z3.And(writer_participation, data_fence,
        coordinator_lost, data_commit, change), 'unsat'),
    ('coordinator-only-fence-leaves-commit-loss-window', z3.And(writer_participation,
        z3.Not(data_fence), coordinator_lost, data_commit, change), 'sat'),
    ('one-original-permit-prohibits-fragment-union', z3.And(one_lease,
        z3.Not(same_tuple(candidate, a)), z3.Not(same_tuple(candidate, b))), 'unsat'),
    ('multiple-permits-enable-fragment-union', z3.And(member_union, anchor_a != anchor_b,
        pid_a != pid_b, lo_a != lo_b, hi_a != hi_b,
        z3.Not(same_tuple(candidate, a)), z3.Not(same_tuple(candidate, b))), 'sat'),
]
results = []
for name, formula, expected in queries:
    solver = z3.Solver(); solver.set(timeout=10000); solver.add(formula)
    smt = solver.to_smt2(); (out / (name + '.smt2')).write_text(smt)
    observed = str(solver.check())
    assert observed == expected, (name, observed)
    replay = z3.Solver(ctx=z3.Context()); replay.set(timeout=10000); replay.from_string(smt)
    assert str(replay.check()) == expected
    results.append({'id': name, 'expected': expected, 'observed': observed,
        'model': str(solver.model()) if observed == 'sat' else None,
        'smt2Sha256': hashlib.sha256(smt.encode()).hexdigest()})
receipt = {'status': 'conditional-model-passed', 'solver': z3.get_version_string(),
    'sourceSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'queries': results,
    'scope': 'Exact 64-bit xid partition, Boolean current-authority admission, data-held exclusion and original complete permit tuple versus fragment union.',
    'limitations': ['No native issuer, anchor, privilege, pg_locks, peer, SQL or original Weft selection refinement theorem.',
        'Authentic issuer, complete original source/scope, live coordinator and exact participating writer fence are premises.',
        'One permit per original coordinator transaction must be independently enforced; the union counterexample shows why.',
        'No cryptographic token or Python comparison issues authority; no preparation/seal/backend acceptance promotion.']}
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': receipt['status'], 'queries': len(results)}))
