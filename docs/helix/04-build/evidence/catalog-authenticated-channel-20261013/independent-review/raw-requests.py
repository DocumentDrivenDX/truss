from pathlib import Path
import sys,socket,threading,json,hashlib
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent
source_sha=hashlib.sha256((ROOT/'scripts/security_catalog_channel.py').read_bytes()).hexdigest()
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'packages/python/src')]
from security_catalog_channel import AuthenticatedReadChannel,REQUEST
from truss.execution import Ok
secret=bytes(range(32));auth=b'Authorization: Bearer '+secret.hex().encode()
default=[b'Host: localhost',auth,b'Content-Type: application/json',b'Content-Length: '+str(len(REQUEST)).encode()]
records=[]
def probe(name,headers=None,body=REQUEST,line=b'POST /protected/read HTTP/1.1'):
 calls=[]
 def operation(publish):calls.append(True);publish(b'{"rows":[]}');return Ok(b'{"rows":[]}')
 server=AuthenticatedReadChannel(secret,operation);worker=threading.Thread(target=server.serve_forever,kwargs={'poll_interval':0.01},daemon=True);worker.start()
 try:
  with socket.create_connection(server.server_address,timeout=2) as peer:
   peer.settimeout(2);peer.sendall(line+b'\r\n'+b'\r\n'.join(default if headers is None else headers)+b'\r\n\r\n'+body)
   data=b''
   while True:
    chunk=peer.recv(65536)
    if not chunk:break
    data+=chunk
   status=int(data.split(b' ',2)[1]);response_body=data.split(b'\r\n\r\n',1)[1]
 finally:server.shutdown();server.server_close();worker.join(2)
 assert not worker.is_alive()
 records.append({'name':name,'status':status,'operationCalls':len(calls),'body':response_body.decode('utf8')})
probe('valid')
probe('duplicate authorization',default+[auth])
probe('combined authorization',[default[0],auth+b', Bearer '+secret.hex().encode(),*default[2:]])
probe('lowercase bearer',[default[0],auth.replace(b'Bearer',b'bearer'),*default[2:]])
probe('nonASCII authorization',[default[0],auth[:-1]+b'\xff',*default[2:]])
probe('duplicate content length',default+[default[-1]])
probe('leading zero content length',default[:-1]+[b'Content-Length: 0'+str(len(REQUEST)).encode()])
probe('missing content length',default[:-1])
probe('duplicate content type',default+[default[2]])
probe('transfer encoding',default+[b'Transfer-Encoding: chunked'])
probe('forbidden subject header',default+[b'X-Subject: admin'])
probe('header terminator defect followed by forbidden subject',default+[b'Invalid Header: x',b'X-Subject: admin'])
probe('header name whitespace hides transfer encoding',default+[b'Transfer-Encoding : chunked'])
probe('folded host hides subject-like continuation',default+[b' continuation: admin'])
probe('unknown route',line=b'POST /sql HTTP/1.1')
probe('query substitution',line=b'POST /protected/read?actor=admin HTTP/1.1')
probe('absolute URI',line=b'POST http://localhost/protected/read HTTP/1.1')
probe('double slash alias',line=b'POST //protected/read HTTP/1.1')
probe('GET with valid body',line=b'GET /protected/read HTTP/1.1')
probe('TRACE with valid body',line=b'TRACE /protected/read HTTP/1.1')
probe('HTTP1.0',line=b'POST /protected/read HTTP/1.0')
probe('malformed JSON body',body=b'x'*len(REQUEST))
assert hashlib.sha256((ROOT/'scripts/security_catalog_channel.py').read_bytes()).hexdigest()==source_sha
record={'scope':'Actual loopback HTTP parser and fixture operation only; no native database','sourceSha256':source_sha,'controls':records}
(OUT/'raw-requests-after.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
