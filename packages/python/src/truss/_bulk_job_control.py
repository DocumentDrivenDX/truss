# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pure bulk job-control core (UMF CONTRACT-904 / Truss CONTRACT-013); no I/O, no native custody.

It evaluates control-state transitions, fences, item tokens, the delegation -> guard -> tx/1 decision
order and the CONTRACT-013 capacity rule from supplied facts only. It reads no clock, opens no
connection, authenticates nobody and attests nothing about native locks or PostgreSQL commit.
States are plain dicts shaped like the UMF owner fixture. The native executor must call this and
persist the result under the job lock; this module is not that executor.
"""
import copy
import re

TERMINAL = frozenset(('completed', 'stopped', 'cancelled'))
_FENCE = re.compile(r'^(0|[1-9][0-9]*)$')
_SEGMENT = re.compile(r'^[A-Za-z0-9_-]{1,128}$')
_CANONICAL = _FENCE


class BulkRefusal(ValueError):
    def __init__(self, code, message=''):
        super().__init__(f'{code}: {message}' if message else code)
        self.code = code


def _refuse(code=None):
    return {'ok': False, 'code': code} if code else {'ok': False}


def _accept(state, basis=None):
    return {'ok': True, 'state': state, 'basis': basis} if basis else {'ok': True, 'state': state}


def next_fence(fence):
    """Exact unsigned decimal text incremented without wrap; anything else refuses."""
    if not isinstance(fence, str) or not _FENCE.match(fence):
        raise BulkRefusal('PAP_FENCE', 'fence must be exact unsigned decimal text')
    return str(int(fence) + 1)


def _advance(s):
    nxt = s['nextBatch'] + 1
    s['nextBatch'] = nxt
    s['committedBatches'] += 1
    s['claim'] = None
    # Nothing remains to cancel once every batch is committed, so completed wins over a pending cancel
    # (matches BulkUpdate.tla TerminalPreserved: cancelled implies fewer than all batches committed).
    s['status'] = 'completed' if nxt == s['batchCount'] else ('cancelled' if s['cancelRequested'] else 'queued')
    return s


def apply_event(state, event):
    """Apply one event to a job state (None before submit); never mutates its inputs."""
    kind = event.get('kind')
    if state is None:
        if kind != 'submit':
            return _refuse()
        n = event.get('batchCount')
        if isinstance(n, bool) or not isinstance(n, int) or n < 0:
            return _refuse()
        return _accept({'status': 'completed' if n == 0 else 'queued', 'batchCount': n, 'nextBatch': 0,
                        'committedBatches': 0, 'fence': '0', 'claim': None, 'cancelRequested': False, 'stop': None},
                       'empty-manifest' if n == 0 else 'seal-delegation-intent-capacity')
    s = copy.deepcopy(state)
    if s['status'] in TERMINAL:
        if kind == 'cancel':
            return _accept(s, 'terminal-noop')
        if s['status'] == 'cancelled' and kind in ('claim', 'execute'):
            return _refuse('PAP_CANCELLED')
        return _refuse()
    if kind == 'cancel':
        claim = s['claim']
        if s['status'] == 'queued' or (s['status'] == 'running' and claim is not None and not claim['effectAdmitted']):
            s['status'] = 'cancelled'
            s['claim'] = None
            return _accept(s)
        s['cancelRequested'] = True
        return _accept(s, 'cancel-requested')
    if s['status'] == 'queued':
        if kind == 'claim':
            fence = next_fence(s['fence'])
            s['status'], s['fence'] = 'running', fence
            s['claim'] = {'batch': s['nextBatch'], 'fence': fence, 'effectAdmitted': False}
            return _accept(s)
        return _refuse('PAP_FENCE') if kind == 'execute' else _refuse()
    claim = s['claim']
    if s['status'] == 'running' and claim is not None:
        if kind == 'execute':
            if s['cancelRequested']:
                return _refuse('PAP_CANCELLED')
            if event.get('fence') != claim['fence']:
                return _refuse('PAP_FENCE')
            if event.get('batch') != claim['batch']:
                return _refuse('PAP_ORDER')
            if claim['effectAdmitted']:
                return _refuse()
            claim['effectAdmitted'] = True
            return _accept(s)
        if kind == 'commit':
            return _accept(_advance(s)) if claim['effectAdmitted'] else _refuse()
        if kind == 'failure':
            s['status'], s['stop'], s['claim'] = 'stopped', {'batch': claim['batch'], 'code': event['code']}, None
            return _accept(s)
        if kind == 'lose-custody':
            if not claim['effectAdmitted']:
                return _refuse()
            s['status'] = 'reconciling'
            return _accept(s)
        if kind == 'expire-claim':
            if claim['effectAdmitted'] or not event.get('confirmedNoExecution'):
                return _refuse()
            s['status'], s['claim'] = 'queued', None
            return _accept(s)
        return _refuse()
    if s['status'] == 'reconciling' and claim is not None and kind == 'reconcile':
        evidence = event.get('evidence')
        if evidence == 'committed':
            return _accept(_advance(s))
        if evidence == 'noncommit-admitted':
            s['status'], s['claim'] = 'stopped', None
            s['stop'] = {'batch': claim['batch'], 'code': 'PAP_ABORT_DISPOSITION_UNKNOWN'}
            return _accept(s)
        return _accept(s, 'unresolved')  # not-found, null status, expired lease etc. never prove rollback
    return _refuse()


def decision_order(delegation, guards, tx1=None, guard_item=None):
    """Delegation, then batch guards, then tx/1; guard conflicts are never translated to tx/1 codes."""
    if delegation != 'valid':
        return {'status': 'denied', 'code': 'AUTHORIZATION', 'tx1Invoked': False, 'itemOutcome': False}
    if guards != 'pass':
        out = {'status': 'conflict', 'code': 'PAP_GUARD', 'tx1Invoked': False, 'itemOutcome': False}
        if guard_item is not None:
            out['item'] = guard_item
        return out
    if tx1 is None:
        raise BulkRefusal('PAP_ORDER', 'tx/1 result required once guards pass')
    d = tx1['decision']
    if d == 'committed':
        return {'status': 'committed', 'tx1Invoked': True, 'itemOutcome': True}
    if d in ('conflict', 'rejected'):
        return {'status': d, 'code': tx1['code'], 'item': tx1['item'], 'tx1Invoked': True, 'itemOutcome': True}
    return {'status': 'rejected', 'code': 'ENTITY_MISSING', 'item': tx1['item'], 'tx1Invoked': True,
            'itemOutcome': True, 'qualificationFault': True}


def _ordinal(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


def item_token(namespace, id_, batch, item):
    """`pap1/<namespace>/<id>/<batch>/<item>`; restricted ASCII segments make it injective."""
    if not (isinstance(namespace, str) and _SEGMENT.match(namespace) and isinstance(id_, str) and _SEGMENT.match(id_)):
        raise BulkRefusal('PAP_INVALID', 'JobRef segments must match [A-Za-z0-9_-]{1,128}')
    if not (_ordinal(batch) and _ordinal(item)):
        raise BulkRefusal('PAP_INVALID', 'batch and item must be canonical unsigned integers')
    return f'pap1/{namespace}/{id_}/{batch}/{item}'


def parse_item_token(key):
    p = key.split('/') if isinstance(key, str) else []
    if len(p) != 5 or p[0] != 'pap1' or not _SEGMENT.match(p[1]) or not _SEGMENT.match(p[2]) \
            or not _CANONICAL.match(p[3]) or not _CANONICAL.match(p[4]):
        raise BulkRefusal('PAP_INVALID', 'malformed reserved bulk token')
    return {'namespace': p[1], 'id': p[2], 'batch': int(p[3]), 'item': int(p[4])}


def is_reserved_key(key):
    return isinstance(key, str) and key.startswith('pap1/')


def check_key_use(key, via_bulk):
    """Reserved keys are valid only on the registered bulk path."""
    return {'ok': False, 'code': 'PAP_RESERVED'} if is_reserved_key(key) and not via_bulk else {'ok': True}


def check_capacity(manifest_control_bound, max_items, batch_size, per_batch_result, per_job_total):
    """CONTRACT-013: manifestControlBound + ceil(maxItems/batchSize) x R <= C, else registration refuses."""
    for v in (manifest_control_bound, max_items, batch_size, per_batch_result, per_job_total):
        if not _ordinal(v):
            raise BulkRefusal('PAP_LIMIT', 'capacity inputs must be unsigned integers')
    if batch_size == 0:
        raise BulkRefusal('PAP_LIMIT', 'batchSize must be positive')
    batches = -(-max_items // batch_size)
    need = manifest_control_bound + batches * per_batch_result
    if need > per_job_total:
        raise BulkRefusal('PAP_LIMIT', f'retained space {need} exceeds job bound {per_job_total}')
    return {'batches': batches, 'required': need, 'spare': per_job_total - need}
