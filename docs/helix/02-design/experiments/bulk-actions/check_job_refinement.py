#!/usr/bin/env python3
"""@covers US-048-AC7 / UMF US-904-AC7. Refinement of the bounded batch model onto the UMF job table.

Every reachable edge of check_model.py is projected to a job-level status plus durable committed-batch
count. The projected step must stutter or equal a (from, to, committed-delta) triple that the UMF owner
fixture (docs/helix/03-test/fixtures/bulk-update/transitions.json, hand-authored from CONTRACT-904)
lists as permitted. Nothing is derived from UMF code. Controls: the model's unsafe mutations must
violate either an invariant or this refinement. Design-level only; no native proof, no TLC here.
Usage: check_job_refinement.py --fixture /path/to/transitions.json [--out receipt.json]
"""
import argparse, hashlib, json
from collections import deque
from pathlib import Path
import check_model as m

def project(s):
    prefix = s.prefix - (1 if s.phase == 'commit_unknown' else 0)  # durable only once the original result is observed
    # Effects are admitted only after the confirmed marker, so registration_unknown is still an unadmitted running claim.
    unknown = ('commit_unknown', 'rollback_unknown', 'rolled_back', 'conflict_unknown')
    if s.stopped and s.phase == 'settled': status = 'stopped'
    elif s.cancel_status == 'cancelled': status = 'cancelled'
    elif s.phase in unknown or (s.recovering and s.phase != 'registration_unknown'): status = 'reconciling'
    elif prefix == 2 and s.phase in ('idle', 'committed'): status = 'completed'
    elif s.phase == 'committed' or (s.phase == 'idle' and (s.owner == -1 or s.expired)): status = 'queued'
    else: status = 'running'
    return status, prefix

def allowed_triples(fx):
    out = {}
    for c in fx['transitions']:
        e = c['expect']
        if not e.get('ok') or c['state'] is None: continue
        s0, s1 = c['state'], e['state']
        d = s1.get('committedBatches', s0['committedBatches']) - s0['committedBatches']
        out.setdefault((s0['status'], s1['status'], d), []).append(c['id'])
    return out

def check(mutation, allowed):
    initial = [m.State(changes=tuple(bool(k & (1 << i)) for i in range(3))) for k in range(8)]
    seen = set(initial); queue = deque(initial); used = {}; bad = None
    while queue and bad is None:
        cur = queue.popleft(); a = project(cur)
        for ev, nxt in m.transitions(cur, mutation):
            b = project(nxt)
            if m.violations(nxt):
                bad = {'kind': 'invariant', 'event': ev, 'violations': m.violations(nxt)}; break
            if a != b:
                t = (a[0], b[0], b[1] - a[1])
                if t not in allowed:
                    bad = {'kind': 'refinement', 'event': ev, 'from': a, 'to': b}; break
                used.setdefault(t, set()).add(ev)
            if nxt not in seen: seen.add(nxt); queue.append(nxt)
    return {'states': len(seen), 'violation': bad, 'used': {str(k): sorted(v) for k, v in used.items()}}

def main():
    p = argparse.ArgumentParser(); p.add_argument('--fixture', required=True); p.add_argument('--out'); a = p.parse_args()
    raw = Path(a.fixture).read_bytes(); fx = json.loads(raw); allowed = allowed_triples(fx)
    good = check(None, allowed); assert good['violation'] is None, good
    controls = {n: check(n, allowed) for n in ('broken_terminal', 'missing_lookup_reclaim', 'broken_recovery', 'premature_cancel', 'broken_cancel')}
    refinement_caught = {n: r['violation'] for n, r in controls.items() if r['violation'] and r['violation']['kind'] == 'refinement'}
    assert refinement_caught, 'no control was caught by the refinement itself: ' + json.dumps(controls)
    uncovered = sorted(str(t) for t in allowed if str(t) not in good['used'])
    report = {'scope': 'Bounded model refinement onto UMF job table; no native proof', 'passed': True,
              'fixtureSha256': hashlib.sha256(raw).hexdigest(), 'fixtureStatus': fx['status'],
              'modelStates': good['states'], 'stepsUsed': good['used'], 'fixtureTriplesNotExercisedByModel': uncovered,
              'controls': {n: r['violation'] for n, r in controls.items()},
              'sourceSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    if a.out: Path(a.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'modelStates', 'fixtureTriplesNotExercisedByModel')}))
    print(json.dumps({n: (v or {}).get('kind') + ':' + (v or {}).get('event', '') for n, v in report['controls'].items()}))
if __name__ == '__main__': main()
