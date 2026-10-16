from pathlib import Path
import json,hashlib,sys,copy
sys.path.insert(0,'/private/tmp/truss-graph-requirements-final-weft-installed-20261016')
import weft,weft.weft as native
wire=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
base=Path('/private/tmp/truss-graph-closing-native-20261016/native-inputs-base')
initial=json.loads((base/'initialize.json').read_bytes())
r=json.loads(Path('/private/tmp/weft-graph-bridge-frozen-review-20261016/tests/current-query-presence/fixtures/unadmitted-context.request.json').read_text())
r['modules']=json.loads((base/'accepted-request.json').read_bytes())['modules'];r['sql']='SELECT r.salary FROM Resource r'
for module in r['modules']:module['selectedModuleIds']=['m']
for s in r['opaqueSources']:
 role=s['role']
 if role in ('policy','catalog','ontology','owner'):
  value=initial['owner'] if role=='owner' else initial['sources'][role]
  s['utf8']=wire(value);s['sha256']=sha(s['utf8'].encode());s['identity']={'documentId':value.get('id',value.get('documentId')),'revision':value['revision']}
p=next(s for s in r['opaqueSources'] if s['role']=='presence-designation');d=json.loads(p['utf8']);d['modelPins']=[m['pin'] for m in r['modules']];d['sources']=[{k:s[k] for k in ('role','identity','sha256')} for s in r['opaqueSources'] if s['role'] in ('policy','catalog','ontology','owner')];d['targets']=[{'documentId':'adoc','moduleId':'m','elementId':'Resource'}];p['utf8']=wire(d);p['sha256']=sha(p['utf8'].encode())
raw=wire(r);Path('/private/tmp/truss-actual-graph-request-debug.json').write_text(raw);parent=weft.prepare_application_lineage(raw);current=parent.prepare_current_presence();encoded=current.graph_requirements_json();g=json.loads(encoded)
assert current.source_preparation() is parent
assert g['sourceRequestJson']==raw and g['sourceRequestSha256']==sha(raw.encode())
assert g['preparationSha256']==sha(current.json().encode())
assert g['modelRequirementsSha256']==sha(current.model_requirements_json().encode())
assert g['complete'] is False and g['authority'] is False and g['securityReady'] is False
expected=initial['sources']['ontology']['associations'];assert len(g['associations'])==len(expected)
for ordinal,(a,e) in enumerate(zip(g['associations'],expected)):
 assert a['ordinal']==ordinal and a['selection']==e
 if e['kind']=='core-relationship':
  assert a['reference']==e['relationship'] and 'relationshipId' in a['reference']
  document=json.loads(r['modules'][0]['documentJson']);module=next(m for m in document['modules'] if m['id']==e['relationship']['moduleId'])
  assert a['authored']==next(x for x in module['relationships'] if x['id']==e['relationship']['relationshipId'])
  for endpoint in a['endpoints']:
   original=next(x for x in e['endpoints'] if x['role']==endpoint['role'])
   assert endpoint['side']==original['side'] and endpoint['key']['id']==original['keyId']
   assert endpoint['target']['element']==original['target']['elementId']
   assert endpoint['key']['record']==endpoint['target']
   record=next(x for x in module['elements'] if x['id']==endpoint['target']['element'])
   key=next(x for x in record['keys'] if x['id']==endpoint['key']['id'])
   assert [(f['module'],f['element']) for f in endpoint['key']['fields']]==[(f['module'],f['element']) for f in key['fields']]
  assert a['witness']==e['witness']
out=Path('/private/tmp/truss-actual-graph-requirements-20261016');out.mkdir(exist_ok=True)
for name,data in [('original-request.json',raw),('issued-graph-requirements.json',encoded),('issued-model-requirements.json',current.model_requirements_json()),('issued-preparation.json',current.json())]:(out/name).write_text(data)
(out/'receipt.json').write_text(json.dumps({'scope':'Actual same-context bridge over previously captured native fixture source; no live native custody/admission','nativeBinarySha256':sha(Path(native.__file__).read_bytes()),'associations':len(expected),'coreRelationships':sum(a['kind']=='core-relationship' for a in g['associations']),'sameOriginalParent':True,'nativeAdmission':False,'acceptancePromotion':False},indent=2)+'\n')
print((out/'receipt.json').read_text())
