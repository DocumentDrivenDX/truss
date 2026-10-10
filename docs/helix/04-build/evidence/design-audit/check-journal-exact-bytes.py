"""Exact-byte transport experiment, not the registered canonical JSON/native decoder."""
import base64,hashlib,json
from pathlib import Path

def require(ok,message):
    if not ok: raise ValueError(message)
def decode(carrier):
    require(isinstance(carrier,str) and len(carrier)>0 and len(carrier)<=4096,'experiment input ceiling')
    original=carrier.encode('ascii')
    raw=base64.b64decode(original,validate=True)
    require(base64.b64encode(raw)==original,'noncanonical padding/pad bits')
    raw.decode('utf-8',errors='strict')
    return raw
vectors=[
 ('escaped embedded NUL',b'{"kind":"string","text":"a\\u0000b"}'),
 ('Unicode members','{"members":[{"name":"é","value":"雪"},{"name":"a/b","value":null}]}'.encode()),
 ('token spelling 1.0',b'{"kind":"number","token":"1.0"}'),
 ('token spelling 1.00',b'{"kind":"number","token":"1.00"}'),
 ('preserved member order',b'{"members":[{"name":"z"},{"name":"a"}]}')
]
outcomes=[]
for name,raw in vectors:
    carrier=base64.b64encode(raw).decode('ascii')
    recovered=decode(carrier)
    require(recovered==raw,'byte loss '+name)
    outcomes.append({'name':name,'inputSha256':hashlib.sha256(raw).hexdigest(),'bytesBase64':carrier,'exactRoundTrip':True})
require(outcomes[2]['inputSha256']!=outcomes[3]['inputSha256'],'token spelling collapsed')
negative=[('empty',''),('missing padding','e30'),('nonzero pad bits','Zh=='),('URL alphabet','____'),('invalid UTF8',base64.b64encode(b'\xff').decode()),('embedded whitespace','e3 0=')]
for name,carrier in negative:
    try: decode(carrier)
    except (ValueError,UnicodeError): outcomes.append({'name':name,'refused':True})
    else: raise ValueError('invalid carrier accepted '+name)
helper=Path(__file__)
print(json.dumps({'scope':'five original byte-preservation and six canonical-base64/strict-UTF8 refusal experiments; 4096-byte local guard is not a production limit','helperSha256':hashlib.sha256(helper.read_bytes()).hexdigest(),'outcomes':outcomes,'nativeExecuted':False,'canonicalJsonQualified':False,'adopted':False},indent=2))
