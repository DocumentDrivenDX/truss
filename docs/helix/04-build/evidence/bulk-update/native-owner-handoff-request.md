# Native bulk integration handoff request — 2026-10-14

Sent to both owner chats on 2026-10-14 after Erik explicitly authorized coordination. Both tool calls confirmed delivery. Owner protocol/interface and native qualification responses remain pending.

Destinations: “Assess security control support” (`01a11b8b-06bb-7091-a11a-b7eba0a432eb`) and “Truss Impl” (`01a10c68-3279-7310-9e05-1b216e469b79`).

## Proposed message

We are implementing the reviewed portable SQL-to-actions frozen UPDATE slice across UMF, Weft and Truss, with the live UMF website example `UPDATE products SET name = 'Foo' WHERE id = 'bar'`. Original UMF preparation and portable plan/manifest APIs, original Weft compiler/lowering, a compile-only website preview, a bounded batch state model and private Python registration/value consumers exist. Latest numeric-meaning corrections are tested but await Astra re-review because its account usage limit was reached. No protected bulk execution is claimed.

The SQL-to-actions checkout of Truss is on an older branch and its old handoff still says the original security contract and seven native bodies are missing. Current integration source is substantially newer: Truss commit e4a75b06 and security commit ebc72959 include catalog runtime0.63-candidate/PostgreSQL18.6/layout1.0, native catalog/groups and registered Subject/guarded reads. We need to adopt current original source/profile artifacts, not create a competing engine or rely on stale component gaps.

There is a concrete protocol mismatch requiring owner resolution: reviewed Truss CONTRACT-013 requires engine-owned REPEATABLE READ materialization, one coherent original authorized cut, fresh authority/catalog correspondence after locking, and protected seal-control persistence. Current catalog runtime.sql explicitly refuses non-READ COMMITTED authorization. Current Subject installation/observation also admits only READ COMMITTED, and the security task is adding an old-snapshot refusal witness. We will not switch bulk materialization to READ COMMITTED or weaken current authority to bypass this requirement.

Please provide the original versioned native interface/artifacts for a qualified fixed-cut bulk read under current authority, or coordinate the governing contract change needed to supply it. Identify actual caller/connecting-person versus elevated executor custody, current policy/head/source exclusions, freshness revalidation, protected cut issuance and native completion/recovery. The control/subject connection can remain READ COMMITTED if a separately qualified original bridge binds it to the exact fixed data cut; such a bridge must be owner-defined and witnessed, not a caller-authored principal or snapshot assertion.

For Truss, identify the current supported original transaction/group APIs, accepted core0.8 model/value/Key representation, immutable object ID nonreuse/whole-row-version guarantees, exact current layout/binding export, and engine-owned outer-transaction adoption. Existing apply_in_transaction/group capabilities may be reusable internally, but per-item commits/retries, live predicates, direct consumer registry writes or synthetic issuer grants are not acceptable substitutes. Please name source/release/profile pins and native ordinary-role evidence so we can build on your implementation while leaving your active checkout untouched.

Current bulk references: Truss docs/helix/02-design/contracts/CONTRACT-013-bulk-action-execution.md and TD-046/047/048/049; UMF CONTRACT-902/903/904; Weft CONTRACT-006. The pending native deliverable is frozen selection/guard/seal followed by one atomic registered set-action batch with complete original outcomes and original attempt/control custody. The full website/Truss goal stays open.

## Evidence inspected

- Truss current branch here: codex/refresh-helix-specs, a9cfb691.
- Current Truss integration commit inspected read-only: e4a75b06a012409cd128ec9bc5d15169ecaafe15. Active uncommitted container work is not adopted.
- Current security integration commit inspected read-only: ebc7295923905e52e77282796aeb382713fcad3b.
- `/private/tmp/truss-main-integration-20261010/packages/python/src/truss/catalog_runtime.py`: native install/accept/configure/group/apply APIs; ordinary-person READ COMMITTED requirement.
- Same checkout `_catalog_runtime/runtime.sql`: lines34–35 enforce catalog authorization READ COMMITTED.
- Security checkout `_psycopg_subject_observation.py` and Subject installation modules admit read_committed/read_write.
- Existing CONTRACT-013: engine-owned REPEATABLE READ data/selection/seal transaction and original current-authority cut correspondence.

This request is a concrete missing dependency handoff, not authorization to alter the reviewed bulk semantics or promote unqualified native support.
