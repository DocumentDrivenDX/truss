from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/private/tmp/weft-native-correspondence-wheel-r1-20261016')
import weft
root=Path(__file__).parent
request=json.loads((root/'packages/python/tests/fixtures/native-model-correspondence/weft-original-request.json').read_text())
model=json.loads(request['modules'][0]['documentJson']);elements=model['modules'][0]['elements']
field=next(e for e in elements if e['id']=='staffId');field['facets']={'retainedUnknownQualifier':'x'*1_500_000}
for e in elements:
 if e['kind']=='record' and e['id']!='Staff':e['members'].append({'module':'m','element':'staffId'})
request['modules'][0]['documentJson']=json.dumps(model,separators=(',',':'));original=json.dumps(request,separators=(',',':'))
parent=weft.prepare_application_lineage(original);current=parent.prepare_current_presence();report=current.model_requirements_json();q=json.loads(report)
assert len(original.encode())<4_000_000 and 8_388_608<len(report.encode())<=16_000_000
assert all(d['kind']=='scalar' and d['type']['nullable'] is False for r in q['records'] for f in r['fields'] for d in f['descriptors'])
result={'requestBytes':len(original.encode()),'requirementsBytes':len(report.encode()),'records':len(q['records']),'scalarOnly':True,'unknownFacetCopies':sum(d['type']['facets'].get('retainedUnknownQualifier')=='x'*1_500_000 for r in q['records'] for f in r['fields'] for d in f['descriptors']),'requestSha256':hashlib.sha256(original.encode()).hexdigest(),'requirementsSha256':hashlib.sha256(report.encode()).hexdigest(),'scope':'Actual issued scalar descriptor capacity probe; no native capture, domain interpretation or admission.'}
(root/'capacity-scalar-probe-r1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
