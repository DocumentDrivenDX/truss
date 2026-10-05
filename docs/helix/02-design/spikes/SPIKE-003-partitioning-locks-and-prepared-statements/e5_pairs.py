"""E5: pair uniqueness of edges (same relationship, same source, same target) on the adopted layout.
Race: does a duplicate pair get committed by concurrent creates? Cost: insert latency per option.
Options: none | unique_out (the existing edge_out index made unique) | pair_table (a table with a primary key per pair, deleted with the edge) | engine_lock (lock the source object, check, insert)."""
import argparse, json, random, threading, time
from common import *

def setup(c, v):
    c.execute("set search_path=s")
    c.execute("select indexname from pg_indexes where schemaname='s' and tablename='edge'")
    idx = [r[0] for r in c.execute("select indexname from pg_indexes where schemaname='s' and tablename='edge'").fetchall()]
    c.execute("create index if not exists edge_out_t on edge(source_id, rel_type_id) include (target_id, target_type)")
    c.execute("create index if not exists edge_in_t on edge(target_id, rel_type_id) include (source_id, source_type)")
    if v == "unique_out":
        c.execute("drop index edge_out_t")
        c.execute("create unique index edge_out_u on edge(source_id, rel_type_id, target_id) include (target_type)")
    if v == "pair_table":
        c.execute("create table edge_pair(rel_type_id int not null, source_id bigint not null, target_id bigint not null, edge_id bigint not null references edge(id) on delete cascade, primary key(rel_type_id, source_id, target_id))")
        c.execute("insert into edge_pair select rel_type_id, source_id, target_id, id from edge")
    c.execute("analyze")

def create_edge(c, v, r, s, st, t, tt):
    with c.transaction():
        if v == "engine_lock":
            c.execute("select 1 from object where id=%s and type_id=%s for no key update", (s, st))
            if c.execute("select 1 from edge where source_id=%s and rel_type_id=%s and target_id=%s", (s, r, t)).fetchone(): raise ValueError("dup")
        i = c.execute("select nextval('id_seq')").fetchone()[0]
        c.execute("insert into edge(id,rel_type_id,source_id,source_type,target_id,target_type) values (%s,%s,%s,%s,%s,%s)", (i, r, s, st, t, tt))
        if v == "pair_table": c.execute("insert into edge_pair values (%s,%s,%s,%s)", (r, s, t, i))

def run(lib, N, n_obj, n_edge, out):
    data = Data(N, n_obj, n_edge); R = {"lib": lib, "types": N}
    for v in ("none", "unique_out", "pair_table", "engine_lock"):
        srv, d = start_server(lib); uri = srv.get_uri()
        try:
            c = conn(uri); R["pg"] = version(c); build(c, "L2_flat_key_table", data)
            # unique_out needs the loaded edges to be pair-unique already; drop duplicates the generator made
            c.execute("set search_path=s")
            c.execute("delete from edge a using edge b where a.id>b.id and a.rel_type_id=b.rel_type_id and a.source_id=b.source_id and a.target_id=b.target_id")
            setup(c, v); c.close()
            rng = random.Random(11); c = conn(uri, prepare_threshold=0); c.execute("set search_path=s")
            known = set((e[1], e[2], e[4]) for e in c.execute("select id, rel_type_id, source_id, source_type, target_id, target_type from edge").fetchall() and [])
            xs = []; t_end = 0
            for n in range(2200):
                r, s, t = rng.choice(data.endpoints); si = rng.choice(data.by_type[s]); ti = rng.choice(data.by_type[t])
                t0 = time.perf_counter()
                try: create_edge(c, v, r, si, s, ti, t); ok = True
                except Exception: ok = False
                if ok and n >= 200: xs.append((time.perf_counter() - t0) * 1000)
            R[v] = {"insert_edge_ms": summ(xs)}
            # the race: two connections create the same new pair at the same moment, 300 times
            dup = 0; refused = 0
            a, b = conn(uri), conn(uri); a.execute("set search_path=s"); b.execute("set search_path=s")
            for k in range(300):
                r, s, t = rng.choice(data.endpoints); si = rng.choice(data.by_type[s]); ti = rng.choice(data.by_type[t])
                bar = threading.Barrier(2); res = []
                def w(cc):
                    bar.wait()
                    try: create_edge(cc, v, r, si, s, ti, t); res.append("ok")
                    except Exception: res.append("refused")
                th = [threading.Thread(target=w, args=(a,)), threading.Thread(target=w, args=(b,))]
                [x.start() for x in th]; [x.join() for x in th]
                n = c.execute("select count(*) from edge where rel_type_id=%s and source_id=%s and target_id=%s", (r, si, ti)).fetchone()[0]
                if n > 1: dup += 1
                refused += res.count("refused")
            R[v]["race_pairs_with_duplicate_edges_of_300"] = dup; R[v]["race_refusals"] = refused
            print(v, json.dumps(R[v]), flush=True)
        finally:
            try: srv.cleanup()
            except Exception: pass
    open(out, "a").write(json.dumps(R) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--types", type=int, default=1000)
    ap.add_argument("--objects", type=int, default=200000); ap.add_argument("--edges", type=int, default=400000); ap.add_argument("--out", default="out/e5.jsonl")
    a = ap.parse_args(); run(a.lib, a.types, a.objects, a.edges, a.out)
