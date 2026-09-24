---
ddx:
  id: SPIKE-001
  type: tech-spike
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.component-profile-apache-age
      kind: informed_by
    - id: truss.concerns
      kind: informed_by
    - id: truss.product-vision
      kind: informed_by
---

# SPIKE-001: Apache AGE 1.8.0 on PostgreSQL 18 against truss's required capabilities

Executed evidence for bake-off option B. Everything here was run on
2026-09-24 in a single cloud sandbox; the documentation-based assessment is in
[component-profile-apache-age.md](../../00-discover/component-profile-apache-age.md) and is not repeated as evidence here. Each
finding quotes raw output from [`SPIKE-001-apache-age/out/`](SPIKE-001-apache-age/out/); scripts are in [`SPIKE-001-apache-age/`](SPIKE-001-apache-age/).

## Objective

Settle, by running AGE, the capabilities the public record left Unknown or
only described (C1–C12 of the profile), with emphasis on value fidelity (C2,
C3, C8), database enforcement under Cypher writes (C4), index use (C5),
concurrency (C7), the TypeScript read path (C9), plain-SQL conversion (C10) and
an indicative latency comparison with a hand-designed schema (C12).

Time box: 45 minutes of setup; actual setup took about 5 minutes (PostgreSQL
and AGE built from source in 2 min 18 s, cluster initialised in under a
minute). All tests and the write-up fit inside the session.

## Hypothesis

H1. AGE stores truss's scalar values exactly and keeps absent distinct from
null. H2. PostgreSQL constraints on AGE label tables are honoured by Cypher
writes. H3. The planner uses property indexes for Cypher predicates. H4.
Concurrent Cypher writes behave like ordinary PostgreSQL updates (no lost
updates, waits instead of errors at READ COMMITTED). H5. Fetch and one-to-three
hop traversal stay within 2× p95 of a hand-designed relational schema.

## Approach

Environment (raw: `out/00_environment.txt`):

| Item | Value |
|------|-------|
| OS / kernel | Ubuntu 24.04.4 LTS, Linux 6.18.44 |
| Hardware | 4 vCPU "Intel(R) Xeon(R) Processor @ 2.80GHz", 16 GB RAM, shared cloud VM |
| PostgreSQL | 18.6 built from GitHub mirror tag `REL_18_6` (commit `724edf9`), gcc 13.3.0, `--without-icu`, locale `C.UTF-8`, `shared_buffers=1GB`, `work_mem=64MB`, `shared_preload_libraries='age'` |
| Apache AGE | tag `PG18/v1.8.0-rc0` (commit `e43dc1a`, 2026-07-07), `extversion` 1.8.0 |
| PG 19 check | PostgreSQL 19beta4 (`REL_19_BETA4`, commit `b73d13c`) with AGE tag `PG19/v1.8.0-rc0` (commit `d03d1cb`) |
| Clients | Node 22.22.2 with `pg` 8.23.0 and AGE's `pg-age` 1.0.0-alpha built from the tag; Bun 1.3.11 (`pg` and `Bun.sql`) |

Why built from source: `apt.postgresql.org`, `postgresql.org` and
`age.apache.org` were blocked by the sandbox egress proxy (HTTP 403 on
CONNECT); the Ubuntu archive and `git` over github.com worked. The runtime copy
of the build sits in `/var/lib/postgresql/age-spike` because the sandbox's
working directory was not traversable by the `postgres` OS user. Raw outputs
were captured there verbatim, so psql error prefixes in `out/*.txt` show the
original sandbox paths.

Method: SQL scripts run through `psql -e` with errors recorded rather than
stopping; each value probe writes through Cypher and reads back both through
Cypher and as the raw `properties::text` of the label table. Concurrency uses
parallel `psql` sessions. Latency uses `pgbench` (single client, simple query
protocol for both systems, random start key per transaction, warm-up
discarded, per-transaction logs for percentiles).

Reproduce: `SPIKE-001-apache-age/build/build.sh`, then initialise a cluster as described
above, then `SPIKE-001-apache-age/run_all.sh` (writes `out/*.txt`). Scripts resolve
paths relative to their own location; `PGRT` in `env.sh` names the runtime directory.

## Findings

Status words: **confirmed** (the spike shows the capability as the row
defines it), **contradicted**, **partial** (some parts hold, some fail).
"Desk status" is the profile's status from the public record.

### C1. PostgreSQL 17/18, path to 19, managed services

Run: built AGE `PG18/v1.8.0-rc0` against PostgreSQL 18.6 and AGE
`PG19/v1.8.0-rc0` against PostgreSQL 19beta4; smoke test on 19
(`out/13_pg19_smoke.txt`). PostgreSQL 17 was not built. Managed services cannot
be tested from a sandbox.

```
PostgreSQL 19beta4 on x86_64-pc-linux-gnu, compiled by gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0, 64-bit
CREATE EXTENSION
 extversion
 1.8.0
SELECT * FROM cypher('smoke', $$ MATCH (a:P {n: 1})-[:K*1..2]->(x) RETURN x.n ORDER BY x.n $$) AS (n agtype);
 2
 3
SELECT * FROM cypher('smoke', $$ MERGE (p:P {n: 9}) ON CREATE SET p.created = true RETURN properties(p) $$) AS (p agtype);
 {"n": 9, "created": true}
```

Result: 18.6 works; the unreleased PG19 branch builds and passes a smoke test
on 19beta4 (not its regression suite). Managed availability untested. Desk
status Unknown → still **Unknown** (self-hosted 18 and a 19 path confirmed;
managed coverage not testable here).

### C2. Exact storage of the nine scalar families

Run: `sql/01_types_nulls.sql` → `out/01_types_nulls.txt`.

Integers store exactly at both int64 bounds:

```
 {"k": "int", "max": 9223372036854775807, "min": -9223372036854775808}
```

but a literal just outside the range silently becomes a float, and integer
arithmetic silently wraps on overflow (PostgreSQL's own `bigint` errors):

```
SELECT * FROM cypher('fid', $$ RETURN 9223372036854775808 $$) ...        -> 9.223372036854776e+18
... RETURN n.max + 1 ...   -> -9223372036854775808
... RETURN n.max * 2 ...   -> -2
... RETURN n.min - 1 ...   -> 9223372036854775807
... RETURN -n.min ...      -> -9223372036854775808
... SET n.wrapped = n.max + 1 RETURN n.wrapped  -> -9223372036854775808   (stored)
SELECT 9223372036854775807::bigint + 1;  -> ERROR:  bigint out of range
... RETURN toInteger('9223372036854775808') ... -> 9223372036854775807    (clamped)
```

Exact decimals: a Cypher numeric literal is parsed as a float before the
`::numeric` annotation applies, so precision and scale are lost silently;
only a string cast or an annotated parameter keeps them:

```
CREATE (n:V {k:'dec', d_num: 12345678901234567890.123456789::numeric, s_num: 0.10::numeric, s_num2: 1.500::numeric})
 -> d_num 12345678901234600000::numeric | s_num 0.1::numeric | s_num2 1.5::numeric
RETURN '12345678901234567890.123456789'::numeric, '0.10'::numeric
 -> 12345678901234567890.123456789::numeric | 0.10::numeric
EXECUTE put_dec('{"d": 12345678901234567890.123456789, "s": 0.10}')                    -> 1.2345678901234567e+19 | 0.1
EXECUTE put_dec('{"d": 12345678901234567890.123456789::numeric, "s": 0.10::numeric}')  -> 12345678901234567890.123456789::numeric | 0.10::numeric
```

A JSON-style parameter number with a fraction becomes a float, so an
application sending ordinary JSON loses decimal precision without an error.

Floats, including specials, round-trip (`0.1`, `1.7976931348623157e+308`,
`5e-324`, `-0.0`, `NaN`, `-Infinity`). Unicode strings round-trip without
normalisation (emoji with a skin-tone modifier; `e`+U+0301 and U+00E9 stay
distinct: `same = false`, sizes 3 and 2). U+0000 is rejected with an error
(`Unicode code point value 0000 is not allowed in quoted strings`), which is
explicit, not silent.

No binary or temporal types exist:

```
... RETURN '\x00ff'::bytea ...           -> ERROR:  invalid escape sequence at or near "\x"
SELECT '\x00ff'::bytea::agtype            -> ERROR:  cannot cast type bytea to agtype
... RETURN date('2026-09-24') ...        -> ERROR:  function date does not exist
... RETURN datetime('2026-09-24T10:00:00+02:00') ... -> ERROR:  function datetime does not exist
... RETURN '2026-09-24'::date ...        -> ERROR:  cannot cast type date to agtype for column "d"
SELECT now()::agtype                      -> ERROR:  cannot cast type timestamp with time zone to agtype
SELECT to_jsonb(now())::agtype            -> "2026-09-24T05:20:26.788272+00:00"   (a string)
```

Result: **contradicted**. Boolean, int64 at rest, floats and Unicode strings
are exact; exact decimals are exact only through string casts or annotated
parameters; binary, date, time and timestamp have no type; integer overflow
wraps silently. Desk status Unmet → **Unmet, strengthened** (silent
wraparound and literal-precision loss are new, undocumented losses).

### C3. Absent vs explicit null; lists; maps

```
CREATE (n:V {k:'nul1', p: null, q: 1}) RETURN properties(n), keys(n)
 -> {"k": "nul1", "q": 1} | ["k", "q"]
MATCH (n:V {k:'nul1'}) SET n.q = null RETURN properties(n)          -> {"k": "nul1"}
... RETURN n.p IS NULL, n.never_set IS NULL, exists(n.p), exists(n.never_set) -> true | true | false | false
SET n += {r: null, s: 2}                                             -> {"k": "nul1", "s": 2}
EXECUTE put_null('{"p": null}')                                      -> {"k": "nulparam"}
CREATE (n:V {k:'lst', l: [3, 1, 3, null, 1, 'x', [1,1]], empty_l: [], m: {a: null, b: 1, c: [null]}, empty_m: {}})
 -> [3, 1, 3, null, 1, "x", [1, 1]] | [] | {"a": null, "b": 1, "c": [null]} | {}
```

Result: **partial**. Top-level null-valued properties are dropped silently on
CREATE, SET, `+=` and parameters, so absence and explicit null are
indistinguishable at the property level; nested maps keep null-valued keys and
lists keep order, duplicates and nulls. Desk status Unmet → **Unmet
(confirmed)**; a truss encoding could keep explicit nulls one level down.

### C4. Database-enforced rules under Cypher CREATE / MERGE / SET

Run: `sql/02_constraints.sql` → `out/02_constraints.txt`. DDL applied to the
label table `con."Person"`: a unique expression index on
`agtype_access_operator(VARIADIC ARRAY[properties, '"email"'::agtype])`,
`CHECK (properties ? 'name'::text)`, a range CHECK on `age`, a BEFORE ROW
trigger, and foreign keys from the edge table to the endpoint label tables.

Unique index — honoured by CREATE, MERGE and SET:

```
CREATE (p:Person {name: 'Dup', email: 'a@x.com'})  -> ERROR:  duplicate key value violates unique constraint "person_email_uq"
MERGE (p:Person {email: 'a@x.com', name: 'Different'}) -> ERROR:  duplicate key value violates unique constraint "person_email_uq"
MATCH (p:Person {name: 'Upper'}) SET p.email = 'a@x.com' -> ERROR:  duplicate key value violates unique constraint "person_email_uq"
```

Binary string equality holds (`'A@x.com'` next to `'a@x.com'`; precomposed and
combining `josé` both accepted), but numeric kinds collide: with `email: 1`
stored, `1.0` and `1::numeric` are rejected as duplicates, so a key cannot
distinguish UMF integer, float and decimal values:

```
CREATE (p:Person {name: 'F1', email: 1.0})       -> ERROR:  duplicate key value ... =(1.0) already exists.
CREATE (p:Person {name: 'N1', email: 1::numeric}) -> ERROR:  duplicate key value ... =(1::numeric) already exists.
```

CHECK constraints — enforced, but CREATE violations surface as an internal
error rather than a check violation, and MERGE checks before ON CREATE SET:

```
CREATE (p:Person {email: 'noname@x.com'})                   -> ERROR:  invalid perminfoindex 0 in RTE with relid 0
CREATE (p:Person {name: 'Old', email: 'old@x.com', age: 200}) -> ERROR:  invalid perminfoindex 0 in RTE with relid 0
MATCH (p:Person {name: 'Ann'}) SET p.age = -1               -> ERROR:  new row for relation "Person" violates check constraint "person_age_range"
MATCH (p:Person {name: 'Ann'}) REMOVE p.name                -> ERROR:  new row for relation "Person" violates check constraint "person_name_required"
MERGE (p:Person {email: 'm@x.com'}) ON CREATE SET p.name = 'Merged'
                                                            -> ERROR:  new row for relation "Person" violates check constraint "person_name_required"
```

Row triggers and trigger-based foreign keys — bypassed by Cypher writes, while
plain SQL honours them:

```
SELECT tg_op, props FROM public.trigger_log   -> (0 rows)   after five successful Cypher CREATEs
CREATE (o)-[r:PLACED]->(p)   (Order -> Person, violating both FKs)  -> "PLACED"   (accepted)
 start_label | end_label:  "Person" | "Order"   and   "Order" | "Person"
INSERT INTO con."PLACED"(start_id, end_id) SELECT o.id, p.id ...   -> ERROR:  insert or update on table "PLACED" violates foreign key constraint "placed_start_fk"
```

Edge endpoint restriction works through a CHECK on the label id encoded in the
graphid (`_extract_label_id(start_id) = <Person label id>`):

```
CREATE (o)-[r:PLACED]->(p) -> ERROR:  new row for relation "PLACED" violates check constraint "placed_endpoint_labels"
```

Result: **partial**. Unique indexes and CHECK constraints are enforced for
Cypher writes; triggers and foreign keys are silently bypassed; CREATE's CHECK
errors are internal errors; MERGE cannot satisfy a required-property CHECK
through ON CREATE SET; unique keys conflate 1, 1.0 and 1::numeric. All
constraint DDL lives in the graph schema that the maker's manual says should
not receive DDL. Desk status Unknown → **partial**: truss could report
"database" enforcement for uniqueness, CHECK-expressible rules and endpoint
labels on AGE storage, but not for anything trigger-based.

### C5. Property indexes used by the planner

Run: `sql/03_indexes.sql` on the 100k-vertex, 500k-edge `bench` graph →
`out/03_indexes.txt`.

```
-- no property index
 Seq Scan on "Person" p ... Filter: (properties @> '{"uid": 4242}'::agtype) Rows Removed by Filter: 99999   Execution Time: 26.599 ms
-- GIN on properties, MATCH map pattern
 Bitmap Index Scan on person_props_gin  Index Cond: (properties @> '{"uid": 4242}'::agtype)                Execution Time: 0.136 ms
-- GIN only, WHERE p.uid = 4242
 Seq Scan on "Person" p  Filter: (agtype_access_operator(...) = '4242'::agtype)                             Execution Time: 51.009 ms
-- BTREE expression index, WHERE equality / range / prepared parameter
 Index Scan using person_uid_btree ... Index Cond: (agtype_access_operator(...) = '4242'::agtype)         Execution Time: 0.073 ms
 Index Scan using person_uid_btree ... Index Cond: ((... >= '1000'::agtype) AND (... < '1010'::agtype))   Execution Time: 0.036 ms
 Bitmap Index Scan on person_age_btree ... Index Cond: (... > '88'::agtype)                                Execution Time: 1.347 ms
 EXECUTE by_uid('{"u": 4242}') -> Index Scan using person_uid_btree                                        Execution Time: 0.019 ms
-- one hop from an indexed start
 Index Scan using person_uid_btree on "Person" a -> Bitmap Index Scan on "KNOWS_start_id_idx" -> Index Scan using "Person_pkey" on "Person" b
```

Result: **confirmed** for AGE 1.8.0: B-tree expression indexes serve WHERE
equality, range and parameterised predicates; GIN serves MATCH property maps;
the automatic edge endpoint indexes serve traversal. Caveat: which index is
used depends on how the predicate is written (map pattern → `@>` → GIN; WHERE
→ `agtype_access_operator` → B-tree), unless `age.enable_containment = off`.
ORDER BY index use (issue 1522) was not tested. Desk status Unknown →
**Met on this evidence**.

### C6. Cypher coverage and SQL composition

Run: `sql/04_cypher.sql` → `out/04_cypher.txt`. Worked: two-hop patterns,
variable-length `*1..3`, `*`, `*0..2`, OPTIONAL MATCH, WITH/aggregation/
collect/ORDER BY/LIMIT, UNWIND, list comprehension, CASE, EXISTS subquery,
prepared-statement parameters for reads and writes, SET of one property,
`SET +=`, REMOVE, MERGE with ON CREATE/ON MATCH SET (vertex and edge), DELETE
(refused while edges exist), DETACH DELETE, UNION, joins/CTEs/LATERAL with a
relational table, a Cypher write inside a CTE, SQL and Cypher writes rolling
back together, and the 1.8.0 `age_shortest_path` function.

Errors:

```
CREATE (x:A:B {k: 1})                                   -> ERROR:  syntax error at or near ":"      (one label per vertex)
FOREACH (x IN [1] | SET c.touched = true)                -> ERROR:  syntax error at or near "FOREACH"
CALL { WITH c MATCH (c)-[:PLACED]->(o) RETURN count(o) } -> ERROR:  syntax error at or near "{"
[(c)-[:PLACED]->(o) | o.no]                              -> ERROR:  syntax error at or near "|"     (pattern comprehension)
shortestPath((a)-[*]-(b))                                -> ERROR:  syntax error at or near "shortestPath"
LOAD CSV ...                                             -> ERROR:  syntax error at or near "LOAD"
CREATE CONSTRAINT / CREATE INDEX FOR ...                 -> ERROR:  syntax error at or near "FOR"
LATERAL cypher(..., jsonb_build_object('cid', c.cid)::agtype) -> ERROR:  third argument of cypher function must be a parameter
SELECT * FROM crm JOIN cypher('cov', $$ CREATE ... $$) ... -> ERROR:  cypher create clause cannot be rescanned
```

Result: **confirmed with gaps**: every operation the row names works; a SQL
column cannot be passed into `cypher()` per row (no correlated parameters),
vertices have a single label, and several openCypher constructs are missing.
Desk status Met → **Met**.

### C7. Concurrency

Run: `sql/05_concurrency.sh` → `out/05_concurrency.txt`.

Two overlapping transactions SET different properties of one vertex:

```
[A] ... SET n.a = 1 RETURN properties(n)  -> {"a": 1, "k": 1, "cnt": 0}   (then sleeps 3 s, commits)
[B] ... SET n.b = 2 RETURN properties(n)  -> ERROR:  Entity failed to be updated: 3
final properties: {"a": 1, "k": 1, "cnt": 0}
```

The same happens at REPEATABLE READ, and when the first writer is a plain SQL
UPDATE. PostgreSQL's own READ COMMITTED UPDATE would wait and re-apply; AGE
errors with an internal error code, confirmed with verbose error reporting
(appended to `out/05_concurrency.txt`):

```
ERROR:  XX000: Entity failed to be updated: 3
LOCATION:  update_entity_tuple, cypher_set.c:228
```

XX000 is `internal_error`, not the retryable serialization failure 40001.

Eight clients × 100 autocommit increments of one counter:

```
AGE  SET n.cnt = n.cnt + 1:          attempted=800 errors=649 final={"k": 1, "cnt": 151}
SQL  UPDATE ctr SET cnt = cnt + 1:   attempted=800 errors=0   final cnt=800
```

Concurrent MERGE of ten keys by eight clients:

```
[no index]     MERGE attempts=800 over 10 keys; errors=0   -> 0|2 1|2 2|1 3|1 4|1 5|1 6|1 7|1 8|1 9|2   (duplicates for keys 0, 1, 9)
[unique index] MERGE attempts=800 over 10 keys; errors=7   -> 0|1 1|1 ... 9|1   (7 × duplicate key value violates unique constraint "u_key_uq")
```

Result: **partial**. No lost updates (every successful increment counted), but
any concurrent write to the same vertex fails the second writer, even at READ
COMMITTED, with a non-retryable-looking internal error; MERGE creates
duplicates unless a unique index exists, and with one it raises unique
violations instead of matching. Desk status Unknown → **partial**: truss on
AGE would need its own retry wrapper keyed on the error text and mandatory
unique indexes for every merge key.

### C8. Retention of unknown properties

```
CREATE (n:V {k:'nest', unknown_key_1: {a: {b: {c: [1, {d: 'x'}, [2, 3]]}}}, `key with spaces`: 1, `ключ`: 'v', `👍`: true})
 -> {"k": "nest", "👍": true, "ключ": "v", "unknown_key_1": {"a": {"b": {"c": [1, {"d": "x"}, [2, 3]]}}}, "key with spaces": 1}
```

The CSV loader adds keys the source did not have (`"id": 1, ..., "__id__": 1`
in `out/10_load.txt`). Result: **confirmed**, subject to the C2/C3 losses
(null-valued top-level keys and unrepresentable types). Desk status Met →
**Met**.

### C9. TypeScript on Node and Bun without precision loss

Run: `node/c9_client.mjs` (Node 22 and Bun) and `node/c9_bunsql.ts` →
`out/06_c9_client.txt`.

```
[pg default]  imax: string "9223372036854775807"; dnum: string "12345678901234567890.123456789::numeric"; scale: string "0.10::numeric"
[pg default + JSON.parse]  imax: 9223372036854776000; i2p53p1: 9007199254740992; dnum: "JSON.parse error: Unexpected non-whitespace character after JSON at position 30"
[pg-age driver]  imax: bigint 9223372036854775807n; dnum: number 12345678901234567000; scale: number 0.1; m.nested.dec: 0.1
[pg-age write via param map]  big: bigint 9223372036854775807n; dec: number 12345678901234567000; deca: number 12345678901234567000
[JSON.stringify of a BigInt param]  error: Do not know how to serialize a BigInt
[Bun.sql 1.3.11] imax: typeof=string value=9223372036854775807 ; scale: typeof=string value=0.10::numeric
```

Result: **partial**. The default `pg` and `Bun.sql` paths return agtype as
exact text, but the text is not JSON (`::numeric`, `::vertex` suffixes), so
`JSON.parse` fails or loses int64 precision; AGE's own driver keeps int64 as
`BigInt` but turns exact decimals into lossy JavaScript numbers and drops
scale. Lossless use needs a truss-written agtype parser and serializer.
Desk status Unknown → **Unmet for the maker's driver; achievable with custom
code**.

### C10. Plain-SQL reads and conversion to SQL types

Run: `sql/07_casts.sql` → `out/07_casts.txt`. Casts exist from agtype to
`bigint`, `integer`, `smallint`, `double precision`, `boolean`, `text`,
`json`, `jsonb`, `integer[]` and `graphid`, but not `numeric`.

```
(properties -> 'max'::text)::bigint                    -> 9223372036854775807
properties ->> 'emoji'::text                           -> thumbs 👍🏽 ok
(properties -> 'd'::text)::numeric                     -> ERROR:  cannot cast type agtype to numeric
(properties ->> 'd'::text)::numeric, (... 's')::numeric -> 12345678901234567890.123456789 | 0.10
'{"a": "0.10", "b": 0.10::numeric, "c": 0.1}' ->> a/b/c -> 0.10 | 0.10 | 0.1        (text loses the value's type)
'0.10::numeric'::agtype::jsonb                         -> ERROR:  cannot cast agtype numeric to json
'0.1'::agtype::jsonb                                   -> ERROR:  cannot cast agtype float to json
'{"n": 12345678901234567890.123456789::numeric, "s": 0.10::numeric}'::agtype::jsonb -> {"n": 12345678901234567890.123456789, "s": 0.10}
'1.9'::agtype::int -> 2 ;  '"42"'::agtype::int -> 42  (silent rounding and string coercion)
```

A view over the label table was readable by a role with only `SELECT` on the
view. Result: **confirmed with caveats**: plain tables and views work; exact
decimals need `->>` then `::numeric`; scalar numeric and float values do not
cast to `jsonb`; the text path erases the string/number distinction; casts
round and coerce silently. Desk status Met → **Met with caveats**.

### C11. Maintenance

Not a hands-on question; see the profile (22 commit authors on `master` in the
12 months to 2026-09-24, one author with 51 of 118 commits; 17 commits by 4
authors in the 12 months before). The spike adds one operational observation:
the 1.8.0 CSV loader only reads files under the hard-coded directory
`/tmp/age/` (`File or path does not exist [/tmp/age//var/lib/...]`,
`out/10_load.txt` before the fix), which managed services and hardened hosts
may not allow. Desk status Unknown → **Unknown**.

### C12. Indicative latency: AGE vs a hand-designed schema

**Not a benchmark of record.** One shared 4-vCPU VM, one client, data fully
cached (100k vertices, 500k edges: AGE tables 18 MB + 59 MB, relational 11 MB +
42 MB), 3,000 timed transactions per query after 300 warm-up, simple query
protocol for both (every call parsed and planned). Relational schema:
`person(id pk, uid unique, name, age)`, `knows(src, dst)` with `(src, dst)` and
`(dst)` indexes. AGE: B-tree expression index on `uid`, automatic
`start_id`/`end_id` indexes. Result counts match exactly over start keys
1..200 (`out/12_bench.txt`):

```
rel_hop1 rows=984      age_hop1 rows=984
rel_hop2 rows=5012     age_hop2 rows=5012
rel_hop3 rows=24985    age_hop3 rows=24985
rel_vle13 rows=30981   age_vle13 rows=30981
```

Latency in ms:

| Query | Relational p50 | Relational p95 | AGE p50 | AGE p95 | p95 ratio |
|-------|---------------:|---------------:|--------:|--------:|----------:|
| Fetch by key | 0.103 | 0.146 | 0.142 | 0.207 | 1.42× |
| 1 hop | 0.294 | 0.403 | 0.434 | 0.522 | 1.30× |
| 2 hops (fixed pattern) | 0.546 | 0.713 | 1.082 | 1.408 | 1.97× |
| 3 hops (fixed pattern) | 1.047 | 1.517 | 4.797 | 6.322 | 4.17× |
| 1..3 hops (recursive CTE vs VLE), warm session | 0.695 | 1.212 | 0.994 | 1.683 | 1.39× |

The fixed 3-hop plan joins every anonymous intermediate vertex against an
Append over `_ag_label_vertex` and `Person` and adds an edge-uniqueness filter;
in a fresh session, planning took 8.2 ms versus 1.3 ms for the relational
join (`out/12_bench_plans.txt`).

Variable-length queries depend on a per-backend graph cache
(`out/12_vle_cache.txt`):

```
-- session 1:  127 Time: 592.258 ms   127 Time: 1.353 ms   127 Time: 1.222 ms
-- session 2:  127 Time: 577.820 ms   127 Time: 1.289 ms   127 Time: 1.029 ms
== after a write:  127 Time: 569.241 ms   Time: 5.285 ms (CREATE)   127 Time: 599.951 ms   127 Time: 1.003 ms
```

Every new connection pays about 0.6 s on this graph before its first VLE query,
and any write invalidates the cache. With 10% single-property writes mixed in
(`out/12_bench_mixed.txt`, 1,000 transactions):

```
rel vle1..3 read n=904 p50=0.631ms p95=1.116ms
age vle1..3 read n=900 p50=1.139ms p95=577.003ms mean=55.067ms
```

Result: **partial / contradicted for the target**. Fetch, one hop and warm
read-only VLE fall within 2×; two hops sits at the boundary (1.97×); fixed
three-hop patterns (4.17×) and VLE under concurrent writes (about 500× at p95)
miss it. Desk status Unknown → **Unmet on this indicative evidence**, pending
the project's benchmark corpus.

### Measurements

| Capability | Desk status (profile) | Spike result |
|------------|----------------------|--------------|
| C1 | Unknown | 18.6 works; PG19 branch smoke-tested on 19beta4; managed untested → Unknown |
| C2 | Unmet | Unmet: no binary/temporal types; silent int64 wraparound; decimal literals lose precision and scale |
| C3 | Unmet | Unmet: null-valued top-level properties dropped silently; nested nulls, list order and duplicates kept |
| C4 | Unknown | Partial: unique indexes and CHECK enforced; triggers and FKs bypassed; MERGE ON CREATE SET vs CHECK conflict; numeric kinds collide in unique keys |
| C5 | Unknown | Met: B-tree expression and GIN indexes used; endpoint indexes used |
| C6 | Met | Met, with missing multi-label, FOREACH, CALL {}, pattern comprehension, correlated parameters |
| C7 | Unknown | Partial: no lost updates, but concurrent same-vertex writes fail with internal error XX000 (649/800); MERGE duplicates without unique index |
| C8 | Met | Met (subject to C2/C3) |
| C9 | Unknown | Unmet for `pg-age` (decimals lossy); text path exact with a custom parser |
| C10 | Met | Met with caveats: no numeric cast; jsonb cast fails for scalar numbers; silent rounding casts |
| C11 | Unknown | Unknown (not a hands-on question) |
| C12 | Unknown | Unmet on indicative data: 3-hop 4.17× p95; VLE with 10% writes 577 ms p95 |

## Analysis

The spike moves four Unknowns and sharpens two Unmets. Against the hypotheses:
H1 is false (C2, C3); H2 is partly true (unique and CHECK yes, triggers and FKs
no); H3 is true on 1.8.0; H4 is false (no lost updates, but errors instead of
waits); H5 holds only for fetch, one hop and warm read-only VLE.

Of these findings the silent ones matter most, because truss's defining
promise is "never lose data silently" and "report which rules are enforced":
integer wraparound, decimal literal truncation, JSON-number parameters turning
into floats, null-valued keys disappearing, and foreign keys and triggers
skipped by Cypher writes. Each is invisible to a caller who does not already
know to look.

### Risks

- The CHECK-violation path in Cypher CREATE returns `invalid perminfoindex 0
  in RTE with relid 0`, which suggests the constraint path on PostgreSQL 18 is
  lightly exercised; truss would depend on behaviour the maker does not
  document or test.
- Constraint DDL goes into the graph schema, which the manual says not to
  touch; a future AGE release could drop or rewrite label tables differently.
- The VLE cache makes latency depend on connection lifetime and write rate,
  which breaks with transaction-mode poolers and write-heavy workloads.
- Only one PostgreSQL major (18) was exercised in depth; 17 was not built, and
  19 was only smoke-tested on an unreleased branch.
- Latency numbers come from one small cached dataset on a shared VM.

## Conclusions

AGE 1.8.0 on PostgreSQL 18 is a working Cypher layer: indexes are used, the
core read and write clauses work, and plain SQL can read the data. It does not
meet truss's fidelity and enforcement requirements without a layer above it:
temporal and binary values, explicit nulls, exact decimal input and int64
arithmetic all need truss-side encoding or guards; enforcement is limited to
what a unique index or CHECK expression on a whole-properties map can say;
concurrent writes need a retry layer; and a TypeScript client needs a custom
agtype codec. Those layers are most of what option C proposes to build, but
over an opaque `agtype` map instead of ordinary PostgreSQL types.

## Recommendations

Next steps for the bake-off, not a choice among options (that belongs to the
ADR):

1. Run the same scripts against the option A and option C prototypes so that
   C2–C4, C7, C9, C10 and C12 compare on identical probes; `sql/01`, `02`,
   `05` and `bench/` are written to be ported.
2. If option B stays in the bake-off, add a spike for a truss-side agtype
   encoding of dates, times, binary data and explicit nulls, and measure what
   it costs in index use and Cypher readability.
3. Repeat C12 on the project's benchmark corpus with concurrent writers and a
   connection pooler, since the VLE cache result dominates the p95.
4. Ask the AGE maintainers whether the SET conflict error, the CHECK error on
   CREATE and trigger/FK bypass are intended, and whether a PostgreSQL 19
   release is planned.
5. Read the managed providers' extension lists from an unblocked network
   before treating option B as deployable for the project's users.

## Artifacts

All paths under [`SPIKE-001-apache-age/`](SPIKE-001-apache-age/). Cloned sources, build trees and per-transaction latency logs were not kept.

| Path | What |
|------|------|
| `build/build.sh`, `build/build_pg19.sh` | Repeatable builds: PostgreSQL 18.6 + AGE PG18 tag; PostgreSQL 19beta4 + AGE PG19 tag with smoke test |
| `env.sh`, `run_all.sh` | Connection settings; re-runs every probe and writes `out/` |
| `sql/01_types_nulls.sql` | C2, C3, C8 value probes |
| `sql/02_constraints.sql` | C4 constraints, triggers, foreign keys, endpoint checks |
| `sql/03_indexes.sql` | C5 plans |
| `sql/04_cypher.sql` | C6 coverage and SQL composition |
| `sql/05_concurrency.sh` | C7 overlapping sessions, counters, concurrent MERGE |
| `node/c9_client.mjs`, `node/c9_bunsql.ts` | C9 Node/Bun client checks (AGE's `pg-age` driver was built from its tag; the build tree was not kept) |
| `sql/07_casts.sql` | C10 casts and views |
| `bench/00_load.sql`, `bench/run_bench.sh`, `bench/run_mixed.sh`, `bench/vle_cache.sh` | C12 dataset, latency, mixed workload, VLE cache cost |
| `out/*.txt` | Raw outputs quoted above (`00_environment`, `01`–`07`, `10_load`, `12_*`, `13_pg19_smoke`) |
