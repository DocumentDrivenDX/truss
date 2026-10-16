----------------------------- MODULE BulkUpdate -----------------------------
EXTENDS Integers, Sequences, TLC
\* Design model only: actual PostgreSQL/authority obligations are external premises.
VARIABLE s
vars == <<s>>
Ids == <<2, 10, 11>>
Batch(b) == IF b = 0 THEN {1, 2} ELSE {3}
Active == s.phase \in {"admitted", "writing"}
Blocked == s.cancel_fenced \/ s.stopped \/ s.restored
Init == \E change \in [1..3 -> BOOLEAN]: s = [rollback_after_write |-> FALSE, crashed_after_rollback |-> FALSE, changes |-> change,
      outcomes |-> <<0,0,0>>,
      results |-> <<"","","">>,
      published_results |-> <<"","","">>,
      current_ids |-> <<2,10,11>>,
      versions |-> <<1,1,1>>,
      owner |-> -1,
      fence |-> 0,
      expired |-> FALSE,
      attempt_owner |-> -1,
      attempt_fence |-> 0,
      batch |-> 0,
      phase |-> "idle",
      staged |-> <<0,0,0>>,
      effects |-> <<0,0,0>>,
      receipts |-> <<FALSE,FALSE>>,
      prefix |-> 0,
      observed |-> 0,
      cancel_requested |-> FALSE,
      cancel_fenced |-> FALSE,
      terminal_cutoff |-> 2,
      cancel_status |-> "",
      stopped |-> FALSE,
      restored |-> FALSE,
      recovering |-> FALSE,
      attempts |-> <<0,0>>,
      late_dispatch |-> FALSE,
      native_actual |-> "none",
      native_observed |-> "none",
      marker_actual |-> "none",
      marker_observed |-> "none",
      expired_admission |-> FALSE,
      stale_write |-> FALSE,
      identity_changed |-> FALSE]
RequestCancel ==
 /\ ~s.cancel_requested
                 /\ s' = [s EXCEPT !.cancel_requested = TRUE]
PersistCancel ==
 /\ s.cancel_requested /\ ~s.cancel_fenced /\ ~s.stopped /\ s.prefix < 2 /\ ~Active
                 /\ s' = [s EXCEPT !.cancel_fenced = TRUE, !.terminal_cutoff = IF s.prefix < @ THEN s.prefix ELSE @,
      !.cancel_status = IF s.phase \in {"idle","committed","settled"} /\ s.native_observed \in {"none","committed","aborted"} THEN "cancelled" ELSE "reconciling"]
RestoreFence ==
 /\ ~s.restored /\ s' = [s EXCEPT !.restored = TRUE, !.terminal_cutoff = IF s.prefix < @ THEN s.prefix ELSE @]
Expire ==
 /\ s.owner >= 0 /\ ~s.expired
          /\ s' = [s EXCEPT !.expired = TRUE]
Claim(w) ==
 /\ s.phase = "idle" /\ s.prefix < 2 /\ ~Blocked
            /\ s.fence < 2 /\ (s.owner = -1 \/ s.expired)
            /\ s' = [s EXCEPT !.owner = w, !.fence = @ + 1, !.expired = FALSE]
Register ==
 /\ s.phase = "idle" /\ s.prefix < 2 /\ ~Blocked
            /\ s.owner >= 0 /\ ~s.expired
            /\ s' = [s EXCEPT !.phase = "native_open", !.rollback_after_write = FALSE, !.crashed_after_rollback = FALSE, !.native_actual = "open", !.native_observed = "open", !.marker_actual = "none", !.marker_observed = "none", !.late_dispatch = @ \/ s.prefix >= s.terminal_cutoff, !.attempt_owner = s.owner,
      !.attempt_fence = s.fence, !.batch = s.prefix,
      !.attempts[s.prefix+1] = @ + 1]
GuardOK == \A i \in Batch(s.batch): s.current_ids[i] = Ids[i] /\ s.versions[i] = 1
LiveClaim == s.owner = s.attempt_owner /\ s.fence = s.attempt_fence /\ ~s.expired
Admit ==
 /\ LiveClaim /\ s.phase = "registered" /\ ~s.cancel_fenced /\ ~s.restored /\ GuardOK
         /\ s' = [s EXCEPT !.phase = "admitted", !.expired_admission = @ \/ ~LiveClaim]
ExpiredClaimNoncommit ==
 /\ s.phase = "registered" /\ ~s.cancel_fenced /\ ~s.restored /\ ~LiveClaim
 /\ s' = [s EXCEPT !.phase = "rolled_back", !.native_actual = "aborted", !.native_observed = "aborted"]
GuardConflict(ack) ==
 /\ LiveClaim /\ s.phase = "registered" /\ ~s.cancel_fenced /\ ~s.restored /\ ~GuardOK
 /\ s' = [s EXCEPT !.phase = IF ack THEN "settled" ELSE "conflict_unknown",
      !.stopped = TRUE, !.terminal_cutoff = IF s.prefix < @ THEN s.prefix ELSE @,
      !.native_actual = "committed", !.native_observed = IF ack THEN "committed" ELSE "unknown", !.recovering = ~ack]
MarkerPending ==
 /\ s.phase = "native_open"
 /\ s' = [s EXCEPT !.phase = "marker_pending", !.marker_actual = "pending", !.marker_observed = "unknown"]
MarkerCommit(commit,ack) ==
 /\ s.phase = "marker_pending"
 /\ s' = [s EXCEPT !.marker_actual = IF commit THEN "committed" ELSE "aborted",
      !.marker_observed = IF ack THEN (IF commit THEN "committed" ELSE "aborted") ELSE "unknown",
      !.phase = IF ack THEN (IF commit THEN "registered" ELSE "marker_aborted") ELSE "registration_unknown", !.recovering = ~ack]
RecoverRegistration ==
 /\ s.phase = "registration_unknown"
 /\ s.marker_actual \in {"committed","aborted"}
 /\ s' = [s EXCEPT !.phase = IF s.marker_actual = "committed" THEN "registered" ELSE "marker_aborted",
      !.marker_observed = s.marker_actual, !.recovering = FALSE]
CloseUnadmitted ==
 /\ s.phase = "marker_aborted"
 /\ s' = [s EXCEPT !.phase = "settled", !.native_actual = "aborted", !.native_observed = "aborted",
      !.stopped = TRUE, !.terminal_cutoff = IF s.prefix < @ THEN s.prefix ELSE @,
      !.cancel_status = IF s.cancel_fenced THEN "stopped" ELSE @]
CancelNoncommit ==
 /\ s.phase = "registered" /\ s.cancel_fenced
 /\ s' = [s EXCEPT !.phase = "rolled_back", !.native_actual = "aborted", !.native_observed = "aborted", !.recovering = TRUE]
CrashRunning ==
 /\ Active /\ ~s.restored /\ ~s.recovering
 /\ s' = [s EXCEPT !.recovering = TRUE, !.native_observed = "unknown"]
ReconcileConflict ==
 /\ s.phase = "conflict_unknown"
 /\ s' = [s EXCEPT !.phase = "settled", !.native_observed = "committed", !.recovering = FALSE,
      !.cancel_status = IF s.cancel_fenced THEN (IF s.stopped THEN "stopped" ELSE IF s.prefix = 2 THEN "completed" ELSE "cancelled") ELSE @]
ExternalEdit(i) ==
 /\ ~Active /\ s.versions[i] = 1 /\ s.effects[i] = 0
                   /\ s' = [s EXCEPT !.versions[i] = 2]
ExternalRebind(i) ==
 /\ ~Active /\ s.current_ids[i] = Ids[i] /\ s.effects[i] = 0
                     /\ s' = [s EXCEPT !.current_ids[i] = @ + 100]
Write(i) ==
 /\ Active /\ ~s.restored /\ i \in Batch(s.batch)
            /\ s.attempt_fence = s.fence /\ s.staged[i] = 0
            /\ s' = [s EXCEPT !.staged[i] = 1, !.phase = "writing",
      !.stale_write = @ \/ s.attempt_fence # s.fence,
      !.identity_changed = @ \/ s.current_ids[i] # Ids[i] \/ s.versions[i] # 1]
Commit(ack) ==
 /\ Active /\ ~s.restored /\ \A i \in Batch(s.batch): s.staged[i] = 1
 /\ s' = [s EXCEPT !.effects = [i \in 1..3 |-> s.effects[i] + (IF s.changes[i] THEN s.staged[i] ELSE 0)],
      !.versions = [i \in 1..3 |-> s.versions[i] + (IF s.changes[i] THEN s.staged[i] ELSE 0)],
      !.outcomes = [i \in 1..3 |-> s.outcomes[i] + s.staged[i]],
      !.results = [i \in 1..3 |-> IF s.staged[i] = 1 THEN (IF s.changes[i] THEN "changed" ELSE "noop") ELSE s.results[i]],
      !.native_actual = "committed", !.native_observed = IF ack THEN "committed" ELSE "unknown", !.receipts[s.batch+1] = TRUE, !.prefix = @ + 1,
      !.phase = IF ack THEN "committed" ELSE "commit_unknown",
      !.recovering = ~ack, !.staged = <<0,0,0>>]
Rollback(ack) ==
 /\ Active /\ ~s.restored
 /\ s' = [s EXCEPT !.phase = IF ack THEN "rolled_back" ELSE "rollback_unknown",
      !.recovering = ~ack, !.rollback_after_write = (\E i \in 1..3: s.staged[i] = 1), !.native_actual = "aborted", !.native_observed = IF ack THEN "aborted" ELSE "unknown", !.staged = <<0,0,0>>]
CrashAfterRollback ==
 /\ s.phase = "rolled_back" /\ s.rollback_after_write
 /\ s' = [s EXCEPT !.phase = "rollback_unknown", !.native_observed = "unknown", !.recovering = TRUE, !.crashed_after_rollback = TRUE]
LookupUnavailable ==
 /\ s.phase \in {"commit_unknown", "rollback_unknown", "rolled_back"}
                     /\ s' = [s EXCEPT !.recovering = TRUE]
ReconcileCommit ==
 /\ s.phase = "commit_unknown"
                   /\ s' = [s EXCEPT !.phase = "committed", !.recovering = FALSE, !.native_observed = "committed", !.cancel_status = IF s.cancel_fenced THEN (IF s.stopped THEN "stopped" ELSE IF s.prefix = 2 THEN "completed" ELSE "cancelled") ELSE @]
ReconcileNoncommit ==
 /\ s.phase \in {"rollback_unknown", "rolled_back"}
 /\ s' = [s EXCEPT !.phase = "settled", !.stopped = TRUE, !.recovering = FALSE, !.native_observed = "aborted", !.terminal_cutoff = IF s.prefix < @ THEN s.prefix ELSE @, !.cancel_status = IF s.cancel_fenced THEN "stopped" ELSE @]
Publish ==
 /\ s.phase = "committed"
 /\ s' = [s EXCEPT !.phase = "idle", !.observed = s.prefix, !.published_results = s.results, !.owner = -1,
      !.expired = FALSE, !.attempt_owner = -1, !.attempt_fence = 0]
Next ==
 \/ RequestCancel \/ PersistCancel \/ RestoreFence \/ Expire \/ Register \/ Admit
 \/ ExpiredClaimNoncommit \/ MarkerPending \/ RecoverRegistration \/ CloseUnadmitted \/ CancelNoncommit
 \/ CrashRunning \/ CrashAfterRollback \/ ReconcileConflict \/ LookupUnavailable \/ ReconcileCommit \/ ReconcileNoncommit \/ Publish
 \/ (\E w \in {0,1}: Claim(w))
 \/ (\E b \in BOOLEAN: GuardConflict(b) \/ Commit(b) \/ Rollback(b))
 \/ (\E c \in BOOLEAN: \E a \in BOOLEAN: MarkerCommit(c,a))
 \/ (\E i \in 1..3: ExternalEdit(i) \/ ExternalRebind(i) \/ Write(i))
Spec == Init /\ [][Next]_vars
OneEffect == \A i \in 1..3: s.outcomes[i] \in 0..1
AtomicBatch == s.outcomes[1] = s.outcomes[2]
CompleteReceipts == \A b \in 0..1: \A i \in Batch(b):
      s.outcomes[i] = IF s.receipts[b+1] THEN 1 ELSE 0
ContiguousPrefix == \A b \in 0..1: s.receipts[b+1] = (b < s.prefix)
OriginalObservation == s.observed <= s.prefix
LiveAdmission == ~s.expired_admission
NoLateDispatch == ~s.late_dispatch /\ s.prefix <= s.terminal_cutoff
ObservedCommit == s.native_observed = "committed" => s.native_actual = "committed"
NativeCommitResult == (s.phase \in {"committed","commit_unknown"}) => (s.native_actual = "committed" /\ s.receipts[s.batch+1])
TerminalPreserved == s.cancel_status = "cancelled" => (~s.stopped /\ s.prefix < 2)
NoInventedNoncommit == s.native_observed = "aborted" => s.native_actual = "aborted"
ConfirmedMarker == Active => (s.marker_actual = "committed" /\ s.marker_observed = "committed")
SettledCancel == s.cancel_status = "cancelled" => (s.phase \in {"idle","committed","settled"} /\ s.native_actual \in {"none","committed","aborted"} /\ s.native_observed \in {"none","committed","aborted"})
ExactChanges == \A i \in 1..3: s.effects[i] = IF s.changes[i] THEN s.outcomes[i] ELSE 0
ExactResults == \A i \in 1..3: s.results[i] = IF s.outcomes[i] = 0 THEN "" ELSE (IF s.changes[i] THEN "changed" ELSE "noop")
OriginalResults == \A i \in 1..3: s.published_results[i] = IF (i <= 2 /\ s.observed >= 1) \/ (i = 3 /\ s.observed = 2) THEN s.results[i] ELSE ""
NoStaleWrite == ~s.stale_write
FrozenTarget == ~s.identity_changed
NoAdmittedRetry == \A b \in 1..2: s.attempts[b] <= 1
\* No unconditional liveness property: original termination/authorized lookup
\* and fairness assumptions are not guaranteed during partition or revocation.
=============================================================================
