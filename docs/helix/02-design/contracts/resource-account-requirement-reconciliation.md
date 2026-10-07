# Resource account and host requirement reconciliation

PRD FR-43 requires no session state and transaction-mode pooling with and without prepared statements. FR-33–35 require honest enforcement classification and bypass evidence. FR-56 requires complete reproducible physical layout plus parity/behavior evidence. CONTRACT-007's backend-local cumulative account is an unadopted realization proposal; it cannot override those requirements by excluding poolers or calling its backend affinity an accepted support restriction.

## Composition gate

Distinguish connection/backend incarnation, actual transaction epoch and assembly lifetime. A transaction-mode pooler may move later transactions to another backend; no later transaction can depend on a previous backend's private account. Account creation must be explicit original transaction admission, all participating work must stay on its admitted epoch, and confirmed epoch termination must make old custody unusable before backend reuse. Unknown termination preserves recovery custody without transferring a live account to another backend. Pooler/backend reuse cannot reset a still-live operation's cumulative spend.

The profile must reconcile these internal enforcement facts with FR-43's no-session-state meaning in the governing architecture/ADR. Ordinary session settings, warmed callbacks or preloaded backend memory cannot become an undocumented prerequisite. If the proposed account requires state surviving transaction handoff or session affinity, it conflicts with FR-43 and cannot be adopted as the required profile. A proposed alternative must preserve the governing pooler/transaction semantics; narrowing support needs an explicit owner requirement change.

Prepared and unprepared execution need independently equivalent semantic/account/cleanup results, not an assumption from shared SQL text. Parallel/delegated work, supplied host commands and native administrative paths must each be accounted for or explicitly excluded from the candidate without misrepresenting the required product's support. No caller-owned commit, callback retry or private pooled connection may repair a lost account.

## Required selection record

Before choosing a native extension or driver account implementation, record: original epoch/incarnation producer, account creation/charge/cleanup signatures, complete participating path inventory, transaction-mode pooler handoff procedure, prepared/unprepared behavior, original failure/recovery custody, finite capacity/work rules and deployment continuity. The owner permits an extension only when it ships with the selected RDS PostgreSQL, Aurora PostgreSQL and Lakebase profiles. No common extension/version evidence is currently supplied by this source audit.

This document does not claim the native proposal is impossible or select a substitute. It identifies the missing compatibility proof. Numerical candidate limits and a host ledger cannot by themselves establish unavoidable native accounting. Likewise, the PRD does not currently name every rollback-resistant cumulative native counter as a separate numbered requirement; each claimed guarantee needs explicit governing traceability and its chosen enforcement classification.

## Independent planned schedules

RA-P01: two successive pooler transactions use different native backends, preserving admitted behavior without account reuse or session setup dependence.

RA-P02: a backend serves two unrelated transaction epochs; the second cannot spend against, observe or revive the first's custody, including after rollback.

RA-P03: lose termination acknowledgment and let pooler reuse become uncertain; prevent new admission/publication under old custody until original settlement is independently observed.

RA-P04: compare prepared/unprepared execution across fresh/reused backends, cancellation, savepoint rollback and failure, with independently observed counters and graph/host state.

RA-P05: execute native bypass and delegated/parallel paths; independently demonstrate the claimed unavoidable accounting or report its exact unqualified/excluded candidate scope without asserting full FR-43 support.

These schedules are not_run. The open item is original requirement/profile reconciliation followed by implementation evidence; it is not a new UMF feature or Weft compiler request.
