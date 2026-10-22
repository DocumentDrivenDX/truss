---
ddx:
  id: ADR-008
  type: adr
  activity: design
  status: accepted
  authoring:
    home: repo
  links:
    - id: ADR-003
      kind: informed_by
    - id: CONTRACT-007
      kind: informed_by
---

# ADR-008: Trust the embedding host and registered database adapter

| Date | Status | Deciders | Related | Confidence |
| --- | --- | --- | --- | --- |
| 2026-10-09 | Accepted | Product owner | ADR-003, CONTRACT-007 | High for scope; native integration unqualified |

## Context

Truss is an embeddable toolkit. Python object identity and private admission
registries can enforce correct in-process orchestration, but PostgreSQL cannot
independently authenticate a Python object's identity from a SQL argument.
Requiring protection from a malicious embedding process with the same database
credentials would impose a different deployment boundary.

## Decision

### Owner clarification — validation placement, 2026-10-18

The trusted application engine owns schema interpretation and semantic write validation. PostgreSQL is not required to independently reproduce them. Retain low-cost, high-value database protections such as atomic transactions, uniqueness, foreign keys, locks and revision/version conflict checks. A further database check needs a concrete failure it prevents and a resource-cost analysis that justifies its cost and complexity; blanket placement in PostgreSQL is rejected.

Compile or load the selected immutable schema into efficient application-memory indexes once per revision. Reuse those indexes for field resolution, value validation and batch preparation. Schema persistence and any justified native index serve database responsibilities; they do not replace this application cache. Permission changes and concurrent catalog changes must remain effective. Cache schema meaning, not a permanent authorization decision.

Do not repeatedly reconstruct complete semantic history or revalidate unchanged values merely to prove that the trusted engine performed its own work. Produce the required journal and current-state changes atomically and qualify their behavior through independent tests. This clarification narrows earlier exhaustive native-effect verification proposals; it does not turn a failed, stale, unauthorized or unresolved operation into success. Report the actual enforcement layer and any separate direct-SQL guarantees accurately.

Efficiency is justified first by request/statement analysis: identify cardinalities, indexed access, byte copies, retained state and asymptotic cost for each operation. Remove redundant replay and quadratic accumulation before qualification. Timing alone cannot establish an efficient design. Run representative correctness and capacity qualification on the final implementation; repeated noisy local timing campaigns are not a substitute for the analysis.

The PRD's RES-05/06 and ADR-002 govern the corresponding performance and storage boundary.

Trust the embedding application and its registered database adapter. Enforce
isolation, authorization, integrity and transaction rules against their data
callers. The owner explicitly adopted this recommendation and the minimum security
handoff for installation and initial Python operations.

The trusted host preserves genuine connection/transaction custody, exclusive
execution, non-rewinding operation ordinals, practical workload limits and
original attempt/recovery associations. These are host obligations to qualify,
not facts proven by PostgreSQL inspecting object identity. Ordinary data callers
cannot supply trusted callbacks, registrations or administrative credentials.

Native procedures still verify actual transaction/session identity, effective
privileges, current authorization, epoch/configuration and allowed effects.
Asserted origin metadata cannot grant authority. An authenticated database actor
remains distinct from a host-supplied actor field. Trusting the adapter does not
make forged input, stale admission, partial finalization or unknown settlement
successful. SQL-only supported writer routes retain their independently specified
native enforcement; this decision does not authorize bypassing them.

## Alternatives

| Option | Assessment |
| --- | --- |
| Trusted embedding host and adapter | Selected: fits embedded Python and the owner direction to bound controlled work. |
| Protect against a malicious host using the same credentials | Requires separately privileged service/credential boundaries; not the selected embedded deployment. |

## Consequences and qualification

Python custody can supply the original issued ordinal through the trusted
registered port. PostgreSQL need not prove its provenance from Python object
identity; native conflict/current-context checks remain mandatory. All four
admission families must stop deriving ordinals from surviving rows together.

Qualification must exercise rollback/nonreuse, multiple facades over the same
connection, exclusive dispatch, expiry/exhaustion, late failure and original
unknown-outcome recovery. Host trust is not a passing implementation receipt.

The security owner supplies the exact adopted subset/interface, authenticated
actor/current-permission observation, freshness/revocation/publication protocol,
required native routines/owners/grants and independent allowed/denied tests.
Installation and initial Python operations need this concrete subset; unrelated
security capabilities are not prerequisites. Truss must not fork its resolver or
adopt a partial component count as a complete handoff.

## Owner decision — forward migrations to the latest release, 2026-10-21

This decision supersedes the 2026-10-18 withdrawal of predecessor installation
upgrades. Truss supports one application runtime: the latest release. Previous
releases are supported solely by migrating their databases forward to the latest.
There is no obligation to keep older runtimes, APIs, compiler cohorts or source
admission paths operational. Retaining migration recipes and preservation tests
must not create permanent old-runtime compatibility branches.

UMF 0.10.0 is the initial migration baseline; pre-0.10 compatibility is excluded.
The first qualified path starts at Truss v0.0.44 and ends at the migration-enabled
current release. Subsequent releases MUST preserve a forward path from every
installation admitted to this migration lineage. Skipping releases MUST work
through the latest migration tooling, using immutable ordered recipes as needed,
without running intermediate application versions. No age-based migration expiry
or reset requirement is implied. Future source-format changes require explicit
conversion and retained-meaning preservation before release.

Every future release MUST classify changes to installed routines, storage,
privileges, encodings and metadata meaning. It MUST ship and qualify the required
forward path, or prove that the exact existing installation requires no migration.
A release that strands an admitted database MUST NOT ship. Unknown, modified or
unsupported source installations refuse without effects; failure or uncertain
commit must preserve recovery custody. Migration MUST preserve existing data,
accepted source bytes, unknown extension content, identities, history, receipts,
feed continuation and acknowledgments, or provide an explicit verified semantic
conversion. Successful upgrade admits only the latest runtime; old runtimes must
refuse before application effects.

Operators invoke migrations explicitly with administrative authority. Fresh
installation continues to refuse existing data; application startup does not
upgrade, reset or rewrite a database. Live catalog evolution and historical reads
remain supported by the latest runtime. Downgrades and parallel old-runtime
operation are excluded. Recovery uses a forward fix or a tested backup restore;
a restored older database is eligible for migration, not supported old-runtime
operation. Historical release claims retain their original scope.

See the [restoration plan](../../04-build/runtime-migration-restoration-plan.md) for implementation gates. This decision
specifies required behavior; it does not claim that migration tooling is shipped.
