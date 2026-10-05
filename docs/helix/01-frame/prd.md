---
ddx:
  id: truss.prd
  type: prd
  activity: frame
  status: draft
  authoring:
    home: repo
  links:
    - id: truss.product-vision
      kind: informed_by
    - id: truss.concerns
      kind: informed_by
    - id: truss.research-plan
      kind: informed_by
    - id: ADR-001
      kind: informed_by
    - id: ADR-002
      kind: informed_by
kind: product
---

# Product Requirements Document

## Summary

truss stores connected data, typed by UMF (DocumentDrivenDX's machine-readable metamodel and schema interchange fabric) schemas, in a fixed set of PostgreSQL tables. A team adds an entity type, property or relationship by publishing a UMF schema revision, never by migrating tables. Every value is kept exactly, every change is journaled in the transaction that made it, nothing the schema does not define is dropped, and for every rule truss reports whether PostgreSQL enforces it, truss enforces it, or nothing does.

The users are data platform engineers who run PostgreSQL and keep evolving, connected domain data in it, and the engineers who embed or reimplement truss in another language or host. The problem is that the usual options hide integrity (JSONB), churn migrations (per-type tables), or need a second database. The approach is a fixed table layout, written down as contracts and verified by a language-neutral conformance corpus, so that more than one implementation can share one database.

The three measures that matter first: every UMF assertion in the corpus carries a verified enforcement status; no value is dropped on import; and single-object reads, single writes and one-to-three hop traversals meet stated latency targets on the supported PostgreSQL versions.

## Problem and Goals

### Problem

Connected, evolving domain data in PostgreSQL forces a choice. Per-type tables turn every new entity or relationship into a migration and a table lock; one measured design took 330 ms to plan a one-hop query at 1,000 types and took an exclusive lock on the object table whenever a type was added (SPIKE-003). Schemaless JSONB or entity-attribute-value tables hide which rules hold, and a graph extension or separate graph database moves the data out of the database the rest of the platform uses. Whichever is chosen, the team cannot see before go-live which of its schema's rules are actually enforced, and a value that fits no known field is quietly lost on import.

Software that sits on the same database has further needs the first three do not meet. It needs a change record that cannot be skipped, even by plain SQL. It needs writes governed by database role grants. It needs a catalog that can change while writes run, without a stale write being accepted. And it needs a layout stable enough that an implementation in another language can share the tables.

### Goals

1. A new type, property, key or relationship is a catalog revision: rows inserted, no DDL, no table rewrite.
2. Every rule in an accepted UMF schema has a machine-readable enforcement status that has been verified against a real PostgreSQL.
3. No value is silently dropped; data that matches no definition is retained and reported.
4. Every change is journaled atomically with its origin, including the database role that made it, and a consumer can read the journal incrementally without missing a change.
5. The layout and its protocols are specified as contracts and a conformance corpus, so a second implementation can interoperate over one database.
6. Reads, writes and short traversals stay fast as the number of types grows.

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Enforcement transparency (primary) | 100% of UMF assertions in the conformance corpus carry a machine-readable enforcement status (database, engine, none) | Conformance suite on every supported PostgreSQL version |
| No silent loss | 0 values dropped across the import corpus; every unbound value is in the retained-value report | Round-trip tests on the value corpus |
| Evidence-backed claims | 100% of published support claims name the PostgreSQL version and UMF version and link executable evidence | Review of the claims against the evidence index |
| Traversal and fetch (vision) | Single-object fetch and 1 to 3 hop traversal p95 within 2× of a hand-designed schema on the benchmark corpus | Benchmark corpus, same machine and dataset |
| Singleton latency (proposed) | p95 read of one object by id or key at most 1 ms; p95 write of one object, with its journal rows, at most 3 ms; both on a local connection at 1,000,000 objects and 1,000 types, with prepared statements | The benchmark harness; baseline in SPIKE-003: 0.02 ms and 0.09 to 0.17 ms at 200,000 objects |
| Type enumeration (proposed) | p95 listing of all types in the catalog at most 20 ms at 1,000 types | The benchmark harness; not yet measured |
| Catalog independence (proposed) | Planning cost of a read does not change with the number of types: p95 plan time at 1,000 types within 2× of the figure at 10 | SPIKE-003 method; baseline: 0.02 ms for a key lookup and 0.04 ms for a one-hop query at both 10 and 1,000 types |
| Adoption | At least 1 production consumer outside the truss maintainers | Reported by the consumer |

The proposed targets are for the owner to agree. Measured baselines come from embedded PostgreSQL 16.2 and 17.9 on a loaded development machine over a local socket (SPIKE-003), so they are indicative, not a guarantee.

### Non-Goals

- truss does not define UMF semantics. It consumes UMF and never extends it.
- truss does not authenticate people or manage accounts. It records an asserted actor and the database role.
- truss does not provide a user interface or a hosted service.
- truss does not generate per-type tables, and does not make a document the unit of storage.
- truss does not support a second backing database engine in this version; PostgreSQL only.
- truss does not choose retention periods or partition intervals for the journal; a deployment does.

Deferred items are tracked in `docs/helix/parking-lot.md` when it exists.

## Users and Scope

### Primary Persona: Data platform engineer

**Role**: Engineer who runs PostgreSQL for a platform team and maintains UMF or TableSpec schemas for connected domain data.
**Goals**: Evolve the schema by publishing a revision, load existing data without loss, query related records, and know which rules are enforced.
**Pain Points**: Migrations for every new entity, JSONB that hides integrity, no evidence of what is enforced, and data that does not fit the schema being dropped on import.

### Secondary Persona: Implementer or embedder

**Role**: Developer who embeds truss in an application, or builds an implementation in another language, on a database that other tools also use.
**Goals**: Share the tables with other implementations, govern writes by role grants, keep a change record that plain SQL cannot bypass, and run the same layout on embedded PostgreSQL in tests and on a server in production.
**Pain Points**: A layout that is not specified, so a second implementation diverges; locks that stall writers when the schema changes; and per-type structure that cannot be reproduced in another language.

## Requirements

### Must Have (P0)

1. Import UMF documents as an ordered, all-or-nothing catalog revision with a full acceptance report.
2. Store typed objects and edges, with exact values and nothing dropped, in a fixed table set that needs no DDL for catalog changes.
3. Enforce keys, endpoint types and a maximum multiplicity of one in the database.
4. Make every write follow one protocol that detects a catalog change that races with it.
5. Journal every change atomically with its origin, and let a consumer read the journal without missing a change.
6. Report the enforcement layer of every UMF assertion, and verify the report against a real PostgreSQL.
7. Specify the layout, journal, catalog revision and mutation protocol as contracts with a conformance corpus that other implementations can pass.

### Should Have (P1)

1. Traversal of one to three hops and bounded edge listing.
2. Reads and listings that stay fast as the number of types grows.
3. Extension points for a host: its own tables, row-level security, triggers and role grants.
4. Operation on embedded PostgreSQL for development and test, and behind a transaction-mode pooler.

### Nice to Have (P2)

1. Declared indexes and extended statistics, within a reported index budget.
2. A journal consumer that publishes to a warehouse.
3. Typed views over the graph for tools that expect tables.

## Functional Requirements

### Subsystem: Catalog and revisions

- **FR-1** — A set of UMF documents is accepted as one catalog revision, or rejected as a whole with every reason reported; a rejected set changes nothing.
- **FR-2** — Documents are ordered so a document comes after those it depends on, deterministically, and documents that depend on each other are accepted together.
- **FR-3** — A relationship may name an entity type that no document in the set defines. The import policy decides: reject, create a provisional type that is reported until defined, or skip the relationship and report the loss.
- **FR-4** — A type, property, key or relationship keeps its identifier for as long as its UMF identity is unchanged, and an identifier is never reused, including after the element is retired.
- **FR-5** — A revision that tightens or adds a rule lists every stored object that would violate it before it is accepted, and is rejected if any does.
- **FR-6** — A revision that changes a property's type or cardinality is accepted only with a declared total transform applied in the same acceptance.
- **FR-7** — Accepting a revision creates no table, partition, column or index. Its cost is catalog rows only.
- **FR-8** — Every acceptance produces a report of the UMF versions seen, the elements added, retired and provisional, the data re-bound, and the enforcement layer of every assertion.
- **FR-47** — Every accepted catalog revision records who or what accepted it: the actor the caller asserted and the database role, which comes from the database and never from the caller.

### Subsystem: Storage, identity and exactness

- **FR-9** — Objects of every type are stored in one fixed table set, and edges in their own table, with typed properties kept in a map keyed by property identifier.
- **FR-10** — Property values round-trip exactly: integers beyond 2^53, decimals with trailing zeros, timestamps with their offset, binary, an explicit null versus an absent property, and strings with any code point except U+0000.
- **FR-11** — A value that matches no definition is retained under its original name and reported; when a later revision defines it, it is re-bound and the re-binding is reported and journaled.
- **FR-12** — An object may hold named keys. A key value is unique within its type, is held in a way the database enforces, and is looked up by its canonical text, which is equal for equal values of the declared type.
- **FR-13** — An edge connects two existing objects of types its relationship allows, and the database refuses any other. There is at most one edge for a relationship, a source and a target, enforced by the database even under concurrent creates. An object that still has edges cannot be deleted.
- **FR-14** — A maximum multiplicity of one on a relationship is enforced by the database, without a per-relationship index; larger maxima are enforced in the write protocol under the parent lock.
- **FR-15** — Every identifier of an object or an edge comes from one sequence and is never reused.
- **FR-45** — Importing the same records again changes nothing: a record is identified by its type and primary key (an edge by its relationship and endpoints); one that is held or was deleted is skipped; and the import reports what was created, skipped and rejected. A deployment chooses whether a key an object has held stays reserved against a direct create.
- **FR-46** — An imported record keeps the load it came from and the source's own facts (author, time, system), recorded once and never changed, apart from the actor recorded in the journal.

### Subsystem: Mutation and concurrency

- **FR-16** — Every write follows one protocol in one transaction: check the catalog revision, lock the target, check the expected version, validate against the catalog and report every violation, apply the change, and write the journal.
- **FR-17** — A catalog revision accepted while a write runs is detected, under READ COMMITTED and under REPEATABLE READ, and the write is not accepted against the old revision.
- **FR-18** — A catalog acceptance can wait for running writers, sets a timeout, and may be retried; an optional queue keeps it from starving under constant write load.
- **FR-19** — A writer may pass an expected version and the write is refused if it differs; a change that alters no value writes nothing and does not raise the version.
- **FR-20** — Errors are of defined kinds (invalid, endpoint violation, has edges, key conflict, version conflict, catalog changed, retry, not found, unavailable), each with a stated retry rule.
- **FR-21** — Cross-row rules lock the parent object or run serializable; a deferred trigger under READ COMMITTED alone is never reported as database enforcement.

### Subsystem: Journal and history

- **FR-22** — Every change to an object or edge writes journal rows in the same transaction, and a failure to write them fails the change.
- **FR-23** — A journal row records the entity, the version, the operation, the property and its old and new value, the catalog revision, and an origin that carries the actor the caller asserted and the database role, which comes from the database and never from the caller.
- **FR-24** — A deployment can require that every change be journaled, including a change made by plain SQL, by having the database write the journal.
- **FR-25** — A consumer can read the journal incrementally, in a stable order, without missing a row that commits late.
- **FR-26** — A record can be reconstructed as of any version from its journal, interpreting each value with the definition in force when it was written.
- **FR-27** — The journal is append-only for every role truss or a host recognizes, is partitioned by time with no default partition, and is trimmed only by dropping whole partitions.

### Subsystem: Reads and traversal

- **FR-28** — An object is read by identifier or by key, and the result carries its version and its catalog revision.
- **FR-29** — Objects of one type are listed in keyset pages with a required limit and a marker that says whether more remain; the cost of a page does not depend on the number of other types.
- **FR-30** — The edges of one object are listed, bounded, in a stable order, with the same marker. *(P1)*
- **FR-31** — A traversal of one to three hops from an object returns related objects within the latency target. *(P1)*
- **FR-32** — The types of the catalog can be enumerated, with their properties, keys and relationship endpoints, from one catalog revision.

### Subsystem: Enforcement reporting

- **FR-33** — Every UMF assertion has an enforcement status of database, engine or none, a rule name, and the evidence for it.
- **FR-34** — A statement of what truss supports names the PostgreSQL version and UMF version and links the executable evidence.
- **FR-35** — A database-level guarantee is reported only if the guarantee holds for a caller that bypasses the engine; otherwise it is reported as engine enforcement.

### Subsystem: Conformance and portability

- **FR-36** — The storage layout, the journal, the catalog revision steps and the mutation protocol are specified as contracts that do not depend on a programming language.
- **FR-37** — A conformance corpus, held as data, gives the expected results, state, journal and report for each case; expected SQL is informative only.
- **FR-38** — An implementation passes a corpus version on a named PostgreSQL version, and an interchange check shows two implementations can read what the other wrote.
- **FR-39** — The layout declares a version, and an implementation refuses a database of a different major version.
- **FR-40** — The layout DDL and its check pass on every supported PostgreSQL version.

### Subsystem: Host integration

- **FR-41** — A host may add its own tables, functions, roles, triggers and row-level security in its own schema, and may not change a truss column, key or constraint. The contracts say which are permitted.
- **FR-42** — Writes can be governed by database role grants: a host can assume a role per transaction, and truss records the assumed role in the journal.
- **FR-43** — truss keeps no session state and works through a transaction-mode pooler, with or without prepared statements.
- **FR-44** — The layout and its protocols work on an embedded PostgreSQL for development and tests, with the same DDL as a server.

## Acceptance Test Sketches

| Requirement | Scenario | Input | Expected Output |
|-------------|----------|-------|-----------------|
| FR-47 | Revision origin | Accept a revision as role `w` with actor `a` | The revision records actor `a` and role `w`; a role sent by the caller is ignored |
| FR-1, FR-8 | Reject a bad set | Two documents, one failing UMF validation | Neither accepted; the report names the failure; no row written |
| FR-3 | Unknown endpoint | A relationship naming a type no document defines, under each policy | Reject; provisional type reported; or relationship skipped and reported as a loss |
| FR-5 | Tightened rule | A revision shortening a text limit, with 3 objects over it | Rejected; the 3 objects listed |
| FR-7 | No DDL | Accept a revision that adds a type, a property and a relationship, with sixteen writers running | No table, partition or index created; writers not blocked beyond the head-row wait |
| FR-10, FR-11 | Exact values and retention | The value corpus plus a field the schema does not define | Every value reads back exactly; the extra field is retained and reported |
| FR-45, FR-46 | Repeat an import | Import 51 records with source facts, correct one, delete one, import again | Nothing changes, the deleted record stays deleted, each imported record still names its load and source facts |
| FR-12, FR-13 | Keys and endpoints | A second object with the same key; an edge to a missing or wrongly typed object; delete of an object with an edge | Each refused by the database with its error kind |
| FR-17 | Stale writer | A write that read revision N while revision N+1 is accepted, under READ COMMITTED and REPEATABLE READ | Never accepted against N; reported as catalog changed or retry |
| FR-22, FR-23 | Journal | Change two properties of one object as role `w` with actor `a` | Two rows with old and new values, the same version, origin actor `a` and role `w`; a forced journal failure leaves the change unmade |
| FR-24 | Plain SQL | Update an object with plain SQL in journal-trigger mode | A journal row is written |
| FR-25 | Late commit | An older transaction still open when a newer one commits | The consumer's read withholds the newer rows until the older transaction ends, then returns both in order |
| FR-29 | Listing | List a type with 3 objects and one with 200,000, at 10 and at 1,000 types | Same page cost; the marker says whether more remain |
| FR-33 | Enforcement report | The corpus model | Every assertion has a status; a rule that only the engine enforces is not reported as database enforcement |
| FR-38, FR-40 | Corpus on two versions | The seed corpus on PostgreSQL 16 and 17 | Every case passes; the DDL check passes on both |

## Technical Context

This section records current decisions; it does not make them.

- **Language/Runtime**: TypeScript on Bun for the first implementation, with a portable core free of I/O (ADR-001). Other languages may implement the contracts (ADR-003, proposed).
- **Key Libraries**: UMF's TypeScript library, version 0.7.0 at the time of the spikes (ADR-001 D4).
- **Data/Storage**: PostgreSQL. The adopted layout is one object table with a key table and no per-type DDL (ADR-002). Tested on PostgreSQL 16.2 and 17.9; 18 and managed PostgreSQL services are unverified. The minimum supported version of 16 is proposed.
- **APIs**: none yet. The contracts (`02-design/contracts/`) define the tables and protocols; the query and mutation engines are later.
- **Platform Targets**: Linux and macOS; Bun first, Node support provisional (ADR-001).
- **Scale**: measured at 200,000 objects and 400,000 edges across 10, 100 and 1,000 types (SPIKE-003). No larger size has been measured.

## Constraints, Assumptions, Dependencies

### Constraints

- **Technical**: PostgreSQL only. UMF semantics are UMF's. Values are read as text and parsed exactly. Every layout change that affects a second implementation needs a layout version.
- **Business**: pre-build; no consumer outside the maintainers yet.
- **Legal/Compliance**: none identified.

### Assumptions

- Teams that need this already run PostgreSQL and maintain UMF or TableSpec schemas (owner report; wider validation pending).
- A catalog revision is rare compared with writes, so a brief wait for running writers is acceptable.
- A layout of about 70% more disk than a partitioned one (key table separate) is acceptable (SPIKE-003; reversal condition in ADR-002).

### Dependencies

- UMF core and its TypeScript library, for validation and import.
- A PostgreSQL that supports the version checks and row-level features the contracts name.
- The conformance corpus, which has to be built from SPIKE-002's inputs before any conformance claim.

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Provisional layout points change after a second implementation depends on them | Medium | High | Layout versions; the corpus carries the version; re-pin by a recorded decision |
| The corpus is too thin to catch divergence | Medium | High | Seed from SPIKE-002; require the interchange check; add a case with every contract change |
| Catalog acceptance starves under constant write load | Medium | Medium | Lock timeout and retry; the optional advisory queue (ADR-002 D10) |
| Layout is slower than a hand-designed schema at the target scale | Medium | High | Measure the 2× bar at production size; reversal conditions in ADR-002 |
| Measurements are not representative: one loaded machine, two embedded engines, no managed service | High | Medium | Re-run the harness on a quiet machine, on PostgreSQL 18 and on a managed service before fixing the targets |
| Foreign-key and unique checks reveal that a row exists in a hidden row-level-security scope | Low | Medium | Documented in the contracts; the host decides how to report |
| A second implementation's needs leak into truss's tables | Medium | Medium | Extension rules; host cases tagged `x-<host>` |

## Open Questions

- [ ] What scale should truss commit to, if any: the proposal is up to about 10^9 objects, unmeasured above 2×10^5? — blocks the scale and latency targets, ask the owner.
- [ ] Are the proposed absolute latency targets (1 ms read, 3 ms write, 20 ms enumeration) the right bar? — blocks FR-29 to FR-32 acceptance, ask the owner.
- [ ] Which PostgreSQL versions are supported: minimum 16, and 18? — blocks FR-40, ask the owner.
- [ ] Is the unexplained read tail on the edge-limit table at 1,000 relationships a defect? — blocks the multiplicity design in FR-14 being final; re-run SPIKE-003 E1b.
- [ ] How are `json`-like properties represented in UMF core? — blocks FR-10 for that value family, ask the UMF maintainers.

## Success Criteria

- Every P0 requirement has a passing acceptance scenario on PostgreSQL 16 and 17.
- The conformance corpus exists and one implementation passes it; a second implementation passes it and the interchange check.
- The enforcement report is verified for every assertion in the corpus, with no assertion unclassified.
- The proposed latency targets are agreed, measured on a quiet machine and met.
- At least one consumer outside the maintainers runs it.
