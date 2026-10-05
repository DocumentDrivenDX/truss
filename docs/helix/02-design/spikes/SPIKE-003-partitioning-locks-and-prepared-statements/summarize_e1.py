import json, sys
def load(p):
    try: return [json.loads(l) for l in open(p)]
    except FileNotFoundError: return []
short={"L0_flat_partial_idx":"L0 flat + partial idx/type","L1_list_per_type":"L1 partition/type","L2_flat_key_table":"L2 flat + key table","L3_hot_partitions_plus_default":"L3 20 hot parts + default"}
for p,eng in (("out/e1_pg16.jsonl","PostgreSQL 16.2"),("out/e1_pg17.jsonl","PostgreSQL 17.9")):
    rows=load(p)
    if not rows: continue
    print(f"\n######## {eng}  (200k objects, 400k edges; ms; prepared; single connection)")
    for N in sorted({r['types'] for r in rows}):
        print(f"\n--- {N} types")
        print(f"{'layout':<27}{'build s':>8}{'rels':>6}{'MB':>7} | {'plan key':>8}{'plan hop':>9} | {'readID':>11}{'keyTail':>12}{'hop1':>12}{'insObj':>12}{'insEdge':>12}{'update':>12} | {'fresh p50':>9} | {'add-type ms (5)':>26} {'wr p95 base':>11}{'during':>8}{'max':>7}")
        for r in rows:
            if r['types']!=N: continue
            L=r['latency_ms']; f=lambda k:f"{L[k]['p50']:.2f}/{L[k]['p95']:.2f}"; d=r['ddl']
            print(f"{short[r['layout']]:<27}{r['build']['build_s']:>8}{r['build']['relations']:>6}{r['build']['size_mb']:>7} | {r['plan_ms']['read_key_tail']:>8}{r['plan_ms']['hop1']:>9} | {f('read_id'):>11}{f('read_key_tail'):>12}{f('hop1'):>12}{f('insert_obj'):>12}{f('insert_edge'):>12}{f('update_props'):>12} | {r['fresh_connection_first_query_ms']['p50']:>9} | {str([int(x) for x in d['add_type_ms']]):>26} {d['writer_base']['p95']:>11}{d['writer_during_ddl']['p95']:>8}{d['writer_max_ms_overall']:>7}")
        print("   locks on object during add-type:", {short[r['layout']]:[x.replace('Lock','') for x in r['ddl']['locks_seen_on_object']] for r in rows if r['types']==N})
