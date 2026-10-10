---
ddx:
  id: truss-requirements
  type: design-note
  activity: design
  status: draft
  owner: Erik LaBianca
  updated: 2026-10-09
  authoring:
    home: repo
  links:
    - id: ADR-013
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# Requirements on Truss from a Python host

Written to be handed to the Truss project as-is. It states generic requirements of an embedded Python host that uses Truss as its authoritative mutable store on Lakebase (Databricks managed Postgres); it names no host-specific concept, and Truss's docs need not either. Source: a read of the Truss repository on 2026-10-08, revised on 2026-10-09 against its commits through 20:47 that day (ADR-001 to ADR-007, CONTRACT-001 to CONTRACT-012, the implementation plan, `packages/python`). Nothing was run.

## What the host needs from Truss

A Python 3.11 process that, for each person using it, over a connection authenticated as that person:

- reads objects and edges by key, by indexed equality filter, by relationship, with keyset paging and `COUNT(*) GROUP BY`;
- applies a module-scoped action as one atomic group with preconditions, an idempotency key and a receipt, and can dry-run it;
- imports records in bulk with provenance;
- asks whether a receipt's position is included in the data it can see (`reached`);
- learns which module revisions exist and at what layout version.

The host holds no table of its own, no role map and no access decision: Truss and the database decide.

## Current state

| State observed (2026-10-09) | Consequence |
|-----------------------------|-------------|
| ADR-003 is accepted: Truss ships and maintains a tested embeddable Python 3.11 implementation in its own repository; ADR-001 is amended. The implementation plan maps R1 to R10 to delivery slices. | The route exists (R1 closed). |
| `packages/python` has about 1,200 lines: a local PostgreSQL lifecycle (pgserver 0.1.4, bundled PostgreSQL 16.2), exact numeric and timestamp conveniences, a Weft compiler boundary, private query coordination, a receipt-position locator decoder, migration planning. It says it is "not released mutation/query/installation APIs". | Plumbing only. Nothing to call for catalog, apply, import or read; no published wheel. |
| No `apply_group`, key lookup, edge read or `import_batch` code in any package; they remain contracts and SQL. | Unchanged. |
| No published conformance corpus. Truss has mapped the host's own corpus into its handoffs and found one incompatibility (see R7). The conformance runner exists as declarations and type witnesses. | R2 open. |
| Layout is still a 0.16 candidate with install and conversion unfinished; Truss ships its own migration tooling to be invoked outside the host's transaction. | R3 open. |
| Module isolation by connecting-person role membership and the origin actor are designed (CONTRACT-005, security workstream) but not installed. | R4 and R5 open. |

## Requirements

Each is stated as an outcome, with the evidence that would close it.

### R1. A decision on Python (ADR-003)

**Closed 2026-10-09.** ADR-003 is accepted, Truss owns the Python implementation in its repository, and ADR-001 points to it. What remains is delivery: a public package that passes R2.

### R2. A published, language-neutral conformance corpus

The corpus is data, not TypeScript tests: each case gives setup (catalog revision, objects, edges, roles), calls, and expected results, errors and journal rows, with expected SQL informative only (ADR-001). It covers at least CONTRACT-004's operations: atomic group, preconditions, idempotent repeat from the journal, dry-run leaving no row, bulk atomic and per-item, import identity and provenance, a refused action changing nothing. Positions and tokens are opaque in cases: a case saves a receipt's token and asks whether it is `reached`. A corpus version is named so an implementation can claim one and a runner can report a newer one rather than pass it. It includes the interchange check STP-028 describes: two implementations over one database.

Closes when: a versioned corpus and runner exist and the TypeScript engine passes them.

### R3. A stable, versioned layout to install

Name the layout version a consumer may build against and the compatibility rule: what a major version change means, and that a database of a different major version is refused. Publish its DDL as a single artifact with a digest, and the check script that runs after install or change. Say whether installation is by the consumer's migrations or by Truss's installer; the host needs the first (it runs migrations on deploy) or a clear statement that it must use the second.

Closes when: a layout version is declared stable for consumers, with its DDL and check script, and a consumer can install it on plain PostgreSQL and on Lakebase.

### R4. Module isolation decided by the connecting person

CONTRACT-005 today decides by the acting role. The host connects as the person with their own token, and the person is a member of a module's reader or writer role. Isolation must decide by that role membership on reads and on every effect of a group, in the database, with no `SET ROLE` by the caller and no role map held by the host.

Closes when: corpus cases show a member of a module's writer role applying, a reader being refused a write, a non-member being refused a read, and a call with no authenticated identity failing before any statement.

### R5. The person as origin actor, from the connection

The journal's origin actor must be the authenticated connecting person, taken from the database's own session identity, with no caller-supplied actor and no fallback to a request role or a definer owner. The action's name travels in an `x-` key and survives to the journal row.

Closes when: a journal row from a group applied as a person names that person, and a corpus case refuses a supplied actor that differs.

### R6. Caller-controlled transactions for dry-run

CONTRACT-007's `adopt_transaction` is the basis. A dry-run must evaluate preconditions and effects exactly as `apply_group` would, in a transaction the caller rolls back, leaving no journal row and no recorded request id; constraint and catalog violations must surface as in a real apply. State whether this needs a savepoint or the caller's own transaction, and that either is supported on Lakebase.

Closes when: a corpus case compares a dry-run's violations with the real apply's on the same plan, and shows no row afterward.

### R7. A receipt token with `reached`

A receipt must carry a position that is opaque to the consumer, comparable only through a stated operation, and sufficient to ask "is this included in the data visible here?". On the authority it is true once the commit is confirmed. On a replica fed by the change feed it is true when the complete transaction has been durably applied. Truss's plan makes the token commit to the source installation and epoch, and rejects the host's earlier assumption of a last `(xid, seq)` as a commit-order frontier; the host accepts that and asks only that the token's form and comparison operation be published. The host also needs to know how it stays valid across feed restarts and source-epoch change, and how long a receipt and its idempotency key are honored (the host asks for at least 24 hours of retained journal rows).

A token that is malformed, or that the source never issued, must be refused, not answered `false`: `false` means "not yet" and invites a wait. The host's corpus now expects this (an `Invalid` error), which matches Truss's stated position that unavailable or malformed input cannot map to an available `false`. Truss should keep refusal and "not yet reached" as distinct outcomes in its own cases.

Closes when: a token can be rebuilt from a repeated group's journal rows (including no-op groups), a feed consumer can publish its position in a form comparable with it, and the corpus distinguishes reached, not yet reached and refused.

### R8. Reads the consumer can serve interactively

State, per read shape, whether it is bounded and indexed: key lookup, equality over key and indexed properties, relationship predicates, `alias.*` with a cap on relationship columns, keyset paging ordered by key, `COUNT(*) GROUP BY` one property. A read must run in a read-only transaction as the person. Say which shapes Weft compiles and which are direct reads, so a consumer knows which to use; the host parses its own statement and wants parameterized SQL, not text it must re-parse.

Closes when: each shape is listed with its plan and bound, and the corpus covers it.

### R9. Exact values in Python

Truss returns stored integers, decimals, timestamps and JSON as text that the consumer parses exactly (ADR-001, CONTRACT-010). Say the exact text forms, so Python can map them to `int`, `Decimal`, timezone-aware `datetime` and `json` without a float on the path, and so a corpus case can assert a round trip.

Closes when: the text forms are specified per type and covered by corpus cases.

### R10. A published dependency

The host cannot vendor an unpublished repository. Whatever carries R1 to R9 (a Python package, or DDL plus corpus) must be published with versions, and releases must state which corpus and layout versions they pass. Pinning by commit is acceptable only as a recorded interim.

Closes when: a versioned release names its layout and corpus versions.

## What the host has done and will do

- It supplies its own conformance corpus (data, with a runner) as an input to R2; Truss has already mapped it.
- It has changed that corpus so an unissued or malformed token is `Invalid`, not `false` (R7).
- It has added authored core names to every Record and Field in its conformance and example models, which Weft's application model requires; the original files had none and relied on extension metadata. The key id `identity` and the relationship key selectors are unchanged.
- It builds its adapter against its own contract and a fake, and re-targets the shared corpus when R2 lands. It treats the layout as provisional and vendors nothing until R3.

## Open questions for Truss

1. *(Answered: a Truss-maintained Python implementation, ADR-003.)* What is the first package, and which of R2 to R10 does its first release claim?
2. Is Lakebase a supported target, or only PostgreSQL 17.9 as in the current evidence? Version limits and extension availability matter for isolation and caller-controlled transactions.
3. Does the feed's position (CONTRACT-006) carry enough to answer `reached` on a replica, or does the replica need a different position?
4. What is the expected order of R1 to R10? The host would sequence R1, R2 and R4 first, since they decide whether the route exists.
