#!/usr/bin/env python3
"""@covers US-048-AC7. Exhaustive bounded transition analysis, not native proof.

Two workers, two batches, three frozen targets; finite claim/lease bound.
State records actual graph/outcome persistence separately from observations.
Native transaction termination is nondeterministic; no timeout infers rollback.
"""
from collections import deque
from dataclasses import dataclass, replace, asdict
import hashlib
import json
from pathlib import Path

BATCHES = ((0, 1), (2,))
FROZEN_IDS = (2, 10, 11)

@dataclass(frozen=True)
class State:
    rollback_after_write: bool = False
    crashed_after_rollback: bool = False
    changes: tuple = (True, True, True)
    outcomes: tuple = (0,0,0)
    results: tuple = ("","","")
    published_results: tuple = ("","","")
    current_ids: tuple = FROZEN_IDS
    versions: tuple = (1, 1, 1)
    owner: int = -1
    fence: int = 0
    expired: bool = False
    attempt_owner: int = -1
    attempt_fence: int = 0
    batch: int = 0
    phase: str = 'idle'
    staged: tuple = (0, 0, 0)
    effects: tuple = (0, 0, 0)
    receipts: tuple = (False, False)
    prefix: int = 0
    observed: int = 0
    cancel_requested: bool = False
    cancel_fenced: bool = False
    terminal_cutoff: int = 2
    cancel_status: str = ""
    stopped: bool = False
    restored: bool = False
    recovering: bool = False
    attempts: tuple = (0, 0)
    late_dispatch: bool = False
    native_actual: str = "none"
    native_observed: str = "none"
    marker_actual: str = "none"
    marker_observed: str = "none"
    expired_admission: bool = False
    stale_write: bool = False
    identity_changed: bool = False


def transitions(s, mutation=None):
    """Each edge models a distinct protected/physical linearization point."""
    if not s.cancel_requested:
        yield 'request_cancel', replace(s, cancel_requested=True)
    # This intent request is not a durable cancel until the job lock is acquired.
    if s.cancel_requested and (s.stopped or s.prefix==2):
        yield 'cancel_terminal_observation',s
    if s.cancel_requested and not s.cancel_fenced and not s.stopped and s.prefix<2 and s.phase not in ('admitted', 'writing'):
        yield 'persist_cancel', replace(s, cancel_fenced=True, terminal_cutoff=min(s.terminal_cutoff,s.prefix),
                cancel_status='cancelled' if mutation=='premature_cancel' or (s.phase in ('idle','committed','settled') and s.native_observed in ('none','committed','aborted')) else 'reconciling')
    if not s.restored:
        # Without a complete graph/control/outcome consistency proof, restore fences.
        yield 'restore_fence', replace(s, restored=True, terminal_cutoff=min(s.terminal_cutoff,s.prefix))
    if s.owner >= 0 and not s.expired:
        yield 'expire_lease', replace(s, expired=True)
    if s.phase == 'idle' and s.prefix < 2 and not (s.restored or (s.cancel_fenced and mutation!='broken_cancel') or (s.stopped and mutation!='broken_terminal')):
        if (s.owner == -1 or s.expired) and s.fence < 2:
            for worker in (0, 1):
                yield f'claim_{worker}', replace(s, owner=worker, fence=s.fence+1, expired=False)
        if s.owner >= 0 and not s.expired:
            a = list(s.attempts); a[s.prefix] += 1
            yield 'open_original_native', replace(s, phase='native_open',rollback_after_write=False,crashed_after_rollback=False, native_actual='open',native_observed='open', marker_actual='none',marker_observed='none', attempt_owner=s.owner,
                attempt_fence=s.fence, batch=s.prefix, attempts=tuple(a),late_dispatch=s.late_dispatch or s.prefix>=s.terminal_cutoff)
    if s.phase=='native_open':
        yield 'register_marker_pending',replace(s,phase='marker_pending',marker_actual='pending',marker_observed='unknown')
    if s.phase=='marker_pending':
        for actual, phase in [('committed','registered'),('aborted','marker_aborted')]:
            yield 'marker_'+actual+'_ack',replace(s,phase=phase,marker_actual=actual,marker_observed=actual)
            yield 'marker_'+actual+'_ack_loss',replace(s,phase='registration_unknown',marker_actual=actual,marker_observed='unknown',recovering=True)
    if s.phase=='marker_aborted':
        yield 'close_unadmitted_native_abort',replace(s,phase='settled',native_actual='aborted',native_observed='aborted',stopped=True,terminal_cutoff=min(s.terminal_cutoff,s.prefix),cancel_status='stopped' if s.cancel_fenced else s.cancel_status)
    if s.phase not in ('admitted', 'writing') or mutation == 'broken_guard':
        for target in range(3):
            if s.versions[target] == 1 and s.effects[target] == 0:
                versions=list(s.versions);versions[target]=2
                yield f'external_edit_{target}', replace(s, versions=tuple(versions))
            if s.current_ids[target] == FROZEN_IDS[target] and s.effects[target] == 0:
                ids=list(s.current_ids);ids[target]+=100
                yield f'external_rebind_{target}', replace(s, current_ids=tuple(ids))
    if mutation=='broken_terminal' and s.phase=='settled' and s.stopped:
        yield 'unsafe_restart_stopped', replace(s,phase='idle',owner=-1)
    if s.cancel_fenced and s.phase=='registered':
        yield 'cancel_original_noncommit',replace(s,phase='rolled_back',recovering=True,native_actual='aborted',native_observed='aborted')
    if s.phase == 'registered' and not (s.cancel_fenced or s.restored):
        live_claim = s.owner==s.attempt_owner and s.fence==s.attempt_fence and not s.expired
        if (live_claim or mutation=='broken_admission') and all(s.current_ids[i]==FROZEN_IDS[i] and s.versions[i]==1 for i in BATCHES[s.batch]):
            yield 'confirm_admission_guard_lock', replace(s, phase='admitted', expired_admission=s.expired_admission or not live_claim)
        elif not live_claim:
            yield 'expired_claim_native_noncommit', replace(s, phase='rolled_back',native_actual='aborted',native_observed='aborted')
        else:
            for ack in (True,False):
                yield 'guard_conflict_commit_ack' if ack else 'guard_conflict_commit_ack_loss', replace(s,phase='settled' if ack else 'conflict_unknown',stopped=True,terminal_cutoff=min(s.terminal_cutoff,s.prefix),native_actual='committed',native_observed='committed' if ack else 'unknown',recovering=not ack)
    if s.phase == 'registration_unknown':
        # Exact original result recovery: never invent a second registration.
        if s.marker_actual=='committed':
            yield 'recover_registration_commit', replace(s,phase='registered',marker_observed='committed',recovering=False)
        elif s.marker_actual=='aborted':
            yield 'recover_registration_noncommit', replace(s,phase='marker_aborted',marker_observed='aborted',recovering=False)
        yield 'registration_lookup_unavailable',s
    if s.phase in ('admitted', 'writing') and not s.restored:
        if not s.recovering:
            yield 'crash_unresolved_running',replace(s,recovering=True,native_observed='unknown')
        if mutation=='missing_lookup_reclaim' and s.recovering:
            yield 'unsafe_missing_means_noncommit',replace(s,phase='idle',owner=-1,native_observed='aborted')
        fields = BATCHES[s.batch]
        if mutation == 'broken_fence' and s.expired and s.fence < 2:
            yield 'unsafe_takeover', replace(s, fence=s.fence+1, owner=1-s.owner, expired=False)
        if mutation == 'broken_recovery' and s.expired:
            yield 'unsafe_retry_admitted', replace(s, phase='idle', staged=(0, 0, 0), recovering=False)
        if s.attempt_fence == s.fence or mutation == 'broken_fence':
            for target in fields:
                if s.staged[target] == 0:
                    staged = list(s.staged); staged[target] = 1
                    yield f'write_{target}', replace(s, staged=tuple(staged), phase='writing',
                        stale_write=s.stale_write or s.attempt_fence != s.fence,
                        identity_changed=s.identity_changed or s.current_ids[target]!=FROZEN_IDS[target] or s.versions[target]!=1)
        if all(s.staged[i] == 1 for i in fields):
            effects = tuple(s.effects[i]+s.staged[i]*int(s.changes[i]) for i in range(3))
            outcomes=tuple(s.outcomes[i]+s.staged[i] for i in range(3))
            results=tuple(('changed' if s.changes[i] else 'noop') if s.staged[i] else s.results[i] for i in range(3))
            receipts = list(s.receipts); receipts[s.batch] = True
            for ack, phase in ((True, 'committed'), (False, 'commit_unknown')):
                yield 'commit_ack' if ack else 'commit_ack_loss', replace(s, effects=effects,
                    receipts=tuple(receipts),outcomes=outcomes,results=results, prefix=s.prefix+1, phase=phase,
                    recovering=not ack, staged=(0, 0, 0),
                    versions=tuple(s.versions[i]+s.staged[i]*int(s.changes[i]) for i in range(3)),native_actual='committed',native_observed='committed' if ack else 'unknown')
        if mutation == 'partial_commit' and any(s.staged):
            yield 'unsafe_partial_commit', replace(s, effects=tuple(s.effects[i]+s.staged[i] for i in range(3)),
                phase='commit_unknown', staged=(0, 0, 0), recovering=True)
        for ack, phase in ((True, 'rolled_back'), (False, 'rollback_unknown')):
            yield 'rollback_ack' if ack else 'rollback_ack_loss', replace(s, phase=phase,
                staged=(0, 0, 0), recovering=not ack,rollback_after_write=any(s.staged),native_actual='aborted',native_observed='aborted' if ack else 'unknown')
    if s.phase=='rolled_back' and s.rollback_after_write:
        yield 'crash_after_rollback_before_stop',replace(s,phase='rollback_unknown',native_observed='unknown',recovering=True,crashed_after_rollback=True)
    if s.phase=='conflict_unknown':
        yield 'reconcile_original_guard_conflict',replace(s,phase='settled',native_observed='committed',recovering=False,cancel_status=('stopped' if s.stopped else ('completed' if s.prefix==2 else 'cancelled')) if s.cancel_fenced else s.cancel_status)
        yield 'conflict_lookup_unavailable',s
    if s.phase in ('commit_unknown', 'rollback_unknown', 'rolled_back'):
        # Lost/absent/expired observations cannot settle original native work.
        yield 'lookup_unavailable', replace(s, recovering=True)
        if s.phase == 'commit_unknown':
            yield 'reconcile_original_commit', replace(s, phase='committed', recovering=False,native_observed='committed',cancel_status=('stopped' if s.stopped else ('completed' if s.prefix==2 else 'cancelled')) if s.cancel_fenced else s.cancel_status)
        else:
            yield 'reconcile_original_noncommit_stop', replace(s, phase='settled', stopped=True, recovering=False,native_observed='aborted', terminal_cutoff=min(s.terminal_cutoff,s.prefix), cancel_status='stopped' if s.cancel_fenced else s.cancel_status)
    if s.phase == 'committed':
        yield 'publish_original_result', replace(s, phase='idle', observed=s.prefix,published_results=s.results,
            owner=-1, expired=False, attempt_owner=-1, attempt_fence=0)
    # Refusals are observation-only: outsiders and not-found cannot mutate valid state.
    # They are explicit labels (self-loops); visited-state pruning retains their count.
    yield 'outsider_denied', s
    if s.recovering:
        yield 'not_found_unresolved', s


def violations(s):
    errors=[]
    if any(n > 1 for n in s.outcomes): errors.append('one_effect_per_item')
    if s.outcomes[0] != s.outcomes[1]: errors.append('atomic_first_batch')
    for b, fields in enumerate(BATCHES):
        if any(s.outcomes[i] != int(s.receipts[b]) for i in fields):errors.append('effects_and_complete_receipt_atomic')
    if any(s.effects[i]!=s.outcomes[i]*int(s.changes[i]) for i in range(3)):errors.append('exact_noop_or_changed_effect')
    if any(s.results[i] != (('changed' if s.changes[i] else 'noop') if s.outcomes[i] else '') for i in range(3)):errors.append('complete_original_item_results')
    if any(s.published_results[i] != (s.results[i] if i in tuple(j for b in range(s.observed) for j in BATCHES[b]) else '') for i in range(3)):errors.append('unchanged_published_results')
    if s.receipts != tuple(i < s.prefix for i in range(2)):errors.append('contiguous_durable_prefix')
    if s.observed > s.prefix:errors.append('observations_require_original_commit')
    if s.prefix>s.terminal_cutoff:errors.append('no_commit_beyond_terminal_cutoff')
    if s.late_dispatch:errors.append('no_dispatch_beyond_terminal_cutoff')
    if s.native_observed=='committed' and s.native_actual!='committed':errors.append('original_commit_observation')
    if s.phase in ('committed','commit_unknown') and (s.native_actual!='committed' or not s.receipts[s.batch]):errors.append('native_commit_complete_result')
    if s.native_observed=='aborted' and s.native_actual!='aborted':errors.append('no_invented_noncommit')
    if s.phase in ('admitted','writing') and (s.marker_actual!='committed' or s.marker_observed!='committed'):errors.append('confirmed_marker_before_effects')
    if s.cancel_status=='cancelled' and (s.stopped or s.prefix==2):errors.append('terminal_state_preserved')
    if s.cancel_status=='cancelled' and (s.phase not in ('idle','committed','settled') or s.native_observed not in ('none','committed','aborted') or s.native_actual not in ('none','committed','aborted')):errors.append('cancelled_requires_original_settlement')
    if s.expired_admission:errors.append('live_claim_at_job_lock')
    if s.stale_write:errors.append('no_stale_fence_write')
    if s.identity_changed:errors.append('frozen_target_identity')
    if any(a > 1 for a in s.attempts):errors.append('no_retry_admitted_original_batch')
    return errors


def trace(parent, s):
    result=[]
    while parent[s] is not None:
        previous, event=parent[s];result.append(event);s=previous
    return list(reversed(result))


def explore(mutation=None):
    initial=[State(changes=tuple(bool(mask & (1<<i)) for i in range(3))) for mask in range(8)]
    queue=deque(initial);parents={s:None for s in initial};events={};witnesses={}
    while queue:
        current=queue.popleft()
        for event, next_state in transitions(current, mutation):
            events[event]=events.get(event,0)+1
            errors=violations(next_state)
            if errors:
                return {'safe':False,'states':len(parents),'violations':errors,'trace':trace(parents,current)+[event]}
            for e,w in [('reconcile_original_commit','lost_ack_recovery'),('reconcile_original_noncommit_stop','rollback_before_stop'),('crash_unresolved_running','unresolved_original_running')]:
                if event==e and w not in witnesses and (w!='rollback_before_stop' or (current.rollback_after_write and current.crashed_after_rollback)):witnesses[w]=trace(parents,current)+[event]
            if next_state not in parents:
                parents[next_state]=(current,event);queue.append(next_state)
                if next_state.prefix==2 and next_state.observed==2 and not next_state.stopped:
                    witnesses.setdefault('two_batch_commit',trace(parents,next_state))
                if next_state.cancel_fenced and next_state.prefix==1:witnesses.setdefault('cancel_preserves_prefix',trace(parents,next_state))
    return {'safe':True,'states':len(parents),'edges':sum(events.values()),'events':events,'witnesses':witnesses}


def main():
    good=explore();assert good['safe'],good
    assert set(good['witnesses'])=={'two_batch_commit','lost_ack_recovery','rollback_before_stop','cancel_preserves_prefix','unresolved_original_running'},good
    controls={name:explore(name) for name in ('broken_fence','broken_recovery','partial_commit','broken_guard','broken_admission','broken_cancel','broken_terminal','premature_cancel','missing_lookup_reclaim')}
    assert all(not x['safe'] for x in controls.values()),controls
    report={'scope':'Bounded design state model; no native adapter or temporal fairness qualification',
        'targets':list(FROZEN_IDS),'batches':[list(x) for x in BATCHES],'workers':2,
        'claimFenceBound':2,'initialChangeMasks':8,'passed':True,'model':good,'negativeControls':controls,
        'sourceSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'livenessPremises':['fair scheduling','eventual original native termination','available current-authorized original lookup'],
        'livenessVerified':False,'nativeQualified':False}
    output=Path(__file__).resolve().parents[3]/'04-build/evidence/bulk-update/batch-model-results.json'
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('model','negativeControls')},indent=2))
    print(json.dumps({'states':good['states'],'edges':good['edges'],'controls':{k:v['violations'] for k,v in controls.items()}}))

if __name__=='__main__':main()
