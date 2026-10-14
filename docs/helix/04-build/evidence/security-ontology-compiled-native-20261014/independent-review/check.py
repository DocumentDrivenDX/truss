"""Bounded source-predicate and retained packet checks; no native execution."""
import ast, hashlib, json, pathlib, types
root=pathlib.Path(__file__).resolve().parents[6]
folder=pathlib.Path(__file__).resolve().parent.parent
source=root/'scripts/security_ontology_compiled_read.py'
raw=source.read_bytes(); tree=ast.parse(raw)
checks=[node.test for node in ast.walk(tree) if isinstance(node,ast.If) and any(isinstance(n,ast.Constant) and n.value=='Original graph result checker correspondence required' for s in node.body for n in ast.walk(s))]
assert len(checks)==1
predicate=compile(ast.Expression(checks[0]),str(source),'eval')
sha256=hashlib.sha256
packet_path=folder/'compiled-native-results.json'
packet=json.loads(packet_path.read_bytes()); results=[]
expected_keys={'Alice':['RA'],'Bob':['RB'],'Outsider':[]}
for item in packet['results']:
 request=item['request'].encode(); output=json.loads(item['output']); query=output['query']; batch=json.loads(item['batch']); report=json.loads(item['resultCheck'])
 assert json.loads(request)['sql']=='SELECT r.resourceId, r.salary FROM Resource r'
 assert output['sourceRequestSha256']==sha256(request).hexdigest()
 assert output['bindingSha256']==sha256(json.loads(request)['bindingJson'].encode()).hexdigest()
 assert query['contextSha256']==output['contextSha256']
 assert query['graphSourceSha256']==output['graph']['graphSourceSha256']
 assert query['securityReady'] is False and query['nativeAdmission']=='required'
 assert batch['rows']==item['cells'] and batch['resultContractSha256']==query['resultContractSha256']
 assert [row[0]['value']['string'] for row in item['cells']]==expected_keys[item['subject']]
 for row in item['cells']:
  assert len(row)==2 and row[1]=={'outcomeId':'withheld','disposition':'withheld'}
 assert report['sourceRequestSha256']==sha256(request).hexdigest()
 assert report['sourceOutputSha256']==sha256(item['output'].encode()).hexdigest()
 assert report['batchSha256']==sha256(item['batch'].encode()).hexdigest()
 assert report['securityReady'] is False and report['status']=='inspected'
 results.append({'control':'retained-'+item['subject'],'passed':True})
item=packet['results'][0]
base=json.loads(item['resultCheck'])
context={'request':item['request'].encode(),'compiled':types.SimpleNamespace(stdout=item['output'].encode()),'batch':item['batch'],'sha256':sha256}
variants=[('exact',base,False)]
for value in (0,0.0,True,None,'false'):
 variants.append(('securityReady-'+repr(value),{**base,'securityReady':value},True))
variants += [('extra',{**base,'extra':1},True),('missing',{k:v for k,v in base.items() if k!='status'},True),('wrong-status',{**base,'status':'prepared'},True),('wrong-batch-hash',{**base,'batchSha256':'0'*64},True),('wrong-request-hash',{**base,'sourceRequestSha256':'0'*64},True),('wrong-output-hash',{**base,'sourceOutputSha256':'0'*64},True),('wrong-version',{**base,'version':'different'},True)]
for name,value,expected_refuse in variants:
 try: observed=bool(eval(predicate,{**context,'result_check':value}))
 except Exception: observed=True
 results.append({'control':name,'expectedRefuse':expected_refuse,'observedRefuse':observed,'passed':observed is expected_refuse})
legacy=[n for n in ast.walk(checks[0]) if isinstance(n,ast.Compare) and isinstance(n.left,ast.Name) and n.left.id=='result_check' and isinstance(n.comparators[0],ast.Dict)]
assert len(legacy)==1
legacy_predicate=compile(ast.Expression(legacy[0]),str(source),'eval')
legacy_witnesses=[{'securityReady':v,'legacyBareEqualityRefuses':bool(eval(legacy_predicate,{**context,'result_check':{**base,'securityReady':v}}))} for v in (0,0.0)]
assert all(not w['legacyBareEqualityRefuses'] for w in legacy_witnesses)
print(json.dumps({'legacyEqualityWitnesses':legacy_witnesses,'scope':'Original source predicate isolated, plus offline retained native packet correspondence; no subprocess/native execution or refinement theorem.','sourceSha256':sha256(raw).hexdigest(),'packetSha256':sha256(packet_path.read_bytes()).hexdigest(),'predicate':ast.unparse(checks[0]),'controls':results,'allPassed':all(r['passed'] for r in results)},indent=2))
