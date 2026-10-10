"""Finite reservation transfer exploration; not native refinement or authority."""
from collections import deque
from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import platform
import sys

ROWS, BYTES, ATTEMPTS, WORK = 3, 5, 2, 12
@dataclass(frozen=True)
class State:
    inventory: tuple = (1,)
    rows: int = 1
    bytes: int = 1
    phase: str = 'idle'
    remaining_rows: int = 0
    remaining_bytes: int = 0
    initial_rows: int = 0
    initial_bytes: int = 0
    used_rows: int = 0
    used_bytes: int = 0
    snapshot: tuple = ()
    begin_work: int = 0
    issued: int = 0
    work: int = 0
    closed: bool = False

def cleared(s, **changes):
    values=dict(phase='idle',remaining_rows=0,remaining_bytes=0,
        initial_rows=0,initial_bytes=0,used_rows=0,used_bytes=0,
        snapshot=(),begin_work=0)
    values.update(changes)
    return replace(s,**values)

def successors(s, mutant):
    if s.phase=='unknown':
        if mutant=='unknown-resume':yield 'resume-unknown',replace(s,phase='active',closed=False)
        return
    if s.phase=='committed':return
    if s.phase=='idle':
        yield 'host-commit',replace(s,phase='committed')
        if s.issued<ATTEMPTS and s.work<WORK:
            for r in range(1,ROWS-s.rows+1):
                for b in range(1,BYTES-s.bytes+1):
                    yield f'reserve:{r}:{b}',replace(s,phase='prepared',initial_rows=r,initial_bytes=b,
                        remaining_rows=r,remaining_bytes=b,snapshot=s.inventory,
                        issued=s.issued+1,begin_work=s.work,work=s.work+1)
        return
    yield 'containment-unknown',replace(s,phase='unknown',closed=True)
    yield 'rollback-confirmed',cleared(s,inventory=s.snapshot,rows=len(s.snapshot),bytes=sum(s.snapshot),
        issued=s.issued-1 if mutant=='rewind-ordinal' else s.issued,
        work=s.begin_work if mutant=='refund-work' else s.work)
    if s.work>=WORK:return
    if s.phase=='active':
        yield 'finalize',cleared(s,work=s.work+1,
            bytes=s.bytes-s.initial_bytes if mutant=='subtract-initial' else s.bytes,
            remaining_bytes=s.remaining_bytes if mutant=='clear-with-remaining' else 0)
        for i,v in enumerate(s.inventory):
            if v>1:
                inv=s.inventory[:i]+(v-1,)+s.inventory[i+1:]
                yield f'shrink:{i}',replace(s,inventory=inv,bytes=s.bytes-1,work=s.work+1,
                    remaining_bytes=s.remaining_bytes+1 if mutant=='shrink-refund' else s.remaining_bytes)
            if s.remaining_bytes>0:
                inv=s.inventory[:i]+(v+1,)+s.inventory[i+1:]
                yield f'grow:{i}',replace(s,inventory=inv,bytes=s.bytes+1,work=s.work+1,
                    used_bytes=s.used_bytes+1,remaining_bytes=s.remaining_bytes-1)
    if s.remaining_rows>0 and s.remaining_bytes>0:
        name='register-operation' if s.phase=='prepared' else 'new-touch'
        yield name,replace(s,phase='active',inventory=s.inventory+(1,),rows=s.rows+1,bytes=s.bytes+1,
            used_rows=s.used_rows+1,used_bytes=s.used_bytes+1,work=s.work+1,
            remaining_rows=s.remaining_rows if mutant=='consume-without-transfer' else s.remaining_rows-1,
            remaining_bytes=s.remaining_bytes if mutant=='consume-without-transfer' else s.remaining_bytes-1)

def violation(before,s):
    if s.rows!=len(s.inventory) or s.bytes!=sum(s.inventory):return 'CR-01-retained-parity'
    if min(s.rows,s.bytes,s.remaining_rows,s.remaining_bytes)<0 or s.rows+s.remaining_rows>ROWS or s.bytes+s.remaining_bytes>BYTES:return 'CR-02-capacity-conservation'
    if s.phase in ('idle','committed'):
        if any((s.remaining_rows,s.remaining_bytes,s.initial_rows,s.initial_bytes,s.used_rows,s.used_bytes)) or s.snapshot:return 'CR-03-cleared-slot'
    elif s.remaining_rows!=s.initial_rows-s.used_rows or s.remaining_bytes!=s.initial_bytes-s.used_bytes:return 'CR-04-no-spend-refund'
    if before and s.work<before.work:return 'CR-05-work-monotonic'
    if before and s.issued<before.issued:return 'CR-06-ordinal-monotonic'
    if before and before.closed and not s.closed:return 'CR-07-unknown-quarantine'
    return None

def explore(mutant):
    start=State(); queue=deque([start]); parents={start:None}; edges=0; witnesses={}
    def trace(state):
        out=[]
        while parents[state] is not None:
            previous,action=parents[state];out.append(action);state=previous
        return list(reversed(out))
    while queue:
        s=queue.popleft()
        for action,n in successors(s,mutant):
            edges+=1
            bad=violation(s,n)
            if bad:return {'property':bad,'trace':trace(s)+[action],'before':s.__dict__,'after':n.__dict__}
            if action=='host-commit' and n.rows>1:witnesses.setdefault('successful-retained-commit',trace(s)+[action])
            if action=='rollback-confirmed' and s.issued==2 and len(s.snapshot)>1 and s.phase=='active' and len(s.inventory)>len(s.snapshot):witnesses.setdefault('finalized-A-B-rollback-A-survives',trace(s)+[action])
            if action.startswith('grow:') and any(a.startswith('shrink:') for a in trace(s)):witnesses.setdefault('shrink-regrow-spends-again',trace(s)+[action])
            if n not in parents:parents[n]=(s,action);queue.append(n)
    if len(witnesses)!=3:raise ValueError('Required non-vacuity witnesses missing')
    return {'states':len(parents),'transitions':edges,'witnesses':witnesses}

if __name__=='__main__':
    if len(sys.argv)!=2 or Path(sys.argv[1]).name!=sys.argv[1]:raise SystemExit('Supply fresh receipt basename')
    here=Path(__file__).resolve().parent; destination=here/sys.argv[1]
    if destination.exists():raise SystemExit('Receipt exists')
    baseline=explore(None)
    if 'property' in baseline:raise ValueError('Baseline reservation property failed')
    controls={}
    for mutant,expected in {'consume-without-transfer':'CR-04-no-spend-refund','subtract-initial':'CR-01-retained-parity','refund-work':'CR-05-work-monotonic','rewind-ordinal':'CR-06-ordinal-monotonic','shrink-refund':'CR-04-no-spend-refund','clear-with-remaining':'CR-03-cleared-slot','unknown-resume':'CR-07-unknown-quarantine'}.items():
        result=explore(mutant)
        if result.get('property')!=expected:raise ValueError('Expected broken-mechanism property not observed: '+mutant)
        controls[mutant]=result
    root=here.parents[4]
    sources=['docs/helix/02-design/contracts/row-home-capacity-v0.1.proposal.sql','docs/helix/02-design/contracts/row-home-capacity-reservation-v0.1.proposal.sql','docs/helix/02-design/contracts/CONTRACT-001-storage-layout.md','docs/helix/02-design/contracts/CONTRACT-009-group-planning-and-locks.md']
    receipt={'scope':'Finite complete transition exploration of reservation transfer and non-refund rules; no implementation refinement/native authority/installation claim',
      'python':platform.python_version(),'bounds':{'rows':ROWS,'bytes':BYTES,'attempts':ATTEMPTS,'applicationWork':WORK},'baseline':baseline,'negativeControls':controls,
      'producerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'sourceSha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},'nativeCorrespondenceReviewed':False,'installerReady':False,
      'limitations':['Units abstract full carrier bytes and one installation/host transaction only','Atomic original SQL/exclusion/issuer/authority/account assumptions remain unproved','No database faults/commit_unknown reconciliation/disclosure/delivery/fairness or native resource/cancellation proof','Bounded graph exploration does not establish unbounded behavior or native enforcement']}
    with destination.open('x') as output:output.write(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'states':baseline['states'],'transitions':baseline['transitions'],'negativeControls':len(controls)}))
