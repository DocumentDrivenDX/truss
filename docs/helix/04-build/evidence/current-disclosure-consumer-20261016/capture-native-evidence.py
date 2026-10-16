from pathlib import Path
from hashlib import sha256
import json,zipfile,sys,importlib.metadata
root=Path('/private/tmp/truss-presence-consumer-rebased-29470-20261016')
packet=Path('/private/tmp/truss-presence-consumer-rebased-review-r5-20261016.zip');assert sha256(packet.read_bytes()).hexdigest()=='3664ef8bd6a5b0142c1774c6a1bf361f43fdc43f6cfb7b8e0b0d71b3f724ee86'
with zipfile.ZipFile(packet) as z:
 manifest=json.loads(z.read('manifest.json'))
 inputs={n:sha256((root/n).read_bytes()).hexdigest() for n in manifest['files'] if n.startswith('packages/')}
 assert all(inputs[n]==manifest['files'][n]['sha256'] for n in inputs)
critical=['packages/python/src/truss/local_runtime.py','packages/python/src/truss/psycopg_host.py','packages/python/src/truss/_current_query_facts.py','packages/python/src/truss/_current_query_subjects.py','packages/python/src/truss/_current_query_protection.py','packages/python/src/truss/_installation_privileges.py','packages/python/tests/test_catalog_runtime_native.py','packages/python/tests/test_current_query_runtime_native.py','packages/python/tests/test_current_query_subjects_native.py']
for name in critical:inputs[name]=sha256((root/name).read_bytes()).hexdigest()
for p in (root/'packages/python/src/truss/_catalog_runtime').iterdir():
 if p.is_file():inputs[str(p.relative_to(root))]=sha256(p.read_bytes()).hexdigest()
module=Path('/private/tmp/weft-presence-python-combined-installed-20261016/weft/weft.abi3.so');assert sha256(module.read_bytes()).hexdigest()=='a94439b3949c6db574ded8d95d9b81b23e128b0cbb7570edff65228d3737c402'
inputs[str(module)]=sha256(module.read_bytes()).hexdigest()
log=Path('/private/tmp/truss-disclosure-rebased-scram-native-20261016.log');text=log.read_text();assert 'Ran 6 tests' in text and text.rstrip().endswith('OK') and 'skipped' not in text
receipt={'status':'passed','trussBaseline':'29470b1eb99f1bc556d895b02b319aff37f8ded4','sourcePacketSha256':sha256(packet.read_bytes()).hexdigest(),'nativeTests':6,'nativeTestsSeconds':25.511,'scope':'Actual stock owned localPG18.6/psycopg3.3.6 SCRAM caller and direct tagged disclosure query path. Masked, all-denied, empty, post-transport tamperedV2 header, actualsourcearchive driftbeforeclosing, credentialcontrol. No fullgraphcapture/nativebindingadmission/managedservice/whole132 promotion. The binding remains explicitly unadmitted.','proofBoundary':'All43sourcepacket members compared at ending endpoint, additional critical runtime/source hashes retained; priorpacket fixes starting source. Not held-file/ABA/hermetic proof.','cleanup':'Successful class cleanup invokes ownedLocalPostgres.close with postmaster.pid absence check then removes owned directory; tests assert no truss_presence staging relations remain. HBA original bytes restored and reload accepted. No general physical storage erasure claim.','python':sys.version,'packages':{n:importlib.metadata.version(n) for n in ('psycopg','psycopg-binary','pgserver-pg18')},'umfRevision':'206951ff20d766874b9af7d29fdf8027c3bab499','weftRevision':'b8c34c84f3c8cae8e07680e4960942d685f9bb63','nativeLogSha256':sha256(log.read_bytes()).hexdigest(),'inputs':inputs}
receipt['packagedSourceEndingHashes']={str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in sorted((root/'packages/python/src/truss').rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc',)}
receipt['proofBoundary']+=' All packaged Truss source files also hashed at ending endpoint; dependencies identified by installed versions. No claim of hermetic complete dependency or in-run file custody.'
out=Path('/private/tmp/truss-disclosure-rebased-native-receipt-20261016.json');out.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'status':'passed','nativeTests':6,'sourceInputs':len(inputs),'receiptSha256':sha256(out.read_bytes()).hexdigest()}))
