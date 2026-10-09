# Local runtime, installation and migration execution plan

## Updated goal and selected direction — 2026-10-09

Complete Truss's remaining governed design and execution-ready implementation/test
planning for an embeddable toolkit plus reference implementation, synchronized
with UMF and Weft. Additionally deliver a Truss-maintained tested embeddable
Python implementation, document-qualified catalog identity, explicit pre-effect
stale refusal without automatic retry loops, and host-supplied PostgreSQL connection
embedding. Truss owns installation and migration profile selection and ships a
pgserver-based default runtime that starts easily for local development/testing.
Shipped migrations are explicit and infrequent; ordinary UMF model revisions are
DDL-free. Pool provisioning/operation is the host's responsibility. These criteria
extend, rather than replace, the original 45-story scope and conformance obligations.

## Ownership and profile selection

Truss owns the Python package in this repository, installation bundles, migration
recipes, verification and recovery composition. UMF owns schema interpretation and
generic DDL generation; Weft owns logical SQL lowering; the existing security
workstream owns authorization and publication protocols. Source pins, finite driver
bounds and security admission remain explicit engineering outputs, not new product
votes. The source-epoch0.16 plus configuration/migration adjuncts are composition
inputs, not a claim of one complete installed bundle.

Select pgserver 0.1.4 as the first local runtime candidate with Python3.11. Pin
actual wheel/platform/dependency and bundled PostgreSQL version before support.
Its upstream README advertises PostgreSQL16.2; existing Truss17.9 evidence cannot
qualify that server. Audit SQL/catalog/xid/status dependencies against the actual
binary. Implement compatibility where possible and explicitly refuse an unsupported
complete installation; do not silently switch to Docker or system PostgreSQL.
An external PostgreSQL connection remains a supported embedding route under its
own qualified version/profile. Aurora and Lakebase retain independent obligations.

## Delivery sequence

1. Implement local server lifecycle: explicit start with caller-selected data
   directory, connection information, readiness, signal-safe stop and persistent
   restart. Fresh temporary fixtures are isolated. Server startup alone performs
   no Truss upgrade. No global process termination or unrelated data deletion.
2. Compose one complete UMF-generated installation bundle: storage, report/history,
   configuration/receipt homes, routines, grants, dependencies, initialization and
   verifier inputs. Choose exact symbolic definitions now; inspect actual native
   identifiers only after installation. Installer owns a dedicated administrative
   transaction and runs target/parity checks before publication. Existing ordinary
   or incompatible data is never mistaken for a fresh installation.
3. Implement Python host entrypoints against caller connections and transactions,
   shared protected PostgreSQL operations and Rust Weft. Expose exact carriers,
   whole atomic network batches, complete durable retry receipts and current-person
   authorization. No TypeScript service or second Python SQL compiler is required.
4. Select one complete populated migration source/target route using the same
   installation composition. Preserve object/key/edge IDs, values, reports, journal,
   retry receipts, epochs/feed positions and unresolved attempt custody. Implement
   M2–M5 from the existing migration handoff; administrative recovery does not
   repeat uncertain recipes. Startup reports incompatibility rather than migrating.
5. Qualify clean Python distribution and TypeScript/Python interchange, then each
   advertised managed target. Retain independent expected data and complete effects;
   a local server smoke or development wheel is not a complete Truss runtime.

## Independent acceptance scenarios

- Fresh local start needs no separately provisioned PostgreSQL or Docker; observe
  actual server version and successful native query. Stop and restart the same
  directory preserves committed data; concurrent isolated directories do not collide.
- Missing/incompatible local binaries refuse with actionable dependency/version
  information; no fallback changes the selected profile without disclosure.
- Fresh installation verifies complete original generated/native inventory; late
  failure leaves no published installation. Opening an existing installation is
  read-only until explicit deployment, and ordinary model acceptance adds no DDL.
- A host connection retains ownership: Truss neither closes it nor commits a caller
  transaction. Failed/unknown containment retains original custody; no pool manager
  or hidden connection substitution is introduced.
- Deterministic stale pre-effect admission returns the original refusal once, with
  no mutation/journal/report effects or automatic second submission. Caller retry
  is a new explicitly requested admission under existing request idempotency rules.
- Same module/element names in two documents remain distinct through acceptance,
  native grants, compiler binding, keys and output. Document identity is retained.
- Populated explicit migration passes independently expected preservation, late
  rollback, lost acknowledgement and fresh-process reconcile cases. Clean installed
  packages contain every registered recipe/profile/verification input.
- Complete required Python corpus and bidirectional committed interchange run on
  the exact local profile; known unsupported behavior never becomes a skipped pass.

## Traversal clarification

The earlier question concerned whether a separate multi-hop direct-read API returns
unique terminal entities or path records. The owner did not select either and asked
for its rationale. Review actual consumer uses before proposing that extra API;
compiled SQL relationship predicates keep Weft's original semantics. This isolated
read-surface question does not block local runtime, installation or Python delivery.

## Goal control

The user explicitly resumed/unblocked the work with these criteria. This document
is the persisted expanded execution objective. The available goal tools expose
only complete/blocked/paused status updates and cannot edit an existing objective
or resume blocked status; do not mark the old goal complete merely to replace it.
Continue authorized work while reporting that control-plane limitation accurately.

## Initial runnable developer path

```sh
python3.11 -m venv .venv
.venv/bin/pip install -r packages/python/local-runtime-requirements.txt
.venv/bin/python scripts/local-postgres.py --data-dir .local/truss-postgres
```

The launcher emits local connection information and remains alive until SIGINT or
SIGTERM. `--probe` verifies readiness then stops; cleanup mode is `stop`, retaining
data. The launcher uses argv-based bundled psql execution with ON_ERROR_STOP and
an explicit readiness timeout. It neither installs Truss nor upgrades an existing
layout. This is the first executable development component; package-level public
runtime embedding and complete installation follow the delivery sequence above.

Actual initial macOS arm64/Python3.11 probe observed pgserver0.1.4 and PostgreSQL16.2.
Full Truss SQL compatibility and installer qualification remain required on that
exact server; retained17.9 evidence is separate.
