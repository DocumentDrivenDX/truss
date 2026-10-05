"""E4: cost of sub-graph isolation by row-level security on the adopted layout (L2) at 1,000 types and 10 sub-graphs.
Variants: none | grants only | RLS via a mapping table (type_owner) | RLS via type_def.module | RLS via a SECURITY DEFINER function.
Each op is one transaction: begin; set local role; statement; commit (the role-per-transaction pattern)."""
import argparse, json, random, time
from common import *

NSG = 10
VARIANTS = ['none', 'grants', 'mapping', 'type_def', 'function', 'layer']
def setup(c, data):
    c.execute("set search_path=s")
    c.execute("alter table type_def add column module text")
    c.execute(f"update type_def set module = 'sg' || (type_id % {NSG})")
    c.execute("create table subgraph(name text primary key, reader_role text unique, writer_role text unique)")
    c.execute("create table type_owner(type_id int primary key, sg text not null)")
    c.execute("insert into type_owner select type_id, module from type_def")
    for g in range(NSG):
        c.execute(f"drop role if exists sg{g}_r"); c.execute(f"create role sg{g}_r nologin")
        c.execute(f"drop role if exists sg{g}_w"); c.execute(f"create role sg{g}_w nologin")
        c.execute("insert into subgraph values (%s,%s,%s)", (f"sg{g}", f"sg{g}_r", f"sg{g}_w"))
    c.execute("create or replace function can_read(tid int) returns boolean language sql stable security definer set search_path=s as "
              "$$ select exists (select 1 from type_def d join subgraph s on s.name=d.module where d.type_id=tid and current_user in (s.reader_role, s.writer_role)) $$")
    c.execute("create table module_access(module text primary key, reader_role text not null, writer_role text not null)")
    c.execute("insert into module_access select name, reader_role, writer_role from subgraph")
    c.execute("create function acting_role() returns text language sql stable as $$ select coalesce(nullif(current_setting('role'),'none'), session_user)::text $$")
    c.execute("create function module_readable(m text) returns boolean language sql stable as $$ select exists (select 1 from module_access a where a.module=m and acting_role() in (a.reader_role, a.writer_role)) $$")
    c.execute("create function type_readable(t int) returns boolean language sql stable as $$ select module_readable((select d.module from type_def d where d.type_id=t)) $$")
    c.execute("analyze")

def variant(c, v):
    c.execute("set search_path=s")
    for t in ("object", "edge"): c.execute(f"alter table {t} disable row level security"); c.execute(f"drop policy if exists p on {t}")
    for g in range(NSG):
        for r in ("r", "w"):
            c.execute(f"revoke all on all tables in schema s from sg{g}_{r}"); c.execute(f"grant usage on schema s to sg{g}_{r}"); c.execute(f"grant select on object, edge to sg{g}_{r}")
            if v in ("type_def", "mapping", "layer", "layer2"): c.execute(f"grant select on type_def, subgraph, type_owner, module_access to sg{g}_{r}")
            if v == "function": c.execute(f"grant execute on function can_read(int) to sg{g}_{r}")
    if v in ("mapping", "type_def", "function", "layer", "layer2"):
        for t, col in (("object", "type_id"), ("edge", "source_type")):
            c.execute(f"alter table {t} enable row level security"); c.execute(f"alter table {t} force row level security")
            if v == "mapping":
                c.execute(f"create policy p on {t} for select using (exists (select 1 from type_owner o join subgraph s on s.name=o.sg where o.type_id={t}.{col} and current_user in (s.reader_role, s.writer_role)))")
            elif v == "layer":
                c.execute(f"create policy p on {t} for select using (type_readable({t}.{col}) and type_readable({t}.{'target_type' if t=='edge' else col}))" if t=="edge" else f"create policy p on {t} for select using (type_readable({t}.{col}))")
            elif v == "layer2":
                ex = lambda col: f"exists (select 1 from type_def d join module_access a on a.module=d.module where d.type_id={t}.{col} and acting_role() in (a.reader_role, a.writer_role))"
                c.execute(f"create policy p on {t} for select using ({ex(col)} and {ex('target_type')})" if t=="edge" else f"create policy p on {t} for select using ({ex(col)})")
            elif v == "type_def":
                c.execute(f"create policy p on {t} for select using (exists (select 1 from type_def d join subgraph s on s.name=d.module where d.type_id={t}.{col} and current_user in (s.reader_role, s.writer_role)))")
            else:
                c.execute(f"create policy p on {t} for select using (can_read({t}.{col}))")

def run(lib, N, n_obj, n_edge, out):
    data = Data(N, n_obj, n_edge); srv, d = start_server(lib); uri = srv.get_uri()
    R = {"lib": lib, "types": N, "sgs": NSG}
    try:
        c = conn(uri); R["pg"] = version(c); build(c, "L2_flat_key_table", data); setup(c, data); c.close()
        rng = random.Random(5)
        # sample records in sub-graph 3 (types with type_id % 10 == 3)
        mine = [o for o in data.objs if o[1] % NSG == 3]; rng.shuffle(mine); mine = mine[:5000]
        etypes = {}
        edges = [e for e in data.edges[:50000] if e[3] % NSG == 3] if len(data.edges[0]) > 3 else []
        small = [t for t in range(1, N + 1) if t % NSG == 3 and len(data.by_type[t]) < 500][:50]
        for v in VARIANTS:
            c = conn(uri, prepare_threshold=0); variant(c, v if v != "grants" else "grants")
            role = "sg3_r"
            def tx(sql, args):
                with c.transaction():
                    if v != "none": c.execute(f"set local role {role}")
                    return c.execute(sql, args).fetchall()
            def read_id():
                i, t, k, n = mine[rng.randrange(len(mine))]; tx("select props::text from object where id=%s and type_id=%s", (i, t))
            def list_page():
                t = small[rng.randrange(len(small))]; tx("select id from object where type_id=%s order by id limit 50", (t,))
            def hop():
                e = edges[rng.randrange(len(edges))]
                tx("select t.id from edge e join object t on t.id=e.target_id and t.type_id=e.target_type where e.source_id=%s and e.rel_type_id=%s limit 100", (e[2], e[1]))
            ops = {"read_id": read_id, "list_page_50": list_page}
            if edges: ops["hop1"] = hop
            res = {}
            for nm, fn in ops.items():
                for _ in range(300): fn()
                xs = []
                for _ in range(3000):
                    t0 = time.perf_counter(); fn(); xs.append((time.perf_counter() - t0) * 1000)
                res[nm] = summ(xs)
            # visibility check: sg3_r must see nothing of sg4
            if v in ("mapping", "type_def", "function", "layer", "layer2"):
                o = [x for x in data.objs if x[1] % NSG == 4][0]
                with c.transaction():
                    c.execute(f"set local role {role}"); res["sees_other_sg_rows"] = len(c.execute("select 1 from object where id=%s and type_id=%s", (o[0], o[1])).fetchall())
            R[v] = res; print(v, json.dumps(res), flush=True); c.close()
    finally:
        try: srv.cleanup()
        except Exception: pass
    open(out, "a").write(json.dumps(R) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--types", type=int, default=1000)
    ap.add_argument("--objects", type=int, default=200000); ap.add_argument("--edges", type=int, default=400000); ap.add_argument("--out", default="out/e4.jsonl")
    ap.add_argument("--variants", default=""); a = ap.parse_args()
    if a.variants: VARIANTS[:] = a.variants.split(",")
    run(a.lib, a.types, a.objects, a.edges, a.out)
