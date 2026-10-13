"""Bounded actual installer preflight and exact selected metadata checks; no DB."""
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import ast,hashlib,inspect,json,types
from truss import _security_catalog_subject_installation as m
from truss._security_mapping import PreparedSecurityMapping
from truss.execution import Error
ROOT=Path('/private/tmp/truss-security-main-integration');OUT=Path(__file__).parent;checks=[]
def check(n,fn):fn();checks.append({'name':n,'passed':True})
def eq(a,b):assert a==b,(a,b)
def refused(fn):
 try:fn()
 except (ValueError,TypeError,KeyError):return
 raise AssertionError('Refusal required')
def make():
 request=json.dumps({'ontologyJson':json.dumps({'subject':{'documentId':'domain','moduleId':'m','elementId':'Staff'},'entities':[{'type':{'documentId':'domain','moduleId':'m','elementId':'Staff'},'keyId':'pk'}]})},separators=(',',':')).encode()
 inventory={'types':[{'document_id':'domain','module':'m','element':'Staff','retired_rev':None,'kind':'record','provisional':False,'type_id':5}], 'properties':[{'type_id':5,'definition_document_id':'domain','declaration_module':'m','element':'staffId','retired_rev':None,'home':'json','scalar_type':'string','cardinality':'one','nullability':'required','prop_id':8}], 'keys':[{'type_id':5,'key_id':'pk','retired_rev':None,'prop_ids':[8]}]}
 return PreparedSecurityMapping(request,b'original response',accepted_catalog_assessment=json.dumps({'inventory':inventory}).encode(),native_dependencies=b'original dependencies')
base=make();check('selected original Staff recipe',lambda:eq(m._staff_recipe(base),(5,'8')))
for collection,field,val in [('types','document_id','foreign'),('types','module','other'),('types','element','Other'),('types','retired_rev',1),('types','kind','entity'),('types','provisional',True),('types','type_id',True),('properties','definition_document_id','foreign'),('properties','declaration_module','other'),('properties','element','other'),('properties','home','row'),('properties','scalar_type','integer'),('properties','cardinality','many'),('properties','nullability','nullable'),('properties','retired_rev',1),('properties','prop_id',True),('keys','key_id','alternate'),('keys','retired_rev',1),('keys','prop_ids',[8,9])]:
 def probe(c=collection,f=field,v=val):
  parsed=json.loads(base.accepted_catalog_assessment);parsed['inventory'][c][0][f]=v
  refused(lambda:m._staff_recipe(replace(base,accepted_catalog_assessment=json.dumps(parsed).encode())))
 check('recipe '+collection+'.'+field+'='+str(val),probe)
for collection in ('types','properties','keys'):
 for mutation in ('empty','duplicate'):
  def probe(c=collection,mutation=mutation):
   parsed=json.loads(base.accepted_catalog_assessment);original=parsed['inventory'][c];parsed['inventory'][c]=[] if mutation=='empty' else original*2
   refused(lambda:m._staff_recipe(replace(base,accepted_catalog_assessment=json.dumps(parsed).encode())))
  check('recipe '+collection+' '+mutation,probe)
class Cursor:
 def __init__(self,codes,rows):self.description=None if codes is None else [types.SimpleNamespace(type_code=c) for c in codes];self.rows=rows;self.fetched=0
 def execute(self,*args,**kw):pass
 def fetchmany(self,n):self.fetched+=1;return self.rows
for codes in (None,[19],[25,19]):
 def probe(codes=codes):
  c=Cursor(codes,[('ok',)]);refused(lambda:m._text_rows(c,'q'));eq(c.fetched,0)
 check('foreign descriptors refuse before fetch '+str(codes),probe)
for rows in [[(None,)],[(b'raw',)],[(True,)],[('a',),('b',)]]:
 check('foreign rows/excess refuse '+str(rows),lambda r=rows:refused(lambda:m._text_rows(Cursor([25],r),'q',limit=1)))
source=ROOT/'packages/python/src/truss/_security_bootstrap/catalog-subject.sql'
check('packaged helper exact original bytes and pin',lambda:eq((source.read_bytes(),hashlib.sha256(source.read_bytes()).hexdigest()),((ROOT/'scripts/security-catalog-subject.sql').read_bytes(),m._SOURCE_SHA256)))
def dispatch(mapping=base,bindings=(('consumer','s1'),),read_mutation=None):
 state={'calls':0};host=object.__new__(m.PsycopgHost)
 def operation(self,tx,callback):
  state['calls']+=1;captured=inspect.getclosurevars(callback).nonlocals
  state['request']=captured['mapping'].original_request;state['bindings']=captured['bindings'];state['source']=captured['source'];return 'dispatch-only'
 real=Path.read_bytes
 def read(path):
  if path==source and read_mutation:read_mutation()
  return real(path)
 with patch.object(m.PsycopgHost,'_run_operation',operation),patch.object(Path,'read_bytes',read):
  result=m.bootstrap_catalog_subjects_in_transaction(host,object(),mapping=mapping,bindings=bindings)
 return result,state
for value in ([],(),(('consumer','s1'),)*257,(('consumer','s1'),('consumer','s2')),(('consumer',),),(('consumer',''),),(('','s1'),),(('x'*64,'s1'),),(('consumer','x'*4097),),(('consumer',bytearray(b's1')),),(('consumer','x\0y'),)):
 def probe(v=value):
  result,state=dispatch(bindings=v);assert isinstance(result,Error);eq(state['calls'],0)
 check('binding shape/limit refusal '+repr(value)[:90],probe)
for field,value in [('original_request',b''),('original_request',bytearray(b'{}')),('original_response',b''),('accepted_catalog_assessment',b'[]'),('native_dependencies',b'')]:
 def probe(f=field,v=value):
  result,state=dispatch(mapping=replace(base,**{f:v}));assert isinstance(result,Error);eq(state['calls'],0)
 check('original mapping preflight '+field+' '+str(type(value)),probe)
def bound():
 result,state=dispatch(bindings=tuple(('role'+str(i),'s1') for i in range(256)));eq(result,'dispatch-only');eq(len(state['bindings']),256)
check('256 unique roles bounded preflight succeeds',bound)
def custody():
 original=make();raw=original.original_request
 result,state=dispatch(mapping=original,read_mutation=lambda:object.__setattr__(original,'original_request',b'substituted'))
 eq(result,'dispatch-only');eq(state['request'],raw);eq(state['source'],source.read_bytes())
check('mapping captured before packaged helper read',custody)
for label,entities in [('missing',[]),('duplicate',[{'type':{'documentId':'domain','moduleId':'m','elementId':'Staff'},'keyId':'pk'}]*2),('wrong key',[{'type':{'documentId':'domain','moduleId':'m','elementId':'Staff'},'keyId':'other'}])]:
 def probe(entities=entities):
  request=json.loads(base.original_request);ontology=json.loads(request['ontologyJson']);ontology['entities']=entities;request['ontologyJson']=json.dumps(ontology)
  refused(lambda:m._staff_recipe(replace(base,original_request=json.dumps(request).encode())))
 check('ontology selected key '+label,probe)
# Execute exactly the extracted final privilege-query assignment and refusal gate.
module_path=ROOT/'packages/python/src/truss/_security_catalog_subject_installation.py'
tree=ast.parse(module_path.read_text());outer=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='bootstrap_catalog_subjects_in_transaction');inner=next(n for n in outer.body if isinstance(n,ast.FunctionDef) and n.name=='install')
index=next(i for i,n in enumerate(inner.body) if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='reads')
gate=compile(ast.Module(body=inner.body[index:index+2],type_ignores=[]),str(module_path),'exec')
for schema,select in [('true','true'),('true','false'),('false','true'),('false','false')]:
 def probe(schema=schema,select=select):
  captures=[]
  def rows(cursor,q,params,limit):captures.append((q,params,limit));return [(schema,select)]
  env={'cursor':None,'owner':42,'_text_rows':rows}
  if schema==select=='true':exec(gate,env)
  else:refused(lambda:exec(gate,env))
  eq(captures[0][1],(42,['truss.object','truss.catalog_subject_map','truss.catalog_runtime_installation','truss.type_def','truss.prop_def'],42));eq(captures[0][2],1)
 check('exact owner schema/read gate '+schema+'/'+select,probe)
output={'scope':'Real selected recipe, source pin, descriptor, immutable input and pre-host controls only. Synthetic cursor and host dispatch; no native effects, role privilege proof or completed admission.','count':len(checks),'passed':True,'controls':checks,'sourceSha256':hashlib.sha256((ROOT/'packages/python/src/truss/_security_catalog_subject_installation.py').read_bytes()).hexdigest()}
(OUT/'installer-results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'count':len(checks),'passed':True}))
