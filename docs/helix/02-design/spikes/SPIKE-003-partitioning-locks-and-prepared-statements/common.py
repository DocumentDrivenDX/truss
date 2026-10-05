"""SPIKE-003 shared harness (throwaway). Starts an embedded PostgreSQL, builds layout alternatives, runs workloads.
Run with: uv run --python 3.11 --with pgserver --with 'psycopg[binary]' python e1_layout.py --lib pgserver ...
          uv run --python 3.12 --with pgembed  --with 'psycopg[binary]' python e1_layout.py --lib pgembed ...
"""
import json, math, random, statistics, tempfile, time, shutil, sys, threading
import psycopg

def start_server(lib):
    d = tempfile.mkdtemp(prefix="spike3-")
    srv = __import__(lib).get_server(d, cleanup_mode="delete")
    return srv, d

def conn(uri, **kw):
    kw.setdefault("autocommit", True)
    return psycopg.connect(uri, **kw)

def pct(xs, p):
    if not xs: return float("nan")
    xs = sorted(xs); k = max(0, min(len(xs) - 1, math.ceil(p / 100 * len(xs)) - 1)); return xs[k]

def summ(xs):
    return {"n": len(xs), "p50": round(pct(xs, 50), 3), "p95": round(pct(xs, 95), 3), "p99": round(pct(xs, 99), 3),
            "mean": round(statistics.fmean(xs), 3) if xs else None}

def version(c): return c.execute("select current_setting('server_version')").fetchone()[0]

# ---------------------------------------------------------------- data
def zipf_counts(n_types, total, s=1.1, base=5):
    w = [1 / (i ** s) for i in range(1, n_types + 1)]; sw = sum(w); rest = total - base * n_types
    c = [base + int(rest * x / sw) for x in w]; c[0] += total - sum(c); return c   # type 1 is the biggest

class Data:
    def __init__(self, n_types, n_obj, n_edge, seed=7, n_rel=30):
        rng = random.Random(seed); self.N = n_types
        counts = zipf_counts(n_types, n_obj); self.counts = counts
        items = [(t + 1, i) for t in range(n_types) for i in range(counts[t])]
        rng.shuffle(items)
        self.objs = []            # (id, type, key, intval)
        self.by_type = {t: [] for t in range(1, n_types + 1)}
        for idx, (t, i) in enumerate(items, start=1):
            self.objs.append((idx, t, f"k{t}-{i}", i)); self.by_type[t].append(idx)
        self.n_obj = n_obj
        pop = list(range(1, n_types + 1)); wts = counts
        self.endpoints = []       # (rel, src_type, tgt_type)
        for r in range(1, n_rel + 1):
            for _ in range(3):
                s = rng.choices(pop, wts)[0]; t = rng.choices(pop, wts)[0]; self.endpoints.append((r, s, t))
        self.endpoints = sorted(set(self.endpoints))
        self.edges = []           # (id, rel, s_id, s_type, t_id, t_type)
        eid = n_obj
        for _ in range(n_edge):
            r, s, t = rng.choice(self.endpoints); eid += 1
            self.edges.append((eid, r, rng.choice(self.by_type[s]), s, rng.choice(self.by_type[t]), t))
        self.next_id = eid + 1
        self.rng = rng
    def props(self, key, i):
        return json.dumps({"1": key, "2": i, "3": "x" * 60 + key})

LAYOUTS = ["L0_flat_partial_idx", "L1_list_per_type", "L2_flat_key_table", "L3_hot_partitions_plus_default"]
HOT = 20

def build(c, layout, data, log=print):
    """Create tables, bulk load, then indexes and foreign keys, ANALYZE. Returns timings."""
    t0 = time.perf_counter(); N = data.N; T = {}
    c.execute("create schema if not exists s"); c.execute("set search_path=s")
    c.execute("create table type_def(type_id int primary key)")
    c.execute("create table rel_endpoint(rel_type_id int, source_type int, target_type int, primary key(rel_type_id, source_type, target_type))")
    c.execute("create sequence id_seq")
    hot = set(range(1, min(HOT, N) + 1))
    if layout == "L1_list_per_type":
        c.execute("create table object(id bigint not null, type_id int not null, props jsonb not null, ver bigint not null default 1, primary key(id,type_id)) partition by list(type_id)")
        for t in range(1, N + 1):
            c.execute(f"create table object_t{t} partition of object for values in ({t})")
    elif layout == "L3_hot_partitions_plus_default":
        c.execute("create table object(id bigint not null, type_id int not null, props jsonb not null, ver bigint not null default 1, primary key(id,type_id)) partition by list(type_id)")
        c.execute("create table object_default partition of object default")
        for t in sorted(hot): c.execute(f"create table object_t{t} partition of object for values in ({t})")
    else:
        c.execute("create table object(id bigint not null, type_id int not null, props jsonb not null, ver bigint not null default 1, primary key(id,type_id))")
    if layout == "L2_flat_key_table":
        c.execute('create table object_key(type_id int not null, key_id smallint not null, k text collate "C" not null, object_id bigint not null, primary key(type_id,key_id,k))')
    c.execute("create table edge(id bigint primary key, rel_type_id int not null, source_id bigint not null, source_type int not null, target_id bigint not null, target_type int not null, props jsonb not null default '{}', ver bigint not null default 1)")
    for t in range(1, N + 1): c.execute("insert into type_def values (%s)", (t,))
    with c.cursor().copy("copy rel_endpoint from stdin") as cp:
        for e in data.endpoints: cp.write_row(e)
    t1 = time.perf_counter()
    with c.cursor().copy("copy object(id,type_id,props) from stdin") as cp:
        for (i, t, k, n) in data.objs: cp.write_row((i, t, data.props(k, n)))
    if layout == "L2_flat_key_table":
        with c.cursor().copy("copy object_key from stdin") as cp:
            for (i, t, k, n) in data.objs: cp.write_row((t, 1, k, i))
    with c.cursor().copy("copy edge(id,rel_type_id,source_id,source_type,target_id,target_type) from stdin") as cp:
        for e in data.edges: cp.write_row(e)
    T["load_s"] = round(time.perf_counter() - t1, 2)
    t2 = time.perf_counter()
    # key indexes per layout
    if layout == "L0_flat_partial_idx":
        for t in range(1, N + 1): c.execute(f'create unique index k_{t} on object ((props->>\'1\') collate "C") where type_id={t}')
    elif layout == "L1_list_per_type":
        for t in range(1, N + 1): c.execute(f'create unique index k_{t} on object_t{t} ((props->>\'1\') collate "C")')
    elif layout == "L3_hot_partitions_plus_default":
        for t in sorted(hot): c.execute(f'create unique index k_{t} on object_t{t} ((props->>\'1\') collate "C")')
        for t in range(1, N + 1):
            if t not in hot: c.execute(f'create unique index k_{t} on object_default ((props->>\'1\') collate "C") where type_id={t}')
    c.execute("create index edge_out on edge(source_id, rel_type_id) include (target_id, target_type)")
    c.execute("create index edge_in on edge(target_id, rel_type_id) include (source_id, source_type)")
    T["index_s"] = round(time.perf_counter() - t2, 2)
    t3 = time.perf_counter()
    c.execute("alter table object add constraint object_type_fk foreign key(type_id) references type_def(type_id)")
    c.execute("alter table edge add constraint edge_source_fk foreign key(source_id,source_type) references object(id,type_id) on delete restrict")
    c.execute("alter table edge add constraint edge_target_fk foreign key(target_id,target_type) references object(id,type_id) on delete restrict")
    c.execute("alter table edge add constraint edge_ep_fk foreign key(rel_type_id,source_type,target_type) references rel_endpoint")
    T["fk_s"] = round(time.perf_counter() - t3, 2)
    c.execute(f"select setval('id_seq', {data.next_id})"); c.execute("analyze")
    T["build_s"] = round(time.perf_counter() - t0, 2)
    T["relations"] = c.execute("select count(*) from pg_class where relnamespace='s'::regnamespace").fetchone()[0]
    T["indexes_on_object_tree"] = c.execute("select count(*) from pg_index i join pg_class r on r.oid=i.indrelid where r.relnamespace='s'::regnamespace and (r.relname like 'object%')").fetchone()[0]
    T["size_mb"] = round(float(c.execute("select sum(pg_total_relation_size(oid)) from pg_class where relnamespace='s'::regnamespace and relkind in ('r','p','m') and not relispartition").fetchone()[0]) / 1048576, 1)
    return T

# ---------------------------------------------------------------- operations
class Ops:
    """Operations for a layout. Each returns a callable(rng) -> None that executes one op on cursor `cur`."""
    def __init__(self, layout, data):
        self.layout = layout; self.d = data; self.tail = [t for t in range(1, data.N + 1) if t > HOT] or [1]
        self.src = [e for e in data.edges[:50000]]
    def read_id(self, cur, rng):
        i, t, k, n = self.d.objs[rng.randrange(len(self.d.objs))]
        cur.execute("select props::text from object where id=%s and type_id=%s", (i, t)).fetchone()
    def read_key(self, cur, rng, tail=False):
        if tail:
            t = rng.choice(self.tail); i = rng.choice(self.d.by_type[t]); o = self.d.objs[i - 1]; _, t, k, n = o
        else:
            i, t, k, n = self.d.objs[rng.randrange(len(self.d.objs))]
        if self.layout == "L2_flat_key_table":
            cur.execute("select o.id, o.props::text from object_key ok join object o on o.id=ok.object_id and o.type_id=ok.type_id where ok.type_id=%s and ok.key_id=1 and ok.k=%s", (t, k)).fetchone()
        else:
            cur.execute('select id, props::text from object where type_id=%s and (props->>\'1\') collate "C" = %s', (t, k)).fetchone()
    def read_key_tail(self, cur, rng): self.read_key(cur, rng, tail=True)
    def hop1(self, cur, rng):
        e = self.src[rng.randrange(len(self.src))]
        cur.execute("select t.id, t.props::text from edge e join object t on t.id=e.target_id and t.type_id=e.target_type where e.source_id=%s and e.rel_type_id=%s limit 100", (e[2], e[1])).fetchall()
    def insert_obj(self, cur, rng, t=None):
        t = t or rng.randrange(1, self.d.N + 1); n = rng.randrange(10**9); k = f"w{n}-{rng.randrange(10**9)}"
        with cur.connection.transaction():
            i = cur.execute("select nextval('id_seq')").fetchone()[0]
            cur.execute("insert into object(id,type_id,props) values (%s,%s,%s)", (i, t, self.d.props(k, n)))
            if self.layout == "L2_flat_key_table":
                cur.execute("insert into object_key values (%s,1,%s,%s)", (t, k, i))
    def insert_edge(self, cur, rng):
        r, s, t = rng.choice(self.d.endpoints); si = rng.choice(self.d.by_type[s]); ti = rng.choice(self.d.by_type[t])
        with cur.connection.transaction():
            i = cur.execute("select nextval('id_seq')").fetchone()[0]
            cur.execute("insert into edge(id,rel_type_id,source_id,source_type,target_id,target_type) values (%s,%s,%s,%s,%s,%s)", (i, r, si, s, ti, t))
    def update_props(self, cur, rng):
        i, t, k, n = self.d.objs[rng.randrange(len(self.d.objs))]
        cur.execute("update object set props=jsonb_set(props,'{2}',to_jsonb(%s::int)), ver=ver+1 where id=%s and type_id=%s", (rng.randrange(10**6), i, t))

def timed(fn, cur, rng, warm, n):
    for _ in range(warm): fn(cur, rng)
    xs = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(cur, rng); xs.append((time.perf_counter() - t0) * 1000)
    return xs

def planning_ms(c, sql, runs=25):
    xs = []
    for _ in range(runs):
        rows = c.execute("explain (summary, costs off) " + sql).fetchall()
        for (l,) in rows:
            if l.startswith("Planning Time"): xs.append(float(l.split()[2]))
    return round(statistics.median(xs), 3)
