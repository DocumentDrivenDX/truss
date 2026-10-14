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
        from security_ontology_edge_projection import project_full_ontology_edge_cells
        from security_owned_read import _pin_owned_evaluator_sources,_read_owned_resource_receipt
        import subprocess
        types={name:self.types[('adoc',name)].type_id for name in {row[0] for row in rows}}
        relations={name:reference.relationship_id for name,reference in refs.items()}
        objects=tuple((str(identities[alias]),types[record],stored[alias]) for record,alias,_ in rows)
        edge_rows=tuple(tuple(str(value) for value in row) for row in self.admin.execute('SELECT id,rel_type_id,source_id,source_type,target_id,target_type FROM truss.edge ORDER BY id').fetchall())
        cells=project_full_ontology_edge_cells(objects,edge_rows,types,relations)
        prepared=_pin_owned_evaluator_sources();evaluated={}
        for subject,expected_keys in (('Alice',['RA']),('Bob',['RB']),('Outsider',[])):
            payload=json.dumps({'cells':cells,'subjectKey':[{'string':subject}],'resultMode':'resources'})
            evaluated_run=subprocess.run([os.environ.get('TRUSS_BUN_EXECUTABLE','bun'),str(prepared.tool),'--named-source'],cwd=Path(__file__).resolve().parents[3],input=payload,capture_output=True,text=True,timeout=10)
            self.assertEqual(evaluated_run.returncode,0,evaluated_run.stderr)
            decision=_read_owned_resource_receipt(evaluated_run.stdout)
            self.assertEqual([r['key'][0]['string'] for r in decision['rows']],expected_keys)
            for resource in decision['rows']:self.assertEqual(resource['output'][0]['disposition'],'withheld')
            evaluated[subject]=decision
        for damaged in (edge_rows[:-1],edge_rows+(edge_rows[0],)):
            with self.assertRaises(ValueError):project_full_ontology_edge_cells(objects,damaged,types,relations)
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
            inventory={}
            for name,table,order in (('types','type_def','type_id'),('properties','prop_def','prop_id'),('keys','key_def','type_id,key_num'),('relationships','rel_def','rel_type_id'),('endpoints','rel_endpoint','rel_type_id,source_type,target_type')):
                inventory[name]=[row[0] for row in self.admin.execute('SELECT to_jsonb(t) FROM truss.'+table+' t ORDER BY '+order).fetchall()]
            (folder/'native-inventory.json').write_text(json.dumps({'scope':'Excluded native assessor capture, not authenticated compiler/host admission.','inventory':inventory,'typeSelection':types,'relationshipSelection':relations},indent=2)+'\n')
            (folder/'population.json').write_text(json.dumps({'aliases':identities,'storedValues':stored,'edges':actual,'oracle':observed,'sharedPolicyDecisions':evaluated,'expectedOracle':{'alice':['RA'],'bob':['RB'],'outsider':[]},'nativeEndpointRefusals':refusals,'scope':'Original public seed, explicit graph endpoint binding, shared semantic policy and independent incidence oracle; no authenticated protected visibility admission.'},indent=2,default=lambda value:{'kind':value.kind,'text':value.text})+'\n')
        # Continuous complete source/fact cut through the buffered release.
        # Administrative actor/subject and routine closure remain premises.
        from hashlib import sha256
        from unittest.mock import patch
        from truss import adopt_psycopg_host,Ok,Error
        import psycopg
        import security_ontology_guarded_read as guarded
        request=json.dumps({'modules':[{'pin':{'documentId':d.document_id,'revision':d.document_revision,'umfVersion':'0.8.0','sha256':sha256(d.content).hexdigest()},'documentJson':d.content.decode()} for d in self.documents]}).encode()
        self.admin.execute('BEGIN')
        host=adopt_psycopg_host(self.admin);transaction=host.adopt_transaction().value
        self.admin.execute("CREATE TEMP TABLE graph_guard_prior(value text);INSERT INTO graph_guard_prior VALUES('kept')")
        observations=[];released=[];original_run=guarded.subprocess.run
        def verify_exclusion(stage):
            with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
                for table in guarded.TABLES:
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        with writer.transaction():
                            writer.execute('LOCK TABLE ONLY truss.'+table+' IN ROW EXCLUSIVE MODE NOWAIT')
            observations.append(stage)
        def evaluating(*args,**kwargs):verify_exclusion('evaluation');return original_run(*args,**kwargs)
        def publish(raw):verify_exclusion('publication');released.append(json.loads(raw))
        with patch.object(guarded.subprocess,'run',evaluating):
            protected=guarded.publish_owned_ontology_resource_read(host,transaction,request,'Alice',publish)
        self.assertIsInstance(protected,Ok,str(host._custody.last_attempt.error))
        self.assertEqual(observations,['evaluation','publication'])
        self.assertEqual([r['key'] for r in released[0]['rows']],[[{'string':'RA'}]])
        self.assertEqual(released[0]['rows'][0]['output'][0]['disposition'],'withheld')
        # Same-transaction fact substitution by trusted callback is caught by
        # late recapture; rollback contains it and no bytes reach the receiver.
        changed_counts=[]
        def changed(*args,**kwargs):
            answer=original_run(*args,**kwargs)
            self.admin.execute('DELETE FROM truss.edge WHERE id=(SELECT max(id) FROM truss.edge)')
            changed_counts.append(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone()[0])
            return answer
        with patch.object(guarded.subprocess,'run',changed):
            refused=guarded.publish_owned_ontology_resource_read(host,transaction,request,'Alice',publish)
        self.assertIsInstance(refused,Error);self.assertEqual(len(released),1);self.assertEqual(changed_counts,[11])
        self.assertEqual(str(host._custody.last_attempt.error),'Original complete typed ontology edge projection required')
        self.assertEqual(host._custody.last_attempt.phase,'contained');self.assertIsNone(host._custody.last_attempt.cleanup_error)
        self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.edge').fetchone(),(12,))
        self.assertEqual(self.admin.execute('TABLE graph_guard_prior').fetchall(),[('kept',)])
        host.detach();self.admin.rollback()
        with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
            with writer.transaction():
                for table in guarded.TABLES:writer.execute('LOCK TABLE ONLY truss.'+table+' IN ROW EXCLUSIVE MODE NOWAIT')
        active_property=str(self.admin.execute("SELECT prop_id FROM truss.prop_def WHERE element='active'").fetchone()[0])
        for isolation in ('REPEATABLE READ','SERIALIZABLE'):
            self.admin.execute('BEGIN ISOLATION LEVEL '+isolation)
            # Materialize a native snapshot before the revocation commits.
            self.assertEqual(self.admin.execute('SELECT props->%s->>\'value\' FROM truss.object WHERE id=%s',(active_property,identities['aa'])).fetchone(),('true',))
            host=adopt_psycopg_host(self.admin);adopted=host.adopt_transaction(isolation=isolation.lower().replace(' ','_'))
            self.assertIsInstance(adopted,Ok,str(host._custody.last_attempt.error));transaction=adopted.value
            with psycopg.connect(self.info.connection_uri,autocommit=True) as writer:
                writer.execute("UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s,'value'],'false'::pg_catalog.jsonb) WHERE id=%s",(active_property,identities['aa']))
                self.assertEqual(writer.execute('SELECT props->%s->>\'value\' FROM truss.object WHERE id=%s',(active_property,identities['aa'])).fetchone(),('false',))
            self.assertEqual(self.admin.execute('SELECT props->%s->>\'value\' FROM truss.object WHERE id=%s',(active_property,identities['aa'])).fetchone(),('true',))
            with patch.object(guarded.subprocess,'run') as evaluator:
                refused=guarded.publish_owned_ontology_resource_read(host,transaction,request,'Alice',publish)
                evaluator.assert_not_called()
            self.assertIsInstance(refused,Error);self.assertEqual(len(released),1)
            self.assertIn('fresh READ COMMITTED',str(host._custody.last_attempt.error))
            host.detach();self.admin.rollback()
            with psycopg.connect(self.info.connection_uri,autocommit=True) as writer:
                writer.execute("UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s,'value'],'true'::pg_catalog.jsonb) WHERE id=%s",(active_property,identities['aa']))
