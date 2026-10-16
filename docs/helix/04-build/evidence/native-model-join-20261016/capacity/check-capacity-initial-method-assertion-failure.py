from pathlib import Path
import sys,gzip,json,hashlib,time
root=Path(__file__).parent;out=Path('/private/tmp/truss-model-decoder-capacity-r1-20261016');out.mkdir(exist_ok=True)
sys.path.insert(0,'/private/tmp/weft-model-requirements-main-combined-installed-20261016');import weft
raw=gzip.decompress(Path('/private/tmp/weft-model-requirements-scalar-capacity-r1-20261016/original-request.json.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()=='9979943c2cba3bbcdb297084906194fc4a58532600a582c3faa18a13737a1dc5'
start=time.monotonic();parent=weft.prepare_application_lineage(raw.decode());current=parent.prepare_current_presence();q=current.model_requirements_json().encode();assert current.source_preparation is parent
assert hashlib.sha256(q).hexdigest()=='23d1451bd831aed015c63c6df054dce2ec4165543d115e806f7071d1c0aadea9'
namespace={};exec(compile((root/'packages/python/src/truss/_owner_evidence_json.py').read_bytes(),'_owner_evidence_json.py','exec'),namespace)
old=namespace['decode_owner_evidence_json'];new=namespace['decode_issued_model_requirements_json']
try:old(q)
except ValueError:pass
else:raise AssertionError('old surface guard changed')
parsed=new(q);assert parsed['sourceRequestJson'].encode()==raw
controls=0
for decode,limit in [(old,8_388_608),(new,16_000_000)]:
 assert decode(b'0'+b' '*(limit-1))==0;controls+=1
 for bad in [b'0'+b' '*limit,b'{"x":0,"x":1}',b'NaN',b'1'*513,b'"\\ud800"',b'['*130+b'0'+b']'*130,b'['+b'0,'*4096+b'0]']:
  try:decode(bad)
  except (ValueError,RecursionError):controls+=1
  else:raise AssertionError('strict guard lost')
receipt={'actualCompilerReplay':True,'requestBytes':len(raw),'requirementsBytes':len(q),'requirementsSha256':hashlib.sha256(q).hexdigest(),'old8MiBRefused':True,'new16MScanned':True,'boundaryStrictnessControls':controls,'seconds':time.monotonic()-start,'nativeAuthority':False,'scope':'Actual issued Q and strict decoder capacity only; not complete native join/admission.'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
