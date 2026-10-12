"""Actual public graph ontology fixture; candidate lowering, not admitted security."""
import json,os,subprocess
from pathlib import Path
import psycopg
from truss import Ok
from truss.contracts import TextValue,BooleanValue
from truss.groups import CreateObject,CreateEdge,AuthoredValue,RootlessOwnership,AliasObjectReference,NullOrderKey,GroupSuccess,RequestNone
import test_group_create_native as groups
RECORDS={'Client':{'code':'string'},'Project':{'code':'string'},'Staff':{'code':'string','login':'string'},'Resource':{'code':'string'},'Assignment':{'code':'string','active':'boolean'}}
LINKS={'staff_assignment':('Staff','Assignment'),'assignment_project':('Assignment','Project'),'resource_project':('Resource','Project'),'project_client':('Project','Client')}
class PublicOntologySecurityTests(groups.PublicCreateGroupTests):
 for name in tuple(n for n in dir(groups.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
 def tearDown(self):
  self.admin.rollback();self.admin.execute('DROP SCHEMA IF EXISTS ontology_fixture CASCADE')
  super().tearDown()
 def model(self,document):
  m=document['modules'][0];m['elements']=[];m['relationships']=[]
  for name,fields in RECORDS.items():
   m['elements'].append({'id':name,'kind':'record','members':[{'module':'m','element':name+'-'+f} for f in fields],'keys':[{'id':'pk','primary':True,'fields':[{'module':'m','element':name+'-code'}]}],'extensions':{}})
   for field,scalar in fields.items():m['elements'].append({'id':name+'-'+field,'name':name+'-'+field,'kind':'field','scalarType':scalar,'nullability':'required','cardinality':'one','extensions':{}})
  for name,(source,target) in LINKS.items():m['relationships'].append({'id':name,'name':name,'source':[{'module':'m','element':source}],'target':[{'module':'m','element':target,'key':'pk'}],'sourceMultiplicity':{'min':0,'max':100},'targetMultiplicity':{'min':0,'max':100},'targetLifecycle':'independent','directed':True})
 def test_public_created_membership_graph(self):
  c,h,a,t=self.ready(self.model);ops=[]
  def node(record,code,**extras):
   values={'code':code,**extras};ops.append(CreateObject(type_definition_pin=self.types[('adoc',record)].definition_pin,values=tuple(AuthoredValue(name=record+'-'+f,value=BooleanValue(value=v) if isinstance(v,bool) else TextValue(kind='string',text=v)) for f,v in values.items()),ownership=RootlessOwnership(),alias=code))
  node('Client','C');node('Project','A');node('Project','B')
  for login in ['alice','bob','outsider']:node('Staff','staff-'+login,login=login)
  for code in ['RA','RB','RAB','RO']:node('Resource',code)
  for code,active in [('AA',True),('AB',False),('BB',True)]:node('Assignment',code,active=active)
  connections={'staff_assignment':[('staff-alice','AA'),('staff-alice','AB'),('staff-bob','BB')],'assignment_project':[('AA','A'),('AB','B'),('BB','B')],'resource_project':[('RA','A'),('RB','B'),('RAB','A'),('RAB','B')],'project_client':[('A','C'),('B','C')]}
  for link,pairs in connections.items():
   pin=a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id=link).value.definition_pin
   for i,(source,target) in enumerate(pairs):ops.append(CreateEdge(relationship_definition_pin=pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey(),alias=link+str(i)))
  inp,_=self.input(a,t,tuple(ops));result=a.apply_in_transaction(t,inp,RequestNone(),documents=self.documents,bun_executable='/opt/homebrew/bin/bun');self.assertIsInstance(result,Ok);self.assertIsInstance(result.value,GroupSuccess);h.detach();c.commit()
  packet={'records':{},'links':{}}
  for record,fields in RECORDS.items():
   type_id=self.types[('adoc',record)].type_id;props={name:str(pid) for name,pid in self.admin.execute('SELECT name,prop_id FROM truss.prop_def WHERE type_id=%s',(int(type_id),))}
   packet['records'][record]={'typeId':type_id,'fields':{f:{'id':props[record+'-'+f],'scalar':scalar} for f,scalar in fields.items()}}
  for link,(source,target) in LINKS.items():packet['links'][link]={'id':str(self.admin.execute("SELECT rel_type_id FROM truss.rel_def WHERE document_id='adoc' AND module='m' AND rel_id=%s",(link,)).fetchone()[0]),'source':source,'target':target}
  produced=subprocess.run(['/opt/homebrew/bin/bun',str(Path(__file__).resolve().parents[3]/'tests/fixtures/security-public-ontology.ts')],input=json.dumps(packet),text=True,capture_output=True,timeout=30);self.assertEqual(produced.returncode,0,produced.stderr);sql=json.loads(produced.stdout);observations=[]
  self.admin.execute('CREATE SCHEMA ontology_fixture')
  for name,source in sql['objects'].items():
   valid=self.admin.execute(source['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-object-source-'+name,'observed':valid});self.admin.execute('CREATE VIEW ontology_fixture.'+name.lower()+' AS '+source['sql'])
  for name,source in sql['edges'].items():
   valid=self.admin.execute(source['validitySql']).fetchone()[0];self.assertEqual(valid,'true');observations.append({'id':'complete-edge-endpoints-'+name,'observed':valid});self.admin.execute('CREATE VIEW ontology_fixture.'+name+' AS '+source['sql'])
  self.admin.execute('CREATE VIEW ontology_fixture.assignments AS SELECT a.code,a.active,s.source_code AS staff_code,p.target_code AS project_code FROM ontology_fixture.assignment a LEFT JOIN ontology_fixture.staff_assignment s ON s.target_code=a.code LEFT JOIN ontology_fixture.assignment_project p ON p.source_code=a.code')
  rows=self.admin.execute('SELECT code,active,staff_code,project_code FROM ontology_fixture.assignments ORDER BY code').fetchall();self.assertEqual(rows,[('AA',True,'staff-alice','A'),('AB',False,'staff-alice','B'),('BB',True,'staff-bob','B')]);observations.append({'id':'actual-assignment-business-key-facts','observed':[list(r) for r in rows]})
  self.admin.execute('CREATE ROLE ontology_facts NOLOGIN NOINHERIT NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss,ontology_fixture TO ontology_facts;GRANT SELECT(id,type_id,props) ON truss.object TO ontology_facts;GRANT SELECT(id,rel_type_id,source_id,source_type,target_id,target_type) ON truss.edge TO ontology_facts')
  self.addCleanup(self.admin.execute,'DROP OWNED BY ontology_facts;DROP ROLE ontology_facts')
  for name in [*RECORDS,*LINKS,'assignments']:self.admin.execute('ALTER VIEW ontology_fixture.'+name.lower()+' OWNER TO ontology_facts')
  self.admin.execute('CREATE FUNCTION ontology_fixture.eligible(text) RETURNS bool LANGUAGE SQL SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=on AS $$ SELECT '+sql['predicateSql']+' $$;REVOKE ALL ON FUNCTION ontology_fixture.eligible(text) FROM PUBLIC;GRANT CREATE ON SCHEMA ontology_fixture TO ontology_facts;ALTER FUNCTION ontology_fixture.eligible(text) OWNER TO ontology_facts;REVOKE CREATE ON SCHEMA ontology_fixture FROM ontology_facts')
  self.admin.execute('ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY;ALTER TABLE truss.object FORCE ROW LEVEL SECURITY;CREATE POLICY complete_private_facts ON truss.object FOR SELECT TO ontology_facts USING(true)')
  resource=packet['records']['Resource'];key=resource['fields']['code']['id']
  for login in ['alice','bob','outsider']:
   self.admin.execute('CREATE ROLE '+login+' LOGIN NOSUPERUSER NOBYPASSRLS;GRANT USAGE ON SCHEMA truss,ontology_fixture TO '+login+';GRANT SELECT(id,type_id,props) ON truss.object TO '+login+';GRANT EXECUTE ON FUNCTION ontology_fixture.eligible(text) TO '+login)
   self.addCleanup(self.admin.execute,'DROP OWNED BY '+login+';DROP ROLE '+login)
  self.admin.execute("CREATE POLICY resource_membership ON truss.object FOR SELECT TO alice,bob,outsider USING(type_id="+resource['typeId']+" AND ontology_fixture.eligible(props->'"+key+"'->>'text'))")
  expected={'alice':['RA','RAB'],'bob':['RAB','RB'],'outsider':[]}
  for login,wanted in expected.items():
   params=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);params['user']=login
   with psycopg.connect(**params,autocommit=True) as reader:
    identity=reader.execute('SELECT session_user,current_user').fetchone();self.assertEqual(identity,(login,login));observations.append({'id':'original-native-caller-'+login,'observed':list(identity)})
    actual=[r[0] for r in reader.execute("SELECT props->%s->>'text' FROM truss.object ORDER BY props->%s->>'text'",(key,key))];self.assertEqual(actual,wanted);observations.append({'id':'membership-resource-oracle-'+login,'expected':wanted,'observed':actual})
    count=reader.execute('SELECT count(*) FROM truss.object').fetchone()[0];self.assertEqual(count,len(wanted));observations.append({'id':'membership-count-'+login,'observed':count})
    with self.assertRaises(psycopg.errors.InsufficientPrivilege):reader.execute('SELECT * FROM ontology_fixture.assignments')
    observations.append({'id':'private-assignment-view-denied-'+login,'observed':'42501'})
  if os.environ.get('TRUSS_SECURITY_COMPONENT_EVIDENCE'):Path(os.environ['TRUSS_SECURITY_COMPONENT_EVIDENCE']).write_text(json.dumps({'packet':packet,'sql':sql,'observations':observations,'scope':'Actual public-created objects/edges, typed native joins to business keys and candidate normalized-IR membership lowering under ordinary native RLS. Private views are real graph projections, not seeded flat tables. Not complete source enrollment, held authority or released public API/security compiler admission.'},indent=2)+'\n')
if __name__=='__main__':
 import unittest;unittest.main()
