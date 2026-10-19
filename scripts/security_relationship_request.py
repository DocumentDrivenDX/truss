# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exact source-bound traversal request preparation; never an execution permit."""
from pathlib import Path
from hashlib import sha256
import json,runpy
ROOT=Path(__file__).resolve().parent.parent
FIXTURE=ROOT/'docs/helix/03-test/fixtures/security-public-relationship'

def prepare_relationship_request(physical_request,assessment,*,observation_denied=False,query_sql="SELECT r.resourceId FROM Resource r WHERE HAS_RELATED(r.relatedResources, KEY('RB'))"):
 if type(observation_denied) is not bool or type(query_sql) is not str or not 1<=len(query_sql.encode())<=4000000:raise ValueError('Exact bounded original traversal selection required')
 # These authored files are trusted source premises, not native credentials.
 sources={name:(FIXTURE/(name+'.json')).read_bytes() for name in ('document','resolution','transport')}
 policy_name='policy-observation-denied' if observation_denied else 'policy'
 sources['policy']=(FIXTURE/(policy_name+'.json')).read_bytes()
 derive=runpy.run_path(str(ROOT/'scripts/prepare-security-relationship-correspondence.py'))['derive_relationship_correspondence']
 correspondence=derive(assessment,physical_request,sources)
 native=json.loads(assessment);physical=json.loads(physical_request)
 modules=json.loads((FIXTURE/'modules.json').read_bytes())
 if len(modules)!=1 or modules[0]['documentJson'].encode()!=sources['document'] or modules[0]['pin']['sha256']!=sha256(sources['document']).hexdigest():raise ValueError('Exact selected logical module preimage required')
 source={'version':'weft.truss.security.graph-source/0.2-candidate','nativeSchemaRevision':native['revision'],'physicalModule':{**physical['modules'][0],'selectedModuleIds':['m']},'inventoryJson':assessment.decode(),'correspondenceJson':correspondence.decode(),'logicalResolutionJson':sources['resolution'].decode(),'logicalTransportJson':sources['transport'].decode()}
 binding=json.dumps(source,separators=(',',':')).encode()
 name='query-profile-observation-denied-template' if observation_denied else 'query-profile-template'
 profile=json.loads((FIXTURE/(name+'.json')).read_bytes())
 ontology=(FIXTURE/'ontology.json').read_bytes()
 if profile['policySha256']!=sha256(sources['policy']).hexdigest() or profile['ontologySha256']!=sha256(ontology).hexdigest():raise ValueError('Exact policy and ontology preimages required')
 profile['binding']['sha256']=sha256(binding).hexdigest()
 request={'interfaceVersion':'weft-security-mapping/0.1.0','modules':modules,'policyJson':sources['policy'].decode(),'ontologyJson':ontology.decode(),'queryProfileJson':json.dumps(profile,separators=(',',':')),'bindingJson':binding.decode(),'backendId':profile['binding']['backendId'],'backendVersion':profile['binding']['backendVersion'],'targetProfile':profile['binding']['targetProfile'],'sql':query_sql,'parameters':{}}
 raw=json.dumps(request,separators=(',',':')).encode()
 if len(raw)>4000000:raise ValueError('Bounded complete original traversal request required')
 return raw
