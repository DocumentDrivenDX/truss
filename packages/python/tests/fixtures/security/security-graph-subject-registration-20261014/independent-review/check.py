"""Bounded original graph Subject recipe/issuer comparison controls; no SQL."""
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
from unittest.mock import patch
from types import SimpleNamespace
import ast,json,re
from truss._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source
import truss._security_graph_subject_installation as m
root=Path(__file__).resolve().parents[6];e=root/'docs/helix/04-build/evidence/security-ontology-epoch-read-20261014/merged-runtime061'
source=PreparedGraphSecuritySource(*((e/f).read_bytes() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')))
source=snapshot_graph_security_source(source);native=json.loads(source.accepted_catalog_assessment)['inventory'];record=next(r for r in native['types'] if r['element']=='Staff');prop=next(p for p in native['properties'] if p['type_id']==record['type_id'] and p['element']=='staffId')
results=[]
def check(name,fn):fn();results.append({'name':name,'passed':True})
def require(v):assert v
def refuse(fn,msg=None):
 try:fn()
 except ValueError as ex:
  if msg is not None:assert str(ex)==msg
  return
 raise AssertionError('Required refusal missing')
check('original packaged helper digest',lambda:require(sha256(m._source()).hexdigest()==m._DIGEST))
check('genuine original Staff string-key recipe',lambda:require(m._recipe(source)[1:4]==(record['type_id'],prop['prop_id'],int(json.loads(source.accepted_catalog_assessment)['revision']))))
def request_change(fn):
 request=json.loads(source.native_dependencies);binding=json.loads(request['bindingJson']);corr=json.loads(binding['correspondenceJson']);ontology=json.loads(request['ontologyJson']);fn(corr,ontology)
 binding['correspondenceJson']=json.dumps(corr);request['bindingJson']=json.dumps(binding);request['ontologyJson']=json.dumps(ontology)
 return replace(source,native_dependencies=json.dumps(request).encode())
def entity(c):return next(e for e in c['entities'] if e['logicalType']['elementId']=='Staff')
for name,fn in [('different ontology Subject',lambda c,o:o['subject'].update(elementId='Resource')),('duplicate Staff binding',lambda c,o:c['entities'].append(dict(entity(c)))),('wrong native type',lambda c,o:entity(c)['nativeType'].update(typeId='999')),('wrong native property',lambda c,o:entity(c).update(nativePropertyId='999')),('wrong logical key',lambda c,o:entity(c).update(logicalKeyId='other')),('wrong native key',lambda c,o:entity(c).update(nativeKeyId='other')),('wrong logical key field',lambda c,o:entity(c).update(logicalKeyField='other')),('wrong native key field',lambda c,o:entity(c).update(nativeKeyField='other'))]:
 bad=request_change(fn);check(name,lambda bad=bad:refuse(lambda:m._recipe(bad)))
def census_change(fn):
 data=json.loads(source.accepted_catalog_assessment);r=next(r for r in data['inventory']['types'] if r['element']=='Staff');p=next(p for p in data['inventory']['properties'] if p['type_id']==r['type_id'] and p['element']=='staffId');k=next(k for k in data['inventory']['keys'] if k['type_id']==r['type_id'] and k['key_id']=='pk');fn(r,p,k)
 return replace(source,accepted_catalog_assessment=json.dumps(data).encode())
for name,fn in [('nullable key',lambda r,p,k:p.update(nullability='nullable')),('many-valued key',lambda r,p,k:p.update(cardinality='many')),('nonstring key',lambda r,p,k:p.update(scalar_type='integer')),('wrong key property order/arity',lambda r,p,k:k.update(prop_ids=[p['prop_id'],999])),('provisional Staff',lambda r,p,k:r.update(provisional=True)),('Boolean type ID',lambda r,p,k:r.update(type_id=True))]:
 bad=census_change(fn);check(name,lambda bad=bad:refuse(lambda:m._recipe(bad)))
subjects=m.PendingGraphSubjects('installation',100,b'profile',((200,'Alice'),(201,'Bob')))
body=m._source().decode().split('AS $$',1)[1].split('$$;',1)[0]
row=('321','100','plpgsql','f','0','','2249','true','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,'true','["t", "t", "t", "t", "t"]','["25", "25", "25", "25", "25"]','["staff_key", "installation_id", "database_oid", "role_oid", "profile_sha256"]')
acl=[('100','100','EXECUTE','false'),('200','100','EXECUTE','false'),('201','100','EXECUTE','false')]
with patch.object(m,'_text_rows',side_effect=[[row],acl]):check('exact own-session helper metadata and registered ACL',lambda:require(m.verify_graph_subject_issuer_with_cursor(None,subjects)==321))
for name,index,value in [('wrong definer owner',1,'999'),('security invoker substitution',9,'false'),('foreign return descriptor meaning',18,'["19", "25", "25", "25", "25"]'),('different argument names',19,'[]')]:
 bad=list(row);bad[index]=value
 with patch.object(m,'_text_rows',return_value=[tuple(bad)]):check(name,lambda:refuse(lambda:m.verify_graph_subject_issuer_with_cursor(None,subjects),'Exact original graph Subject issuer definition required'))
with patch.object(m,'_text_rows',side_effect=[[row],[('0','100','EXECUTE','false')]+acl]):check('PUBLIC execute addition refuses',lambda:refuse(lambda:m.verify_graph_subject_issuer_with_cursor(None,subjects),'Exact registered graph Subject issuer ACL required'))
class Cursor:
 description=[SimpleNamespace(type_code=19)]
 fetched=0
 def execute(self,*a,**kw):pass
 def fetchmany(self,n):self.fetched+=1;raise AssertionError('Unexpected decode')
c=Cursor();check('foreign native descriptor refuses before fetch',lambda:refuse(lambda:m.verify_graph_subject_issuer_with_cursor(c,subjects)));require(c.fetched==0)
tree=ast.parse((root/'packages/python/src/truss/_security_graph_subject_installation.py').read_bytes())
assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='dependencies' for t in n.targets))
names=tuple('truss.'+n.value for n in assignment.value.generators[0].iter.elts)
locked=tuple(re.findall(r'LOCK TABLE ONLY (truss\.[a-z_]+) IN SHARE MODE NOWAIT;',m._source().decode()))
check('all nine fixed helper locks covered by owner privilege recipe',lambda:require(len(names)==len(set(names))==9 and names==locked))

result={'scope':'Recipe and exact issuer comparisons on retained original inputs and deliberate local substitutions; not compiler authentication, SQL semantics, native execution or protected query composition','passed':len(results),'failed':0,'controls':results,'sourceSha256':{p:sha256((root/p).read_bytes()).hexdigest() for p in ('packages/python/src/truss/_security_graph_subject_installation.py','packages/python/src/truss/_security_bootstrap/graph-subject.sql')},'inputs':str(e),'inputSha256':{f:sha256((e/f).read_bytes()).hexdigest() for f in ('physical-request.json','compiler-output.json','accepted-catalog.json','compiler-request.json')}}
Path(__file__).with_name('results.json').write_text(json.dumps(result,indent=2)+'\n');print(str(len(results))+' bounded controls passed')
