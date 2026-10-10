#!/usr/bin/env python3
"""Actual Python/TypeScript structural replay; no native or corpus release claim."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: raise SystemExit('usage: check-operation-registry-parity.py NEW_RECEIPT_PATH')
destination=Path(sys.argv[1])
if destination.exists(): raise SystemExit('refusing to replace receipt')
sys.path.insert(0,str(root/'packages/python/src'))
from truss._operation_registry import COLUMNS, decode_operation_registry
fixture=root/'tests/fixtures/operation-registry-decoder.json'
cases=json.loads(fixture.read_bytes())['cases']
script='''import {decodeOperationRegistry,OPERATION_REGISTRY_COLUMNS} from './packages/postgresql/src/index.ts';
const corpus=await Bun.file('tests/fixtures/operation-registry-decoder.json').json();
const results=corpus.cases.map(c=>{try{
 const result={columns:OPERATION_REGISTRY_COLUMNS,rows:c.rows.map(r=>r.map(text=>text===null?{state:'null'}:{state:'text',text})),command:'SELECT',affectedRows:String(c.rows.length)};
 return {id:c.id,status:'admitted',rows:decodeOperationRegistry(c.actualXid,result,{maxRows:c.maxRows,maxBytes:c.maxBytes})};
}catch(error){if(error.message!=='operation-registry:unavailable')throw error;return {id:c.id,status:'refused'};}});
console.log(JSON.stringify(results));'''
run=subprocess.run(['bun','-e',script],cwd=root,capture_output=True,text=True,timeout=30,check=True)
actual_ts=json.loads(run.stdout)
actual_python=[]
for case in cases:
 try:
  rows=decode_operation_registry(case['actualXid'],COLUMNS,case['rows'],'SELECT',str(len(case['rows'])),case['maxRows'],case['maxBytes'])
  result={'id':case['id'],'status':'admitted','rows':[list(row) for row in rows]}
 except ValueError as error:
  if str(error)!='operation-registry:unavailable': raise
  result={'id':case['id'],'status':'refused'}
 assert result['status']==case['expected'],case['id']
 if result['status']=='admitted': assert result['rows']==case['rows']
 actual_python.append(result)
assert actual_ts==actual_python
paths=['tests/fixtures/operation-registry-decoder.json','packages/python/src/truss/_operation_registry.py','packages/postgresql/src/index.ts','scripts/check-operation-registry-parity.py']
receipt={'scope':'Actual independent structural registry vectors in Python and TypeScript; no native observation or authority','cases':len(cases),'results':actual_python,'sources':[{'path':p,'sha256':hashlib.sha256((root/p).read_bytes()).hexdigest()} for p in paths],'typescriptOutputSha256':hashlib.sha256(run.stdout.encode()).hexdigest(),'bunVersion':subprocess.check_output(['bun','--version'],text=True).strip(),'pythonVersion':sys.version,'nativeQualified':False,'fullSharedCorpusQualified':False}
with destination.open('x') as output: output.write(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'cases':len(cases),'pythonTypeScriptParity':True,'nativeQualified':False}))
