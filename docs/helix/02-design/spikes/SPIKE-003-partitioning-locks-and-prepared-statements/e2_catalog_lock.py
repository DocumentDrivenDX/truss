"""E2: how should writers be kept consistent with catalog acceptance?
A  head tuple per revision, writers `SELECT ... ORDER BY rev DESC LIMIT 1 FOR SHARE` (ADR-002 D10 as first read)
B  one head row updated in place, writers `FOR SHARE` it, acceptance UPDATEs it
C  advisory locks: writers shared, acceptance exclusive (CONTRACT-001 draft)
D  no protection (baseline)
Tests: correctness (read committed, repeatable read), throughput, acceptance starvation, DDL stalls, deadlock."""
import argparse, json, random, threading, time
import psycopg
from psycopg import IsolationLevel as IL
from common import *

KEY = "hashtextextended('truss.catalog', 0)"
MECH = ["A_new_row_for_share", "B_head_row_for_share", "C_advisory", "D_none", "E_advisory_then_head_row_for_share"]

def setup(uri):
    c = conn(uri)
    c.execute("drop schema if exists e2 cascade"); c.execute("create schema e2"); c.execute("set search_path=e2")
    c.execute("create table schema_rev(rev int primary key)"); c.execute("insert into schema_rev values (1)")
    c.execute("create table catalog_head(id int primary key, rev int not null)"); c.execute("insert into catalog_head values (1,1)")
    c.execute("create table obj(id bigserial primary key, v int not null default 0, payload text)")
    c.execute("create table pt(id bigint not null, t int not null, v text, primary key(id,t)) partition by list(t)")
    for t in range(1, 201): c.execute(f"create table pt_{t} partition of pt for values in ({t})")
    c.execute("insert into pt select g, (g % 200)+1, 'x' from generate_series(1,20000) g")
    return c

def head_read(c, m):
    if m[0] == "A": return c.execute("select rev from schema_rev order by rev desc limit 1 for share").fetchone()[0]
    if m[0] == "B": return c.execute("select rev from catalog_head where id=1 for share").fetchone()[0]
    if m[0] == "C":
        c.execute(f"select pg_advisory_xact_lock_shared({KEY})"); return c.execute("select max(rev) from schema_rev").fetchone()[0]
    if m[0] == "E":
        c.execute(f"select pg_advisory_xact_lock_shared({KEY})"); return c.execute("select rev from catalog_head where id=1 for share").fetchone()[0]
    return c.execute("select max(rev) from schema_rev").fetchone()[0]

def writer_tx(c, m, expected):
    try:
        with c.transaction():
            head = head_read(c, m)
            if head != expected: return "stale_detected", head
            c.execute("insert into obj(v,payload) values (1,'x')")
            return "write_accepted", head
    except psycopg.errors.SerializationFailure: return "serialization_failure", None
    except psycopg.errors.DeadlockDetected: return "deadlock", None

def acceptance(c, m, hold=0.0, ddl=None):
    with c.transaction():
        if m[0] == "A":
            h = c.execute("select rev from schema_rev order by rev desc limit 1 for update").fetchone()[0]; new = h + 1
        elif m[0] == "B":
            new = c.execute("update catalog_head set rev=rev+1 where id=1 returning rev").fetchone()[0]
        elif m[0] == "C":
            c.execute(f"select pg_advisory_xact_lock({KEY})"); new = c.execute("select max(rev) from schema_rev").fetchone()[0] + 1
        elif m[0] == "E":
            c.execute(f"select pg_advisory_xact_lock({KEY})"); new = c.execute("update catalog_head set rev=rev+1 where id=1 returning rev").fetchone()[0]
        else:
            new = c.execute("select max(rev) from schema_rev").fetchone()[0] + 1
        c.execute("insert into schema_rev values (%s)", (new,))
        if ddl: ddl(c)
        if hold: time.sleep(hold)
    return new

# ---------------------------------------------------------------- T1 / T2 correctness
def t_correctness(uri, iso):
    out = {}
    for m in MECH:
        c0 = setup(uri); c0.close()
        res = {}
        a = conn(uri); a.execute("set search_path=e2"); w = conn(uri); w.execute("set search_path=e2")
        if iso == "rr": w.isolation_level = IL.REPEATABLE_READ
        # a writer that began believing the head is 1 while an acceptance holds the head and has inserted rev 2
        th = threading.Thread(target=lambda: res.__setitem__("acc", acceptance(a, m, hold=0.8))); th.start(); time.sleep(0.25)
        t0 = time.perf_counter(); res["writer"] = writer_tx(w, m, 1); res["writer_waited_ms"] = round((time.perf_counter() - t0) * 1000)
        th.join(); out[m] = {"writer": res["writer"][0], "writer_saw_head": res["writer"][1], "writer_waited_ms": res["writer_waited_ms"]}
        a.close(); w.close()
        # second concurrent acceptance
        a1 = conn(uri); a1.execute("set search_path=e2"); a2 = conn(uri); a2.execute("set search_path=e2"); r2 = {}
        def acc2():
            try: r2["acc2"] = acceptance(a2, m)
            except Exception as e: r2["acc2"] = type(e).__name__
        t1 = threading.Thread(target=lambda: r2.__setitem__("acc1", acceptance(a1, m, hold=0.6))); t1.start(); time.sleep(0.2); t2 = threading.Thread(target=acc2); t2.start(); t1.join(); t2.join()
        out[m]["two_acceptances"] = r2
    return out

# ---------------------------------------------------------------- T3 throughput
def t_throughput(uri, W, secs=5.0):
    out = {}
    for m in MECH:
        setup(uri).close(); stop = threading.Event(); lat = []; lock = threading.Lock(); errs = [0]
        def w():
            c = conn(uri); c.execute("set search_path=e2"); mine = []
            while not stop.is_set():
                t0 = time.perf_counter(); o, _ = writer_tx(c, m, 1); mine.append((time.perf_counter() - t0) * 1000)
                if o not in ("write_accepted",): errs[0] += 1
            with lock: lat.extend(mine)
        ths = [threading.Thread(target=w) for _ in range(W)]; t0 = time.perf_counter(); [t.start() for t in ths]; time.sleep(secs); stop.set(); [t.join() for t in ths]
        el = time.perf_counter() - t0; out[m] = {"tps": round(len(lat) / el), **summ(lat), "non_ok": errs[0]}
    return out

# ---------------------------------------------------------------- T4 starvation of the acceptance
def t_starvation(uri, W=16, secs=14.0):
    out = {}
    for m in MECH:
        if m[0] == "D": continue
        setup(uri).close(); stop = threading.Event(); expected = [1]
        def w():
            c = conn(uri); c.execute("set search_path=e2")
            while not stop.is_set():
                o, h = writer_tx(c, m, expected[0])
                if o == "stale_detected": expected[0] = h
        ths = [threading.Thread(target=w) for _ in range(W)]; [t.start() for t in ths]; time.sleep(1.0)
        ac = conn(uri); ac.execute("set search_path=e2"); waits = []; end = time.time() + secs - 1.0; timeouts = 0
        ac.execute("set lock_timeout='5s'")
        while time.time() < end:
            t0 = time.perf_counter()
            try: new = acceptance(ac, m); expected[0] = new; waits.append((time.perf_counter() - t0) * 1000)
            except psycopg.errors.LockNotAvailable: timeouts += 1
            time.sleep(0.3)
        stop.set(); [t.join() for t in ths]
        out[m] = {"acceptances": len(waits), "lock_timeouts_5s": timeouts, "wait_ms": summ(waits), "max_ms": round(max(waits + [0]), 1)}
    return out

# ---------------------------------------------------------------- T5 partition DDL: stalls and blocking
def t_ddl(uri, variant, long_reader):
    setup(uri).close(); m = "C_advisory"; stop = threading.Event(); lat = {"reader": [], "writer": []}; lk = threading.Lock(); recs = []
    def reader():
        c = conn(uri); c.execute("set search_path=e2"); rng = random.Random()
        while not stop.is_set():
            i = rng.randrange(1, 20000); t0 = time.perf_counter(); c.execute("select v from pt where id=%s and t=%s", (i, (i % 200) + 1)).fetchone()
            with lk: recs.append(("reader", t0, (time.perf_counter() - t0) * 1000))
    def writer():
        c = conn(uri); c.execute("set search_path=e2")
        while not stop.is_set():
            t0 = time.perf_counter(); writer_tx(c, m, 1)
            with lk: recs.append(("writer", t0, (time.perf_counter() - t0) * 1000))
    def holder():  # a reader that keeps a transaction open (AccessShare on pt)
        c = conn(uri); c.execute("set search_path=e2")
        with c.transaction():
            c.execute("select count(*) from pt where t=5").fetchone(); time.sleep(2.5)
    ths = [threading.Thread(target=reader) for _ in range(4)] + [threading.Thread(target=writer) for _ in range(4)]
    [t.start() for t in ths]; time.sleep(1.5)
    if long_reader: hh = threading.Thread(target=holder); hh.start(); time.sleep(0.4)
    ac = conn(uri); ac.execute("set search_path=e2"); ac.execute("set lock_timeout='1s'"); res = {}
    def ddl(c):
        if variant == "create_partition_of": c.execute("create table pt_new partition of pt for values in (999)")
        else:
            c.execute("create table pt_new (like pt including defaults including constraints)"); c.execute("alter table pt attach partition pt_new for values in (999)")
    w0 = time.perf_counter()
    try: acceptance(ac, m, ddl=ddl); res["outcome"] = "ok"
    except psycopg.errors.LockNotAvailable: res["outcome"] = "lock_timeout_after_1s"
    w1 = time.perf_counter(); res["acceptance_ms"] = round((w1 - w0) * 1000)
    time.sleep(0.5); stop.set(); [t.join() for t in ths]
    if long_reader: hh.join()
    inw = {k: [l for (kk, t0, l) in recs if kk == k and w0 <= t0 <= w1] for k in ("reader", "writer")}
    res["reader_ops_during"] = len(inw["reader"]); res["writer_ops_during"] = len(inw["writer"])
    res["reader_max_ms"] = round(max([l for (kk, t0, l) in recs if kk == "reader" and t0 >= w0 - 0.05] + [0]), 1)
    res["writer_max_ms"] = round(max([l for (kk, t0, l) in recs if kk == "writer" and t0 >= w0 - 0.05] + [0]), 1)
    return res

# ---------------------------------------------------------------- T6 lock ordering and deadlock
def t_deadlock(uri):
    out = {}
    for order in ("lock_first", "lock_late"):
        setup(uri).close(); m = "C_advisory"; res = {}
        a = conn(uri); a.execute("set search_path=e2"); w = conn(uri); w.execute("set search_path=e2")
        a.execute("set deadlock_timeout='300ms'"); w.execute("set deadlock_timeout='300ms'")
        def acc():
            try: res["acc"] = acceptance(a, m, ddl=lambda c: c.execute("alter table obj add column z int"))   # needs ACCESS EXCLUSIVE on obj
            except Exception as e: res["acc"] = type(e).__name__
        def wr():
            try:
                with w.transaction():
                    if order == "lock_first": w.execute(f"select pg_advisory_xact_lock_shared({KEY})"); w.execute("insert into obj(v) values (1)")
                    else:
                        w.execute("insert into obj(v) values (1)"); time.sleep(0.4); w.execute(f"select pg_advisory_xact_lock_shared({KEY})")
                res["writer"] = "committed"
            except Exception as e: res["writer"] = type(e).__name__
        # writer starts first and holds RowExclusive on obj when the acceptance arrives
        tw = threading.Thread(target=wr); tw.start(); time.sleep(0.15) if order == "lock_late" else None
        ta = threading.Thread(target=acc); ta.start(); tw.join(); ta.join(); out[order] = res
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--out", default="out/e2.json"); ap.add_argument("--mechs", default=""); a = ap.parse_args()
    if a.mechs: MECH[:] = [m for m in MECH if m[0] in a.mechs.split(",")]
    srv, d = start_server(a.lib); uri = srv.get_uri(); R = {"lib": a.lib, "pg": version(conn(uri))}
    try:
        R["correctness_read_committed"] = t_correctness(uri, "rc"); print("rc", json.dumps(R["correctness_read_committed"]), flush=True)
        R["correctness_repeatable_read"] = t_correctness(uri, "rr"); print("rr", json.dumps(R["correctness_repeatable_read"]), flush=True)
        R["throughput"] = {f"W{W}": t_throughput(uri, W) for W in (1, 4, 16)}; print("tp", json.dumps(R["throughput"]), flush=True)
        R["starvation"] = t_starvation(uri); print("starve", json.dumps(R["starvation"]), flush=True)
        R["ddl"] = {f"{v}__long_reader_{lr}": t_ddl(uri, v, lr) for v in ("create_partition_of", "create_then_attach") for lr in (False, True)}; print("ddl", json.dumps(R["ddl"]), flush=True)
        R["deadlock"] = t_deadlock(uri); print("deadlock", json.dumps(R["deadlock"]), flush=True)
    finally:
        with open(a.out, "w") as f: json.dump(R, f, indent=1)
        try: srv.cleanup()
        except Exception: pass
