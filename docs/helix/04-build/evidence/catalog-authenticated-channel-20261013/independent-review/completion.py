from pathlib import Path
import sys,http.client,threading,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
source_sha=hashlib.sha256((ROOT/'scripts/security_catalog_channel.py').read_bytes()).hexdigest()
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
from security_catalog_channel import AuthenticatedReadChannel,REQUEST,ROUTE
from truss.execution import Ok
secret=bytes(range(32));records=[];private='PRIVATE-NATIVE-DIAGNOSTIC'
def run(name,action,expected_status,expected_body):
 calls=[]
 def operation(publish):calls.append(True);return action(publish)
 server=AuthenticatedReadChannel(secret,operation);worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01},daemon=True);worker.start()
 def request():
  c=http.client.HTTPConnection(*server.server_address,timeout=2)
  try:
   c.request('POST',ROUTE,REQUEST,{'Authorization':'Bearer '+secret.hex(),'Content-Type':'application/json'})
   response=c.getresponse();return response.status,response.read()
  finally:c.close()
 try:
  status,body=request();retry=request()
  assert (status,body)==(expected_status,expected_body),(name,status,len(body))
  assert retry==(403,b'{}') and calls==[True] and private.encode() not in body
  records.append({'name':name,'passed':True,'status':status,'bodyBytes':len(body),'bodySha256':hashlib.sha256(body).hexdigest(),'retryStatus':retry[0],'operationCalls':len(calls),'ownerFailureType':type(server._failure).__name__ if server._failure else None})
 finally:server.shutdown();server.server_close();worker.join(2)
 assert not worker.is_alive()
def raised(p):raise RuntimeError(private)
run('failure before publication generic503',raised,503,b'{}')
run('None completion without publication',lambda p:None,503,b'{}')
run('Ok completion without publication',lambda p:Ok(b'{}'),503,b'{}')
for name,value in [('None',None),('mutable',bytearray(b'{}')),('empty',b''),('over1MiB',b'x'*1048577)]:run('invalid packet '+name,lambda p,v=value:p(v),503,b'{}')
def publish_then_raise(p):p(b'{}');raise RuntimeError(private)
def double(p):p(b'{}');p(b'{"other":1}');return Ok(b'{}')
def mismatch(p):p(b'{}');return Ok(b'{"other":1}')
def no_completion(p):p(b'{}');return None
run('postpublication exception adds no error packet',publish_then_raise,200,b'{}')
run('duplicate publication emits only first packet',double,200,b'{}')
run('mismatched original completion closes after original packet',mismatch,200,b'{}')
run('None completion after original packet',no_completion,200,b'{}')
maximum=b' '*1048574+b'{}'
def largest(p):p(maximum);return Ok(maximum)
run('exact1MiB packet accepted once',largest,200,maximum)
assert hashlib.sha256((ROOT/'scripts/security_catalog_channel.py').read_bytes()).hexdigest()==source_sha
record={'scope':'Actual loopback HTTP and synthetic trusted operation; no native database or external delivery acknowledgment claim','sourceSha256':source_sha,'count':len(records),'controls':records}
(OUT/'completion.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'controls':len(records),'passed':True}))
