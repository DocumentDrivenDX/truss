from pathlib import Path
import json,sys,threading,weakref,warnings,hashlib
from unittest.mock import patch
from psycopg import pq
import truss.psycopg_host as m
from truss.execution import TransactionHandle,Ok,Error
records=[]
class Connection: pass
class Cursor:
 def __init__(self):self.closed=False;self.statusmessage='';self.commands=[]
 def execute(self,q,*a,**k):
  text=q if isinstance(q,str) else q.as_string(None);self.commands.append(text);self.statusmessage='RELEASE' if text.startswith('RELEASE') else ''
 def close(self):self.closed=True
class Deadline:
 def __init__(self,*a):self.stopped=False;self.stop_result=False
 def finish(self):return True
 def check(self):pass

def host():
 h=object.__new__(m.PsycopgHost);h._connection=Connection();h._issuer=object();h._closed=False;h._deadline_ms=5000;h._timeout=2000
 h._custody=m._ConnectionCustody(threading.Lock());h._custody.attached=weakref.ref(h);m._registry[h.connection]=h._custody
 ident=('123','1/2','read_committed','read_write');t=TransactionHandle(h._issuer,'key','read_committed','read_write');h._transactions={'key':m._TransactionCustody(t,ident,None)}
 c=Cursor();h._cursor=lambda:c;h._status=lambda:pq.TransactionStatus.INTRANS;h._observe=lambda cur:(ident,None,'10000');return h,t,c

def run(name,f):f();records.append({'name':name,'passed':True})

def success():
 h,t,c=host();got=[]
 def publish(v):
  assert c.closed and h._custody.last_attempt.phase=='released' and h._custody.pending is not None
  assert not h._custody.lease.acquire(False)
  nested=[];r=h._run_operation(t,lambda *a:nested.append(True));assert isinstance(r,Error) and not nested
  got.append(v)
 r=h._run_published_operation(t,lambda *a:b'packet',publish)
 assert isinstance(r,Ok) and got==[b'packet'] and r.value is got[0] and h._custody.pending is None and h._custody.last_attempt.phase=='published' and h._custody.lease.acquire(False);h._custody.lease.release()

def uncertain(kind):
 h,t,c=host();got=[];err=kind('uncertain')
 def publish(v):got.append(v);raise err
 try:r=h._run_published_operation(t,lambda *a:b'packet',publish)
 except BaseException as e:assert kind is KeyboardInterrupt and e is err
 else:assert kind is RuntimeError and isinstance(r,Error) and r.error.code=='transaction_unusable' and r.error.retry_scope=='none'
 assert h._custody.quarantined and h._custody.pending is not None and h._custody.last_attempt.error is err and h._custody.last_attempt.phase=='released'
 r=h._run_published_operation(t,lambda *a:b'again',publish);assert isinstance(r,Error) and got==[b'packet']

def late_observation():
 h,t,c=host();got=[];original=h._observe
 def observe(cur):
  if h._custody.last_attempt.phase=='command_returned':raise ValueError('late')
  return original(cur)
 h._observe=observe;r=h._run_published_operation(t,lambda *a:b'packet',got.append)
 assert isinstance(r,Error) and got==[] and h._custody.last_attempt.phase=='contained' and not h._custody.quarantined

def bad_close():
 h,t,c=host();got=[]
 def close():raise RuntimeError('close')
 c.close=close;r=h._run_published_operation(t,lambda *a:b'packet',got.append)
 assert isinstance(r,Error) and got==[] and h._custody.quarantined

def deferred(kind):
 h,t,c=host();got=[];objects=[]
 async def async_sink(v):got.append(v)
 def gen_sink(v):got.append(v);yield
 sink=async_sink if kind=='coroutine' else gen_sink
 def retain(v):o=sink(v);objects.append(o);return o
 r=h._run_published_operation(t,lambda *a:b'packet',retain)
 for o in objects:o.close()
 return {'kind':kind,'result':r.status,'phase':h._custody.last_attempt.phase,'bodyCalls':len(got),'quarantined':h._custody.quarantined}

with patch.object(m,'_Deadline',Deadline):
 run('synchronous publication after cursor close under lease',success)
 run('ordinary sink failure quarantines without repeat',lambda:uncertain(RuntimeError))
 run('BaseException sink failure quarantines and preserves original',lambda:uncertain(KeyboardInterrupt))
 run('late observation refusal gives zero delivery and containment',late_observation)
 run('cursor close failure gives zero delivery and quarantine',bad_close)
 deferred_observations=[deferred('coroutine'),deferred('generator')]
result={'scope':'Actual private host methods with synthetic connection/cursor/deadline and manually registered synthetic custody; not native qualification','controls':records,'deferredObservations':deferred_observations,'hostSha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
p=Path(sys.argv[1]);p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
