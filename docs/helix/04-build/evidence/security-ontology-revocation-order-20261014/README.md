# Original graph Assignment revocation ordering

A real independent PostgreSQL writer now revokes Alice's active Assignment while the original native-caller graph read is inside its synchronous receiver. Native pg_locks confirms the writer's RowExclusiveLock on truss.object is ungranted. The admitted reader releases its earlier RA decision while writer commit acknowledgment is still false. After receiver completion, the writer remains alive with acknowledgment false until the reader's outer transaction settles.

After outer rollback releases the reader's held cut, the writer commits successfully and acknowledges; an independent readback confirms active=false. A new actual ordinary Alice read with fresh READ COMMITTED caller/executor contexts returns no resources. The complete ontology/nativecaller case and previous source/fact/role/map/wrong-peer/raw-column/stale-snapshot/late-mutation controls pass in18.449s on PostgreSQL18.6/runtime0.59.

This is evidence for the selected Assignment writer/read cut and real native commit acknowledgment. It does not establish a complete authority-generation producer for policy/role/subject/mapping changes, all writer paths, cursor/cache invalidation, temporal transitions or transport qualification. Host authentication and trusted original registration/admin writer/private executor/native routine/activity/DDL/config/source custody remain premises. No original backend/lifecycle acceptance case is promoted; all132 remain required.

Astra identified that failure before the old join site could leave the worker running into teardown. Worker settlement now runs unconditionally in finally after releasing the executor cut, with a bounded join and stock cancellation/join fallback. The finalr3 replay additionally pins the original executor in native pg_blocking_pids. Historicalr1 remains separately logged; final source pins and observation packet belong to r3. Failure cleanup is source-reviewed; this run does not inject receiver failure.

Finalr3 additionally uses bounded stock cancel_safe(timeout=1.0), bounded connection setup and nested-finally settlement so executor cleanup/cancellation errors cannot skip the last worker join.
