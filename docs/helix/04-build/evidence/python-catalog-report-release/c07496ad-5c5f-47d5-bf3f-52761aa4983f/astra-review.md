# Astra review — standalone archive self-write fence

Disposition: **no remaining blocker within the standalone private actual-ShareLock component scope.** This is not installed configured-profile integration, authentication, a full source/authority cut or accepted backend admission. The reviewer inspected sources and retained native evidence and independently replayed saved SMT, without implementation edits or native/producer execution.

## Native source and controls

The BEFORE STATEMENT trigger validates the exact archive relation, timing, statement level and four write event classes. Its refusal depends on the current backend's actual granted relation ShareLock in the current database, rather than an xid or host flag. It is SECURITY INVOKER with fixed search_path, PUBLIC execution revoked and the trigger ENABLE ALWAYS. Ordinary reads remain possible; writes before acquisition or after rollback across acquisition remain possible. Holding some stronger lock alone is not defined as admission to this fence; the tested upgrade begins with the original ShareLock.

The final eight component methods cover valid INSERT, UPDATE, DELETE and TRUNCATE plus zero-row INSERT/UPDATE; attempted change/restore cannot begin; savepoint RELEASE preserves/reparents the fence; later rollback preserves it; rollback across acquisition removes the actual ShareLock under the same parent xid and permits a later change. SHARE then ACCESS EXCLUSIVE retains an independently observed ShareLock and still refuses a write. Replica mode retains the ALWAYS fence. The installed ACL check expands default ACLs and requires the original function row, so omitted REVOKE would not falsely pass because proacl was NULL.

Initialab2c0a02 is a failed fixture attempt: TRUNCATE encountered pending deferred-trigger events before the fence, and a generated-column INSERT was not a valid isolated trigger control. The final marker/immediate-constraint fixture and explicit writable columns correct those issues. Refusal checks now roll back/release their savepoint in finally, preserving independent state even when the deliberate weakened implementation unexpectedly permits a statement.

The omitted-fence variant changes only the pg_locks IF to FALSE AND EXISTS. It retains trigger/event checks, installation and privilege declarations. Exactly ten expected-refusal assertions fail across the selected write/lifetime methods, with no incidental constraint/aborted-transaction errors. The original row is restored between subtests. This demonstrates that the controls exercise the fence rather than unrelated native refusal.

## Retained native evidence

Under Truss `docs/helix/04-build/evidence/python-catalog-report-release/`:

- Positivec07496ad-5c5f-47d5-bf3f-52761aa4983f: receipt SHA256 `407c6ddb1a9dde1c3c30a1787e341d42fe00a55c3cfb37dc0f27dfc5b7984cdc`.
- Countercontrolf0d2f27a-035a-4a31-8de4-1a00e38880f5: receipt SHA256 `bc09409573aea4eb022a9de65de1528cabb4c22c00863bb3605ae3a1b10be244`.

The positive executes8 fence +14 dispatch +15 incoming source/metadata methods (37 tests). The counter executes8 fence methods with ten deliberate assertion failures plus14 passing dispatch regressions; auxiliary15 are not run. The fence is installed in its separate component database, not silently added to the configured catalog fixture. Both packets retain273 source/dependency pins and exact ZIP preimages,1,614 native file digests and owned stop0/status3/socket absence. The companion audit checks exact test populations, countervariant bytes, current pins and cleanup. The legacy executedReleaseSqlSha256 receipt field describes the release selector, not this fence; fence execution correspondence is assessed from frozen/copied source, setup path and exact retained fence variant rather than misusing that field.

## Conditional analysis

Final formal packet: `docs/helix/04-build/evidence/archive-self-write-fence-formal/43b2b85f-e215-4086-94ac-cdd64424fd6c/receipt.json`, SHA256 `5d936c15da7cf5bbf9b20047505b27dfdff9decf8d841d0c2aaed16d6b118242`.

Independent fresh-context replay matches all7 saved formulas:4 UNSAT/3 SAT, with exact SMT digests and4 current source/preimage matches. A supplemental active-fence attempted mutation with a distinct desired state has a satisfiable premise population. The transition equation conditionally preserves an opaque archive state when installed/live; the two-step ABA counterexample models change and restoration explicitly when the fence is omitted. Finite-history preservation is a mathematical induction over repeated modeled steps with the premises maintained, not an encoded native history or SQL refinement. The rollback-named SAT query stipulates not-live; it does not derive native rollback semantics. The earlier stipulated-restoration model remains historical.

The proof assumes truthful ShareLock observation and every relevant mutation reaching the installed fence. It proves neither installation/protection nor complete mutation coverage, acquisition/reparenting, PostgreSQL semantics, authentication, immutable source closure or final-disclosure lifetime. Native schedules supply separate limited evidence.

## Remaining limits

The fixture uses administrative native privileges and trusted installed trigger/function definitions. A privileged actor capable of disabling/replacing triggers, changing source or bypassing the selected table is outside its threat model. The fence does not establish protection from same-process tampering, complete DDL/source/configuration changes, or other archive representations. It does not remove upstream lock waits/contention or qualify whole CPU/allocation/scan/resource budgets. Integration with the original configured selector, protected host acquisition lifetime and final disclosure remains a later obligation. No full report authority/publication or security acceptance case is promoted.

Companions: `/private/tmp/astra-archive-self-write-fence-audit.json` and `/private/tmp/astra-archive-self-write-fence-replay.json`.
