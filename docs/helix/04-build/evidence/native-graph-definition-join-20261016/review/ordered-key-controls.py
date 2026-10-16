from pathlib import Path
import sys,json,copy
p=Path(__file__).resolve().parent;sys.path.insert(0,str(p/'working/packages/python/src'))
from truss._native_graph_correspondence import _endpoint
r=json.loads((p/'packet/docs/helix/04-build/evidence/native-graph-definition-join-20261016/model-report.json').read_bytes())
row=copy.deepcopy(next(r for r in r['records'] if len(r['fields'])>=2));row['selectedKey']['fields']=[f['field'] for f in row['fields'][:2]];endpoint={'target':row['record'],'key':{'record':row['record'],'id':row['selectedKey']['id'],'fields':row['selectedKey']['fields']}}
assert _endpoint(endpoint,[row]) is row
names=['exact ordered synthetic composite accepted']
for label,change in [('reversed components',lambda e:e['key']['fields'].reverse()),('foreign revision',lambda e:e['key']['fields'][0].update(revision='foreign')),('wrong authored Key',lambda e:e['key'].update(id='other'))]:
 e=copy.deepcopy(endpoint);change(e)
 try:_endpoint(e,[row])
 except ValueError as ex:assert 'ordered endpoint Key' in str(ex);names.append(label+' refused')
 else:raise AssertionError(label)
(p/'ordered-key-controls.json').write_text(json.dumps({'passed':True,'controls':names,'scope':'Pure supplied metadata comparison only; no native composite-Key campaign.'},indent=2)+'\n');print('4 supplied composite-Key comparison controls passed')
