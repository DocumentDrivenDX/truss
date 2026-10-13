from pathlib import Path
from types import SimpleNamespace
from dataclasses import FrozenInstanceError
from unittest.mock import patch
import sys,json,hashlib
root=Path('/private/tmp/truss-security-main-integration');out=Path('/private/tmp/python-subject-composition-review-20261013')
sys.path[:0]=[str(root/'packages/python/src'),'/private/tmp/truss-psycopg-baseline-env/lib/python3.11/site-packages','/private/tmp/subject-consumer-python']
import weft
from truss.psycopg_host import PsycopgHost
from truss._psycopg_subject_observation import _SubjectSelection,_observe_ordinary_subject_key
from truss._umf_key_tuples import encode_literal_key_tuple
assert Path(weft.__file__).resolve()==Path('/private/tmp/subject-consumer-python/weft.so')
native=json.loads(Path('/private/tmp/python-subject-composition-native.json').read_text());request=json.dumps(native['originalRequest']).encode();source=native['originalRequest']['modules'][0]['documentJson'].encode()
selection=_SubjectSelection(request,source,'m','Staff','pk','alice','selected','subject',tuple('k'+str(i) for i in range(5)))
class Cursor:
 def __init__(self,values,late=False):self.values=values;self.late=late;self.stage=0
 def execute(self,*a,**kw):
  self.stage+=1;self.description=[SimpleNamespace(type_code=25,name=n)for n in (selection.columns if self.stage==2 else ('principal','effective','super','bypass','encoding'))]
 def fetchmany(self,n):return [self.values] if self.stage==2 else [('alice','foreign' if self.stage==4 and self.late else 'alice','false','false','UTF8')]
results=[]
def run(values,encodings,late=False,encoder=None):
 c=Cursor(values,late);host=object.__new__(PsycopgHost);state={'operations':0,'active':False,'encoderInside':[]}
 def operation(tx,callback):
  state['operations']+=1;state['active']=True
  try:return callback(c,(('pid','vxid','repeatable_read','read_only'),None,'2000'))
  finally:state['active']=False
 host._run_operation=operation
 def original(*a,**k):state['encoderInside'].append(state['active']);return (encoder or encode_literal_key_tuple)(*a,**k)
 with patch('truss._umf_key_tuples.encode_literal_key_tuple',side_effect=original):
  value=_observe_ordinary_subject_key(host,object(),selection,weft.inspect_security_mapping_subject_key_json,encodings,bun_executable='/opt/homebrew/bin/bun')
 assert state=={'operations':1,'active':False,'encoderInside':[True]}
 assert c.stage==4
 return value
texts=tuple(native['nativeText']);encodings=('core-literal-json',)*5
v=run(texts,encodings);assert v.tuple_bytes.hex()==native['tupleHex'] and v.original_receipt_bytes.decode()==native['originalReceipt'];results.append({'name':'one-original-operation-five-family-correspondence','passed':True})
mixed=(json.loads(texts[0])['string'],*texts[1:]);v=run(mixed,('string',*encodings[1:]));assert v.tuple_bytes.hex()==native['tupleHex'];assert v.observation.values==mixed;results.append({'name':'mixed-string-and-original-literal-json-correspondence','passed':True})
for name,fn in [('all-string-domain-refusal',lambda:run(texts,('string',)*5)),('postcodec-principal-refusal',lambda:run(texts,encodings,late=True)),('mutable-encoding-refusal',lambda:run(texts,list(encodings))),('encoding-arity-refusal',lambda:run(texts,encodings[:-1])),('unknown-encoding-refusal',lambda:run(texts,('other',*encodings[1:]))),('nonstring-encoding-refusal',lambda:run(texts,(True,*encodings[1:]))),('codec-exception-refusal',lambda:run(texts,encodings,encoder=lambda *_a,**_k:(_ for _ in ()).throw(ValueError('codec'))))]:
 try:fn();raise AssertionError('did not refuse: '+name)
 except ValueError:pass
 results.append({'name':name,'passed':True})
try:v.tuple_bytes=b'foreign';raise AssertionError('mutable')
except FrozenInstanceError:pass
results.append({'name':'frozen-composed-result','passed':True})
(out/'results.json').write_text(json.dumps({'status':'passed','count':len(results),'results':results,'scope':'Actual composed observer plus original compiled Weft and pinned UMF owner; synthetic host callback/cursor. Original-operation count and postcodec principal ordering only; native deadlines/savepoint/lease custody use separately retained parent native controls.','sourceSha256':hashlib.sha256(root.joinpath('packages/python/src/truss/_psycopg_subject_observation.py').read_bytes()).hexdigest()},indent=2)+'\n')
print('Passed',len(results),'composition controls')
