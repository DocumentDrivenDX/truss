"""E6: idempotent group application without a table. A request id travels in the journal origin; a partial
expression index finds the rows of an earlier group; a transaction-scoped advisory lock serializes duplicates.
Measures: lookup plan and time across many partitions, the index's effect on inserts without a request id, and
the duplicate rate of 300 concurrent same-id requests with and without the lock."""
import argparse, json, threading, time
import psycopg
from common import *

DDL = "/private/tmp/claude-501/truss-spec-wt/docs/helix/02-design/contracts/storage-layout.sql"

def setup(c, months):
    c.execute(open(DDL).read())
    # monthly partitions: the past `months` months and two ahead
    for k in range(-months, 3):
        c.execute(f"create table truss.journal_m{k + months} partition of truss.journal for values from (date_trunc('month', now()) + interval '{k} month') to (date_trunc('month', now()) + interval '{k + 1} month')")
    c.execute("insert into truss.schema_rev values (1, now(), '{}'); update truss.schema_head set rev = 1")

def fill(c, n_plain, n_req, months):
    c.execute("""insert into truss.journal (at, entity_kind, entity_id, entity_type, ver, op, rev, origin)
                 select date_trunc('month', now()) + ((g % %s) - %s) * interval '1 month' + (g %% 1000) * interval '1 second', 'o', g, 1, 1, 'create', 1, '{"actor":"x"}'
                 from generate_series(1, %s) g""" % ("%s", "%s", "%s"), (months, months - 1, n_plain)) if False else None
    c.execute(f"""insert into truss.journal (at, entity_kind, entity_id, entity_type, ver, op, rev, origin)
                  select date_trunc('month', now()) - (g % {months}) * interval '1 month' + (g % 1000) * interval '1 second', 'o', g, 1, 1, 'create', 1, '{{"actor":"x"}}'
                  from generate_series(1, {n_plain}) g""")
    c.execute(f"""insert into truss.journal (at, entity_kind, entity_id, entity_type, ver, op, rev, origin)
                  select date_trunc('month', now()) - (g % {months}) * interval '1 month' + (g % 1000) * interval '1 second', 'o', {n_plain} + g, 1, 1, 'create', 1,
                         jsonb_build_object('actor','x','request',jsonb_build_object('id','req-'||g,'hash','h'))
                  from generate_series(1, {n_req}) g""")

def group(c, rid, use_lock):
    with c.transaction():
        if use_lock: c.execute("select pg_advisory_xact_lock(hashtextextended(%s, 0))", (rid,))
        found = c.execute("select count(*) from truss.journal where origin ? 'request' and origin #>> '{request,id}' = %s and at > now() - interval '1 month' * 3", (rid,)).fetchone()[0]
        if found: return "replay"
        c.execute("insert into truss.journal (entity_kind, entity_id, entity_type, ver, op, rev, origin) values ('o', 1, 1, 1, 'create', 1, %s::jsonb)",
                  (json.dumps({"actor": "x", "request": {"id": rid, "hash": "h"}}),))
        time.sleep(0.002)
        return "applied"

def run(lib, months, out):
    srv, d = start_server(lib); uri = srv.get_uri(); R = {"lib": lib, "months": months}
    try:
        c = conn(uri); R["pg"] = version(c); setup(c, months)
        t0 = time.perf_counter(); fill(c, 400000, 2000, months); R["fill_s"] = round(time.perf_counter() - t0, 1)
        # insert cost of plain rows without and with the partial index
        def ins(n):
            t0 = time.perf_counter()
            c.execute("insert into truss.journal (entity_kind, entity_id, entity_type, ver, op, rev, origin) select 'o', g, 1, 1, 'create', 1, '{\"actor\":\"x\"}' from generate_series(1, %s) g", (n,))
            return (time.perf_counter() - t0) * 1000
        R["insert_100k_plain_ms_without_index"] = round(min(ins(100000) for _ in range(3)), 1)
        c.execute("create index journal_request on truss.journal ((origin #>> '{request,id}')) where origin ? 'request'")
        R["insert_100k_plain_ms_with_index"] = round(min(ins(100000) for _ in range(3)), 1)
        R["index_size_mb"] = round(c.execute("select coalesce(sum(pg_relation_size(i.indexrelid)),0)/1048576.0 from pg_index i where i.indexrelid::regclass::text like 'truss.journal_m%_expr_idx' or i.indexrelid::regclass::text like 'journal_m%_expr_idx'").fetchone()[0], 2)
        c.execute("analyze truss.journal")
        plan = [r[0] for r in c.execute("explain (analyze, summary off, costs off) select count(*) from truss.journal where origin ? 'request' and origin #>> '{request,id}' = 'req-77' and at > now() - interval '1 month' * 3").fetchall()]
        R["lookup_plan"] = plan
        xs = []
        for i in range(500):
            t0 = time.perf_counter(); c.execute("select count(*) from truss.journal where origin ? 'request' and origin #>> '{request,id}' = %s and at > now() - interval '1 month' * 3", (f"req-{i+1}",)).fetchone(); xs.append((time.perf_counter() - t0) * 1000)
        R["lookup_ms"] = summ(xs)
        # concurrency
        for use_lock in (False, True):
            a, b = conn(uri), conn(uri); dup = 0
            for k in range(300):
                rid = f"race-{use_lock}-{k}"; bar = threading.Barrier(2); res = []
                def w(cc):
                    bar.wait(); res.append(group(cc, rid, use_lock))
                th = [threading.Thread(target=w, args=(a,)), threading.Thread(target=w, args=(b,))]
                [t.start() for t in th]; [t.join() for t in th]
                n = c.execute("select count(*) from truss.journal where origin #>> '{request,id}' = %s", (rid,)).fetchone()[0]
                if n > 1: dup += 1
            R[f"duplicates_of_300_{'with' if use_lock else 'without'}_lock"] = dup
        print(json.dumps({k:v for k,v in R.items() if k!="lookup_plan"}, default=str), flush=True)
    finally:
        try: srv.cleanup()
        except Exception: pass
    open(out, "a").write(json.dumps(R, default=str) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--months", type=int, default=12); ap.add_argument("--out", default="out/e6.jsonl")
    a = ap.parse_args(); run(a.lib, a.months, a.out)
