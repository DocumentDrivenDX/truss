"""Isolate actual local source/context predicates; no native execution."""
import ast,copy,hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[6];folder=pathlib.Path(__file__).resolve().parent.parent
source=root/'scripts/security_ontology_compiled_read.py';raw=source.read_bytes();tree=ast.parse(raw)
def predicate(message):
 nodes=[n.test for n in ast.walk(tree) if isinstance(n,ast.If) and any(isinstance(c,ast.Constant) and c.value==message for s in n.body for c in ast.walk(s))]
 assert len(nodes)==1
 return compile(ast.Expression(nodes[0]),str(source),'eval'),ast.unparse(nodes[0])
context,context_text=predicate('Original selected graph compiler query context required')
home,home_text=predicate('Original compiled native Staff home required')
item=json.loads((folder/'compiled-native-results.json').read_text())['results'][0]
output=json.loads(item['output']); original=output['query']; tid=original['execution']['subjectSlot']['nativeTypeId']
cases=[('exact',original,False)]
for key,values in [('policyParameters',[[1],[1.0],[False],[],[True,True],True,None]),('ordinal',[2.0,'2',None,3]),('nativeTypeId',[float(tid),str(tid),None,tid+1])]:
 for value in values:
  query=copy.deepcopy(original)
  target=query['execution'] if key=='policyParameters' else query['execution']['subjectSlot']
  target[key]=value
  cases.append((key+'-'+repr(value),query,True))
checks=[]
for name,query,expected in cases:
 scope={'query':query,'output':output,'execution':query['execution'],'slot':query['execution']['subjectSlot'],'staff':[{'type_id':tid}]}
 try:refused=bool(eval(context,scope) or eval(home,scope))
 except Exception:refused=True
 checks.append({'control':name,'expectedRefusal':expected,'observedRefusal':refused,'passed':expected is refused})
print(json.dumps({'scope':'Actual source predicate isolation only; trusted original owner binary remains a premise.','sourceSha256':hashlib.sha256(raw).hexdigest(),'packetSha256':hashlib.sha256((folder/'compiled-native-results.json').read_bytes()).hexdigest(),'predicates':[context_text,home_text],'controls':checks,'allPassed':all(c['passed'] for c in checks)},indent=2))
