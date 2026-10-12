"""Exhaustive finite state exploration of two one-shot original claims."""
from collections import deque
import json
# phase 0:not registered, 1:publication pending, 2:completed, 3:settled.
# Native loss changes only liveness; neither settlement nor completion follows.
def explore(auto_clear):
 initial=((0,0),(False,False),False);paths={initial:[]};queue=deque([initial]);edges=0;bad=[]
 while queue:
  state=queue.popleft();phases,lost,ack=state
  if ack and 1 in phases:bad.append(paths[state])
  next_states=[]
  for i in range(2):
   def phase(n,event):
    p=list(phases);p[i]=n;next_states.append(((tuple(p),lost,ack),event+str(i)))
   if not ack and phases[i]==0:phase(1,'register')
   if phases[i]==1:phase(2,'complete-publication-or-withhold')
   if phases[i]==2:phase(3,'settle')
   if phases[i] in (1,2) and not lost[i]:
    l=list(lost);l[i]=True;next_states.append(((phases,tuple(l),ack),'native-loss'+str(i)))
  outstanding=any(p in (1,2) and not(auto_clear and lost[i]) for i,p in enumerate(phases))
  if not ack and not outstanding:next_states.append(((phases,lost,True),'authority-ack'))
  for target,event in next_states:
   edges+=1
   if target not in paths:paths[target]=paths[state]+[event];queue.append(target)
 return {'states':len(paths),'edges':edges,'unsafeStates':len(bad),'counterexample':bad[0] if bad else None}
safe=explore(False);unsafe=explore(True)
assert safe['unsafeStates']==0 and unsafe['unsafeStates']>0
print(json.dumps({'durable':safe,'autoClearOnLoss':unsafe,'scope':'All reachable states of exactly two one-shot operations in one generation. Claim registration serialized with authority, settlement only after final publication/completely withheld result, and complete writer participation are premises. Native loss does not authenticate completion. No arbitrary-cardinality, native implementation refinement, external sink authenticity, commit uncertainty or real-time proof.'},indent=2))
