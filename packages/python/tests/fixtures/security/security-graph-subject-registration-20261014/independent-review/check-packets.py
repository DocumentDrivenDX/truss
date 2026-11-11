"""Independent retained-r4 packet correspondence; no native execution."""
from pathlib import Path
from hashlib import sha256
import json
from truss._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source
from truss._security_graph_subject_installation import _recipe
here=Path(__file__).resolve().parent;folder=here.parent;root=here.parents[5]
names=('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')
raw={n:(folder/n).read_bytes() for n in names}
source=snapshot_graph_security_source(PreparedGraphSecuritySource(*(raw[n] for n in names)))
pin,type_id,property_id,revision,request=_recipe(source)
expected={'version':'truss.registered-graph-subject/0.1-candidate','physicalRequestSha256':sha256(source.original_request).hexdigest(),'acceptedCatalogSha256':sha256(source.accepted_catalog_assessment).hexdigest(),'graphBindingSha256':sha256(request['bindingJson'].encode()).hexdigest(),'ontologySha256':sha256(request['ontologyJson'].encode()).hexdigest(),'policySha256':sha256(request['policyJson'].encode()).hexdigest(),'physicalPin':pin,'nativeTypeId':str(type_id),'nativePropertyId':str(property_id)}
assert (folder/'subject-profile.json').read_bytes()==json.dumps(expected,sort_keys=True,separators=(',',':')).encode()
out=json.loads((folder/'native-subject-registration.json').read_bytes())
assert out['observations']==[{'principal':n,'subjectKey':n,'ownNativeSession':True,'rawReads':False} for n in ('Alice','Bob','Outsider')]
assert all(out[n] is True for n in ('missingStaffNoEffects','revokedOwnerSelectRefused','revokedOwnerShareRefused','rollbackPreservesPriorWork','reuseRefused','unregisteredExecuteRefused','publicAclDriftRefused'))
assert out['securityReady'] is False
paths=names+('subject-profile.json','native-subject-registration.json','issued-profile.json','native-source-epoch.json')
result={'status':'pass','scope':'Retained r4 source snapshot and exact derived profile-byte correspondence; outcome packet is parent-native evidence, not independently rerun SQL','nativeRecipe':{'typeId':type_id,'propertyId':property_id,'revision':revision},'packetSha256':{n:sha256((folder/n).read_bytes()).hexdigest() for n in paths}}
(here/'packet-results.json').write_text(json.dumps(result,indent=2)+'\n')
print('Current r4 source/profile/outcome packet correspondence passed')
