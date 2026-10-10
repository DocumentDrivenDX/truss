"""Original full-source custody for four reference fields; not accepted/native registration."""
from pathlib import Path
import base64, hashlib, json, sys
root=Path(__file__).resolve().parents[5]
source='docs/helix/02-design/contracts/bindings/reference-account-items-v0.1.proposal.umf.json'
expected='94f8367c3dd2462fb3f32a624f053bf56f023ddd3bf86bf5219bbc1e24b6fcc1'
raw=(root/source).read_bytes()
if hashlib.sha256(raw).hexdigest()!=expected: raise ValueError('original source drift')
doc=json.loads(raw)
fields=[]
for index, element, owner, family in [(0,'Account.code','Account','string'),(1,'Item.code','Item','string'),(2,'Item.amount','Item','decimal'),(3,'Item.note','Item','string')]:
 field=doc['modules'][0]['elements'][index]
 if doc['id']!='truss.integration.account-items.v1' or doc['modules'][0]['id']!='integration' or field['id']!=element or field['scalarType']!=family:raise ValueError('original field membership drift')
 records=[e for e in doc['modules'][0]['elements'] if e.get('id')==owner]
 if len(records)!=1 or records[0].get('kind')!='record' or records[0].get('members',[]).count({'module':'integration','element':element})!=1:raise ValueError('original record membership missing or duplicated')
 fields.append({'documentId':doc['id'],'module':'integration','element':element,'recordOwner':owner,'sourcePointer':f'/modules/0/elements/{index}','sourceArtifactIdentity':source,'decodedDefinitionWitness':field,'acceptedRevisionIdentity':None,'nativeCatalogIdentity':None})
result={'scope':__doc__,'sourceArtifact':{'identity':source,'bytesBase64':base64.b64encode(raw).decode('ascii'),'sha256':expected},'fields':fields,'sourceRule':'Field locator resolves original full source bytes. Decoded witness is supplementary; reserialized fragments are not original document bytes. Accepted revision/profile and native identity remain unassigned.'}
target=root/'docs/helix/04-build/evidence/design-audit/reference-field-original-source.json'
if sys.argv[1:]==['--check']:
 if json.loads(target.read_text())!=result:raise ValueError('stale original field source custody')
elif not sys.argv[1:]:target.write_text(json.dumps(result,indent=2)+'\n')
else:raise ValueError('usage: capture-reference-field-source.py [--check]')
print('Complete original source bytes and four field locators verified; acceptance/native identities unassigned.')
