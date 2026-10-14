"""@covers US-056-AC2
Actual authored relationship installation/population prerequisite, not protected traversal.
"""
import json,os
from pathlib import Path
import test_group_create_native as base
from test_security_ontology_edges_native import ontology_document
from truss.contracts import MapValue,TextValue,BooleanValue
from truss.groups import CreateObject,CreateEdge,RootlessOwnership,AuthoredValue,AliasObjectReference,NullOrderKey,GroupSuccess

class PublicRelationshipNativeTests(base.PublicCreateGroupTests):
 for _name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):
  locals()[_name]=None
 def test_actual_authored_resource_relationship_and_population(self):
  root=Path(__file__).resolve().parents[3]
  logical=json.loads((root/'docs/helix/03-test/fixtures/security-public-relationship/document.json').read_bytes())
  relationship=logical['modules'][0]['relationships'][0]
  physical=ontology_document('adoc');physical['modules'][0]['relationships'].append(relationship)
  def source(document):document.clear();document.update(physical)
  connection,host,assembly,tx=self.ready(source,document_ids=('adoc',))
  rows=(('Client','c',{'clientId':'C'}),('Project','pa',{'projectId':'A'}),('Project','pb',{'projectId':'B'}),('Staff','alice',{'staffId':'Alice'}),('Staff','bob',{'staffId':'Bob'}),('Staff','outsider',{'staffId':'Outsider'}),('Resource','ra',{'resourceId':'RA','salary':100}),('Resource','rb',{'resourceId':'RB','salary':200}),('Resource','ro',{'resourceId':'RO','salary':300}),('Assignment','aa',{'assignmentId':'AA','active':True}),('Assignment','ai',{'assignmentId':'AI','active':False}),('Assignment','ba',{'assignmentId':'BA','active':True}),('Ownership','oa',{'ownershipId':'OA'}),('Ownership','ob',{'ownershipId':'OB'}))
  policy_links=(('ProjectClient','pa','c'),('ProjectClient','pb','c'),('StaffAssignment','alice','aa'),('StaffAssignment','alice','ai'),('StaffAssignment','bob','ba'),('AssignmentProject','aa','pa'),('AssignmentProject','ai','pb'),('AssignmentProject','ba','pb'),('OwnershipResource','oa','ra'),('OwnershipResource','ob','rb'),('OwnershipProject','oa','pa'),('OwnershipProject','ob','pb'))
  query_links=tuple(('ResourceRelatedResource',s,t) for s,t in (('rb','rb'),('rb','ra'),('ra','rb'),('ro','rb')))
  links=policy_links+query_links
  refs={name:assembly.get_relationship_reference_in_transaction(tx,document_id='adoc',module_id='m',relationship_id=name).value for name in {r[0] for r in links}}
  operations=[]
  for record,alias,fields in rows:
   values=tuple(AuthoredValue(name=name,value=BooleanValue(value=value) if type(value) is bool else TextValue(kind='integer' if type(value) is int else 'string',text=str(value))) for name,value in fields.items())
   operations.append(CreateObject(type_definition_pin=self.types[('adoc',record)].definition_pin,values=values,ownership=RootlessOwnership(),alias=alias))
  operations.extend(CreateEdge(relationship_definition_pin=refs[name].definition_pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey()) for name,source,target in links)
  context=assembly.group_context_in_transaction(tx).value
  result=self.apply(assembly,tx,context.input(tuple(operations),MapValue(entries=())),context.request('public-relationship-source-seed'))
  self.assertIsInstance(result,GroupSuccess)
  ids={item.alias:int(item.identity.id) for item in result.response.semantic.aliases}
  host.detach();connection.commit()
  expected=[(int(refs[name].relationship_id),ids[s],ids[t]) for name,s,t in links]
  observed=self.admin.execute('SELECT rel_type_id,source_id,target_id FROM truss.edge ORDER BY id').fetchall()
  self.assertEqual(observed,expected)
  self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(14,))
  self.assertEqual(len(observed),16)
  # Native catalog identity is observed, never copied from the old fixture IDs.
  directory=os.environ.get('TRUSS_SECURITY_PUBLIC_RELATIONSHIP_EVIDENCE')
  if directory:
   out=Path(directory);out.mkdir(parents=True,exist_ok=True)
   for document in self.documents:(out/(document.document_id+'-accepted-source.json')).write_bytes(document.content)
   from hashlib import sha256
   from truss._security_catalog_assessment import capture_accepted_catalog,SOURCE_TABLES
   from psycopg import sql
   physical_request=json.dumps({'modules':[{'pin':{'documentId':d.document_id,'revision':d.document_revision,'umfVersion':'0.8.0','sha256':sha256(d.content).hexdigest()},'documentJson':d.content.decode()} for d in self.documents]}).encode()
   with self.admin.transaction():
    self.admin.execute(sql.SQL('LOCK TABLE {} IN SHARE MODE').format(sql.SQL(',').join(sql.Identifier('truss',name) for name in SOURCE_TABLES)))
    with self.admin.cursor() as cursor:assessment=capture_accepted_catalog(cursor,physical_request)
    (out/'accepted-assessment.json').write_bytes(assessment)
    import runpy
    derive=runpy.run_path(str(root/'scripts/prepare-security-relationship-correspondence.py'))['derive_relationship_correspondence']
    fixture=root/'docs/helix/03-test/fixtures/security-public-relationship'
    selected={name:(fixture/(name+'.json')).read_bytes() for name in ('document','resolution','policy','transport')}
    duplicate=b'{"inventory":{},"inventory":{}}'
    with self.assertRaisesRegex(ValueError,'Duplicate correspondence source member'):derive(duplicate,physical_request,selected)
    for suffix,policy_file in [('', 'policy'),('-observation-denied','policy-observation-denied')]:
     sources={**selected,'policy':(fixture/(policy_file+'.json')).read_bytes()}
     correspondence=derive(assessment,physical_request,sources)
     mapped=json.loads(correspondence)
     self.assertEqual(mapped['inventorySha256'],sha256(assessment).hexdigest())
     self.assertEqual(mapped['logicalSourceDigests']['policy'],sha256(sources['policy']).hexdigest())
     self.assertEqual(mapped['queryRelationships'][0]['nativeRelationshipId'],str(refs['ResourceRelatedResource'].relationship_id))
     (out/('live-correspondence'+suffix+'.json')).write_bytes(correspondence)
     from security_relationship_request import prepare_relationship_request
     request=prepare_relationship_request(physical_request,assessment,observation_denied=bool(suffix))
     selected_request=json.loads(request)
     self.assertEqual(json.loads(selected_request['bindingJson'])['inventoryJson'].encode(),assessment)
     self.assertEqual(selected_request['policyJson'].encode(),sources['policy'])
     self.assertEqual(json.loads(selected_request['queryProfileJson'])['binding']['sha256'],sha256(selected_request['bindingJson'].encode()).hexdigest())
     (out/('compiler-request'+suffix+'.json')).write_bytes(request)
   (out/'physical-request.json').write_bytes(physical_request)
   catalog={}
   for name,table,order in (('types','type_def','type_id'),('properties','prop_def','prop_id'),('keys','key_def','type_id,key_num'),('relationships','rel_def','rel_type_id'),('endpoints','rel_endpoint','rel_type_id,source_type,target_type')):
    catalog[name]=[row[0] for row in self.admin.execute('SELECT pg_catalog.to_jsonb(t)::pg_catalog.text FROM truss.'+table+' t ORDER BY '+order).fetchall()]
   (out/'catalog-inventory.json').write_text(json.dumps({'scope':'Excluded assessor raw native TEXT JSONB capture; no protected source admission','revision':str(self.admin.execute('SELECT rev FROM truss.schema_head WHERE id=1').fetchone()[0]),'inventoryTextRows':catalog},indent=2)+'\n')
   (out/'physical-document.json').write_text(json.dumps(physical,separators=(',',':'))+'\n')
   capture={'status':'native-installation-population-prerequisite-passed','securityReady':False,'serverVersion':self.admin.execute('SHOW server_version').fetchone()[0],'relationId':str(refs['ResourceRelatedResource'].relationship_id),'expectedEdges':expected,'observedEdges':observed,'objectIds':ids,'catalogRelations':[r[0] for r in self.admin.execute('SELECT pg_catalog.to_jsonb(r)::pg_catalog.text FROM truss.rel_def r ORDER BY rel_type_id').fetchall()],'nativeEdges':[r[0] for r in self.admin.execute('SELECT pg_catalog.to_jsonb(e)::pg_catalog.text FROM truss.edge e ORDER BY id').fetchall()]}
   (out/'native-capture.json').write_text(json.dumps(capture,indent=2)+'\n')
