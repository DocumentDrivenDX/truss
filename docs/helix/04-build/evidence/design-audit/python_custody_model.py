"""Finite abstract custody exploration; not implementation refinement/proof.

One issuer, two ordinal values, two original confirmations/tickets. Native actor,
driver, account, recovery, registry epochs and liveness are outside this model.
"""
from collections import deque
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import sys
import time


@dataclass(frozen=True)
class State:
    next_ordinal: int = 0
    issued: tuple = ()
    issuer_closed: bool = False
    registered: tuple = (False, False)
    consumed: tuple = (False, False)
    calls: tuple = (0, 0)
    effects: tuple = (0, 0)
    closed: bool = False
    active: int = -1
    phase: int = 0  # idle, verify, verified, gate-checked, callback, returning
    foreign_consumed: bool = False
    effect_after_close: bool = False


def set_at(values, index, value):
    return values[:index] + (value,) + values[index+1:]


def successors(s, variant):
    if not s.issuer_closed and s.next_ordinal <= 1:
        yield 'issue', replace(s,next_ordinal=s.next_ordinal+1,issued=s.issued+(s.next_ordinal,))
    yield 'close-issuer', replace(s,issuer_closed=True)
    rewind=variant=='rewind' or variant=='rewind-open' and not s.issuer_closed
    yield 'rollback', replace(s,next_ordinal=0) if rewind else s
    yield 'close-registry', replace(s,closed=True)
    # Original identity tags are distinct atoms; foreign/copy refusals are stutters.
    yield 'foreign-owner-refused', s
    yield 'foreign-ticket-refused', s
    if variant=='copied-ticket' and not s.closed and s.active==-1:
        yield 'accept-copied-ticket', replace(s,foreign_consumed=True)
    if not s.closed and s.active==-1:
        for i in range(2):
            if not s.registered[i]:
                yield f'register-{i}', replace(s,registered=set_at(s.registered,i,True))
            elif not s.consumed[i]:
                yield f'begin-{i}', replace(s,active=i,phase=1,consumed=set_at(s.consumed,i,True))
    if s.active!=-1:
        if s.phase==1:
            yield 'verify-success', replace(s,phase=2)
        if s.phase==2 and (not s.closed or variant=='bypass-close-gate'):
            yield 'check-open-gate', replace(s,phase=3)
        if s.phase==3:
            yield 'dispatch', replace(s,phase=4,calls=set_at(s.calls,s.active,s.calls[s.active]+1))
        if s.phase==4:
            yield 'callback-effect', replace(s,phase=5,effects=set_at(s.effects,s.active,s.effects[s.active]+1),effect_after_close=s.effect_after_close or s.closed)
            yield 'callback-no-effect', replace(s,phase=5)
        if s.phase==5:
            yield 'finish', replace(s,active=-1,phase=0)
        consumed = set_at(s.consumed,s.active,False) if variant=='restore-permission' else s.consumed
        yield 'escaped-failure', replace(s,active=-1,phase=0,closed=variant!='failure-stays-open',consumed=consumed)


def violation(old, action, new, check_fence):
    if new.issued!=tuple(range(len(new.issued))) or len(new.issued)>2:
        return 'PY-ORD-001'
    if old.issuer_closed and (not new.issuer_closed or old.next_ordinal!=new.next_ordinal):
        return 'PY-ORD-002'
    if new.foreign_consumed or any(n>1 for n in new.calls) or new.active!=-1 and not new.consumed[new.active]:
        return 'PY-ADM-001'
    if any(a and not b for a,b in zip(old.registered,new.registered)) or any(a and not b for a,b in zip(old.consumed,new.consumed)):
        return 'PY-ADM-002'
    if old.closed and not new.closed or action=='escaped-failure' and not new.closed:
        return 'PY-ADM-003'
    if action=='check-open-gate' and old.closed:
        return 'PY-ADM-004'
    if check_fence and new.effect_after_close:
        return 'LOCAL-CLOSE-IS-NATIVE-FENCE (expected false implication)'
    return None


def explore(variant='baseline', check_fence=False):
    initial=State(); queue=deque([initial]); parent={initial:None}; edges=0
    witnesses={}; started=time.monotonic()
    while queue:
        s=queue.popleft()
        if any(s.effects): witnesses.setdefault('native-effect',s)
        if s.closed and any(s.effects): witnesses.setdefault('failure-or-close-after-effect',s)
        if all(s.calls): witnesses.setdefault('two-original-tickets-dispatched',s)
        for action,new in successors(s,variant):
            edges+=1
            problem=violation(s,action,new,check_fence)
            if problem:
                trace=[action]; cursor=s
                while parent[cursor] is not None:
                    previous,label=parent[cursor];trace.append(label);cursor=previous
                return {'status':'violation','property':problem,'trace':list(reversed(trace)),
                    'states':len(parent),'transitions':edges,'seconds':time.monotonic()-started}
            if new not in parent:
                if len(parent)>=100000:
                    return {'status':'incomplete','reason':'state ceiling','states':len(parent)}
                parent[new]=(s,action);queue.append(new)
    return {'status':'completed_bounded_check','states':len(parent),'transitions':edges,
        'seconds':time.monotonic()-started,'nonVacuity':sorted(witnesses)}


def main():
    root=Path(__file__).resolve().parents[5]
    if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1] or not sys.argv[1].endswith('.json'):
        raise SystemExit('usage: python_custody_model.py NEW_RECEIPT_BASENAME.json')
    destination=Path(__file__).parent/sys.argv[1]
    if destination.exists(): raise SystemExit('Refusing to replace original analysis receipt')
    positive=explore()
    negative={v:explore(v) for v in ('rewind','rewind-open','restore-permission','copied-ticket','failure-stays-open','bypass-close-gate')}
    fence=explore(check_fence=True)
    success=positive['status']=='completed_bounded_check' and len(positive['nonVacuity'])==3
    expected={'rewind':'PY-ORD-002','rewind-open':'PY-ORD-001',
        'restore-permission':'PY-ADM-002','copied-ticket':'PY-ADM-001',
        'failure-stays-open':'PY-ADM-003','bypass-close-gate':'PY-ADM-004'}
    success=success and all(negative[v].get('property')==p for v,p in expected.items())
    success=success and fence.get('property')=='LOCAL-CLOSE-IS-NATIVE-FENCE (expected false implication)'
    sources=['packages/python/src/truss/_operation_ordinal.py','packages/python/src/truss/_operation_admission.py']
    record={'scope':'Author-reviewed finite abstract component model; no implementation refinement, native authority or liveness proof',
        'tool':'Truss standard-library explicit-state BFS/0.1','python':sys.version,
        'command':[sys.executable,str(Path(__file__).resolve()),sys.argv[1]],
        'configuration':{'issuers':1,'ordinalMaximum':1,'confirmationCapacity':2,'stateCeiling':100000,'search':'complete reachable-state BFS'},
        'modelSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'sourceSha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},
        'properties':['PY-ORD-001','PY-ORD-002','PY-ADM-001','PY-ADM-002','PY-ADM-003','PY-ADM-004'],
        'positive':positive,'negativeControls':negative,'localCloseFenceCounterexample':fence,
        'expectedAnalysisOutcomesObserved':success,'implementationRefinementProven':False,'nativeQualified':False,
        'review':{'reviewer':'Truss author-agent','independentReview':'not performed'},
        'excluded':['liveness/fairness/timing','PY-ADM-005 Python deferred-object semantics','full PY-NATIVE-001 authority','account/driver/security integration','connection registry/epochs','process crash and durable recovery','larger/unbounded state domains']}
    with destination.open('x') as output:output.write(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'states':positive.get('states'),'expectedAnalysisOutcomesObserved':success,'nativeQualified':False}))
    if not success:raise SystemExit(1)


if __name__=='__main__':main()
