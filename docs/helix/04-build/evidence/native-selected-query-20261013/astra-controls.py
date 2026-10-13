from pathlib import Path
import json,hashlib,subprocess,ast
out=Path(__file__).parent;packets=Path('/private/tmp/native-selected-query-final-20261013');test=Path('/private/tmp/truss-security-main-integration/packages/python/tests/test_security_predicate_native.py');binary=Path('/private/tmp/weft-042-release-target-a/debug/examples/security_predicate_spike')
def load(n):return json.loads((packets/(n+'.json')).read_bytes())
results=[]
def check(name,condition):assert condition,name;results.append({'case':name,'passed':True})
source=test.read_text();ast.parse(source);check('finalTestSourceParses',True)
request,assessment,output=load('request'),load('assessment'),load('rendered')
check('modulePinsMatchOriginalBytes',all(hashlib.sha256(m['documentJson'].encode()).hexdigest()==m['pin']['sha256'] for m in request['modules']))
check('assessmentModelPinsMatchOriginalSources',assessment['modelPins']==[m['pin'] for m in request['modules']])
run=subprocess.run([str(binary)],input=json.dumps({'request':request,'assessment':assessment}).encode(),capture_output=True,timeout=30);check('originalRendererPacketReplayed',run.returncode==0 and json.loads(run.stdout)==output)
truths=load('native-truths');eligibility=load('native-eligibility');comparisons=load('original-simulator-comparisons');cells=load('native-selected-cells');sql=load('native-selection-sql')
selected=next(e for e in output['eligibility'] if e['action']=='read' and e['target']['elementId']=='Resource');projections=','.join('('+r['expression']+') AS '+r['truthColumn'] for r in output['rules'] if r['target']['elementId']=='Resource');ids={r['element']:r['type_id'] for r in assessment['inventory']['types']}
permitted=[(s,r) for s,r,t in truths if t is True]
check('sixTruthPairsTwoPermits',len(truths)==6 and permitted==[(1,5),(2,6)])
check('nativeDecisionMatchesEveryTruth',[[s,r,d=='permit'] for s,r,d in eligibility]==truths)
check('originalSimulatorMatchesAllPairs',comparisons==[{'subject':s,'resource':r,'nativeTruth':t,'originalDecision':'permit' if t else 'filtered'} for s,r,t in truths])
for element in ('salary','resourceId'):
 projection=next(d['cellExpression'] for d in selected['disclosure'] if d['field']['elementId']==element)
 expected='SELECT q.sid,q.rid,('+projection+') FROM truss.object r JOIN (SELECT s.id AS sid,r.id AS rid,'+projections+' FROM truss.object s CROSS JOIN truss.object r WHERE s.type_id='+str(ids['Staff'])+' AND r.type_id='+str(ids['Resource'])+') q ON r.id=q.rid WHERE ('+selected['decisionExpression']+")='permit' ORDER BY q.sid,q.rid"
 check(element+'SqlExactOriginalExpressionsAndJoin',sql[element]==expected)
 check(element+'SelectedPairSequence',[(r['subject'],r['resource']) for r in cells[element]]==permitted)
 check(element+'UniquePairCount',len({(r['subject'],r['resource']) for r in cells[element]})==len(permitted))
check('withheldCellsContainNoValue',all(r['cell']=={'outcomeId':'withheld','disposition':'withheld'} for r in cells['salary']))
check('originalIdentityCellsCorrespond',[(r['resource'],r['cell']) for r in cells['resourceId']]==[(5,{'outcomeId':'original','disposition':'original','value':{'string':'ra'}}),(6,{'outcomeId':'original','disposition':'original','value':{'string':'rb'}})])
result={'scope':'Independent retained-packet/source consistency and current original renderer replay. Native SQL and crossed-subject tests were run by parent, not reviewer. Packets represent the final overwriting passing fixture, not independent archives for all8 cases.','passedControls':len(results),'cases':results,'binarySha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'packetDigests':{str(p.relative_to(packets)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(packets.rglob('*.json'))}}
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passedControls':len(results),'path':str(out/'results.json')}))
