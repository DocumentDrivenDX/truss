---
ddx:
  id: ADR-003
  type: adr
  activity: design
  status: accepted
  authoring:
    home: repo
  links:
    - id: ADR-001
      kind: informed_by
    - id: ADR-002
      kind: informed_by
    - id: CONTRACT-001
      kind: informed_by
    - id: CONTRACT-004
      kind: informed_by
---

# ADR-003: Other-language implementations conform to shared contracts and a corpus

| Field | Value |
|-------|-------|
| Status | **Accepted — owner decision 2026-10-09** |
| Date | Proposed 2026-10-04 |
| Decider | Project owner |
| Drafted by | Claude Code agent |
| Evidence | [ADR-001](ADR-001-language-and-portable-core.md) D2, D5, D6, [ADR-002](ADR-002-storage-strategy.md), [CONTRACT-001](../contracts/CONTRACT-001-storage-layout.md) to [CONTRACT-004](../contracts/CONTRACT-004-mutation-and-conformance.md) |

## Context

ADR-001 chose TypeScript first and named four triggers for a Rust core. Trigger T1 fires when "a named consumer needs truss inside a Python (or other non-JavaScript) process, and an out-of-process service does not meet that consumer's needs". A consumer now exists: an application-specific mutable sub-graph store that must run inside a Python 3.11 application deployed as one unit on a managed platform, and wants to share truss's tables rather than design its own. ADR-001 D6 requires that firing T1 be recorded with evidence in a new ADR, and D7 describes only one response: port the core to Rust and call it from the host. ADR-001's consequences also say there is no in-process Python use until a Rust core exists.

The out-of-process alternative does not meet this consumer's needs: the host is deployed as one unit, so a second runtime and service per deployment is a second application to build, deploy and secure, and the host's database connection, credentials and role model would have to cross a process boundary.

ADR-001 D5 already makes the conformance corpus language-neutral data with normative expected results and informative expected SQL, so that a Rust core could be verified against the same cases. The storage layout, the journal, the catalog revision steps and the mutation protocol are now written as contracts (CONTRACT-001 to CONTRACT-004), independent of any language.

## Decision

We will treat the contracts and the corpus as the interface to truss, and accept **a second implementation in another language when it passes the corpus**, as a response to T1 alongside the Rust-core route of ADR-001 D7. The first such implementation is a Python implementation for that consumer. It need not wait for, or become, a Rust core.

**Key Points**: A conforming implementation reads and writes the tables of CONTRACT-001 and follows CONTRACT-002 to CONTRACT-004 | It passes the corpus on each engine version it claims, and the interchange check against the TypeScript engine (CONTRACT-004) | It declares the layout version it was built against and refuses a different major version | It may add host-owned objects in its own schema and may add triggers on truss tables, under the extension rules of CONTRACT-001, and may not change truss's columns or constraints | It consumes pinned UMF owner APIs or a qualified shared callable interpretation boundary; Python orchestration does not define a competing UMF validator, key codec or SQL generator. The corpus checks owner interpretation correspondence, so ADR-001 D4's "UMF through its TypeScript library" applies to the TypeScript core only | The Rust route of ADR-001 D7 stays open and, when taken, is one more conforming implementation

## Selected first Python implementation boundary

The owner requested Python promptly and indicated that pure Python is suitable
if Weft and authorization supply the heavy computation. The proposed response
is Python host orchestration over shared protected PostgreSQL protocols, with
Weft's Rust compiler consumed through its Python bridge. It does not require a
Rust port of Truss and does not create a second ACL resolver or SQL compiler.
The active security workstream owns authorization semantics and its shared
invocation boundary. See [the Python integration design](../python-integration.proposal.md)
for PY-01–07, exact transport and consumer R1–R10.

“Second implementation” here means an independently packaged host API and
adapter conforming to the same behavior. It does not require independently
reimplementing shared database enforcement. Interchange must still exercise
Python-write/TypeScript-read and the reverse with independent expected values
and native observations; sharing SQL routines does not by itself prove host
protocol or codec correctness.

Truss owns, maintains and ships the tested embeddable Python implementation in
the Truss repository. Python 3.11 is the initial consumer target. The owner
accepted this route on 2026-10-09; it amends ADR-001's Python restriction.
Driver/version qualification and published package names are engineering outputs.
Experimental imports alone still do not qualify complete runtime support.

## Alternatives

| Option | Pros | Cons | Evaluation |
|--------|------|------|------------|
| Port the core to Rust with Python bindings (ADR-001 D7) | One engine; memory-safe | Not built; per-platform binary builds; waits on a measured need beyond T1's wording | Kept open, not required for T1 |
| Run the TypeScript engine as a service for Python callers | Reuses code | A second runtime and service; the trigger text already excludes it where it does not meet the consumer's needs | Rejected for this consumer |
| A Python implementation with its own table design | Fast to start | Not interchangeable with truss; a second storage design | Rejected |
| **A Python implementation conforming to the shared contracts and corpus** | Interchangeable over one database; verified by data; no Rust dependency | Two implementations to keep in step; the contracts and corpus must exist first | **Accepted** |

## Consequences

| Type | Impact |
|------|--------|
| Positive | The layout is shared by Ashlar's feed, truss and a Python host. Divergence is caught by the corpus and the interchange check, not by reading prose. |
| Negative | The contracts become a maintained interface with versions. Two implementations multiply the work of every change to the layout. The seed corpus must be built from SPIKE-002's inputs before any conformance claim is possible. |
| Neutral | ADR-001's triggers T2 to T4 are unaffected. |

## Risks

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| The provisional points of ADR-002 change the layout after a second implementation depends on it | M | H | Layout versions; the corpus carries the version; re-pin by a recorded decision |
| The corpus is too thin to catch divergence | M | H | Build the seed corpus from SPIKE-002 first; require the interchange check; add cases with every contract change |
| The Python implementation's needs (host-owned roles, stronger audit) leak into truss's tables | M | M | Extension rules in CONTRACT-001; host cases tagged `x-<host>` |

## Validation

| Success Metric | Review Trigger |
|----------------|----------------|
| A Python implementation passes the corpus and the interchange check against the TypeScript engine on a named PostgreSQL version | A case fails, or an implementation diverges |
| The layout DDL and its check pass on every supported PostgreSQL version | A statement fails on a supported version |

## Concern Impact

- **Concern selection**: none changes. `typescript-bun` still governs the TypeScript core; a conforming implementation in another language follows its own language concerns.
- **Practice override**: ADR-001 D4 applies to the TypeScript core only.
- **Amendment**: this ADR amends ADR-001's consequence that there is no in-process Python use until a Rust core exists. ADR-001 now points here.

## References

- [ADR-001](ADR-001-language-and-portable-core.md), [ADR-002](ADR-002-storage-strategy.md)
- [CONTRACT-001](../contracts/CONTRACT-001-storage-layout.md), [CONTRACT-002](../contracts/CONTRACT-002-journal.md), [CONTRACT-003](../contracts/CONTRACT-003-catalog-revision.md), [CONTRACT-004](../contracts/CONTRACT-004-mutation-and-conformance.md)
