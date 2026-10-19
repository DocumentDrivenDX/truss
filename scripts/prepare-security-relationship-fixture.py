# SPDX-License-Identifier: MIT OR Apache-2.0
"""Author separate traversal fixture sources; never install or authorize them."""
from pathlib import Path
import copy,hashlib,json
base=Path('docs/helix/04-build/evidence/security-named-source-profile')
out=Path('docs/helix/03-test/fixtures/security-public-relationship');out.mkdir(parents=True,exist_ok=True)
request=json.loads((base/'mapping-request.json').read_bytes())
doc=json.loads(request['modules'][0]['documentJson'])
relation={'id':'ResourceRelatedResource','name':'relatedResources','source':[{'module':'m','element':'Resource'}],'target':[{'module':'m','element':'Resource','key':'pk'}],'sourceMultiplicity':{'min':0,'max':'*'},'targetMultiplicity':{'min':0,'max':'*'},'targetLifecycle':'independent','directed':True}
doc['modules'][0]['relationships']=[relation]
ontology=json.loads(request['ontologyJson']);ontology['revision']='public-relationship-ontology-1';ontology['documents'][0]['revision']='public-relationship-schema-1';ontology['actions'].append('observeResourceRelations')
policy=json.loads(request['policyJson']);original_rules=copy.deepcopy(policy['rules']);policy['revision']='public-relationship-policy-1';policy['ontology']['revision']=ontology['revision']
observation=copy.deepcopy(policy['rules'][0]);observation['id']='resource-relationship-observer';observation['actions']=['observeResourceRelations'];observation.pop('disclosure',None)
policy['rules'].append(observation)
# Existing read eligibility is unchanged. Public observation still requires
# source read and target read independently; this new action grants neither.
assert policy['rules'][:-1]==original_rules
raw=lambda x:json.dumps(x,separators=(',',':'))
hashof=lambda x:hashlib.sha256(raw(x).encode()).hexdigest()
module={**request['modules'][0],'pin':{**request['modules'][0]['pin'],'revision':'public-relationship-schema-1','sha256':hashof(doc)},'documentJson':raw(doc)}
profile=json.loads(request['queryProfileJson']);profile['version']='weft.security.query-profile/0.2-candidate';profile['id']='public-resource-relationship';profile['revision']='p1';profile['modelPins']=[module['pin']];profile['policySha256']=hashof(policy);profile['ontologySha256']=hashof(ontology)
profile['binding']['sha256']='0'*64
profile['relationships']=[{'relationship':{'documentId':'domain','moduleId':'m','relationshipId':'ResourceRelatedResource'},'operator':'hasRelated','observationAction':'observeResourceRelations','targetAction':'read'}]
denied_policy=copy.deepcopy(policy);denied_policy['rules']=copy.deepcopy(original_rules);denied_policy['revision']='public-relationship-observation-denied-1'
denied_profile=copy.deepcopy(profile);denied_profile['id']='public-resource-relationship-observation-denied';denied_profile['policySha256']=hashof(denied_policy)
for name,value in [('document',doc),('modules',[module]),('ontology',ontology),('policy',policy),('query-profile-template',profile),('resolution',{'ontology':ontology,'documents':[{'revision':'public-relationship-schema-1','document':doc}]}),('policy-observation-denied',denied_policy),('query-profile-observation-denied-template',denied_profile)]:
 (out/(name+'.json')).write_bytes(raw(value).encode())
(out/'source-manifest.json').write_text(json.dumps({'status':'authored-uninstalled-fixture','sources':{name:hashof(value) for name,value in [('document',doc),('ontology',ontology),('policy',policy),('policy-observation-denied',denied_policy)]},'originalReadRulesUnchanged':True,'nativeCorrespondence':None,'bindingDigestPlaceholder':'0'*64,'requiredNativeEdges':[['RB','RB'],['RB','RA'],['RA','RB'],['RO','RB']],'expectedBob':['RB'],'expectedRevokedAlice':[],'expectedOutsider':[],'expectedObservationDeniedBob':[]},indent=2)+'\n')
print(json.dumps({'status':'authored-uninstalled-fixture','directory':str(out)}))
