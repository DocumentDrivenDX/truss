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
        # Full graph decisions now derive from native SESSION_USER/OID on an
        # independent ordinary connection; caller has no fact or map access.
        import uuid
        from psycopg import sql
        import security_ontology_native_subject_read as native_read
        roles={name:'ontology_'+name.lower()+'_'+uuid.uuid4().hex[:10] for name in ('Alice','Bob','Outsider','Unregistered')}
        for role in roles.values():
            self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN').format(sql.Identifier(role)))
            self.admin.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(role)))
            self.addCleanup(self.admin.execute,sql.SQL('DROP OWNED BY {};DROP ROLE {}').format(sql.Identifier(role),sql.Identifier(role)))
        bindings=tuple(sorted((self.admin.execute('SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s',(role,)).fetchone()[0],name) for name,role in roles.items() if name!='Unregistered'))
        self.admin.execute('CREATE TABLE truss.catalog_subject_map(role_oid pg_catalog.oid PRIMARY KEY,staff_key pg_catalog.text COLLATE pg_catalog."C" NOT NULL)')
        self.admin.execute(sql.SQL('ALTER TABLE truss.catalog_subject_map OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
        for binding in bindings:self.admin.execute('INSERT INTO truss.catalog_subject_map VALUES(%s,%s)',binding)
        native_results=[]
        compiled_results=[]
        compiler_binary=os.environ.get('TRUSS_SECURITY_GRAPH_COMPILER_BINARY')
        native_compiler=None
        if compiler_binary:
            from security_ontology_compiled_read import prepare_owned_graph_compiler
            result_binary=os.environ.get('TRUSS_SECURITY_GRAPH_RESULT_BINARY')
            if not result_binary:raise RuntimeError('Original Weft graph result checker required')
            compile_graph=prepare_owned_graph_compiler(compiler_binary,result_binary)
            def native_compiler(cursor,request,before,subject,semantic):
                report=compile_graph(cursor,request,before,subject,semantic)
                compiled_results.append({'subject':subject,**report});return report
        route_refusals=[]
        salary_property=str(self.admin.execute("SELECT prop_id FROM truss.prop_def WHERE element='salary'").fetchone()[0])
        self.admin.execute("CREATE SCHEMA ontology_hostile;CREATE FUNCTION ontology_hostile.hide_name(pg_catalog.name,pg_catalog.name) RETURNS pg_catalog.bool LANGUAGE sql IMMUTABLE AS 'SELECT false';CREATE OPERATOR ontology_hostile.<> (LEFTARG=pg_catalog.name,RIGHTARG=pg_catalog.name,PROCEDURE=ontology_hostile.hide_name);CREATE FUNCTION ontology_hostile.hide_kind(pg_catalog.\"char\",pg_catalog.\"char\") RETURNS pg_catalog.bool LANGUAGE sql IMMUTABLE AS 'SELECT false';CREATE OPERATOR ontology_hostile.= (LEFTARG=pg_catalog.\"char\",RIGHTARG=pg_catalog.\"char\",PROCEDURE=ontology_hostile.hide_kind)")
        original_peer=native_read._verify_native_peer
        cases=[('Alice',['RA']),('Bob',['RB']),('Outsider',[]),('Unregistered',None),('AliceRaw',None),('AliceWrongPeer',None),('AliceDefiner',None),('AliceView',None)]
        if native_compiler:cases.extend([('AliceStaleSource',None),('AliceCorruptCells',None)])
        for name,expected in cases:
            if name=='AliceRaw':self.admin.execute(sql.SQL('GRANT SELECT(props) ON truss.object TO {}').format(sql.Identifier(roles['Bob'])))
            if name=='AliceDefiner':
                self.admin.execute("CREATE FUNCTION public.ontology_export() RETURNS pg_catalog.text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$SELECT props::pg_catalog.text FROM truss.object WHERE id="+str(identities['ra'])+'$$')
            if name=='AliceView':
                self.admin.execute('CREATE VIEW public.ontology_export_view AS SELECT props FROM truss.object WHERE id='+str(identities['ra']))
                self.admin.execute(sql.SQL('GRANT SELECT ON public.ontology_export_view TO {}').format(sql.Identifier(roles['Alice'])))
            role=roles['Alice' if name.startswith('Alice') else name]
            parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=role
            self.admin.execute('BEGIN');executor=adopt_psycopg_host(self.admin);executor_transaction=executor.adopt_transaction().value
            if name in ('AliceDefiner','AliceView'):
                self.admin.execute('SET LOCAL search_path=ontology_hostile,pg_catalog')
                self.assertEqual(self.admin.execute("SELECT 'public'::pg_catalog.name <> 'pg_catalog'::pg_catalog.name,'v'::pg_catalog.\"char\" = 'v'::pg_catalog.\"char\"").fetchone(),(False,False))
            delivered=[];cuts=[]
            def assert_native_cuts(stage):
                with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
                    for statement in (sql.SQL('ALTER ROLE {} BYPASSRLS').format(sql.Identifier(roles['Bob'])),sql.SQL('GRANT {} TO {}').format(sql.Identifier(self.installation.owner_role),sql.Identifier(roles['Alice'])),'DELETE FROM truss.catalog_subject_map WHERE false','DELETE FROM truss.edge WHERE false'):
                        with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute(statement)
                cuts.append(stage)
            def evaluating_native(*args,**kwargs):
                executable=args[0][0]
                stage='compilation' if compiler_binary and executable==compiler_binary else 'result_check' if compiler_binary and executable==result_binary else 'evaluation'
                if name=='AliceCorruptCells' and stage=='result_check':
                    checker_input=json.loads(kwargs['input']);batch=json.loads(checker_input['batchJson'])
                    self.assertEqual(batch['rows'][0][1],{'outcomeId':'withheld','disposition':'withheld'})
                    batch['rows'][0][1]['value']={'integerToken':'100'}
                    checker_input['batchJson']=json.dumps(batch);kwargs['input']=json.dumps(checker_input).encode()
                assert_native_cuts(stage);return original_run(*args,**kwargs)
            def publish_native(raw):assert_native_cuts('publication');delivered.append(raw)
            with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                connection.execute('BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000)
                adopted=caller.adopt_transaction();self.assertIsInstance(adopted,Ok,str(caller._custody.last_attempt.error));caller_transaction=adopted.value
                try:
                    self.assertEqual(connection.execute('SELECT SESSION_USER::pg_catalog.text').fetchone(),(role,))
                    connection.execute("SET LOCAL application_name='caller-owned-context'")
                    if name=='AliceDefiner':self.assertEqual(json.loads(connection.execute('SELECT public.ontology_export()').fetchone()[0])[salary_property],{'kind':'integer','text':'100'})
                    if name=='AliceView':self.assertEqual(connection.execute('SELECT props FROM public.ontology_export_view').fetchone()[0][salary_property],{'kind':'integer','text':'100'})
                    for table in ('truss.object','truss.edge','truss.catalog_subject_map'):
                        self.assertEqual(connection.execute('SELECT pg_catalog.has_table_privilege(%s,\'SELECT\')',(table,)).fetchone(),(False,))
                    from contextlib import ExitStack
                    with ExitStack() as patches:
                        patches.enter_context(patch.object(guarded.subprocess,'run',evaluating_native))
                        if name=='AliceWrongPeer':
                            def wrong_peer(cursor,identity,pid,challenge):return original_peer(cursor,identity,pid,challenge+'-wrong')
                            patches.enter_context(patch.object(native_read,'_verify_native_peer',wrong_peer))
                        selected_request=request
                        if name=='AliceStaleSource':
                            stale=json.loads(request);stale['modules'][0]['pin']['revision']='r2';selected_request=json.dumps(stale).encode()
                        result=native_read.publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,selected_request,bindings,publish_native,compiler=native_compiler)
                    self.assertEqual(connection.execute("SELECT pg_catalog.current_setting('application_name')").fetchone(),('caller-owned-context',))
                    if expected is None:
                        self.assertIsInstance(result,Error);self.assertEqual(delivered,[]);self.assertEqual(cuts,['evaluation','compilation','result_check'] if name=='AliceCorruptCells' else [])
                        reason={'Unregistered':'Original native caller has no registered ontology Subject','AliceRaw':'Unmediated registered ontology raw reads refused','AliceWrongPeer':'Original live native ontology caller/executor correspondence required','AliceDefiner':'Unmediated registered ontology definer/view routes refused','AliceView':'Unmediated registered ontology definer/view routes refused','AliceStaleSource':'Exact accepted compiler source correspondence required','AliceCorruptCells':'Original graph compiler result contract refused'}[name]
                        self.assertEqual(str(executor._custody.last_attempt.error),reason)
                        if name in ('AliceDefiner','AliceView'):route_refusals.append({'route':name,'salaryBeforeProfileCheck':{'kind':'integer','text':'100'},'ordinaryRawSelect':False,'refusedBeforeEvaluatorAndReceiver':True,'hostileOperatorControl':True})
                    else:
                        self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error)+' '+str(executor._custody.last_attempt.error))
                        self.assertEqual(cuts,['evaluation','compilation','result_check','publication'] if native_compiler else ['evaluation','publication']);self.assertEqual(delivered,[result.value])
                        decision=json.loads(delivered[0]);self.assertEqual([r['key'][0]['string'] for r in decision['rows']],expected)
                        for r in decision['rows']:self.assertEqual(r['output'][0]['disposition'],'withheld')
                        native_results.append({'caller':name,'resources':expected,'rawSelect':False,'roleAndMapCutsThroughRelease':True})
                finally:caller.detach();connection.rollback()
            executor.detach();self.admin.rollback()
            if name=='AliceRaw':self.admin.execute(sql.SQL('REVOKE SELECT(props) ON truss.object FROM {}').format(sql.Identifier(roles['Bob'])))
            if name=='AliceDefiner':self.admin.execute('DROP FUNCTION public.ontology_export()')
            if name=='AliceView':self.admin.execute('DROP VIEW public.ontology_export_view')
        directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_NATIVE_SUBJECT_EVIDENCE')
        if directory:
            folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
            (folder/'native-caller-decisions.json').write_text(json.dumps({'results':native_results,'unregisteredRefusedBeforeEvaluation':True,'scope':'Native caller identity and held role/map/graph/source cuts; trusted registration/private administrative executor/routine and authentication custody, not original checked compiler admission.'},indent=2)+'\n')
        directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_ROUTE_EVIDENCE')
        if directory:
            folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
            (folder/'export-route-refusals.json').write_text(json.dumps({'observations':route_refusals,'scope':'Unsafe accessible definer/view installation is refused; routes are not repaired by this checker. DDL/routine lifetime remains an external premise.'},indent=2)+'\n')
        directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_COMPILED_EVIDENCE')
        if directory:
            self.assertEqual([r['subject'] for r in compiled_results],['Alice','Bob','Outsider'])
            folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
            (folder/'compiled-native-results.json').write_text(json.dumps({'results':compiled_results,'scope':'Original compiler SQL/guards under authentic nativecaller role/map/source/fact cut and independent semantic bag comparison; no compiler/native admission credential.'},indent=2)+'\n')
        # A real revocation waits for the admitted reader's outer transaction;
        # commit acknowledgment precedes a fresh read which must see revocation.
        import threading,time
        started=threading.Event();acknowledged=threading.Event();writer_state={};writer_errors=[]
        def revoke():
            try:
                with psycopg.connect(self.info.connection_uri,connect_timeout=2,options='-c statement_timeout=10000 -c lock_timeout=8000') as writer:
                    writer_state['connection']=writer
                    writer_state['pid']=writer.execute('SELECT pg_catalog.pg_backend_pid()').fetchone()[0]
                    started.set()
                    writer.execute("UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s,'value'],'false'::pg_catalog.jsonb) WHERE id=%s",(active_property,identities['aa']))
                    writer.commit();acknowledged.set()
            except Exception as error:writer_errors.append(repr(error));started.set()
        worker=threading.Thread(target=revoke)
        drain_rows=[];drain_decisions=[]
        parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=roles['Alice']
        self.admin.execute('BEGIN');executor=adopt_psycopg_host(self.admin);executor_transaction=executor.adopt_transaction().value
        def receive_before_revocation(raw):
            drain_decisions.append(json.loads(raw));worker.start()
            self.assertTrue(started.wait(2));self.assertEqual(writer_errors,[])
            deadline=time.monotonic()+2
            with psycopg.connect(self.info.connection_uri,autocommit=True) as observer:
                while time.monotonic()<deadline:
                    waiting=observer.execute("SELECT l.mode,l.granted FROM pg_catalog.pg_locks l WHERE l.pid=%s AND l.relation='truss.object'::pg_catalog.regclass AND l.mode='RowExclusiveLock'",(writer_state['pid'],)).fetchall()
                    if waiting==[('RowExclusiveLock',False)]:break
                    time.sleep(.01)
                blockers=observer.execute('SELECT pg_catalog.pg_blocking_pids(%s)',(writer_state['pid'],)).fetchone()[0]
            self.assertEqual(waiting,[('RowExclusiveLock',False)]);self.assertFalse(acknowledged.is_set())
            self.assertIn(self.admin.info.backend_pid,blockers)
            drain_rows.append({'stage':'receiver','writerLock':'RowExclusiveLock','granted':False,'acknowledged':False,'originalExecutorIsNativeBlocker':True})
        try:
            with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                connection.execute('BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);caller_transaction=caller.adopt_transaction().value
                try:
                    result=native_read.publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,request,bindings,receive_before_revocation)
                    self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error)+' '+str(executor._custody.last_attempt.error))
                    self.assertEqual([r['key'][0]['string'] for r in drain_decisions[0]['rows']],['RA'])
                    self.assertFalse(acknowledged.is_set());self.assertTrue(worker.is_alive())
                    drain_rows.append({'stage':'after_receiver_before_outer_settlement','acknowledged':False})
                finally:caller.detach();connection.rollback()
        finally:
            try:executor.detach();self.admin.rollback()
            finally:
                if worker.ident is not None:
                    worker.join(3)
                    if worker.is_alive():
                        try:
                            pending_connection=writer_state.get('connection')
                            if pending_connection is not None:pending_connection.cancel_safe(timeout=1.0)
                        finally:worker.join(3)
                    self.assertFalse(worker.is_alive())
        self.assertEqual(writer_errors,[]);self.assertTrue(acknowledged.is_set())
        self.assertEqual(self.admin.execute('SELECT props->%s->>\'value\' FROM truss.object WHERE id=%s',(active_property,identities['aa'])).fetchone(),('false',))
        drain_rows.append({'stage':'after_outer_settlement','acknowledged':True})
        self.admin.execute('BEGIN');executor=adopt_psycopg_host(self.admin);executor_transaction=executor.adopt_transaction().value
        try:
            with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                connection.execute('BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);caller_transaction=caller.adopt_transaction().value
                try:
                    delivered=[]
                    result=native_read.publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,request,bindings,delivered.append)
                    self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error)+' '+str(executor._custody.last_attempt.error))
                    self.assertEqual(json.loads(delivered[0])['rows'],[])
                    drain_rows.append({'stage':'fresh_admission_after_commit_ack','resources':[]})
                finally:caller.detach();connection.rollback()
        finally:executor.detach();self.admin.rollback()
        directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_REVOCATION_EVIDENCE')
        if directory:
            folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
            (folder/'revocation-order.json').write_text(json.dumps({'observations':drain_rows,'beforeRevocationDecision':drain_decisions[0],'scope':'One actual Assignment.active writer/read cut and native commit acknowledgment; complete policy/role/mapping/cache/paging/clock generation lifecycle not qualified.'},indent=2)+'\n')
