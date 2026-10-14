"""Original public catalog + mutation population for full ontology graph qualification.
Seed/endpoint prerequisite only: no protected read or backend admission claimed.
"""
import base64,json,os
from pathlib import Path
from truss.contracts import MapValue,TextValue,BooleanValue
from truss.groups import CreateObject,RootlessOwnership,AuthoredValue,CreateEdge,AliasObjectReference,NullOrderKey,GroupSuccess,GroupFailed
import test_group_create_native as base


def ontology_document(identity):
    specs={'Client':{'clientId':'string'},'Project':{'projectId':'string'},'Staff':{'staffId':'string'},'Resource':{'resourceId':'string','salary':'integer'},'Assignment':{'assignmentId':'string','active':'boolean'},'Ownership':{'ownershipId':'string'}}
    elements=[]
    for name,fields in specs.items():
        elements.append({'id':name,'name':name,'kind':'record','members':[{'module':'m','element':field} for field in fields],'keys':[{'id':'pk','name':'Key','primary':True,'fields':[{'module':'m','element':next(iter(fields))}]}],'extensions':{}})
        for field,family in fields.items():elements.append({'id':field,'name':field,'kind':'field','scalarType':family,'nullability':'required','cardinality':'one','extensions':{}})
    pairs=(('ProjectClient','Project','Client'),('StaffAssignment','Staff','Assignment'),('AssignmentProject','Assignment','Project'),('OwnershipResource','Ownership','Resource'),('OwnershipProject','Ownership','Project'))
    relationships=[{'id':name,'name':name,'source':[{'module':'m','element':source}],'target':[{'module':'m','element':target,'key':'pk'}],'sourceMultiplicity':{'min':0,'max':'*'},'targetMultiplicity':{'min':0,'max':'*'},'targetLifecycle':'independent','directed':True} for name,source,target in pairs]
    return {'umf':'0.8.0','id':identity,'vocabularies':{},'extensions':{},'modules':[{'id':'m','namespace':'m','extensions':{},'elements':elements,'relationships':relationships}]}


class SecurityOntologyEdgesNativeTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
    def test_original_public_ontology_population_and_endpoint_oracle(self):
        """@covers US-056-AC2; full ontology/typed-edge prerequisite, not B01/B02 admission."""
        def source(document):identity=document['id'];document.clear();document.update(ontology_document(identity))
        try:c,h,a,t=self.ready(source,document_ids=('adoc',))
        except Exception as error:
            for diagnostic in getattr(error,'diagnostics',()):print(diagnostic.decode() if isinstance(diagnostic,bytes) else diagnostic)
            raise
        rows=(('Client','c',{'clientId':'C'}),('Project','pa',{'projectId':'A'}),('Project','pb',{'projectId':'B'}),('Staff','alice',{'staffId':'Alice'}),('Staff','bob',{'staffId':'Bob'}),('Staff','outsider',{'staffId':'Outsider'}),('Resource','ra',{'resourceId':'RA','salary':100}),('Resource','rb',{'resourceId':'RB','salary':200}),('Resource','ro',{'resourceId':'RO','salary':300}),('Assignment','aa',{'assignmentId':'AA','active':True}),('Assignment','ai',{'assignmentId':'AI','active':False}),('Assignment','ba',{'assignmentId':'BA','active':True}),('Ownership','oa',{'ownershipId':'OA'}),('Ownership','ob',{'ownershipId':'OB'}))
        links=(('ProjectClient','pa','c'),('ProjectClient','pb','c'),('StaffAssignment','alice','aa'),('StaffAssignment','alice','ai'),('StaffAssignment','bob','ba'),('AssignmentProject','aa','pa'),('AssignmentProject','ai','pb'),('AssignmentProject','ba','pb'),('OwnershipResource','oa','ra'),('OwnershipResource','ob','rb'),('OwnershipProject','oa','pa'),('OwnershipProject','ob','pb'))
        refs={name:a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id=name).value for name in {r[0] for r in links}}
        operations=[]
        for record,alias,fields in rows:
            values=tuple(AuthoredValue(name=name,value=BooleanValue(value=value) if type(value) is bool else TextValue(kind='integer' if type(value) is int else 'string',text=str(value))) for name,value in fields.items())
            operations.append(CreateObject(type_definition_pin=self.types[('adoc',record)].definition_pin,values=values,ownership=RootlessOwnership(),alias=alias))
        operations.extend(CreateEdge(relationship_definition_pin=refs[name].definition_pin,source=AliasObjectReference(alias=source),target=AliasObjectReference(alias=target),values=(),order_key=NullOrderKey()) for name,source,target in links)
        context=a.group_context_in_transaction(t).value
        result=self.apply(a,t,context.input(tuple(operations),MapValue(entries=())),context.request('security-full-ontology-seed'))
        self.assertIsInstance(result,GroupSuccess)
        identities={item.alias:int(item.identity.id) for item in result.response.semantic.aliases}
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.object').fetchone(),(14,));self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(12,))
        actual=self.admin.execute('SELECT rel_type_id,source_id,target_id FROM truss.edge ORDER BY id').fetchall()
        full_edges=self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall()
        expected=[(int(refs[name].relationship_id),identities[source],identities[target]) for name,source,target in links]
        self.assertEqual(actual,expected)
        c,h,a,t=self.consumer();stored={}
        from truss import ObjectFound
        for record,alias,fields in rows:
            found=a.get_object_in_transaction(t,document_id='adoc',module_id='m',record_id=record,object_id=identities[alias])
            self.assertIsInstance(found.value,ObjectFound);stored[alias]=dict(found.value.object.values)
            self.assertEqual(stored[alias],{name:TextValue(kind='integer',text=str(value)) if type(value) is int else value for name,value in fields.items()})
        # Independent incidence oracle; no compiler predicate or security evaluator is used.
        endpoints={name:{(s,d) for r,s,d in actual if r==int(refs[name].relationship_id)} for name in refs}
        active={identities[alias] for record,alias,fields in rows if record=='Assignment' and stored[alias]['active']}
        owned={(resource,project) for owner,resource in endpoints['OwnershipResource'] for other,project in endpoints['OwnershipProject'] if owner==other}
        observed={}
        for staff in ('alice','bob','outsider'):
            projects={project for person,assignment in endpoints['StaffAssignment'] for other,project in endpoints['AssignmentProject'] if person==identities[staff] and assignment==other and assignment in active}
            observed[staff]=sorted(alias.upper() for alias in ('ra','rb','ro') if any(resource==identities[alias] and project in projects for resource,project in owned))
        self.assertEqual(observed,{'alice':['RA'],'bob':['RB'],'outsider':[]})
        self.assertEqual(endpoints['ProjectClient'],{(identities['pa'],identities['c']),(identities['pb'],identities['c'])})
        # Actual native endpoint validation through the public mutation boundary.
        context=a.group_context_in_transaction(t).value
        from truss.groups import StoredObjectReference
        native_identities={item.alias:item.identity for item in result.response.semantic.aliases}
        from truss.groups import InvalidGroupInput
        refusals={}
        for label,source_alias,target_alias in (('wrong-type','pa','aa'),('reversed','aa','alice')):
            invalid=CreateEdge(relationship_definition_pin=refs['StaffAssignment'].definition_pin,source=StoredObjectReference(identity=native_identities[source_alias]),target=StoredObjectReference(identity=native_identities[target_alias]),values=(),order_key=NullOrderKey())
            refused=self.apply(a,t,context.input((invalid,),MapValue(entries=())),context.request('security-wrong-edge-'+label))
            self.assertIsInstance(refused,GroupFailed);self.assertIsInstance(refused.failure,InvalidGroupInput)
            native_diagnostic=json.loads(base64.b64decode(refused.failure.diagnostic.bytes_base64))
            self.assertEqual(native_diagnostic,{'code':'invalid_input','nativeState':'22023','operationIndex':'0','outcome':'failed'})
            refusals[label]=native_diagnostic
        h.detach();c.commit()
        self.assertEqual(self.admin.execute('SELECT to_jsonb(e) FROM truss.edge e ORDER BY id').fetchall(),full_edges)
        directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_EDGE_EVIDENCE')
        if directory:
            folder=Path(directory)
            for document in self.documents:(folder/(document.document_id+'.json')).write_bytes(document.content)
            (folder/'population.json').write_text(json.dumps({'aliases':identities,'storedValues':stored,'edges':actual,'oracle':observed,'expectedOracle':{'alice':['RA'],'bob':['RB'],'outsider':[]},'nativeEndpointRefusals':refusals,'scope':'Original public seed and independent graph incidence oracle; not protected visibility admission.'},indent=2,default=lambda value:{'kind':value.kind,'text':value.text})+'\n')
