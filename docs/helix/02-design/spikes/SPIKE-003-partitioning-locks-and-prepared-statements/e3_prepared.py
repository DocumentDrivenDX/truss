"""E3: how much do prepared statements matter for each layout, with psycopg 3?
Modes: prep0 (prepare on first use, psycopg prepare_threshold=0), prep5 (psycopg default), none (prepare_threshold=None,
a fresh parse and plan every time, as behind a pooler that cannot keep prepared statements), client_side (ClientCursor:
parameters merged on the client). Also plan_cache_mode under prep0."""
import argparse, json, random, threading, time
import psycopg
from common import *

LAYS = ["L0_flat_partial_idx", "L1_list_per_type", "L2_flat_key_table"]
MODES = {"prep0": {"prepare_threshold": 0}, "prep5": {}, "none": {"prepare_threshold": None}, "client_side": {"cursor_factory": psycopg.ClientCursor}}
OPS_BASE = [("read_id", 2500), ("read_key_tail", 2500), ("hop1", 2500), ("insert_edge", 1200)]
SCALE = [1.0]
def ops_list(): return [(n, max(20, int(k * SCALE[0]))) for n, k in OPS_BASE]

def one(uri, ops, mode, n_each, plan_mode=None):
    c = conn(uri, **MODES[mode]); c.execute("set search_path=s")
    if plan_mode: c.execute(f"set plan_cache_mode={plan_mode}")
    rng = random.Random(5); r = {}
    for name, nn in ops_list():
        fn = getattr(ops, name); r[name] = summ(timed(fn, c, rng, 200, nn))
    r["prepared_statements_on_server"] = c.execute("select count(*) from pg_prepared_statements").fetchone()[0]
    c.close(); return r

def throughput(uri, ops, mode, name, threads=8, secs=3.0):
    stop = threading.Event(); cnt = [0] * threads
    def w(k):
        c = conn(uri, **MODES[mode]); c.execute("set search_path=s"); rng = random.Random(k); fn = getattr(ops, name)
        while not stop.is_set(): fn(c, rng); cnt[k] += 1
    ths = [threading.Thread(target=w, args=(k,)) for k in range(threads)]; [t.start() for t in ths]; time.sleep(secs); stop.set(); [t.join() for t in ths]
    return round(sum(cnt) / secs)

def run(lib, N, n_obj, n_edge, out, layouts, modes, extras):
    data = Data(N, n_obj, n_edge)
    for layout in layouts:
        srv, d = start_server(lib); uri = srv.get_uri(); R = {"lib": lib, "types": N, "layout": layout}
        try:
            c = conn(uri); R["pg"] = version(c); build(c, layout, data); c.close(); ops = Ops(layout, data)
            R["scale"] = SCALE[0]
            R["modes"] = {m: one(uri, ops, m, 0) for m in modes}
            if extras:
                R["plan_cache_mode_prep0"] = {pm: one(uri, ops, "prep0", 0, plan_mode=pm) for pm in ("auto", "force_custom_plan", "force_generic_plan")}
                R["throughput_8_threads_ops_per_s"] = {m: {nm: throughput(uri, ops, m, nm) for nm in ("read_id", "read_key_tail")} for m in ("prep0", "none")}
        finally:
            try: srv.cleanup()
            except Exception: pass
        print(json.dumps(R), flush=True)
        with open(out, "a") as f: f.write(json.dumps(R) + "\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--lib", required=True); ap.add_argument("--types", type=int, required=True)
    ap.add_argument("--objects", type=int, default=200000); ap.add_argument("--edges", type=int, default=400000); ap.add_argument("--out", default="out/e3.jsonl"); ap.add_argument("--layouts", default=",".join(LAYS)); ap.add_argument("--modes", default=",".join(MODES)); ap.add_argument("--scale", type=float, default=1.0); ap.add_argument("--no-extras", action="store_true")
    a = ap.parse_args(); SCALE[0] = a.scale; run(a.lib, a.types, a.objects, a.edges, a.out, a.layouts.split(","), a.modes.split(","), not a.no_extras)
