"""Published byte/digest graph integrity; not production canonicalization/native truth."""
import base64,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
fixture=json.loads((root/'02-design/contracts/bindings/seed-composition-v0.1.vectors.json').read_text())
values={}
for v in fixture['vectors']:
 raw=v['rawUtf8'].encode();assert hashlib.sha256(raw).hexdigest()==v['contentSha256']
 pre=bytes.fromhex(v['canonicalIdentityPreimageHex']);assert pre==(fixture['canonicalProfile']+'\n'+v['domain']+'\n').encode()+raw
 assert hashlib.sha256(pre).hexdigest()==v['canonicalIdentitySha256']
 assert v['canonicalIdentitySha256']!=v['contentSha256']
 values[v['name']]=(json.loads(raw),raw,v['contentSha256'])
cut,cutraw,cutdigest=values['snapshot'];baseline,braw,bdigest=values['baseline'];vis,vraw,vdigest=values['visibility'];inv,iraw,idigest=values['inventory']
assert base64.b64decode(baseline['snapshotEvidence']['bytesBase64'])==cutraw
assert baseline['snapshotEvidence']['sha256']==cutdigest
assert vis['baseline']['sha256']==bdigest
assert inv['baselineSha256']==bdigest and inv['visibilityManifestSha256']==vdigest
assert vis['snapshot']==cut['snapshot']
assert 'visibilityManifestSha256' not in baseline
assert not any(k in cut for k in ['baseline','inventory','visibility'])
receipt={'scope':'Four ASCII artifact byte/digest graph witnesses only; no canonicalizer, native completeness, authority or snapshot qualification','artifacts':4,'contentLinks':4,'identityDigestSubstitutionRejected':True,'failures':[]}
(root/'04-build/evidence/design-audit/seed-composition.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt))
