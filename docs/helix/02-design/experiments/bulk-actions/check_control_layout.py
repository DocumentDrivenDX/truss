#!/usr/bin/env python3
"""Candidate bulk control layout vs the job-control model, on a scratch PostgreSQL cluster.

Applies bulk-control-layout.sql to a throwaway initdb cluster (unix socket only), then checks that
(1) every state reachable from the pure model _bulk_job_control is accepted by the layout's constraints,
(2) the UMF owner fixture's sample states are accepted, and (3) a set of invalid rows are rejected.
Design-level only: no grants, locks, concurrency or install-baseline qualification.
Usage: PYTHONPATH=packages/python/src check_control_layout.py --fixture F --pg-bin DIR [--out receipt.json]
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path
from truss import _bulk_job_control as m

HERE = Path(__file__).resolve().parent


def reachable(max_batches=3):
    seen, out = set(), []
    for n in range(max_batches + 1):
        start = m.apply_event(None, {'kind': 'submit', 'batchCount': n})['state']
        stack = [start]
        while stack:
            s = stack.pop()
            key = json.dumps(s, sort_keys=True)
            if key in seen:
                continue
            seen.add(key); out.append(s)
            if int(s['fence']) >= 2:  # bound the claim/expire loop; fence arithmetic is tested elsewhere
                continue
            ev = [{'kind': 'claim'}, {'kind': 'commit'}, {'kind': 'cancel'}, {'kind': 'lose-custody'},
                  {'kind': 'failure', 'failure': 'conflict', 'code': 'PAP_GUARD'},
                  {'kind': 'expire-claim', 'confirmedNoExecution': True},
                  {'kind': 'reconcile', 'evidence': 'committed'}, {'kind': 'reconcile', 'evidence': 'noncommit-admitted'},
                  {'kind': 'reconcile', 'evidence': 'receipt-not-found'}]
            if s['claim']:
                ev.append({'kind': 'execute', 'batch': s['claim']['batch'], 'fence': s['claim']['fence']})
            for e in ev:
                r = m.apply_event(s, e)
                if r['ok']:
                    stack.append(r['state'])
    return out


def q(v):
    if v is None: return 'NULL'
    if isinstance(v, bool): return 'true' if v else 'false'
    if isinstance(v, int): return str(v)
    return "'" + v.replace("'", "''") + "'"


def job_row(s, ns='ns', job='j1', sha=None, manifest="'\\x01'::bytea"):
    c, st = s['claim'], s['stop']
    return ("INSERT INTO truss_bulk.job VALUES (%s,%s,%s,%d,%d,%s,%s,%s,%s,%s,%s,%s,%s,%s);" % (
        q(ns), q(job), q(s['status']), s['batchCount'], s['committedBatches'], q(s['fence']),
        q(c['batch']) if c else 'NULL', q(c['fence']) if c else 'NULL', q(c['effectAdmitted']) if c else 'NULL',
        q(s['cancelRequested']), q(st['batch']) if st else 'NULL', q(st['code']) if st else 'NULL',
        sha or "decode(repeat('ab',32),'hex')", manifest))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fixture', required=True); ap.add_argument('--pg-bin', required=True); ap.add_argument('--out')
    a = ap.parse_args(); pg = Path(a.pg_bin)
    raw = Path(a.fixture).read_bytes(); fx = json.loads(raw)
    ddl = (HERE / 'bulk-control-layout.sql').read_text()
    cases = []  # (label, expect_ok, sql)
    reach = reachable()
    for i, s in enumerate(reach):
        cases.append((f'reachable:{s["status"]}:{i}', True, job_row(s)))
    for k, s in fx['samples'].items():
        if s is not None: cases.append((f'fixture-sample:{k}', True, job_row(s)))
    base = m.apply_event(None, {'kind': 'submit', 'batchCount': 3})['state']
    running = m.apply_event(m.apply_event(base, {'kind': 'claim'})['state'], {'kind': 'execute', 'batch': 0, 'fence': '1'})['state']
    def mut(s, **kw):
        t = json.loads(json.dumps(s)); [t.__setitem__(k, v) for k, v in kw.items()]; return t
    bad = {
        'committed-over-count': mut(base, committedBatches=4),
        'queued-with-claim': mut(base, claim={'batch': 0, 'fence': '0', 'effectAdmitted': False}),
        'running-without-claim': mut(base, status='running'),
        'completed-incomplete': mut(base, status='completed'),
        'stopped-without-stop': mut(base, status='stopped'),
        'cancelled-with-claim': mut(running, status='cancelled'),
        'noncanonical-fence': mut(base, fence='01'),
        'claim-fence-not-current': mut(running, claim={'batch': 0, 'fence': '9', 'effectAdmitted': True}),
        'claim-not-next-batch': mut(running, claim={'batch': 1, 'fence': '1', 'effectAdmitted': True}),
        'pending-cancel-on-queued': mut(base, cancelRequested=True),
        'reconciling-unadmitted': mut(running, status='reconciling', claim={'batch': 0, 'fence': '1', 'effectAdmitted': False}),
        'half-stop-record': mut(base, status='stopped', stop={'batch': 0, 'code': None}),
        'half-claim-record': mut(running, claim={'batch': 0, 'fence': None, 'effectAdmitted': True}),
        'stop-past-batches': mut(base, status='stopped', stop={'batch': 3, 'code': 'PAP_GUARD'}),
        'cancelled-after-all-batches': mut(base, status='cancelled', committedBatches=3, nextBatch=3),
    }
    for k, s in bad.items(): cases.append((f'reject:{k}', False, job_row(s)))
    cases += [('reject:bad-namespace', False, job_row(base, ns='a/b')),
              ('reject:short-manifest-hash', False, job_row(base, sha="decode('ab','hex')")),
              ('reject:empty-manifest', False, job_row(base, manifest="''::bytea")),
              ('reject:receipt-without-job', False, "INSERT INTO truss_bulk.batch_receipt VALUES ('ns','nojob',0,'1','\\x01'::bytea,decode(repeat('ab',32),'hex'));"),
              ('reject:receipt-over-R', False, "INSERT INTO truss_bulk.job VALUES ('ns','jr','queued',1,0,'0',NULL,NULL,NULL,false,NULL,NULL,decode(repeat('ab',32),'hex'),'\\x01'::bytea);\nINSERT INTO truss_bulk.batch_receipt VALUES ('ns','jr',0,'1',decode(repeat('00',2097153),'hex'),decode(repeat('ab',32),'hex'));")]
    with tempfile.TemporaryDirectory(prefix='truss-bulk-layout-') as d:
        data = Path(d) / 'data'; sock = Path(tempfile.mkdtemp(prefix='tb', dir='/tmp'))  # unix socket paths are length-limited
        env = dict(os.environ, LC_ALL='en_US.UTF-8', LANG='en_US.UTF-8')
        run = lambda *c, **k: subprocess.run([str(x) for x in c], capture_output=True, text=True, env=env, **k)
        r = run(pg / 'initdb', '-D', data, '-A', 'trust', '-U', 'bulk', '--no-sync'); assert r.returncode == 0, r.stderr
        r = run(pg / 'pg_ctl', '-D', data, '-w', '-o', f"-c listen_addresses='' -k {sock} -c fsync=off", '-l', Path(d) / 'log', 'start'); assert r.returncode == 0, r.stderr + (Path(d) / 'log').read_text()
        try:
            psql = lambda sql, **k: run(pg / 'psql', '-X', '-q', '-h', sock, '-U', 'bulk', '-d', 'postgres', '-v', 'ON_ERROR_STOP=0', '-c', sql, **k)
            r = run(pg / 'psql', '-X', '-q', '-h', sock, '-U', 'bulk', '-d', 'postgres', '-v', 'ON_ERROR_STOP=1', '-c', ddl); assert r.returncode == 0, r.stderr
            script = []
            for n, (label, expect_ok, sql) in enumerate(cases):
                script.append('\\warn CASE %d' % n); script.append('BEGIN;'); script.append(sql); script.append('ROLLBACK;')
            r = run(pg / 'psql', '-X', '-q', '-h', sock, '-U', 'bulk', '-d', 'postgres', '-v', 'ON_ERROR_STOP=0', input='\n'.join(script))
            errors = {}; cur = None
            for line in r.stderr.splitlines():
                if line.startswith('CASE '): cur = int(line.split()[1])
                elif 'ERROR:' in line and cur is not None: errors.setdefault(cur, line.split('ERROR:', 1)[1].strip()[:160])
            results = []
            for n, (label, expect_ok, sql) in enumerate(cases):
                accepted = n not in errors
                results.append({'case': label, 'expectAccepted': expect_ok, 'accepted': accepted, 'ok': accepted == expect_ok, 'error': errors.get(n, '')})
        finally:
            run(pg / 'pg_ctl', '-D', data, '-m', 'immediate', '-w', 'stop'); sock.rmdir() if sock.exists() and not any(sock.iterdir()) else None
    failed = [x for x in results if not x['ok']]
    report = {'scope': 'Candidate bulk control layout constraints on scratch PostgreSQL; no grants/locks/concurrency/install baseline',
              'passed': not failed, 'cases': len(results), 'reachableStates': len(reach), 'fixtureSha256': hashlib.sha256(raw).hexdigest(),
              'layoutSha256': hashlib.sha256(ddl.encode()).hexdigest(), 'postgres': run(pg / 'postgres', '--version').stdout.strip(), 'failed': failed}
    if a.out: Path(a.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('passed', 'cases', 'reachableStates', 'postgres')}))
    for x in failed: print('FAIL', x)
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
