from pathlib import Path
from dataclasses import replace
import hashlib,json
import security_catalog_subject_read as read
from truss._psycopg_epoch_cut import _DDLBarrierComparison
from truss._psycopg_fact_cut import _FactColumnComparison,_FactRelationComparison
from truss._security_mapping import PreparedSecurityMapping
OUT=Path(__file__).parent;ROOT=read.ROOT;checks=[]
def check(n,v):assert v,n;checks.append({'name':n,'passed':True})
mapping=PreparedSecurityMapping(b'{"original":"request"}',b'{}',accepted_catalog_assessment=b'{"original":"assessment"}')
c1=_FactColumnComparison('id',1,25,-1,True,0);c2=_FactColumnComparison('value',2,25,-1,False,0)
relations=(_FactRelationComparison('truss','object',10,12,'original guard',(c1,c2)),_FactRelationComparison('truss','catalog_subject_map',11,12,'original guard'))
barrier=_DDLBarrierComparison(12,13,'original DDL barrier',True);helper=b'original helper'
def derive(m=mapping,r=relations,b=barrier,h=helper):return read.derive_catalog_source_epoch_profile(m,r,b,subject_source=h)
base=derive();packet=json.loads(base)
check('exact canonical bounded bytes',type(base) is bytes and len(base)<=65536 and base==json.dumps(packet,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode())
check('source hashes are exact original bytes',packet['requestSha256']==hashlib.sha256(mapping.original_request).hexdigest() and packet['acceptedCatalogSha256']==hashlib.sha256(mapping.accepted_catalog_assessment).hexdigest() and packet['subjectHelperSha256']==hashlib.sha256(helper).hexdigest())
check('relation input order canonicalized',derive(r=relations[::-1])==base)
check('column order retained',derive(r=(replace(relations[0],columns=(c2,c1)),relations[1]))!=base)
check('column count retained',json.loads(derive(r=(replace(relations[0],columns=(c1,)),relations[1])))['factCuts'][0]['columnCount']==1)
for field,value in [('original_request',mapping.original_request+b' '),('accepted_catalog_assessment',mapping.accepted_catalog_assessment+b' ')]:check('exact '+field+' mutation changes packet',derive(m=replace(mapping,**{field:value}))!=base)
check('helper byte mutation changes packet',derive(h=helper+b' ')!=base)
for field,value in [('owner_oid',14),('function_oid',15),('source','changed'),('include_alter_routine',False)]:check('barrier '+field+' bound',derive(b=replace(barrier,**{field:value}))!=base)
for field,value in [('schema','elsewhere'),('name','other'),('oid',20),('owner_oid',19),('guard_source','changed')]:check('fact '+field+' bound',derive(r=(replace(relations[0],**{field:value}),relations[1]))!=base)
for field,value in [('name','newid'),('number',3),('type_oid',23),('type_modifier',4),('not_null',False),('collation_oid',100),('generated','s'),('identity','a')]:
 check('column '+field+' bound',derive(r=(replace(relations[0],columns=(replace(c1,**{field:value}),c2)),relations[1]))!=base)

def refuse(n,fn):
 try:fn()
 except (ValueError,UnicodeError):check(n,True)
 else:raise AssertionError(n)
for field,value in [('original_request',b''),('original_request',bytearray(b'a')),('original_request',b'a'*4000001),('accepted_catalog_assessment',b''),('accepted_catalog_assessment',memoryview(b'a')),('accepted_catalog_assessment',b'a'*1048577)]:refuse('mapping '+field+' '+type(value).__name__+' '+str(len(value))+' refuses',lambda field=field,value=value:derive(m=replace(mapping,**{field:value})))
for value in (b'',bytearray(b'a'),b'a'*65537):refuse('helper '+type(value).__name__+' '+str(len(value))+' refuses',lambda value=value:derive(h=value))
for field,value in [('owner_oid',True),('owner_oid',0),('function_oid',4294967296),('source',''),('source','a'*65537),('include_alter_routine',1)]:refuse('barrier '+field+' invalid refuses',lambda field=field,value=value:derive(b=replace(barrier,**{field:value})))
for label,r in [('list',list(relations)),('empty',()),('duplicate',(relations[0],relations[0])),('foreign',(object(),)),('column list',(replace(relations[0],columns=[c1]),)),('column duplicate',(replace(relations[0],columns=(c1,c1)),)),('column 1601',(replace(relations[0],columns=(c1,)*1601),))]:refuse('recipe '+label+' refuses',lambda r=r:derive(r=r))
check('request and assessment exact upper byte limits accepted',len(derive(m=replace(mapping,original_request=b'a'*4000000,accepted_catalog_assessment=b'b'*1048576)))<=65536)
check('helper and barrier source exact upper byte limits accepted',len(derive(h=b'a'*65536,b=replace(barrier,source='b'*65536)))<=65536)
columns=tuple(replace(c1,name='c'+str(i),number=i) for i in range(1,1601));check('1600 distinct ordered descriptors accepted',json.loads(derive(r=(replace(relations[0],columns=columns),)))['factCuts'][0]['columnCount']==1600)
r32=tuple(replace(relations[0],name='object'+str(i),oid=100+i) for i in range(32));check('32 selected recipes accepted within packet ceiling',len(json.loads(derive(r=r32))['factCuts'])==32)
refuse('33 selected recipes refuse',lambda:derive(r=r32+(replace(relations[0],name='last',oid=200),)))
from truss._security_source_epoch_installation import _MANIFEST_SHA256
check('profile 0.4 exact installed source manifest bound',packet['interfaceVersion']=='truss-owned-catalog-source-profile/0.4' and packet['sourceEpochManifestSha256']==_MANIFEST_SHA256)
for f in ('include_schema_ddl','include_database_ddl'):
 check('barrier '+f+' bound',derive(b=replace(barrier,**{f:True}))!=base)
 refuse('barrier '+f+' rejects integer',lambda f=f:derive(b=replace(barrier,**{f:1})))
record={'scope':'Actual deterministic profile producer and preflight structural validators, no native or authenticated source claim','count':len(checks),'controls':checks,'sourceSha256':hashlib.sha256((ROOT/'scripts/security_catalog_subject_read.py').read_bytes()).hexdigest()}
(OUT/'binding-results.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'count':len(checks),'passed':True}))
