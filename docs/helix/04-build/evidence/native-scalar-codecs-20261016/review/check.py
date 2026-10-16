from pathlib import Path
import ast,hashlib,json,zipfile,base64,subprocess
p=Path(__file__).resolve().parent;s=Path('/private/tmp/truss-native-scalar-codecs-review-20261016');H=lambda b:hashlib.sha256(b).hexdigest();m=json.loads((s/'manifest.json').read_bytes())
for n,h in m.items():
 b=(s/n).read_bytes();assert H(b)==h,n;t=p/'packet'/n;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(b)
(p/'packet/manifest.json').write_bytes((s/'manifest.json').read_bytes());e=p/'packet/docs/helix/04-build/evidence/native-scalar-codecs-20261016';ret=json.loads((e/'retention.json').read_bytes())
for n,h in ret['sourceFiles'].items():assert H((p/'packet'/n).read_bytes())==h
for n,h in ret['files'].items():assert H((e/n).read_bytes())==h
members={}
for prefix in ('initial-single-key','failed-stage','final-native'):
 zname=prefix+'-artifacts.zip';zm=json.loads((e/(zname+'.manifest.json')).read_bytes())
 with zipfile.ZipFile(e/zname) as z:
  assert set(z.namelist())==set(zm)
  for n,v in zm.items():b=z.read(n);assert H(b)==v['sha256'] and len(b)==v['bytes']
  members[prefix]=len(zm)
code=(p/'packet/packages/python/tests/test_current_disclosure_codecs_native.py').read_bytes();tree=ast.parse(code);values=ast.literal_eval(next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='VALUES' for t in n.targets)).value)
def strict(a,b):
 assert type(a) is type(b),(a,b)
 if type(a) is dict:
  assert a.keys()==b.keys()
  for k in a:strict(a[k],b[k])
 elif type(a) is list:
  assert len(a)==len(b)
  for x,y in zip(a,b):strict(x,y)
 else:assert a==b,(a,b)
with zipfile.ZipFile(e/'final-native-artifacts.zip') as z:
 facts=json.loads(z.read('native-inputs-base/facts.json'));result=json.loads(z.read('codec-correspondence.json'));resources={f['key'][0]['string']:f for f in facts if f['type']['elementId']=='Resource'};assert len(resources)==3
 for k,v in values.items():
  f=resources[k];strict(f['key'],[{'string':k},v['codecBytes']]);strict({c['field']['elementId']:c['value'] for c in f['fields']},{'resourceId':{'string':k},**v});strict(f['absent'],[] if 'codecOptional' in v else [{'documentId':'adoc','moduleId':'m','elementId':'codecOptional'}])
 delivered=[];optional=[]
 for o in result['observations']:
  subject=o['subject'];batch=o['decision']['batch'];fields=[c['field']['elementId'] for c in batch['columns']];key={'Alice':'RA','Bob':'RB'}.get(subject)
  if key is None:strict(batch['rows'],[]);continue
  actual={'resourceId':{'string':key},**values[key]};expected=[{'disposition':'original','value':actual[f]} if f in actual else {'disposition':'absent'} for f in fields];strict(batch['rows'],[expected]);delivered.append(key);optional.append(batch['rows'][0][fields.index('codecOptional')])
 assert delivered==['RA','RB'] and optional==[{'disposition':'original','value':None},{'disposition':'absent'}]
 controls=result['negativeControls'];assert len(controls)==8
 for c in controls[:4]:
  assert c['stage']=='original-UMF-global-domain-refusal' and c['ownerlessCorruptedResource']=='RO' and c['subject']=='Alice';r=c['result'];assert r['status']=='refused' and r['resources']==r['decisions']==[] and r['batch'] is None
 assert all(c['stage']=='native-cell-capture-refusal' for c in controls[4:7]);strict(controls[7]['nativeDiagnostic'],{'code':'invalid_input','outcome':'failed','nativeState':'22023','operationIndex':'0'});assert controls[7]['canonicalObjectRowsUnchangedAfterCommit'] is True
 strict(json.loads(z.read('codec-domain-and-decoder-controls.json')),controls[:7])
 summary={'passed':True,'frozenFilesVerified':len(m),'archiveMembersVerified':members,'capturedResourceKeys':['RA','RB','RO'],'renderedResourceKeys':delivered,'renderedOptionalCells':optional,'nativeOnlyROValues':values['RO'],'strictTypeAndTokenPositiveComparison':True,'orderedCompositeKeysExact':True,'negativeStages':[c['stage'] for c in controls],'SQLExecuted':False,'finding':'README says present-empty optional String occurs in public tagged V2 cells, but only denied RO has it and no retained public row renders RO.'}
(p/'checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
