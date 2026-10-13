import json,copy,sys
from pathlib import Path
from hashlib import sha256
from types import SimpleNamespace
from truss._security_graph_mapping import observe_original_catalog,resolve_graph_mapping
from truss._security_mapping import SecurityMappingBoundary
from truss.catalog_runtime import _release
root=Path('/private/tmp/truss-security-main-integration')
out=Path(__file__).parent
manifest,digest,_=_release()
def enc(v):return json.dumps(v,separators=(',',':'),ensure_ascii=False).encode()
def basis_for(original,pin):
 model=json.loads(original);types=[];props=[];keys=[];nextprop=1
 source={'definition_rev':1,'definition_doc_ord':0,'definition_document_id':model['id'],'retired_rev':None}
 for mod in model['modules']:
  for e in mod['elements']:
   if e['kind']!='record':continue
   tid=len(types)+1;types.append(dict(source,document_id=model['id'],module=mod['id'],element=e['id'],type_id=tid));local={}
   for member in e['members']:
    props.append(dict(source,declaration_module=member['module'],element=member['element'],type_id=tid,prop_id=nextprop));local[(member['module'],member['element'])]=nextprop;nextprop+=1
   for i,k in enumerate(e.get('keys',[])):
    keys.append(dict(source,type_id=tid,key_id=k['id'],key_num=i+1,prop_ids=[local[(f['module'],f['element'])] for f in k['fields']]))
 return {'revision':'1','installationId':'synthetic-pure-basis','releaseId':manifest['releaseId'],'releaseSha256':digest,'layoutProfile':manifest['layoutProfile'],'registrationId':'synthetic','reportSha256':'b'*64,'documents':[{'rev':1,'ord':0,'doc_id':model['id'],'doc_revision':pin['revision'],'umf_version':pin['umfVersion'],'document':original,'content_sha256':sha256(original.encode()).hexdigest()}],'types':types,'properties':props,'keys':keys,'relationships':[],'endpoints':[]}
class Cursor:
 description=(SimpleNamespace(type_code=17),)
 def __init__(self,basis):self.data=enc(basis)
 def execute(self,*a,**k):pass
 def fetchmany(self,n):return [(self.data,)]
source=json.loads((root/'packages/python/tests/fixtures/security-mapping-request.json').read_text())
module=source['modules'][0];basis=basis_for(module['documentJson'],module['pin']);view=observe_original_catalog(Cursor(basis),source)
sys.path.insert(0,'/private/tmp/weft-security-mapping-native-20261013');import weft
assert Path(weft.__file__).resolve()==Path('/private/tmp/weft-security-mapping-native-20261013/weft.so')
boundary=SecurityMappingBoundary(weft.prepare_security_mapping_json,enc(source));prepared=boundary.prepare(enc(source));mapping=resolve_graph_mapping(prepared,view)
response=json.loads(prepared.original_response)['handoff']
expected=[]
for scan in response['scans']:
 s=scan['scan'];expected.append((s,None,'scan'))
 for purpose in ('projectionFields','queryFields'):expected.extend((s,None,purpose) for _ in scan[purpose])
 for a in scan['actions']:
  action=a['action'];expected.extend((s,action,'association') for _ in a['associations'])
  for inv in a['fields']:
   expected.append((s,action,'factType'));expected.extend((s,action,'factField') for _ in inv['fields'])
  expected.extend((s,action,'key') for _ in a['keys'])
assert [(r.scan,r.action,r.purpose) for r in mapping.references]==expected
controls={'genuine_weft_scan_inventory_reference_count':len(expected),'scan_count':len(response['scans']),'native_authority_claim':False}
# Current archive matching must not select a matching older archive.
old=copy.deepcopy(basis['documents'][0]);new=copy.deepcopy(old);new['rev']=2;new['doc_revision']='schema-2';new['document']+=' ';new['content_sha256']=sha256(new['document'].encode()).hexdigest()
changed=copy.deepcopy(basis);changed['documents']=[old,new]
try:observe_original_catalog(Cursor(changed),source)
except ValueError as e:controls['old_archive_refused']=str(e)
else:raise AssertionError('old archive accepted')
# Synthetic verified-basis premise only; no database mutated or native admissibility asserted.
large={'umf':'0.8.0','id':'large','modules':[{'id':'m','elements':[{'id':'field','kind':'field','scalarType':'string','name':'field','extensions':{'review':{'padding':'x'*655360}}}]+[{'id':f'T{i}','kind':'record','members':[{'module':'m','element':'field'}]} for i in range(20)]}]}
original=enc(large).decode();pin={'documentId':'large','revision':'1','umfVersion':'0.8.0','sha256':sha256(original.encode()).hexdigest()};req={'modules':[{'documentJson':original,'pin':pin,'selectedModuleIds':['m']}]};large_basis=basis_for(original,pin);cursor=Cursor(large_basis)
assert len(cursor.data)<16777216
large_view=observe_original_catalog(cursor,req)
controls['synthetic_basis_bytes']=len(cursor.data);controls['returned_view_bytes']=len(large_view.original_bytes);controls['returned_view_exceeds_profile_limit']=len(large_view.original_bytes)>16777216
assert controls['returned_view_exceeds_profile_limit']
controls['sourceDigests']={str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in [root/'packages/python/src/truss/_security_graph_mapping.py',root/'packages/python/src/truss/_security_mapping.py',root/'packages/python/src/truss/_catalog_view_build.py',root/'packages/python/src/truss/catalog_runtime.py',root/'packages/python/tests/test_security_graph_mapping_native.py',root/'scripts/check-module-boundaries.py']}
(out/'results.json').write_text(json.dumps(controls,indent=2)+'\n');print(json.dumps(controls,indent=2))
