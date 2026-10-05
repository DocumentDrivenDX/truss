"""E1b: questions the flat key-table layout (L2) leaves open.
 (a) maximum-multiplicity enforcement on `edge`: partial unique index per relationship vs a generic `edge_limit` table
 (b) list objects of one type, keyset paged: with and without an index on (type_id, id)
 (c) key maintenance: update of a key component, delete with the key row cascading, insert with the key row"""
import argparse, json, random, time
from common import *

def build_edge_variants(c, data, R, variant):
    if variant == "partial_idx":
        for r in range(1, R + 1): c.execute(f"create unique index lim_{r} on edge(source_id) where rel_type_id={r}")
    elif variant == "edge_limit":
        c.execute("create table edge_limit(rel_type_id int not null, side char(1) not null, endpoint_id bigint not null, edge_id bigint not null references edge(id) on delete cascade, primary key(rel_type_id, side, endpoint_id))")
        c.execute("insert into edge_limit select rel_type_id, 's', source_id, id from edge")
    c.execute("analyze edge")

def edge_ops(c, data, ops, variant, rng, used):
    def ins():
        # an edge whose (rel, source) is unused, so the limit holds
        for _ in range(50):
            r, s, t = rng.choice(data.endpoints); si = rng.choice(data.by_type[s]); ti = rng.choice(data.by_type[t])
            if (r, si) not in used: used.add((r, si)); break
        with c.transaction():
            i = c.execute("select nextval('id_seq')").fetchone()[0]
            c.execute("insert into edge(id,rel_type_id,source_id,source_type,target_id,target_type) values (%s,%s,%s,%s,%s,%s)", (i, r, si, s, ti, t))
            if variant == "edge_limit": c.execute("insert into edge_limit values (%s,'s',%s,%s)", (r, si, i))
    return ins

def run(lib, N, R, n_obj, n_edge, out):
    data = Data(N, n_obj, n_edge, n_rel=R)
    # keep (rel, source) unique so a maximum-multiplicity limit of 1 can hold for every relationship
    seen = set(); kept = []
    for e in data.edges:
        if (e[1], e[2]) in seen: continue
        seen.add((e[1], e[2])); kept.append(e)
    data.edges = kept
    res = {"lib": lib, "types": N, "rels": R, "edges_kept": len(kept)}
    for variant in ("none", "partial_idx", "edge_limit"):
        srv, d = start_server(lib); uri = srv.get_uri()
        try:
            c = conn(uri); res["pg"] = version(c); build(c, "L2_flat_key_table", data); build_edge_variants(c, data, R, variant); c.close()
            ops = Ops("L2_flat_key_table", data); rng = random.Random(3)
            c = conn(uri, prepare_threshold=0); c.execute("set search_path=s")
            e = ops.src[10]
            r = {"plan_hop1_ms": planning_ms(c, f"select t.id from edge e join object t on t.id=e.target_id and t.type_id=e.target_type where e.source_id={e[2]} and e.rel_type_id={e[1]} limit 100"),
                 "hop1_ms": summ(timed(ops.hop1, c, rng, 300, 3000))}
            used = set((e[1], e[2]) for e in data.edges)
            fn = edge_ops(c, data, ops, variant, rng, used)
            r["insert_edge_ms"] = summ(timed(lambda cc, rr: fn(), c, rng, 200, 1500))
            fc = []
            for _ in range(15):
                t0 = time.perf_counter(); cc = conn(uri, prepare_threshold=0); cc.execute("set search_path=s"); ops.hop1(cc, rng); fc.append((time.perf_counter() - t0) * 1000); cc.close()
            r["fresh_connection_first_query_ms"] = summ(fc)
            r["edge_indexes"] = c.execute("select count(*) from pg_indexes where schemaname='s' and tablename='edge'").fetchone()[0]
            res[variant] = r
        finally:
            try: srv.cleanup()
            except Exception: pass
    # (b) and (c) on a single flat key-table build
    srv, d = start_server(lib); uri = srv.get_uri()
    try:
        c = conn(uri); build(c, "L2_flat_key_table", data); c.close()
        c = conn(uri, prepare_threshold=0); c.execute("set search_path=s"); rng = random.Random(9); big = 1; small = N
        def page(t, after):
            return c.execute("select id, props::text from object where type_id=%s and id>%s order by id limit 50", (t, after)).fetchall()
        def run_pages(t, n=2000):
            xs = []; 
            for _ in range(n):
                a = rng.choice(data.by_type[t]) if rng.random() < .5 else 0
                t0 = time.perf_counter(); page(t, a); xs.append((time.perf_counter() - t0) * 1000)
            return summ(xs)
        no_idx = {"big_type": run_pages(big, 500), "small_type": run_pages(small, 500)}
        no_idx["plan_small_type"] = planning_ms(c, f"select id, props::text from object where type_id={small} and id>0 order by id limit 50")
        no_idx["plan_text"] = c.execute(f"explain select id, props::text from object where type_id={small} and id>0 order by id limit 50").fetchall()[0][0]
        t0 = time.perf_counter(); c.execute("create index object_type_id on object(type_id, id)"); idx_build = round(time.perf_counter() - t0, 2); c.execute("analyze object")
        with_idx = {"big_type": run_pages(big), "small_type": run_pages(small), "index_build_s": idx_build, "plan_small_type": planning_ms(c, f"select id, props::text from object where type_id={small} and id>0 order by id limit 50"),
                    "plan_text": c.execute(f"explain select id, props::text from object where type_id={small} and id>0 order by id limit 50").fetchall()[0][0]}
        res["list_by_type_no_index"] = no_idx; res["list_by_type_with_index"] = with_idx
        # key maintenance
        c.execute("alter table object_key add constraint object_key_fk foreign key(object_id,type_id) references object(id,type_id) on delete cascade")
        def upd_nonkey(cc, rr):
            i, t, k, n = data.objs[rr.randrange(len(data.objs))]; cc.execute("update object set props=jsonb_set(props,'{2}',to_jsonb(%s::int)), ver=ver+1 where id=%s and type_id=%s", (rr.randrange(10**6), i, t))
        def upd_key(cc, rr):
            i, t, k, n = data.objs[rr.randrange(len(data.objs))]; nk = f"u{rr.randrange(10**12)}"
            with cc.transaction():
                cc.execute("update object set props=jsonb_set(props,'{1}',to_jsonb(%s::text)), ver=ver+1 where id=%s and type_id=%s", (nk, i, t))
                cc.execute("update object_key set k=%s where object_id=%s and type_id=%s and key_id=1", (nk, i, t))
        dels = []
        def mk_del(cc, rr):
            t = rr.randrange(1, N + 1); k = f"d{rr.randrange(10**12)}"
            with cc.transaction():
                i = cc.execute("select nextval('id_seq')").fetchone()[0]
                cc.execute("insert into object(id,type_id,props) values (%s,%s,%s)", (i, t, data.props(k, 1))); cc.execute("insert into object_key values (%s,1,%s,%s)", (t, k, i)); dels.append((i, t))
        def do_del(cc, rr):
            i, t = dels.pop()
            with cc.transaction(): cc.execute("delete from object where id=%s and type_id=%s", (i, t))
        for _ in range(1600): mk_del(c, rng)
        res["key_maintenance_ms"] = {"update_non_key_prop": summ(timed(upd_nonkey, c, rng, 200, 1500)), "update_key_component": summ(timed(upd_key, c, rng, 200, 1500)),
                                     "insert_object_with_key": summ(timed(mk_del, c, rng, 100, 1200)), "delete_object_cascading_key_row": summ(timed(do_del, c, rng, 100, 1200)),
                                     "orphan_key_rows_after_deletes": c.execute("select count(*) from object_key k where not exists (select 1 from object o where o.id=k.object_id and o.type_id=k.type_id)").fetchone()[0]}
    finally:
        try: srv.cleanup()
        except Exception: pass
    print(json.dumps(res), flush=True)
    with open(out, "a") as f: f.write(json.dumps(res) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--types", type=int, default=1000); ap.add_argument("--rels", type=int, default=1000)
    ap.add_argument("--objects", type=int, default=200000); ap.add_argument("--edges", type=int, default=400000); ap.add_argument("--out", default="out/e1b.jsonl")
    a = ap.parse_args(); run(a.lib, a.types, a.rels, a.objects, a.edges, a.out)
