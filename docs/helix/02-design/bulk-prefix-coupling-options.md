---
ddx:
  id: truss.bulk-prefix-coupling-options
  type: status-report
  activity: design
  status: draft
  authoring:
    home: repo
  links:
    - id: CONTRACT-013
      kind: informed_by
    - id: CONTRACT-009
      kind: informed_by
    - id: TD-048
      kind: informed_by
---

# Bulk jobs: how the committed prefix is coupled to the effect transaction

Status: **decision needed** (owner). Written 2026-11-10 after the candidate control functions
(`bulk-control-functions.sql`, role `bulk-worker`, job lock at CONTRACT-009 level 4a) were verified on a
scratch PostgreSQL 18.6. Nothing here is installed or qualified.

## The gap

CONTRACT-013 requires that graph data, item replay outcomes, the batch's complete-result receipt, the job's
committed-prefix advance, journal and selected outbox facts **commit together**. The candidate layout does
not yet say which transaction advances `truss_bulk.job.committed_batches`:

- the candidate functions advance it in `worker_event(commit)`, a separate call;
- the receipt is written by the same call, but the graph/journal writes belong to the executor's effect
  transaction, which this repository has not implemented;
- if the call runs in a different transaction from the graph writes, a crash or lost acknowledgement can leave
  the graph committed and the job row behind it (or the reverse).

Which transaction owns the advance decides how recovery works, what `reconciling` means, what the model
and the UMF-portable contract must say, and what can be tested natively.

## What is already established (so it need not be re-decided)

- The job row lock (level 4a) is taken by whoever calls the functions and is held until that transaction
  ends. Verified: a second claimant, a cancel and a waiting `execute` all block on it, in both orders, and a
  call holds relation locks on the job home only (no advisory locks).
- The effect transaction must hold the job lock through native completion (CONTRACT-013, "Original native
  attempt custody"); the control connection registers the admitted attempt **before** the effect transaction
  takes the lock, and does not take a lock the effect transaction holds.
- The job row's CHECK constraints reject any state the model cannot reach, and the candidate functions agree
  with the pure model on 400 random sequences. These hold under every option below.

## Options

### 1. Advance inside the effect transaction (recommended)

The executor calls `worker_event(commit, result)` **in the effect transaction**, after the business writes and
before COMMIT. Receipt insert, prefix advance and the status change share the transaction with the graph,
journal and outbox writes, so they are atomic by construction.

- Lost acknowledgement: the job row is already advanced iff the commit happened. The host's "uncertain"
  condition is resolved by *reading the row*, not by a second write. A control call cannot even record
  `lose-custody` while the effect transaction is in flight: it must take the same lock (a cancel waiting on
  it was verified; `lose-custody` uses the identical lock and was not run concurrently), and after commit it
  finds a queued/completed job and refuses.
- Rolled-back effect transaction: the row is untouched (still running, admission recorded). Reconciliation
  records `noncommit-admitted` and the job stops with `PAP_ABORT_DISPOSITION_UNKNOWN`, as today.
- `reconcile(committed)` stops being a state-advancing write in Truss; it becomes an observation. UMF's
  portable CONTRACT-904 table keeps the row for executors whose control store differs from the effect store.
- Needs: the effect connection runs as `bulk-worker` (already the only role with the function); `commit`
  must require a non-null result (today optional); `reconcile(committed)` must verify the receipt row (today
  it does not).
- Cost: the lock is held across the whole batch (already required), so long batches block cancel until commit
  (already the designed behaviour).

### 2. Advance by trigger on receipt insert (option 1, enforced structurally)

An AFTER INSERT trigger on `batch_receipt` advances the job row (same transaction, lock already held).
A receipt can then never exist without its prefix advance, even if an executor forgets the call.

- Benefit: removes a class of executor bugs; the invariant lives in the database.
- Cost: the state machine is split between function and trigger; the final-batch/cancel rule must be
  implemented once and tested through both paths; harder to read and to qualify; the trigger hides a
  lock-taking write inside an INSERT.
- Variant (cheap, recommended *with* option 1): keep the explicit call, add a **deferred constraint trigger**
  that, at COMMIT, checks `committed_batches` equals the count of contiguous receipts for the job. It adds no
  logic, only a safety net, and is straightforward to test with deliberately wrong executors.

### 3. Advance in a separate control transaction after the effect commits

The effect transaction commits graph, receipt and journal only. A later control transaction observes the
receipt (matching claim fence) and advances the prefix.

- Benefit: no function call inside the effect transaction; the effect path touches only business homes and the
  receipt.
- Cost: a real window where graph and receipt are durable but the prefix is behind. The admitted claim must
  stay pinned (it is: `expire-claim` refuses admitted claims) and recovery must discover receipts after a
  crash. Status counts "confirmed" outcomes, so users see a stale prefix until recovery runs; cancel and a
  new claim must keep refusing across the window. `reconcile(committed)` is a real state-advancing write
  and must verify the receipt.
- This matches the current candidate functions most closely, but it is the option with the most failure
  states to qualify.

## Comparison

| | 1. In effect tx | 2. Trigger | 3. Separate control tx |
| --- | --- | --- | --- |
| Atomic with graph/journal | yes | yes, enforced | no (window) |
| Executor can forget the advance | yes (mitigate: deferred check) | no | yes (recovery covers) |
| `lose-custody` / `reconciling` | resolved by reading the row | same | needed after every crash |
| Failure states to qualify | fewest | few, plus trigger paths | most |
| Change to current candidate | `commit` strictness, `reconcile` verifies receipt | move final-batch rule to trigger | add receipt verification, recovery scan |
| Change to UMF portable contract | none | none | none |

## Recommendation

Option 1, with the deferred constraint-trigger safety net from option 2. It keeps one readable state machine,
makes the contract's "commit together" true by construction, and shrinks the reconciling surface to
"effect transaction rolled back or unknown".

## Decisions needed from the owner

1. Which option (1, 2 or 3), and whether to add the deferred safety net.
2. Whether `reconcile(committed)` in Truss is an observation of the already-advanced row (options 1 and 2) or
   a state-advancing write (option 3).
3. Whether CONTRACT-013 should state the chosen coupling in its normative text; today it says the effects
   "commit together" without naming the transaction that carries the advance.

## What changes after a decision

- Option 1: tighten `commit` and `reconcile` in `bulk-control-functions.sql`; add a native check that runs
  graph-like writes, receipt and advance in one transaction and kills the session at each point
  (before/after the call, before/after COMMIT) asserting the row either fully advanced or not at all;
  update `BulkUpdate.tla` so a lost-acknowledgement commit leaves the job row already advanced and
  re-run TLC; update `_bulk_job_control.py` and its tests only if `reconcile(committed)` semantics change.
- Option 2: as option 1, plus the trigger and tests through both paths.
- Option 3: add receipt-verified advance and a recovery scan, and a native check that crashes between the
  effect commit and the advance.

Not decided by this note: levels 1-4 lock acquisition, authority and custody records, lease timing, the
install baseline, or UMF's export of the layout. Native US-046-049 criteria stay planned.
