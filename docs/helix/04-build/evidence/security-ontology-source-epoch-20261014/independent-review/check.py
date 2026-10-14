"""Bounded offline graph-source review; never invokes a native host operation."""
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace
from unittest.mock import patch
import json
from truss._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source,graph_source_archives,verify_graph_fact_recipe_completeness
from truss._security_catalog_source_epoch import issue_initial_catalog_source_epoch_in_transaction
from truss._security_catalog_source_installation import PendingCatalogSourceMarker
from truss._security_source_epoch_installation import PendingSourceEpochInfrastructure,_MANIFEST_SHA256
from truss._psycopg_epoch_cut import _DDLBarrierComparison
from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison,_prepare_fenced_fact_cut
from truss.psycopg_host import PsycopgHost
from truss.execution import Error
ROOT=Path(__file__).resolve().parents[6]
EVIDENCE=Path(__file__).resolve().parent.parent
results=[]
def check(name,fn):
 fn();results.append({'name':name,'passed':True})
def require(v):
 assert v

def refuse(value):
 try:snapshot_graph_security_source(value)
 except (ValueError,KeyError,TypeError,AttributeError):return
 raise AssertionError('Altered source accepted')
value=PreparedGraphSecuritySource(*((EVIDENCE/f).read_bytes() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')))
def changed_binding(fn):
 request=json.loads(value.native_dependencies);binding=json.loads(request['bindingJson']);fn(binding)
 request['bindingJson']=json.dumps(binding,separators=(',',':'));raw=json.dumps(request,separators=(',',':')).encode()
 output=json.loads(value.original_response);output['sourceRequestSha256']=sha256(raw).hexdigest();output['bindingSha256']=sha256(request['bindingJson'].encode()).hexdigest()
 return replace(value,native_dependencies=raw,original_response=json.dumps(output).encode())
check('genuine retained snapshot',lambda:require(snapshot_graph_security_source(value)==value))
for name,bad in [('native revision integer',changed_binding(lambda b:b.update(nativeSchemaRevision=1))),('physical revision substituted',changed_binding(lambda b:b['physicalModule']['pin'].update(revision='r2'))),('unmatched compiler original bytes',replace(value,native_dependencies=value.native_dependencies+b' ')),('mutable original request',replace(value,original_request=bytearray(value.original_request))),('missing compiler binding',replace(value,native_dependencies=b'{}'))]:check(name,lambda bad=bad:refuse(bad))
def bool_inventory(b):
 inventory=json.loads(b['inventoryJson']);inventory['inventory']['types'][0]['type_id']=True;b['inventoryJson']=json.dumps(inventory)
check('rehashed Boolean versus native integer census',lambda:refuse(changed_binding(bool_inventory)))
for key,mutation in [('outer ready numeric zero',lambda o:o.update(securityReady=0)),('inner ready numeric zero',lambda o:o['query'].update(securityReady=0)),('inner source mismatch',lambda o:o['query'].update(contextSha256='0'*64))]:
 output=json.loads(value.original_response);mutation(output)
 check(key,lambda output=output:refuse(replace(value,original_response=json.dumps(output).encode())))
def detached():
 original=replace(value);captured=snapshot_graph_security_source(original);object.__setattr__(original,'original_request',b'{}');require(captured.original_request==value.original_request)
check('immutable carrier snapshot detached from replaced dataclass field',detached)
manifest=(ROOT/'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes()
archives=graph_source_archives(value,manifest);native=json.loads((EVIDENCE/'native-source-epoch.json').read_bytes())
check('six exact committed archive digests and identities',lambda:require(sorted([r,n,sha256(b).hexdigest(),sha256(n.encode()).hexdigest(),native['installation']] for r,n,b in archives)==sorted(native['archives'])))
profile=json.loads((EVIDENCE/'issued-profile.json').read_bytes())
check('graph profile original byte digests',lambda:require(all(profile[k]==sha256(v).hexdigest() for k,v in [('requestSha256',value.original_request),('acceptedCatalogSha256',value.accepted_catalog_assessment),('compilerRequestSha256',value.native_dependencies),('compilerOutputSha256',value.original_response)])))
check('exact three native fact recipe names',lambda:require({(r['schema'],r['name']) for r in profile['factCuts']}=={('truss','object'),('truss','edge'),('truss','catalog_subject_map')} and len(profile['factCuts'])==3))
column=_FactColumnComparison('id',1,20,-1,True,0)
relation=_FactRelationComparison('truss','object',123,456,'original fixture source',(column,))
class Cursor:
 def __init__(self,oid=25,rows=None):self.description=[SimpleNamespace(type_code=oid)];self.rows=[('1',)] if rows is None else rows;self.fetched=0
 def execute(self,*a,**kw):pass
 def fetchmany(self,n):self.fetched+=1;return self.rows
check('complete native count accepts',lambda:verify_graph_fact_recipe_completeness(Cursor(),(relation,)))
def incomplete_count():
 try:verify_graph_fact_recipe_completeness(Cursor(rows=[('2',)]),(relation,))
 except ValueError as error:require(str(error)=='Complete original graph fact column census required');return
 raise AssertionError('Incomplete census accepted')
check('omitted native column count refuses',incomplete_count)
def foreign_descriptor():
 c=Cursor(oid=19)
 try:verify_graph_fact_recipe_completeness(c,(relation,))
 except ValueError:require(c.fetched==0);return
 raise AssertionError('Foreign descriptor decoded')
check('foreign count descriptor refuses before fetch',foreign_descriptor)
def duplicate_columns():
 try:_prepare_fenced_fact_cut((replace(relation,columns=(column,column)),),lambda c:None)
 except ValueError as error:require(str(error)=='Duplicate native column binding');return
 raise AssertionError('Duplicate column accepted')
check('duplicate recipe cannot satisfy count',duplicate_columns)
host=object.__new__(PsycopgHost)
marker=PendingCatalogSourceMarker('installation','0'*64,'0'*64,b'incarnation')
infrastructure=PendingSourceEpochInfrastructure('installation',_MANIFEST_SHA256,_DDLBarrierComparison(10,11,'source'))
for name,bad in [('missing graph key returns bounded Error',replace(value,native_dependencies=b'{}',native_guard=(b'i',b'p',1))),('invalid UTF8 returns bounded Error',replace(value,native_dependencies=b'\xff',native_guard=(b'i',b'p',1)))]:
 def preflight(bad=bad):
  with patch.object(PsycopgHost,'_run_operation',side_effect=AssertionError('Host entered')):
   require(type(issue_initial_catalog_source_epoch_in_transaction(host,None,mapping=bad,marker=marker,infrastructure=infrastructure,fact_relations=(relation,),subject_source=b's')) is Error)
 check(name,preflight)
(Path(__file__).parent/'results.json').write_text(json.dumps({'scope':'Offline original retained-packet and synthetic descriptor/preflight controls; no native execution or authentication proof','controls':results,'passed':len(results),'failed':0},indent=2)+'\n')
print(f'{len(results)} bounded independent controls passed')
