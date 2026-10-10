"""Public carrier experiment; standard library decoding alone does not prove canonicality."""
from pathlib import Path
import base64,hashlib,json,re
path=Path(__file__).resolve().parents[3]/'02-design/contracts/bindings/binary-canonical-base64-v0.1.vectors.json'
raw=path.read_bytes()
if len(raw)>16384:raise ValueError('experiment fixture bound')
fixture=json.loads(raw);alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
def preflight(text):
 if len(text)>4096:raise ValueError('experiment input bound')
 if re.fullmatch(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',text) is None:raise ValueError('grammar')
 pad=len(text)-len(text.rstrip('='))
 if pad==2 and alphabet.index(text[-3])%16:raise ValueError('pad bits')
 if pad==1 and alphabet.index(text[-2])%4:raise ValueError('pad bits')
 return len(text)//4*3-pad
ids=set();accepted=0;permissive=[]
for v in fixture['vectors']:
 if v['id'] in ids:raise ValueError('duplicate identity')
 ids.add(v['id'])
 try:
  size=preflight(v['text']);decoded=base64.b64decode(v['text'],validate=True)
  if len(decoded)!=size or len(base64.b64encode(decoded))!=4*((size+2)//3):raise ValueError('length')
  admitted=True
 except ValueError:
  decoded=None;admitted=False
 if admitted!=v['admitted']:raise ValueError(v['id'])
 if admitted:
  accepted+=1
  if decoded.hex()!=v['expectedHex'] or base64.b64encode(decoded).decode('ascii')!=v['text']:raise ValueError('independent bytes '+v['id'])
 else:
  try:base64.b64decode(v['text'],validate=True);permissive.append(v['id'])
  except (ValueError,UnicodeError):pass
if raw!=path.read_bytes():raise ValueError('fixture changed')
result={'status':'pass','cases':len(ids),'admitted':accepted,'refused':len(ids)-accepted,'libraryAcceptedRefusedSpellings':permissive,'fixtureSha256':hashlib.sha256(raw).hexdigest(),'scope':fixture['scope'],'nativeExecuted':False,'profileAdopted':False}
Path(__file__).with_name('binary-canonical-base64-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'pass','cases':len(ids),'libraryAcceptedRefusedSpellings':permissive}))
