#!/usr/bin/env python3
"""Summarize latency runs: median over repetitions of p50/p95 per query and option, C/A ratios vs the 2x target."""
import os, re, statistics, glob
here = os.path.dirname(os.path.abspath(__file__)); out = os.path.join(here, '..', 'out')
for f in sorted(glob.glob(os.path.join(out, '51_latency_*.txt'))):
    rows = {}
    for line in open(f):
        m = re.match(r'^([ac])_(\S+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)', line)
        if m: rows.setdefault((m[1], m[2]), []).append((float(m[4]), float(m[5])))
    print(f'== {os.path.basename(f)}: median of per-run p50 / p95 (ms); ratio = C / A')
    print(f'{"shape":22} {"A p50":>7} {"A p95":>7} {"C p50":>7} {"C p95":>7} {"p50 C/A":>8} {"p95 C/A":>8}  within 2x (p95)')
    for shape in sorted({s for _, s in rows}):
        if ('a', shape) not in rows and shape.startswith('q6_update_'):
            base = ('a', 'q6_update')
        else:
            base = ('a', shape)
        if base not in rows or ('c', shape) not in rows: continue
        a50 = statistics.median(x[0] for x in rows[base]); a95 = statistics.median(x[1] for x in rows[base])
        c50 = statistics.median(x[0] for x in rows[('c', shape)]); c95 = statistics.median(x[1] for x in rows[('c', shape)])
        print(f'{shape:22} {a50:7.3f} {a95:7.3f} {c50:7.3f} {c95:7.3f} {c50/a50:8.2f} {c95/a95:8.2f}  {"yes" if c95/a95 <= 2 else "NO"}')
    print()
