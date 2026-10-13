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
 for o in objects:
  assert (o.cr_frame if kind=='coroutine' else o.gi_frame) is None
 assert isinstance(r,Error) and r.error.code=='transaction_unusable' and h._custody.quarantined and not got and h._custody.last_attempt.phase=='released'
 records.append({'name':'returned '+kind+' closes cold and quarantines','passed':True})
 return {'kind':kind,'result':r.status,'phase':h._custody.last_attempt.phase,'bodyCalls':len(got),'quarantined':h._custody.quarantined}

def declared_deferred():
 async def ac(v):pass
 def gen(v):yield v
 async def agen(v):yield v
 class A:
  async def __call__(self,v):pass
 class G:
  def __call__(self,v):yield v
 class AG:
  async def __call__(self,v):yield v
 for sink in (ac,gen,agen,A(),G(),AG()):
  h,t,c=host();entered=[]
  try:h._run_published_operation(t,lambda *a:entered.append(True),sink)
  except ValueError as e:assert str(e)=='Original synchronous private publisher required'
  else:raise AssertionError('deferred publisher admitted')
  assert not entered and not c.commands and h._custody.last_attempt is None
  records.append({'name':'declared deferred sink refuses before host work: '+type(sink).__name__,'passed':True})

def non_none(value):
 h,t,c=host();delivered=[]
 def sink(v):delivered.append(v);return value
 r=h._run_published_operation(t,lambda *a:b'packet',sink)
 assert isinstance(r,Error) and delivered==[b'packet'] and h._custody.quarantined and r.error.retry_scope=='none'
 assert h._custody.last_attempt.phase=='released' and str(h._custody.last_attempt.error)=='Exact synchronous publisher completion required'

def started_cleanup():
 h,t,c=host();seen=[];objs=[];primary=KeyboardInterrupt('cleanup interruption')
 def gen():
  try:yield
  finally:
   seen.append(h._custody.lease.locked());raise primary
 def sink(v):
  g=gen();next(g);objs.append(g);return g
 try:h._run_published_operation(t,lambda *a:b'packet',sink)
 except KeyboardInterrupt as e:assert e is primary
 else:raise AssertionError('primary interruption lost')
 assert seen==[True] and objs[0].gi_frame is None and h._custody.quarantined and h._custody.last_attempt.error is primary

with patch.object(m,'_Deadline',Deadline):
 run('synchronous publication after cursor close under lease',success)
 run('ordinary sink failure quarantines without repeat',lambda:uncertain(RuntimeError))
 run('BaseException sink failure quarantines and preserves original',lambda:uncertain(KeyboardInterrupt))
 run('late observation refusal gives zero delivery and containment',late_observation)
 run('cursor close failure gives zero delivery and quarantine',bad_close)
 deferred_observations=[deferred('coroutine'),deferred('generator')]
 declared_deferred()
 for value in (False,0,b'',object()):run('non-None '+type(value).__name__+' completion quarantines',lambda:non_none(value))
 run('started generator close remains under lease and preserves BaseException',started_cleanup)
result={'scope':'Actual private host methods with synthetic connection/cursor/deadline and manually registered synthetic custody; not native qualification','controls':records,'deferredObservations':deferred_observations,'hostSha256':hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest()}
p=Path(sys.argv[1]);p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
