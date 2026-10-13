"""Bounded source/readback checks; synthetic rows do not establish native refinement."""
import ast, copy, hashlib, json, pathlib, sys, types, zipfile
from unittest.mock import patch
ROOT=pathlib.Path('/private/tmp/truss-security-main-integration')
sys.path.insert(0,str(ROOT/'packages/python/src'))
from truss import _security_source_epoch_installation as m
OUT=pathlib.Path(__file__).parent
results=[]
def check(name,fn):
 fn();results.append({'name':name,'passed':True})
def eq(a,b):
 assert a==b,(a,b)
def refuses(fn,message):
 try:fn()
 except ValueError as e:assert message in str(e),str(e)
 else:raise AssertionError('Expected refusal')
sources=m._sources(); source_map=dict(sources)
check('exact eleven captured original sources',lambda:eq(len(sources),11))
for name,source in sources:
 check('original native bytes '+name,lambda n=name,s=source:eq(s.encode(),(ROOT/'packages/postgresql/native'/('source-epoch-'+n)).read_bytes()))
package=ROOT/'packages/python/src/truss/_security_source_epoch'
class Resource:
 def __init__(self,parts=(),fault=None):self.parts,self.fault=parts,fault
 def joinpath(self,name):return Resource(self.parts+(name,),self.fault)
 def read_bytes(self):
  data=(ROOT/'packages/python/src/truss'/pathlib.Path(*self.parts)).read_bytes()
  return data+b'\n' if self.parts[-1]==self.fault else data
for fault in ['manifest.json']+[n for n,s in sources]:
 def probe(f=fault):
  with patch.object(m,'files',return_value=Resource(fault=f)):
   refuses(m._sources,'Original source epoch')
 check('package substitution refuses '+fault,probe)
class Cursor:
 def __init__(self,codes,rows):self.description=[types.SimpleNamespace(type_code=c) for c in codes] if codes is not None else None;self.rows=rows;self.fetched=0
 def execute(self,*a,**kw):pass
 def fetchmany(self,n):self.fetched+=1;return self.rows
for codes in (None,[19],[25,19]):
 def probe(c=codes):
  cursor=Cursor(c,[('a',)])
  refuses(lambda:m._text_rows(cursor,'q'),'TEXT descriptors');eq(cursor.fetched,0)
 check('foreign descriptors before fetch '+str(codes),probe)
check('exact text/null rows',lambda:eq(m._text_rows(Cursor([25,25],[('a',None)]),'q'),[('a',None)]))
for value in [b'a',1,True,bytearray(b'a')]:
 check('foreign carrier refuses '+type(value).__name__,lambda v=value:refuses(lambda:m._text_rows(Cursor([25],[(v,)]),'q'),'Bounded exact'))
check('row excess refuses',lambda:refuses(lambda:m._text_rows(Cursor([25],[('a',),('b',)]),'q',limit=1),'Bounded exact'))
actor=42
bodies={file:source_map[file].split('AS $$',1)[1].split('$$;',1)[0] for file,*rest in m._FUNCTIONS}
oids={name:str(700+i) for i,(file,name,*rest) in enumerate(m._FUNCTIONS)}
base={}
for file,name,args,return_oid,returns_set in m._FUNCTIONS:
 base['routine:'+name]=[(oids[name],str(actor),'plpgsql','f',args,return_oid,returns_set,'false','v','u','false','false','0','["search_path=pg_catalog, pg_temp"]',bodies[file])]
 base['acl:'+oids[name]]=[(str(actor),str(actor),'EXECUTE','false')]
base['events']=sorted([(name,'ddl_command_start','A',str(actor),oids['runtime_fence_routine_ddl_writer'],None if tags is None else json.dumps(tags)) for name,tags in m._EVENTS])
def hook(table,name,routine,event):return(table,name,oids[routine],'A',event,'0','','true','false','0','false','false')
base['triggers']=sorted([hook('source_epoch_current','runtime_selected_epoch_write_fence','runtime_fence_selected_epoch_writes','62'),hook('source_epoch_registry','runtime_selected_epoch_write_fence','runtime_fence_selected_epoch_writes','62'),hook('source_epoch_registry','runtime_source_epoch_immutable','runtime_immutable_source_epoch','27'),hook('source_epoch_registry','runtime_source_epoch_no_truncate','runtime_immutable_source_epoch','34')])
def verify(rows):
 def read(cursor,query,params=(),limit=16):
  if 'pg_catalog.pg_event_trigger' in query:key='events'
  elif 'pg_catalog.pg_trigger t' in query:key='triggers'
  elif 'aclexplode' in query:key='acl:'+params[0]
  elif 'p.proargtypes' in query:key='routine:'+params[0]
  else:raise AssertionError(query)
  return rows[key]
 with patch.object(m,'_text_rows',side_effect=read):return m._verify(None,sources,actor)
def good():
 barrier=verify(base)
 eq((barrier.owner_oid,barrier.function_oid,barrier.source,barrier.include_alter_routine,barrier.include_schema_ddl,barrier.include_database_ddl),(42,int(oids['runtime_fence_routine_ddl_writer']),bodies['routine-ddl-barrier.sql'],True,True,True))
check('exact selected inventory returns all-three-options barrier',good)
def cell_change(key,row,col,value):
 rows=copy.deepcopy(base);old=list(rows[key][row]);old[col]=value;rows[key][row]=tuple(old);refuses(lambda:verify(rows),'Exact ')
for file,name,*rest in m._FUNCTIONS:
 for col,value,label in [(1,'43','owner'),(7,'true','definer'),(13,'[]','path'),(14,bodies[file]+'\n','body')]:
  check(name+' changed '+label,lambda k='routine:'+name,c=col,v=value:cell_change(k,0,c,v))
 for col,value,label in [(0,'0','public'),(1,'43','grantor'),(3,'true','grantable')]:
  check(name+' ACL '+label,lambda k='acl:'+oids[name],c=col,v=value:cell_change(k,0,c,v))
for row,item in enumerate(base['events']):
 for col,value,label in [(2,'O','not ALWAYS'),(3,'43','owner'),(4,'999','function'),(5,'[]','wrong tags')]:
  check(item[0]+' '+label,lambda r=row,c=col,v=value:cell_change('events',r,c,v))
for row,item in enumerate(base['triggers']):
 for col,value,label in [(3,'D','disabled'),(4,'0','wrong mask'),(6,'00','arguments'),(7,'false','condition')]:
  check(item[1]+' '+item[0]+' '+label,lambda r=row,c=col,v=value:cell_change('triggers',r,c,v))
for key in ('events','triggers','routine:runtime_issue_source_epoch','acl:'+oids['runtime_issue_source_epoch']):
 for mode in ('missing','extra'):
  def probe(k=key,mode=mode):
   rows=copy.deepcopy(base)
   if mode=='missing':rows[k].pop()
   else:rows[k].append(rows[k][0])
   refuses(lambda:verify(rows),'Exact ')
  check(key+' '+mode,probe)
module=ROOT/'packages/python/src/truss/_security_source_epoch_installation.py'
tree=ast.parse(module.read_text())
prepin=[n.args[1].value for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='_text_rows' and len(n.args)>1 and isinstance(n.args[1],ast.Constant) and "current_setting('search_path')" in str(n.args[1].value)]
check('pre-pin path cast exact pg_catalog.text',lambda:eq(prepin,["SELECT pg_catalog.current_setting('search_path')::pg_catalog.text"]))
wheel_report=ROOT/'docs/helix/04-build/evidence/source-epoch-installation-20261013/wheel-final-source-correspondence.json'
report=json.loads(wheel_report.read_text());wheel=pathlib.Path('/private/tmp/truss-source-epoch-wheel-final-20261013')/report['wheel']
with zipfile.ZipFile(wheel) as archive:
 for rel in ['truss/_security_source_epoch_installation.py','truss/_security_source_epoch/manifest.json']+['truss/_security_source_epoch/'+n for n,s in sources]:
  check('wheel exact '+rel,lambda r=rel:eq(archive.read(r),(ROOT/'packages/python/src'/r).read_bytes()))
output={'scope':'Actual Python source/readback helpers with synthetic native-row observations; original source and wheel byte comparisons only. No native lifecycle replay or complete catalog inventory/refinement claim.','count':len(results),'passed':all(x['passed'] for x in results),'sourceSha256':hashlib.sha256(module.read_bytes()).hexdigest(),'wheelSha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),'controls':results}
(OUT/'results.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({k:v for k,v in output.items() if k!='controls'}))
