from pathlib import Path
import sys,json,hashlib,subprocess
root=Path('/private/tmp/truss-security-main-integration');out=Path('/private/tmp/python-literal-key-review-20261013')
sys.path[:0]=[str(root/'packages/python/src'),str(root/'packages/python/tests')]
from truss._umf_key_tuples import encode_literal_key_tuple
from truss._umf_keys08_release import MANIFEST_SHA256
from test_umf_literal_key_tuples import key_source
sha=lambda x:hashlib.sha256(x).hexdigest()
asset=root/'packages/python/src/truss/_umf_keys08';manifest=asset.joinpath('manifest.json').read_bytes();m=json.loads(manifest)
assert sha(manifest)==MANIFEST_SHA256
for name,digest in m['files'].items():assert sha(asset.joinpath(name).read_bytes())==digest
assert asset.joinpath('bridge.mjs').read_bytes()==root.joinpath('packages/umf-bun/src/python-keys.mjs').read_bytes()
assert asset.joinpath('producer.js').read_bytes()==subprocess.check_output(['git','show','HEAD:packages/python/src/truss/_umf_keys08/producer.js'],cwd=root)
legacy=subprocess.check_output(['git','diff','--name-only','HEAD','--','packages/python/src/truss/_umf_keys','packages/python/src/truss/_umf_keys_release.py'],cwd=root,text=True);assert not legacy
corpus=json.loads(root.joinpath('packages/python/tests/fixtures/umf-literal-key-vectors.json').read_bytes())
owner=Path('/Users/erik/.codex/worktrees/security-main-integration/umf')
original=subprocess.check_output(['git','show',corpus['ownerRevision']+':'+corpus['ownerPath']],cwd=owner)
assert sha(original)==corpus['ownerFileSha256']
original=json.loads(original)
assert corpus['vectors']==original['vectors'] and corpus['refusals']==original['refusals']
results=[]
def enc(source,texts,identity=('m','Staff','pk')):return encode_literal_key_tuple(source,identity,texts,bun_executable='/opt/homebrew/bin/bun')
def check(name,fn,refused=False):
 try:value=fn();was=False
 except ValueError:was=True
 assert was==refused,(name,was);results.append({'name':name,'passed':True});return value if not was else None
native=json.loads(Path('/private/tmp/python-literal-subject-native.json').read_text());source=native['originalRequest']['modules'][0]['documentJson'].encode()
assert sha(source)==native['originalRequest']['modules'][0]['pin']['sha256']
texts=tuple(native['nativeText']);assert tuple(v.encode().hex() for v in texts)==tuple(native['nativeUtf8Hex'])
v=check('retained-native-five-family-replay',lambda:enc(source,texts))
assert v.tuple_bytes.hex()==native['tupleHex'] and v.original_receipt_bytes.decode()==native['originalReceipt'] and v.literal_texts==texts and v.original_document==source
single=key_source([{'id':'s','scalarType':'string'}]);literal='{"string":"x"}'
v=check('exact-literal-65536',lambda:enc(single,(literal+' '*(65536-len(literal)),)))
assert json.loads(v.original_receipt_bytes)['values']==[{'string':'x'}]
check('over-literal-65536',lambda:enc(single,(literal+' '*(65537-len(literal)),)),True)
check('duplicate-literal-owner-refusal',lambda:enc(single,('{"string":"a","string":"b"}',)),True)
check('original-version07-refusal',lambda:enc(single.replace(b'0.8.0',b'0.7.0'),(literal,)),True)
check('mutable-source-refusal',lambda:enc(bytearray(single),(literal,)),True)
check('mutable-literal-sequence-refusal',lambda:enc(single,[literal]),True)
check('mutable-identity-refusal',lambda:enc(single,(literal,),['m','Staff','pk']),True)
compound=key_source([{'id':'k'+str(i),'scalarType':'string'}for i in range(32)])
v=check('exact32-components',lambda:enc(compound,(literal,)*32));assert len(json.loads(v.original_receipt_bytes)['values'])==32
check('over32-components',lambda:enc(compound,(literal,)*33),True)
(out/'results.json').write_text(json.dumps({'status':'passed','count':len(results),'results':results,'allManifestFilesVerified':True,'originalBundleUnchangedFromHEAD':True,'legacyAssetsUnchangedFromHEAD':True,'canonicalBridgeMatchesPackagedBridge':True,'vectorsMatchOriginalCommittedOwner':{'revision':corpus['ownerRevision'],'path':corpus['ownerPath'],'sha256':corpus['ownerFileSha256'],'vectors':len(corpus['vectors']),'refusals':len(corpus['refusals'])},'nativePacketReencodedByOriginalOwner':True,'scope':'Actual pinned original producer, no native database execution; immutable native evidence correspondence only.'},indent=2)+'\n');print('Passed',len(results),'actual producer controls and asset/vector integrity checks')
