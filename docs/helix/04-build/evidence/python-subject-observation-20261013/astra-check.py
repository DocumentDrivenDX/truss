from pathlib import Path
from types import SimpleNamespace
from dataclasses import replace,FrozenInstanceError
import json,sys,hashlib
sys.path.insert(0,'/private/tmp/truss-security-main-integration/packages/python/src')
sys.path.insert(0,'/private/tmp/truss-psycopg-baseline-env/lib/python3.11/site-packages')
sys.path.insert(0,'/private/tmp/subject-consumer-python')
import weft
from truss.psycopg_host import PsycopgHost
from truss._psycopg_subject_observation import _SubjectSelection,_observe_ordinary_subject
assert Path(weft.__file__).resolve()==Path('/private/tmp/subject-consumer-python/weft.so')
out=Path('/private/tmp/python-subject-review-20261013')
p=Path('/private/tmp/truss-security-main-integration/packages/python/tests/fixtures/security-mapping-request.json');request=p.read_bytes();source=json.loads(request)['modules'][0]['documentJson'].encode()
base=_SubjectSelection(request,source,'m','Staff','pk','alice','selected','subject',('id',))
original=weft.inspect_security_mapping_subject_key_json
results=[]
class Cursor:
 def __init__(self,oid=25,names=('id',),rows=[('Δ\ufeff9007199254740993',)],principal=None):self.stage=0;self.oid=oid;self.names=names;self.rows=rows;self.principal=principal;self.helper_fetches=0
 def execute(self,*a,**kw):
  self.stage+=1;self.description=[SimpleNamespace(type_code=(25 if self.stage!=2 else self.oid),name=n) for n in (('principal','effective','super','bypass','encoding') if self.stage!=2 else self.names)]
 def fetchmany(self,n):
  if self.stage==2:self.helper_fetches+=1;return self.rows
  return [self.principal or ('alice','alice','false','false','UTF8')]
def call(cursor=None,selection=base,inspector=original,mode=('repeatable_read','read_only')):
 host=object.__new__(PsycopgHost);c=cursor or Cursor();host._run_operation=lambda tx,cb:cb(c,(('pid','vxid',*mode),None,'2000'))
 return _observe_ordinary_subject(host,object(),selection,inspector)
def check(name,fn,want_refuse):
 try:r=fn();refused=False
 except (ValueError,UnicodeError):refused=True
 assert refused==want_refuse,(name,refused);results.append({'name':name,'passed':True})
for mode in [('repeatable_read','read_only'),('serializable','read_only')]:check('profile-'+mode[0],lambda:call(mode=mode),False)
for mode in [('read_committed','read_only'),('repeatable_read','read_write')]:check('profile-refusal-'+mode[0]+'-'+mode[1],lambda:call(mode=mode),True)
for i,value in [(0,'bob'),(1,'role'),(2,'true'),(3,'true'),(4,'LATIN1')]:
 row=['alice','alice','false','false','UTF8'];row[i]=value;check('principal-refusal-'+str(i),lambda:call(Cursor(principal=tuple(row))),True)
for name,c in [('wrong-oid',Cursor(oid=19)),('wrong-name',Cursor(names=('other',))),('empty',Cursor(rows=[])),('two',Cursor(rows=[('a',),('b',)])),('null',Cursor(rows=[(None,)])),('bytes',Cursor(rows=[(b'a',)])),('over-cell',Cursor(rows=[('a'*65537,)]))]:check(name,lambda:call(c),True)
check('exact-cell',lambda:call(Cursor(rows=[('a'*65536,)])),False)
for name,s in [('wrong-source',replace(base,original_document=source+b' ')),('non-subject',replace(base,record='Resource')),('wrong-key',replace(base,key='other'))]:check(name,lambda:call(selection=s),True)
for name,response in [('numeric-false','{"interfaceVersion":"weft-security-subject-selection/0.1.0","status":"inspected","securityReady":0}'),('extra','{"interfaceVersion":"weft-security-subject-selection/0.1.0","status":"inspected","securityReady":false,"extra":0}'),('duplicate','{"interfaceVersion":"weft-security-subject-selection/0.1.0","status":"inspected","securityReady":false,"securityReady":false}')]:check(name,lambda:call(inspector=lambda *_:response),True)
calls=[]
async def deferred(*args):calls.append(True)
check('declared-async-cold',lambda:call(inspector=deferred),True);assert not calls
c=Cursor(oid=19);check('wrong-oid-refuses',lambda:call(c),True)
observed=call();assert observed.utf8_hex==(observed.values[0].encode().hex(),)
try:observed.principal='bob';raise AssertionError('mutable')
except FrozenInstanceError:pass
results.append({'name':'immutable-history-and-supported-driver-reencoding','passed':True})
report={'status':'passed','count':len(results),'results':results,'wrongOidHelperFetchCount':c.helper_fetches,'sourceSha256':hashlib.sha256(Path('/private/tmp/truss-security-main-integration/packages/python/src/truss/_psycopg_subject_observation.py').read_bytes()).hexdigest(),'scope':'Actual module and genuine compiled Weft selector; synthetic exact PsycopgHost operation callback/cursor, not native custody or SQL execution.'}
(out/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':len(results),'wrongOidHelperFetchCount':c.helper_fetches}))
