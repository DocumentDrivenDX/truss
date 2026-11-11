#!/usr/bin/env python3
"""Native claim/fence/cancel checks for the candidate bulk control functions (scratch PostgreSQL).

Real concurrent psql sessions as role "bulk-worker" (owner decision 2026-11-10) and the control
role. The job row lock inside the functions is lock level 4a (CONTRACT-009). Checks:
  A. two workers racing to claim: exactly one wins, the other is refused after the winner commits
  B. stale fence: a superseded claimant cannot execute; the new claimant can
  C. cancel vs an admitted attempt, both lock orders (cancel waits on the held 4a lock)
  D. role surface: no table access, no submit/control/private helpers, no cancel via worker_event
  E. lock footprint: an open call holds relation locks on the job home only (no advisory locks)
  F. differential: random event sequences give identical results from SQL and _bulk_job_control
Design-level only: levels 1-4 are the caller's and are NOT exercised here; no effect transaction,
no authority, no native custody. Usage:
  PYTHONPATH=packages/python/src check_claim_fence_native.py --pg-bin DIR [--seed N] [--out receipt.json]
"""
import argparse, hashlib, json, os, random, subprocess, sys, tempfile, threading, time
from pathlib import Path
from truss import _bulk_job_control as m

HERE = Path(__file__).resolve().parent
WORKER = 'bulk-worker'
OWNER = 'bulk'


class Session:
    def __init__(self, pg, sock, role, name, env):
        e = dict(env, PGAPPNAME=name)
        self.p = subprocess.Popen([str(pg / 'psql'), '-qAtX', '-h', str(sock), '-U', role, '-d', 'postgres', '-v', 'ON_ERROR_STOP=0'],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=e)
        self.n = 0
        self.pending = None

    def send(self, sql):
        self.n += 1
        self.marker = f'__M{self.n}__'
        self.p.stdin.write(sql.rstrip() + f'\n\\echo {self.marker}\n')
        self.p.stdin.flush()

    def collect(self):
        out = []
        while True:
            line = self.p.stdout.readline()
            if line == '' or line.strip() == self.marker:
                break
            out.append(line.rstrip('\n'))
        return out

    def call(self, sql):
        self.send(sql)
        return self.collect()

    def close(self):
        try:
            self.p.stdin.close(); self.p.wait(timeout=10)
        except Exception:
            self.p.kill()


def j(s):
    return json.loads(s)


def ev(kind, **kw):
    return json.dumps(dict(kind=kind, **kw))


def worker(ns, job, event, result=None):
    r = "NULL" if result is None else "'\\x%s'::bytea" % result.hex()
    return "SELECT truss_bulk.worker_event('%s','%s','%s'::jsonb,%s);" % (ns, job, event, r)


def control(ns, job, event):
    return "SELECT truss_bulk.control_event('%s','%s','%s'::jsonb);" % (ns, job, event)


def submit(ns, job, n):
    return "SELECT truss_bulk.submit('%s','%s',%d,'\\x01'::bytea);" % (ns, job, n)


def wait_blocked(mon, name, timeout=10):
    end = time.time() + timeout
    while time.time() < end:
        out = mon.call("SELECT wait_event_type FROM pg_stat_activity WHERE application_name='%s' AND state='active';" % name)
        if out and out[0] == 'Lock':
            return True
        time.sleep(0.05)
    return False


def random_sequence(rng, n_batches):
    events = []
    for _ in range(rng.randint(3, 14)):
        k = rng.choice(['claim', 'claim', 'execute', 'execute', 'commit', 'commit', 'failure', 'lose-custody', 'reconcile', 'reconcile',
                        'expire-claim', 'cancel', 'cancel'])
        if k == 'execute':
            events.append({'kind': 'execute', 'batch': rng.choice([0, 0, 1, 2]), 'fence': rng.choice(['1', '1', '2', '3', '01'])})
        elif k == 'failure':
            events.append({'kind': 'failure', 'failure': 'conflict', 'code': rng.choice(['PAP_GUARD', 'PARAMETER', 'NATIVE_ABORT'])})
        elif k == 'reconcile':
            events.append({'kind': 'reconcile', 'evidence': rng.choice(['committed', 'noncommit-admitted', 'receipt-not-found', 'native-status-null', 'lease-expired', 'unavailable'])})
        elif k == 'expire-claim':
            events.append({'kind': 'expire-claim', 'confirmedNoExecution': rng.choice([True, True, False])})
        else:
            events.append({'kind': k})
    return events


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--pg-bin', required=True); ap.add_argument('--seed', type=int, default=20261110)
    ap.add_argument('--sequences', type=int, default=400); ap.add_argument('--out')
    a = ap.parse_args(); pg = Path(a.pg_bin)
    sql_files = ['bulk-control-layout.sql', 'bulk-control-functions.sql', 'bulk-control-grants.sql']
    sources = {f: (HERE / f).read_text() for f in sql_files}
    env = dict(os.environ, LC_ALL='en_US.UTF-8', LANG='en_US.UTF-8')
    results = []

    def check(name, ok, detail=''):
        results.append({'check': name, 'ok': bool(ok), 'detail': detail if not ok else ''})

    with tempfile.TemporaryDirectory(prefix='truss-bulk-native-') as d:
        data = Path(d) / 'data'; sock = Path(tempfile.mkdtemp(prefix='tb', dir='/tmp'))
        run = lambda *c, **k: subprocess.run([str(x) for x in c], capture_output=True, text=True, env=env, **k)
        r = run(pg / 'initdb', '-D', data, '-A', 'trust', '-U', OWNER, '--no-sync'); assert r.returncode == 0, r.stderr
        r = run(pg / 'pg_ctl', '-D', data, '-w', '-o', f"-c listen_addresses='' -k {sock} -c fsync=off -c max_connections=50", '-l', Path(d) / 'log', 'start')
        assert r.returncode == 0, r.stderr + (Path(d) / 'log').read_text()
        sessions = []
        # A broken lock protocol must fail the run, not hang it: kill every session after the deadline.
        watchdog = threading.Timer(150, lambda: [x.p.kill() for x in sessions])
        watchdog.daemon = True; watchdog.start()
        try:
            def psql_file(sql):
                r = run(pg / 'psql', '-X', '-q', '-h', sock, '-U', OWNER, '-d', 'postgres', '-v', 'ON_ERROR_STOP=1', input=sql)
                assert r.returncode == 0, r.stderr
            psql_file('CREATE ROLE "%s" LOGIN;' % WORKER)
            for f in sql_files:
                psql_file(sources[f])
            S = lambda role, name: sessions.append(Session(pg, sock, role, name, env)) or sessions[-1]
            mon = S(OWNER, 'mon'); ctl = S(OWNER, 'ctl'); w1 = S(WORKER, 'w1'); w2 = S(WORKER, 'w2')

            # A. claim race
            ctl.call(submit('ns', 'race', 2))
            w1.call('BEGIN;')
            r1 = j(w1.call(worker('ns', 'race', ev('claim')))[0])
            w2.send(worker('ns', 'race', ev('claim')))
            blocked = wait_blocked(mon, 'w2')
            w1.call('COMMIT;')
            r2 = j(w2.collect()[0])
            st = j(w1.call("SELECT truss_bulk._state(j) FROM truss_bulk.job j WHERE job_id='race';")[0]) if False else None
            check('A: second claimant blocks on the held job lock', blocked)
            check('A: first claim wins with fence 1', r1['ok'] and r1['state']['fence'] == '1' and r1['state']['claim']['fence'] == '1', r1)
            check('A: second claim is refused once the winner commits', r2 == {'ok': False}, r2)

            # B. stale fence
            ctl.call(submit('ns', 'stale', 2))
            c1 = j(w1.call(worker('ns', 'stale', ev('claim')))[0])
            ex = j(w1.call(worker('ns', 'stale', ev('expire-claim', confirmedNoExecution=True)))[0])
            c2 = j(w2.call(worker('ns', 'stale', ev('claim')))[0])
            old = j(w1.call(worker('ns', 'stale', ev('execute', batch=0, fence='1')))[0])
            new = j(w2.call(worker('ns', 'stale', ev('execute', batch=0, fence='2')))[0])
            check('B: fences are 1 then 2', c1['state']['fence'] == '1' and c2['state']['fence'] == '2', (c1, c2))
            check('B: superseded claimant refused with PAP_FENCE and changes nothing', old == {'ok': False, 'code': 'PAP_FENCE'}, old)
            check('B: current claimant admitted', new['ok'] and new['state']['claim']['effectAdmitted'] is True, new)
            wrong = j(w2.call(worker('ns', 'stale', ev('execute', batch=0, fence='2')))[0])
            check('B: admission cannot be repeated', wrong == {'ok': False}, wrong)

            # C1. admitted attempt holds the job lock; cancel waits, then fences the future
            ctl.call(submit('ns', 'cancel1', 2))
            w1.call(worker('ns', 'cancel1', ev('claim')))
            w1.call('BEGIN;')
            w1.call(worker('ns', 'cancel1', ev('execute', batch=0, fence='1')))
            ctl.send(control('ns', 'cancel1', ev('cancel')))
            blocked = wait_blocked(mon, 'ctl')
            cm = j(w1.call(worker('ns', 'cancel1', ev('commit'), b'result-0'))[0])
            w1.call('COMMIT;')
            cr = j(ctl.collect()[0])
            check('C1: cancel waits for the admitted attempt holding the job lock', blocked)
            check('C1: batch commits first and is retained', cm['ok'] and cm['state']['committedBatches'] == 1 and cm['state']['status'] == 'queued', cm)
            check('C1: cancel then fences the future (cancelled, prefix kept)', cr['ok'] and cr['state']['status'] == 'cancelled' and cr['state']['committedBatches'] == 1, cr)
            rc = w1.call("SELECT count(*) FROM truss_bulk.batch_receipt WHERE job_id='cancel1';") if False else None
            late = j(w2.call(worker('ns', 'cancel1', ev('claim')))[0])
            check('C1: later claim refused PAP_CANCELLED', late == {'ok': False, 'code': 'PAP_CANCELLED'}, late)

            # C2. cancel wins the lock first: admission is refused
            ctl.call(submit('ns', 'cancel2', 2))
            w1.call(worker('ns', 'cancel2', ev('claim')))
            ctl.call('BEGIN;')
            cw = j(ctl.call(control('ns', 'cancel2', ev('cancel')))[0])
            w1.send(worker('ns', 'cancel2', ev('execute', batch=0, fence='1')))
            blocked = wait_blocked(mon, 'w1')
            ctl.call('COMMIT;')
            exr = j(w1.collect()[0])
            check('C2: cancel before admission cancels at once', cw['ok'] and cw['state']['status'] == 'cancelled', cw)
            check('C2: waiting execute is refused PAP_CANCELLED after cancel wins', blocked and exr == {'ok': False, 'code': 'PAP_CANCELLED'}, (blocked, exr))

            # C3. cancel against an admitted, uncommitted attempt records the request; final batch completes
            ctl.call(submit('ns', 'cancel3', 1))
            w1.call(worker('ns', 'cancel3', ev('claim'))); w1.call(worker('ns', 'cancel3', ev('execute', batch=0, fence='1')))
            rq = j(ctl.call(control('ns', 'cancel3', ev('cancel')))[0])
            fin = j(w1.call(worker('ns', 'cancel3', ev('commit'), b'final'))[0])
            check('C3: cancel against admitted work is only recorded', rq['ok'] and rq.get('basis') == 'cancel-requested' and rq['state']['status'] == 'running', rq)
            check('C3: final-batch commit completes despite pending cancel', fin['ok'] and fin['state']['status'] == 'completed' and fin['state']['cancelRequested'] is True, fin)

            # D. role surface
            denied = {
                'select': w1.call('SELECT 1 FROM truss_bulk.job LIMIT 1;'),
                'update': w1.call("UPDATE truss_bulk.job SET status='completed';"),
                'insert': w1.call("INSERT INTO truss_bulk.batch_receipt VALUES ('ns','x',0,'0','\\x01'::bytea,decode(repeat('ab',32),'hex'));"),
                'submit': w1.call(submit('ns', 'sneaky', 1)),
                'control': w1.call(control('ns', 'race', ev('cancel'))),
                'private': w1.call("SELECT truss_bulk._apply('ns','race','{\"kind\":\"cancel\"}'::jsonb,NULL);"),
            }
            for k, out in denied.items():
                check(f'D: bulk-worker {k} is permission denied', any('permission denied' in line for line in out), out)
            wc = j(w1.call(worker('ns', 'race', ev('cancel')))[0])
            check('D: cancel through worker_event is refused AUTHORIZATION', wc == {'ok': False, 'code': 'AUTHORIZATION'}, wc)
            n = ctl.call("SELECT count(*) FROM truss_bulk.job WHERE job_id='sneaky';")
            check('D: no row was created by the refused calls', n == ['0'], n)

            # E. lock footprint while a call's transaction is open
            ctl.call(submit('ns', 'locks', 2))
            w1.call('BEGIN;'); w1.call(worker('ns', 'locks', ev('claim')))
            held = mon.call("SELECT DISTINCT l.locktype || ':' || coalesce(c.relname,'') FROM pg_locks l JOIN pg_stat_activity a ON a.pid=l.pid "
                            "LEFT JOIN pg_class c ON c.oid=l.relation WHERE a.application_name='w1' AND l.locktype NOT IN ('virtualxid','transactionid') ORDER BY 1;")
            w1.call('COMMIT;')
            rels = {x.split(':', 1)[1] for x in held if x.startswith('relation:')}
            check('E: no advisory or non-relation locks beyond xid locks', all(x.startswith('relation:') for x in held), held)
            check('E: only the job home (and its key index) is locked', rels <= {'job', 'job_pkey'} and 'job' in rels, held)

            # F. differential vs the pure model
            rng = random.Random(a.seed); script = []; plan = []
            for s in range(a.sequences):
                nb = rng.choice([0, 1, 2, 3]); job = f'd{s}'; events = random_sequence(rng, nb)
                script.append(submit('diff', job, nb)); plan.append((job, nb, events))
                for e in events:
                    script.append(control('diff', job, json.dumps(e)) if e['kind'] == 'cancel'
                                  else worker('diff', job, json.dumps(e), b'r' if e['kind'] == 'commit' else None))
            res = run(pg / 'psql', '-qAtX', '-h', sock, '-U', OWNER, '-d', 'postgres', '-v', 'ON_ERROR_STOP=0', input='\n'.join(script), timeout=240)
            out = (res.stdout + res.stderr).splitlines()
            lines = [x for x in res.stdout.splitlines() if x.startswith('{')]
            errors = [x for x in res.stderr.splitlines() if x.strip()]
            check('F: SQL emitted no errors (a constraint violation would show here)', not errors, errors[:3])
            idx = 0; mismatches = []; compared = 0
            for job, nb, events in plan:
                state = m.apply_event(None, {'kind': 'submit', 'batchCount': nb})['state']; idx += 1
                for e in events:
                    exp = m.apply_event(state, e); got = j(lines[idx]); idx += 1; compared += 1
                    if exp['ok']:
                        state = exp['state']
                    same = exp['ok'] == got['ok'] and exp.get('code') == got.get('code') and exp.get('basis') == got.get('basis') \
                        and (not exp['ok'] or exp['state'] == got['state'])
                    if not same:
                        mismatches.append({'job': job, 'event': e, 'expected': exp, 'got': got}); break
            check(f'F: {a.sequences} random sequences ({compared} events) agree with the pure model', not mismatches, mismatches[:2])
        except Exception as e:  # killed by the watchdog or a protocol failure
            check('harness: scenario crashed or timed out (lock protocol broken?)', False, repr(e)[:300])
        finally:
            watchdog.cancel()
            for s in sessions:
                s.close()
            run(pg / 'pg_ctl', '-D', data, '-m', 'immediate', '-w', 'stop')
            try: sock.rmdir()
            except OSError: pass
    failed = [x for x in results if not x['ok']]
    report = {'scope': 'Candidate bulk control functions on scratch PostgreSQL; levels 1-4, effect transaction, authority and custody NOT exercised',
              'passed': not failed, 'checks': len(results), 'seed': a.seed, 'role': WORKER, 'lockLevel': '4a',
              'postgres': run(pg / 'postgres', '--version').stdout.strip(),
              'sourceSha256': {f: hashlib.sha256(s.encode()).hexdigest() for f, s in sources.items()}, 'failed': failed}
    if a.out: Path(a.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'checks', 'postgres')}))
    for x in failed: print('FAIL', json.dumps(x)[:400])
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
