"""E1: is a partition per type a good layout? Builds four layouts at N types and measures plan time, latency,
fresh-connection cost, DDL to add a type, and writer stalls during that DDL."""
import argparse, json, random, threading, time, sys, os
from common import *

def run(lib, N, n_obj, n_edge, layouts, out):
    results = []
    data = Data(N, n_obj, n_edge)
    for layout in layouts:
        srv, d = start_server(lib); uri = srv.get_uri(); r = {"lib": lib, "types": N, "layout": layout, "objects": n_obj, "edges": n_edge}
        try:
            c = conn(uri); r["pg"] = version(c)
            r["build"] = build(c, layout, data); c.close()
            ops = Ops(layout, data); rng = random.Random(11)
            c = conn(uri, prepare_threshold=0); c.execute("set search_path=s"); cur = c
            i, t, k, n = data.objs[len(data.objs) // 3]
            tt = ops.tail[len(ops.tail) // 2]; tk = data.objs[data.by_type[tt][0] - 1]
            e = ops.src[10]
            plans = {"read_id": f"select props::text from object where id={i} and type_id={t}",
                     "hop1": f"select t.id from edge e join object t on t.id=e.target_id and t.type_id=e.target_type where e.source_id={e[2]} and e.rel_type_id={e[1]} limit 100",
                     "insert_obj": f"insert into object(id,type_id,props) values (9999999999,{tt},'{{}}')"}
            if layout == "L2_flat_key_table":
                plans["read_key_tail"] = f"select o.id from object_key ok join object o on o.id=ok.object_id and o.type_id=ok.type_id where ok.type_id={tk[1]} and ok.key_id=1 and ok.k='{tk[2]}'"
            else:
                plans["read_key_tail"] = f"select id from object where type_id={tk[1]} and (props->>'1') collate \"C\" = '{tk[2]}'"
            r["plan_ms"] = {k_: planning_ms(c, v) for k_, v in plans.items()}
            lat = {}
            for name, fn, nn in [("read_id", ops.read_id, 3000), ("read_key", ops.read_key, 3000), ("read_key_tail", ops.read_key_tail, 3000),
                                 ("hop1", ops.hop1, 3000), ("insert_obj", ops.insert_obj, 1500), ("insert_edge", ops.insert_edge, 1500), ("update_props", ops.update_props, 1500)]:
                lat[name] = summ(timed(fn, cur, rng, 300, nn))
            r["latency_ms"] = lat
            fc = []
            for _ in range(15):
                t0 = time.perf_counter(); cc = conn(uri, prepare_threshold=0); cc.execute("set search_path=s"); ops.read_id(cc, rng); fc.append((time.perf_counter() - t0) * 1000); cc.close()
            r["fresh_connection_first_query_ms"] = summ(fc)
            r["ddl"] = ddl_test(uri, layout, data, ops, N)
            c.close()
        finally:
            try: srv.cleanup()
            except Exception: pass
        results.append(r); print(json.dumps(r), flush=True)
        with open(out, "a") as f: f.write(json.dumps(r) + "\n")
    return results

def add_type(c, layout, T, mode="default"):
    t0 = time.perf_counter()
    c.execute("insert into type_def values (%s)", (T,))
    if layout == "L0_flat_partial_idx":
        c.execute(f'create unique index concurrently k_{T} on object ((props->>\'1\') collate "C") where type_id={T}')
    elif layout in ("L1_list_per_type", "L3_hot_partitions_plus_default"):
        c.execute(f"create table object_t{T} partition of object for values in ({T})")
        c.execute(f'create unique index k_{T} on object_t{T} ((props->>\'1\') collate "C")')
    return (time.perf_counter() - t0) * 1000

def ddl_test(uri, layout, data, ops, N):
    stop = threading.Event(); recs = []; lock = threading.Lock(); modes = set()
    def writer(seed):
        cc = conn(uri, prepare_threshold=0); cc.execute("set search_path=s"); rng = random.Random(seed)
        while not stop.is_set():
            t0 = time.perf_counter()
            try: ops.insert_obj(cc, rng, t=rng.randrange(1, N + 1))
            except Exception as ex:
                with lock: recs.append((t0, -1.0))
                continue
            with lock: recs.append((t0, (time.perf_counter() - t0) * 1000))
    def sampler():
        sc = conn(uri)
        while not stop.is_set():
            for (m,) in sc.execute("select mode from pg_locks l join pg_class c on c.oid=l.relation where c.relname='object' and c.relnamespace='s'::regnamespace and l.pid<>pg_backend_pid()").fetchall(): modes.add(m)
            time.sleep(0.004)
    ths = [threading.Thread(target=writer, args=(s,)) for s in range(4)] + [threading.Thread(target=sampler)]
    [t.start() for t in ths]; time.sleep(3.0)
    mc = conn(uri); mc.execute("set search_path=s"); windows = []; durs = []
    for j in range(5):
        T = N + 1 + j; w0 = time.perf_counter(); d = add_type(mc, layout, T); windows.append((w0, time.perf_counter())); durs.append(round(d, 1)); time.sleep(1.0)
    stop.set(); [t.join() for t in ths]
    base = [l for (t0, l) in recs if t0 < windows[0][0] and l >= 0]
    inwin = [l for (t0, l) in recs if any(a <= t0 <= b for a, b in windows) and l >= 0]
    errs = sum(1 for (_, l) in recs if l < 0)
    return {"add_type_ms": durs, "locks_seen_on_object": sorted(modes), "writer_base_ops": len(base), "writer_base": summ(base),
            "writer_during_ddl": summ(inwin), "writer_max_ms_overall": round(max([l for (_, l) in recs] + [0]), 1), "writer_errors": errs}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--types", type=int, required=True)
    ap.add_argument("--objects", type=int, default=200000); ap.add_argument("--edges", type=int, default=400000)
    ap.add_argument("--layouts", default=",".join(LAYOUTS)); ap.add_argument("--out", default="out/e1.jsonl")
    a = ap.parse_args(); run(a.lib, a.types, a.objects, a.edges, a.layouts.split(","), a.out)
