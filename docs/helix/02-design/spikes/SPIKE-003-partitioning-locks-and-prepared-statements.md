---
ddx:
  id: SPIKE-003
  type: tech-spike
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: SPIKE-002
      kind: informed_by
    - id: ADR-002
      kind: informs
    - id: CONTRACT-001
      kind: informs
---

# SPIKE-003: Partitioning by type, the catalog lock, and prepared statements

**Spike ID**: SPIKE-003 | **Lead**: Claude Code agent for the project owner | **Status**: Completed as evidence; decisions recorded in [ADR-002](../adr/ADR-002-storage-strategy.md) D2, D9, D10, D11 and in [CONTRACT-001](../contracts/CONTRACT-001-storage-layout.md) | **Run**: 4 October 2026

Executed evidence for three questions ADR-002 left provisional. The scripts, the layouts and the raw output are in [`SPIKE-003-partitioning-locks-and-prepared-statements/`](SPIKE-003-partitioning-locks-and-prepared-statements/) (`out/`). Spike code is throwaway evidence, not truss implementation code.

## Objective

1. **Layout.** Should each type get its own table or partition? Which layout serves a catalog that gains types without DDL? (ADR-002 D2)
2. **Catalog lock.** Is `FOR SHARE` on a catalog head row, or an advisory lock, the right way to stop a write validating against a revision that is being replaced? (ADR-002 D10)
3. **Prepared statements.** Must truss refuse deployments that cannot prepare statements? (ADR-002 D11)

## Method

- **Engines.** PostgreSQL 16.2 (`pgserver` 0.1.4, Python 3.11) and 17.9 (`pgembed` 0.2.0, Python 3.12), each a fresh embedded server per run. Both were exercised on every question. Lakebase itself was not tested.
- **Data.** 200,000 objects and 400,000 edges spread over 10, 100 and 1,000 types, generated with a fixed seed ([`common.py`](SPIKE-003-partitioning-locks-and-prepared-statements/common.py)).
- **Layouts.** L0: one `object` table with a partial index per type. L1: `object` list-partitioned by type. L2: one flat `object` table with a separate `object_key` table (the layout adopted). L3: 20 hot types in their own partitions plus a default partition.
- **Experiments.** E1 layouts ([`e1_layout.py`](SPIKE-003-partitioning-locks-and-prepared-statements/e1_layout.py)); E1b follow-ups on L2 ([`e1b_followups.py`](SPIKE-003-partitioning-locks-and-prepared-statements/e1b_followups.py)); E2 catalog-lock mechanisms A to E ([`e2_catalog_lock.py`](SPIKE-003-partitioning-locks-and-prepared-statements/e2_catalog_lock.py)); E3 prepared-statement modes ([`e3_prepared.py`](SPIKE-003-partitioning-locks-and-prepared-statements/e3_prepared.py)). Run scripts: `run_e1.sh`, `run_e1b.sh`, `run_e2_e3.sh`, `run_e2e.sh`, `run_e3_n1000.sh`.
- **Limits of the environment.** One machine (18 cores, 128 GB) under other load: endpoint-protection daemons and other sessions' PostgreSQL servers kept the load average between 7 and 15. Timings are single runs, not repeats. Treat DDL and index-build durations as upper bounds and differences under about 30% as noise. Latencies are in milliseconds on a local socket, so they exclude network time.

## Findings

### F1. Partition-per-type costs more than it saves (E1)

At 1,000 types on PostgreSQL 16.2, prepared statements, single connection:

| Layout | Plan a one-hop query | Plan a key lookup | First query on a fresh connection | Build time | Disk |
|--------|---------------------|-------------------|-----------------------------------|-----------|------|
| L0 flat, partial index per type | 107.6 ms | 104.5 ms | 99.5 ms | 30.5 s | 140 MB |
| L1 partition per type | **329.8 ms** | 0.008 ms | 5.5 ms | 13.1 s | 82.4 MB |
| L2 flat + key table | **0.039 ms** | 0.017 ms | 2.3 ms | 1.8 s | 139.3 MB |
| L3 20 hot partitions + default | 103.6 ms | 1.3 ms | 3.3 ms | 19.3 s | 82.4 MB |

- L2's planning time is independent of the number of types. L1 and L3 plan a join to `object` across every partition, and L0 plans across a thousand partial indexes. PostgreSQL 17.9 gave the same ranking (L1 329.3 ms, L2 0.041 ms).
- Fresh-connection first-query latency, which is what a host that opens connections per request pays, is 2.3 ms on L2 and 99.5 ms on L0.
- L1 reads by id degrade at 1,000 types (p95 0.75 ms against 0.02 ms on L2) and its writes show p95 up to 4.5 ms.
- **Disk.** L2 uses about 70% more space than the partitioned layouts (139.3 against 82.4 MB at 200,000 objects), because the key table is separate. That is the price of the layout, and it is recorded in ADR-013.
- At 10 types the layouts are close. The differences open up with the type count, and the catalog is expected to grow types without limit.

### F2. Adding a type takes no DDL on the flat layout (E1, E2)

- **Add a type, five times, while four writers run (PG 16.2, 1,000 types).** L2: 3, 2, 0, 0, 2 ms (catalog rows only). L1: 163, 6, 9, 25, 30 ms. L3: 29, 13, 12, 8, 85 ms. Writer p95 during the adds: L2 2.9 ms (max 16.9 ms), L1 6.1 ms (max 186 ms), L3 86 ms (max 86 ms).
- **Lock mode.** A sampler of `pg_locks` on `object` during the adds saw `AccessExclusive` on L1 and L3 and only `RowExclusive` on L2 at 100 and 1,000 types on 16.2. At 10 types, and at 1,000 types on 17.9, it also saw `Exclusive` on L2. The sampler does not say which backend held a lock, and I did not find the source. Writer latency on L2 stayed low during those adds, so no stall appeared, but the `Exclusive` samples are an **unresolved observation**.
- **Partition DDL under a long reader (E2).** `CREATE TABLE ... PARTITION OF` with a transaction holding a read lock timed out after the 1 s `lock_timeout` on both engines. Creating the table first and attaching it succeeded in 15 to 17 ms with a long reader open.
- **A default partition cannot be promoted.** Once rows sit in a default partition, a range or list partition covering them cannot be created. This is why the journal has no default partition (CONTRACT-002).

### F3. Maximum multiplicity: a table, not an index per relationship (E1b)

Edge tables at 1,000 relationships on L2, prepared on first use:

| | None | Partial unique index per relationship | `edge_limit` table |
|---|---|---|---|
| Edge indexes | 3 | 1,003 | 3 |
| Plan a one-hop query, 16.2 / 17.9 | 0.045 / 0.037 | **109 / 128** | 0.041 / 0.046 |
| Fresh connection, first query p50, 16.2 / 17.9 | 2.5 / 2.3 | **138 / 147** | 2.6 / 2.8 |
| Insert edge p50, 16.2 / 17.9 | 0.12 / 0.11 | **0.65 / 0.65** | 0.13 / 0.15 |
| One-hop read p95, 16.2 / 17.9 | 0.05 / 0.04 | 0.04 / 0.05 | **2.3 / 2.5** |

- Per-relationship partial indexes need DDL on every new relationship, which breaks F2, and their cost grows with the relationship count. At 100 relationships the three options are close.
- `edge_limit` keeps planning and inserts at baseline.
- **Unexplained.** `edge_limit` shows a one-hop p95 of 2.3 to 2.5 ms at 1,000 relationships, on both engines, while its p50 is unchanged. The mean is 0.4 ms, so a tail is affected. I did not find the cause and did not re-run it.

### F4. A `(type_id, id)` index is needed to list one type (E1b)

Keyset pages of 50 objects, 16.2 / 17.9:

| | Small type | Big type |
|---|---|---|
| Without the index | 1.6 / 1.9 ms | 0.08 / 0.06 ms |
| With the index | 0.026 / 0.033 ms | 0.043 / 0.049 ms |

Building it took 0.06 to 0.23 s at 200,000 objects. The layout includes it.

### F5. Key maintenance is cheap, except changing a key component (E1b)

| Operation (L2, 16.2 / 17.9) | p50 | p95 |
|---|---|---|
| Update a non-key property | 0.043 / 0.054 | 0.070 / 0.069 |
| Insert an object with a key | 0.099 / 0.098 | 0.140 / 0.150 |
| Delete (key row cascades) | 0.088 / 0.103 | 0.219 / 0.319 |
| Update a key component | 0.523 / 0.572 | 2.517 / 2.647 |

No orphan key rows were left after the deletes. A key-component update costs about ten times a plain update.

### F6. The catalog lock: an in-place head row is correct, an advisory queue in front of it is fair (E2)

Mechanisms: **A** `FOR SHARE` on a new head row inserted per revision; **B** `FOR SHARE` on a single head row updated in place; **C** advisory lock only; **D** no lock; **E** advisory lock then B.

| | A | B | C | D | E |
|---|---|---|---|---|---|
| Stale write detected, READ COMMITTED | no | yes | yes | no | yes |
| Stale write detected, REPEATABLE READ | no | `serialization_failure` | **no** | no | `serialization_failure` |
| Two simultaneous acceptances | second fails (unique violation) | serialized | serialized | second fails | serialized |
| Acceptances in 5 s under 16 continuous writers, 16.2 / 17.9 | 5 / 9 | 4 / 3 | 42 / 41 | not run | 42 / 42 |
| Acceptance wait max, 16.2 / 17.9 | 6.2 s / 5.5 s | 5.1 s / 11.4 s | 34 ms / 192 ms | not run | 45 ms / 22 ms |
| Writer throughput at 16 writers, 16.2 | 3.5k | 3.6k | 3.5k | 4.8k | 3.4k |

- **A** locks a stale row (each revision creates a new one), so it accepts a stale write. **C** takes its snapshot before the lock wait, so under REPEATABLE READ a writer that waited still validates against the old revision.
- **B** is correct under both isolation levels. Its cost is starvation: new writers join the share lock while an acceptance waits, so acceptances take seconds under sustained write load.
- **E** keeps B's correctness and queues acceptances fairly. It costs one more lock call per write, a 6 to 25% throughput reduction across the runs; the spread is wide because of the noise above.
- A, B and C reach about the same throughput at 16 writers; D, with no lock at all, is higher (4.8k against 3.5k to 3.6k). The E column was measured in a later run, alongside its own B (4.2k) and C (3.2k), so compare E with those, not with the first run's figures. The acceptance counts and waits for B, C and E come from that later run; A's come from the first.
- The deadlock test (acceptance with DDL against a writer that locks late) deadlocked, but this layout never runs DDL during a revision, so it does not apply.
- **Not run:** a mixed deployment where some writers use E and others B. I expect it to serialize through the head row, from the lock modes, but did not test it.

### F7. Prepared statements are not required on the flat layout (E3)

Point reads and edge operations at 1,000 types on L2, ms, p50, PostgreSQL 16.2 (17.9 within noise):

| Mode | Read by id | Read by key | One hop | Insert edge |
|---|---|---|---|---|
| Prepared on first use | 0.017 | 0.021 | 0.028 | 0.080 |
| Prepared after five uses | 0.015 | 0.020 | 0.028 | 0.080 |
| Never prepared | 0.025 | 0.047 | 0.077 | 0.091 |
| Client-side binding | 0.023 | 0.044 | 0.074 | 0.087 |

- Forcing generic plans costs nothing (`force_generic_plan` equals `auto`); forcing custom plans equals never preparing.
- Eight-thread throughput: about 22k reads per second prepared and 20 to 21k unprepared.
- On **L0** at 1,000 types an unprepared read took 86 to 92 ms, and a key lookup took 88 to 92 ms even when prepared on first use, because a generic plan cannot use per-type partial indexes (50-operation samples). On **L1** with prepared statements, reads were 0.05 to 0.4 ms in samples of 50 operations; I did not measure L1 unprepared beyond that sample.
- The earlier rule to refuse deployments that cannot prepare came from L0-shaped data. On L2 the penalty is 0.01 to 0.05 ms per operation.

## Decisions

| Question | Decision | Recorded in |
|----------|----------|-------------|
| Layout | One `object` table, a separate `object_key` table, no per-type DDL | ADR-002 D2; CONTRACT-001 |
| Maximum multiplicity | `edge_limit` table, no per-relationship index | ADR-002 D9; CONTRACT-001 |
| List one type | Keep the `(type_id, id)` index | CONTRACT-001 |
| Catalog lock | Single in-place head row, `FOR SHARE` for writers, `FOR UPDATE` for acceptance; an advisory queue in front is optional | ADR-002 D10; CONTRACT-001, 003, 004 |
| Prepared statements | Recommended, not required; adapters report whether they prepare | ADR-002 D11; CONTRACT-001, 004 |
| Journal | Range partitions by time, no default partition | CONTRACT-002 |

## Open points

- The `Exclusive` lock sampled on `object` during L2 type adds (F2) is unattributed.
- The `edge_limit` read tail at 1,000 relationships (F3) is unexplained.
- A mixed E and B deployment (F6) is untested.
- Everything ran on embedded PostgreSQL 16.2 and 17.9 on one noisy machine, over a local socket, without a pooler, and on neither Lakebase nor PostgreSQL 18. Latency targets for a hosted deployment need a rerun there.
- L1 unprepared performance beyond a 50-operation sample was not measured.

## Reproduce

```bash
cd docs/helix/02-design/spikes/SPIKE-003-partitioning-locks-and-prepared-statements
./run_e1.sh && ./run_e2_e3.sh && ./run_e1b.sh && ./run_e2e.sh && ./run_e3_n1000.sh
python summarize_e1.py
```

Each script starts its own embedded server with `uv run --with pgserver` or `--with pgembed` and writes to `out/`. Run them one at a time on a quiet machine.
