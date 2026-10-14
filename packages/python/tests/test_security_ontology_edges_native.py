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
        private_executor=os.environ.get('TRUSS_SECURITY_ONTOLOGY_ORDINARY_EXECUTOR')
        cut_issuer=None;private_parameters=None
        if private_executor:
            private_executor='ontology_private_'+uuid.uuid4().hex[:10]
            self.admin.execute(sql.SQL('CREATE ROLE {} LOGIN').format(sql.Identifier(private_executor)))
            self.addCleanup(self.admin.execute,sql.SQL('DROP OWNED BY {};DROP ROLE {}').format(sql.Identifier(private_executor),sql.Identifier(private_executor)))
            self.admin.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(private_executor)))
            for table in guarded.TABLES+('catalog_subject_map',):self.admin.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(sql.Identifier('truss',table),sql.Identifier(private_executor)))
            # Private service sees live peer metadata, not a client privilege.
            self.admin.execute(sql.SQL('GRANT pg_read_all_stats TO {}').format(sql.Identifier(private_executor)))
            # Fixed source reconstruction routines are INVOKER and cannot gain
            # writes absent native grants; no blanket definer grants are made.
            routines=self.admin.execute("SELECT p.oid::pg_catalog.regprocedure::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='truss' AND NOT p.prosecdef AND p.prokind='f'").fetchall()
            for (signature,) in routines:self.admin.execute(sql.SQL('GRANT EXECUTE ON FUNCTION {} TO {}').format(sql.SQL(signature),sql.Identifier(private_executor)))
            from security_ontology_read_cut import SOURCE,verify_ontology_read_cut_issuer
            self.admin.execute(SOURCE.read_text())
            self.admin.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.acquire_ontology_read_cut() TO {}').format(sql.Identifier(private_executor)))
            owner_oid=self.admin.execute('SELECT oid FROM pg_catalog.pg_roles WHERE rolname=CURRENT_USER').fetchone()[0]
            private_oid=self.admin.execute('SELECT oid FROM pg_catalog.pg_roles WHERE rolname=%s',(private_executor,)).fetchone()[0]
            with self.admin.cursor() as cursor:verify_ontology_read_cut_issuer(cursor,owner_oid,private_oid)
            cut_issuer=(owner_oid,private_oid)
            private_parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);private_parameters['user']=private_executor
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
        if private_executor:self.admin.execute(sql.SQL('GRANT USAGE ON SCHEMA ontology_hostile TO {}').format(sql.Identifier(private_executor)))
        original_peer=native_read._verify_native_peer
        cases=[('Alice',['RA']),('Bob',['RB']),('Outsider',[]),('Unregistered',None),('AliceRaw',None),('AliceWrongPeer',None),('AliceDefiner',None),('AliceView',None)]
        if native_compiler:cases.extend([('AliceStaleSource',None),('AliceCorruptCells',None)])
        if private_parameters:cases.extend([('AliceFactRls',None),('AliceSourceInheritance',None),('AliceFactInheritance',None),('AliceIssuerPublic',None)])
        for name,expected in cases:
            if name=='AliceFactRls':self.admin.execute('ALTER TABLE truss.object ENABLE ROW LEVEL SECURITY')
            if name=='AliceSourceInheritance':self.admin.execute('CREATE TABLE public.ontology_source_child () INHERITS (truss.schema_head)')
            if name=='AliceFactInheritance':self.admin.execute('CREATE TABLE public.ontology_fact_child () INHERITS (truss.object)')
            if name=='AliceIssuerPublic':self.admin.execute('GRANT EXECUTE ON FUNCTION truss.acquire_ontology_read_cut() TO PUBLIC')
            if name=='AliceRaw':self.admin.execute(sql.SQL('GRANT SELECT(props) ON truss.object TO {}').format(sql.Identifier(roles['Bob'])))
            if name=='AliceDefiner':
                self.admin.execute("CREATE FUNCTION public.ontology_export() RETURNS pg_catalog.text LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$SELECT props::pg_catalog.text FROM truss.object WHERE id="+str(identities['ra'])+'$$')
            if name=='AliceView':
                self.admin.execute('CREATE VIEW public.ontology_export_view AS SELECT props FROM truss.object WHERE id='+str(identities['ra']))
                self.admin.execute(sql.SQL('GRANT SELECT ON public.ontology_export_view TO {}').format(sql.Identifier(roles['Alice'])))
            role=roles['Alice' if name.startswith('Alice') else name]
            parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=role
            executor_connection=self.admin if private_parameters is None else psycopg.connect(**private_parameters,autocommit=True,options='-c statement_timeout=10000')
            if private_parameters:self.addCleanup(executor_connection.close)
            executor_connection.execute('BEGIN');executor=adopt_psycopg_host(executor_connection,statement_timeout_ms=10000,operation_timeout_ms=30000);executor_transaction=executor.adopt_transaction().value
            if private_parameters:
                self.assertEqual(executor_connection.execute("SELECT rolsuper,rolbypassrls FROM pg_catalog.pg_roles WHERE rolname=CURRENT_USER").fetchone(),(False,False))
                self.assertEqual(executor_connection.execute("SELECT pg_catalog.has_table_privilege('truss.schema_head','UPDATE')").fetchone(),(False,))
            if name in ('AliceDefiner','AliceView'):
                executor_connection.execute('SET LOCAL search_path=ontology_hostile,pg_catalog')
                self.assertEqual(executor_connection.execute("SELECT 'public'::pg_catalog.name <> 'pg_catalog'::pg_catalog.name,'v'::pg_catalog.\"char\" = 'v'::pg_catalog.\"char\"").fetchone(),(False,False))
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
                        result=native_read.publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,selected_request,bindings,publish_native,compiler=native_compiler,cut_issuer=cut_issuer)
                    self.assertEqual(connection.execute("SELECT pg_catalog.current_setting('application_name')").fetchone(),('caller-owned-context',))
                    if expected is None:
                        self.assertIsInstance(result,Error);self.assertEqual(delivered,[]);self.assertEqual(cuts,['evaluation','compilation','result_check'] if name=='AliceCorruptCells' else [])
                        reason={'Unregistered':'Original native caller has no registered ontology Subject','AliceRaw':'Unmediated registered ontology raw reads refused','AliceWrongPeer':'Original live native ontology caller/executor correspondence required','AliceDefiner':'Unmediated registered ontology definer/view routes refused','AliceView':'Unmediated registered ontology definer/view routes refused','AliceStaleSource':'Exact accepted compiler source correspondence required','AliceCorruptCells':'Original graph compiler result contract refused','AliceFactRls':'Original held complete unfiltered ontology fact cut required','AliceFactInheritance':'Original held complete unfiltered ontology fact cut required','AliceSourceInheritance':'Original held complete accepted catalog source cut required','AliceIssuerPublic':'Exact private graph cut issuer ACL required'}[name]
                        self.assertEqual(str(executor._custody.last_attempt.error),reason)
                        if name in ('AliceDefiner','AliceView'):route_refusals.append({'route':name,'salaryBeforeProfileCheck':{'kind':'integer','text':'100'},'ordinaryRawSelect':False,'refusedBeforeEvaluatorAndReceiver':True,'hostileOperatorControl':True})
                    else:
                        self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error)+' '+str(executor._custody.last_attempt.error))
                        self.assertEqual(cuts,['evaluation','compilation','result_check','publication'] if native_compiler else ['evaluation','publication']);self.assertEqual(delivered,[result.value])
                        decision=json.loads(delivered[0]);self.assertEqual([r['key'][0]['string'] for r in decision['rows']],expected)
                        for r in decision['rows']:self.assertEqual(r['output'][0]['disposition'],'withheld')
                        native_results.append({'caller':name,'resources':expected,'rawSelect':False,'roleAndMapCutsThroughRelease':True})
                finally:caller.detach();connection.rollback()
            if name in ('AliceFactRls','AliceSourceInheritance','AliceFactInheritance','AliceIssuerPublic'):
                self.assertEqual(executor_connection.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,))
            executor.detach();executor_connection.rollback()
            if private_parameters:executor_connection.close()
            if name=='AliceFactRls':self.admin.execute('ALTER TABLE truss.object DISABLE ROW LEVEL SECURITY')
            if name=='AliceSourceInheritance':self.admin.execute('DROP TABLE public.ontology_source_child')
            if name=='AliceFactInheritance':self.admin.execute('DROP TABLE public.ontology_fact_child')
            if name=='AliceIssuerPublic':self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.acquire_ontology_read_cut() FROM PUBLIC')
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
        executor_connection=self.admin if private_parameters is None else psycopg.connect(**private_parameters,autocommit=True,options='-c statement_timeout=10000')
        executor_connection.execute('BEGIN');executor=adopt_psycopg_host(executor_connection,statement_timeout_ms=10000,operation_timeout_ms=30000);executor_transaction=executor.adopt_transaction().value
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
            self.assertIn(executor_connection.info.backend_pid,blockers)
            drain_rows.append({'stage':'receiver','writerLock':'RowExclusiveLock','granted':False,'acknowledged':False,'originalExecutorIsNativeBlocker':True})
        try:
            with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                connection.execute('BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);caller_transaction=caller.adopt_transaction().value
                try:
                    result=native_read.publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,request,bindings,receive_before_revocation,cut_issuer=cut_issuer)
                    self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error)+' '+str(executor._custody.last_attempt.error))
                    self.assertEqual([r['key'][0]['string'] for r in drain_decisions[0]['rows']],['RA'])
                    self.assertFalse(acknowledged.is_set());self.assertTrue(worker.is_alive())
                    drain_rows.append({'stage':'after_receiver_before_outer_settlement','acknowledged':False})
                finally:caller.detach();connection.rollback()
        finally:
            try:
                executor.detach();executor_connection.rollback()
                if private_parameters:executor_connection.close()
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
        executor_connection=self.admin if private_parameters is None else psycopg.connect(**private_parameters,autocommit=True,options='-c statement_timeout=10000')
        executor_connection.execute('BEGIN');executor=adopt_psycopg_host(executor_connection,statement_timeout_ms=10000,operation_timeout_ms=30000);executor_transaction=executor.adopt_transaction().value
        try:
            with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                connection.execute('BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);caller_transaction=caller.adopt_transaction().value
                try:
                    delivered=[]
                    result=native_read.publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,request,bindings,delivered.append,cut_issuer=cut_issuer)
                    self.assertIsInstance(result,Ok,str(caller._custody.last_attempt.error)+' '+str(executor._custody.last_attempt.error))
                    self.assertEqual(json.loads(delivered[0])['rows'],[])
                    drain_rows.append({'stage':'fresh_admission_after_commit_ack','resources':[]})
                finally:caller.detach();connection.rollback()
        finally:
            executor.detach();executor_connection.rollback()
            if private_parameters:executor_connection.close()
        directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_REVOCATION_EVIDENCE')
        if directory:
            folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
            (folder/'revocation-order.json').write_text(json.dumps({'observations':drain_rows,'beforeRevocationDecision':drain_decisions[0],'scope':'One actual Assignment.active writer/read cut and native commit acknowledgment; complete policy/role/mapping/cache/paging/clock generation lifecycle not qualified.'},indent=2)+'\n')

        if os.environ.get('TRUSS_SECURITY_ONTOLOGY_SOURCE_FACTORY'):
            self.assertTrue(compiled_results,'Original owner compiler output required for graph source factory')
            from dataclasses import replace
            from truss._security_graph_source import PreparedGraphSecuritySource,snapshot_graph_security_source
            from truss._security_catalog_source_installation import bootstrap_catalog_source_marker_in_transaction,verify_catalog_source_archive_with_cursor
            from truss._security_home_installation import bootstrap_security_homes_in_transaction
            from truss._security_source_epoch_installation import bootstrap_source_epoch_infrastructure_in_transaction
            from truss._security_catalog_source_epoch import issue_initial_catalog_source_epoch_in_transaction
            from truss._psycopg_fact_cut import _FactRelationComparison,_FactColumnComparison
            record=compiled_results[0];original_compiler=record['request'].encode()
            assessment=json.loads(original_compiler)['bindingJson'];assessment=json.loads(assessment)['inventoryJson'].encode()
            # Preserve the exact native assessment carrier, not a reserialized census.
            from truss._security_catalog_assessment import capture_accepted_catalog
            self.admin.execute('BEGIN');factory_host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);factory_tx=factory_host.adopt_transaction().value
            self.addCleanup(factory_host.detach)
            with self.admin.cursor() as cursor:actual_assessment=capture_accepted_catalog(cursor,request)
            self.assertEqual(json.loads(actual_assessment),json.loads(assessment))
            profile=sha256(original_compiler).digest();guard=(self.installation.installation_id.encode(),profile,1)
            graph=PreparedGraphSecuritySource(request,record['output'].encode(),actual_assessment,original_compiler,guard)
            guarded_binary=os.environ.get('TRUSS_SECURITY_GUARDED_COMPILER_BINARY')
            if guarded_binary:
                guarded_output=original_run([guarded_binary],input=original_compiler,capture_output=True,check=True,timeout=15).stdout
                graph=replace(graph,guarded_response=guarded_output)
            graph=snapshot_graph_security_source(graph)
            homes=bootstrap_security_homes_in_transaction(factory_host,factory_tx,installation_identity=guard[0],authored_profile=profile,max_retained=8)
            self.assertIsInstance(homes,Ok,str(factory_host._custody.last_attempt.error))
            marked=bootstrap_catalog_source_marker_in_transaction(factory_host,factory_tx,graph)
            self.assertIsInstance(marked,Ok,str(factory_host._custody.last_attempt.error))
            self.assertIsInstance(bootstrap_catalog_source_marker_in_transaction(factory_host,factory_tx,graph),Error)
            infrastructure=bootstrap_source_epoch_infrastructure_in_transaction(factory_host,factory_tx,installation_identity=guard[0])
            self.assertIsInstance(infrastructure,Ok,str(factory_host._custody.last_attempt.error))
            source=(Path(__file__).resolve().parents[3]/'packages/postgresql/native/authorization-fact-write-fence.sql').read_text()
            self.admin.execute(source)
            self.admin.execute(sql.SQL('ALTER FUNCTION truss.runtime_fence_authorization_fact_write() OWNER TO {}').format(sql.Identifier(self.installation.owner_role)))
            facts=[]
            for name in ('object','edge','catalog_subject_map'):
                self.admin.execute(sql.SQL('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON {} FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write()').format(sql.Identifier('truss',name)))
                self.admin.execute(sql.SQL('ALTER TABLE {} ENABLE ALWAYS TRIGGER fact_write_fence').format(sql.Identifier('truss',name)))
                oid,owner=self.admin.execute('SELECT oid,relowner FROM pg_catalog.pg_class WHERE oid=%s::pg_catalog.regclass',('truss.'+name,)).fetchone()
                columns=self.admin.execute('SELECT attname,attnum,atttypid,atttypmod,attnotnull,attcollation,attgenerated,attidentity FROM pg_catalog.pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped ORDER BY attnum',(oid,)).fetchall()
                facts.append(_FactRelationComparison('truss',name,oid,owner,source.split('AS $$',1)[1].split('$$;',1)[0],tuple(_FactColumnComparison(*c) for c in columns)))
            inputs=dict(mapping=graph,marker=marked.value,infrastructure=infrastructure.value,fact_relations=tuple(facts),subject_source=(Path(__file__).resolve().parents[3]/'scripts/security_ontology_native_subject_read.py').read_bytes())
            self.admin.execute("CREATE TEMP TABLE graph_factory_prior(value text);INSERT INTO graph_factory_prior VALUES('kept');SAVEPOINT before_graph_epoch")
            issued=issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**inputs)
            self.assertIsInstance(issued,Ok,str(factory_host._custody.last_attempt.error))
            comparison=issued.value.comparison
            self.assertIn(b'truss-owned-graph-source-profile/0.1-candidate',comparison.profile)
            self.assertEqual(self.admin.execute('SELECT source_epoch,profile_bytes,evidence_bytes FROM truss.source_epoch_registry').fetchall(),[(comparison.epoch,comparison.profile,actual_assessment)])
            with self.admin.cursor() as cursor:verify_catalog_source_archive_with_cursor(cursor,graph,self.installation.installation_id)
            self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**inputs),Error)
            self.admin.execute('ROLLBACK TO before_graph_epoch')
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(0,))
            self.assertEqual(self.admin.execute('TABLE graph_factory_prior').fetchall(),[('kept',)])
            stale=replace(graph,native_guard=(guard[0],profile,2))
            self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**{**inputs,'mapping':stale}),Error)
            self.assertEqual(str(factory_host._custody.last_attempt.error),'Original source factory current guard required')
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(0,))
            malformed=replace(graph,native_dependencies=b'{}')
            self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**{**inputs,'mapping':malformed}),Error)
            self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**{**inputs,'fact_relations':tuple(facts[:-1])}),Error)
            incomplete=(replace(facts[0],columns=facts[0].columns[:-1]),*facts[1:])
            self.assertIsInstance(issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**{**inputs,'fact_relations':incomplete}),Error)
            self.assertEqual(str(factory_host._custody.last_attempt.error),'Complete original graph fact column census required')
            self.assertEqual(self.admin.execute('SELECT count(*) FROM truss.source_epoch_registry').fetchone(),(0,))
            issued=issue_initial_catalog_source_epoch_in_transaction(factory_host,factory_tx,**inputs)
            self.assertIsInstance(issued,Ok,str(factory_host._custody.last_attempt.error));comparison=issued.value.comparison
            factory_host.detach();self.admin.commit()
            self.assertEqual(self.admin.execute('SELECT source_epoch,profile_bytes,evidence_bytes FROM truss.source_epoch_registry').fetchall(),[(comparison.epoch,comparison.profile,actual_assessment)])
            directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_SOURCE_EVIDENCE')
            if directory:
                folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
                for name,data in (('physical-request.json',request),('compiler-request.json',original_compiler),('compiler-output.json',record['output'].encode()),('accepted-catalog.json',actual_assessment),('issued-profile.json',comparison.profile)):(folder/name).write_bytes(data)
                archive=self.admin.execute("SELECT artifact_role,artifact_identity,pg_catalog.encode(artifact_sha256,'hex'),pg_catalog.encode(artifact_identity_sha256,'hex'),installation_id FROM truss.installation_archive ORDER BY artifact_identity COLLATE pg_catalog.\"C\"").fetchall()
                (folder/'native-source-epoch.json').write_text(json.dumps({'epoch':comparison.epoch,'installation':comparison.installation,'incarnation':comparison.incarnation,'archives':archive,'committedReadback':True,'controls':['no repair/reuse','outer rollback retains prior work','stale generation','malformed graph preflight','omitted fact relation','omitted fact column'],'securityReady':False,'scope':'Original graph archive and initial native source epoch under trusted original compiler/administrator/routine/DDL custody; registered Subject/native compiler admission pending.'},indent=2)+'\n')

            if os.environ.get('TRUSS_SECURITY_ONTOLOGY_EPOCH_READ'):
                self.assertIsNotNone(private_parameters,'Actual ordinary private executor required')
                from truss._security_graph_epoch_read import bootstrap_graph_epoch_read_cut_in_transaction,GraphEpochReadContext
                self.admin.execute('BEGIN');installation_host=adopt_psycopg_host(self.admin);installation_tx=installation_host.adopt_transaction().value
                installed=bootstrap_graph_epoch_read_cut_in_transaction(installation_host,installation_tx,executor_role=private_executor)
                self.assertIsInstance(installed,Ok,str(installation_host._custody.last_attempt.error))
                self.assertIsInstance(bootstrap_graph_epoch_read_cut_in_transaction(installation_host,installation_tx,executor_role=private_executor),Error)
                installation_host.detach();self.admin.commit()
                context=GraphEpochReadContext(graph,comparison,installed.value,inputs['subject_source'])
                observations=[]
                for label,selected in (('current',context),('stale',replace(context,comparison=replace(comparison,epoch='stale-epoch'))),('guard-drift',context),('archive-drift',context),*((('capsule-drift',context),) if graph.guarded_response is not None else ()),('epoch-rls',context),('issuer-public',context),('compiler-drift',context),('guard-writable',context),('issuer-owner-member',context),('advanced',context),('advanced-current',context)):
                    if label=='advanced':
                        advanced_epoch=self.admin.execute('SELECT truss.runtime_issue_source_epoch(%s,%s,%s,%s,%s)',(comparison.installation,comparison.epoch,comparison.incarnation,comparison.profile,comparison.evidence)).fetchone()[0]
                        self.assertNotEqual(advanced_epoch,comparison.epoch)
                    if label=='advanced-current':selected=replace(context,comparison=replace(comparison,epoch=advanced_epoch))
                    if label=='issuer-owner-member':
                        issuer_owner=self.admin.execute('SELECT rolname FROM pg_catalog.pg_roles WHERE oid=%s',(installed.value.owner_oid,)).fetchone()[0]
                        self.admin.execute(sql.SQL('GRANT {} TO {}').format(sql.Identifier(issuer_owner),sql.Identifier(private_executor)))
                    if label=='guard-writable':self.admin.execute(sql.SQL('GRANT UPDATE(generation) ON truss.policy_generation_guard TO {}').format(sql.Identifier(private_executor)))
                    if label=='guard-drift':self.admin.execute('UPDATE truss.policy_generation_guard SET generation=2')
                    if label=='archive-drift':self.admin.execute("UPDATE truss.installation_archive SET artifact_bytes=artifact_bytes || decode('20','hex') WHERE artifact_identity='graph:original-compiler-output'")
                    if label=='capsule-drift':self.admin.execute("UPDATE truss.installation_archive SET artifact_bytes=artifact_bytes || decode('20','hex') WHERE artifact_identity='graph:original-source-context'")
                    if label=='epoch-rls':self.admin.execute('ALTER TABLE truss.source_epoch_current ENABLE ROW LEVEL SECURITY')
                    if label=='issuer-public':self.admin.execute('GRANT EXECUTE ON FUNCTION truss.acquire_graph_epoch_read_cut() TO PUBLIC')
                    with psycopg.connect(**private_parameters,autocommit=True,options='-c statement_timeout=10000') as private:
                        private.execute('BEGIN');executor=adopt_psycopg_host(private,statement_timeout_ms=10000,operation_timeout_ms=30000);executor_tx=executor.adopt_transaction().value
                        self.assertEqual(private.execute("SELECT pg_catalog.has_table_privilege('truss.source_epoch_current','UPDATE')").fetchone(),(False,))
                        parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=roles['Bob']
                        with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                            connection.execute('BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);caller_tx=caller.adopt_transaction().value;released=[]
                            def receiver(raw):
                                with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
                                    for table in ('source_epoch_current','source_epoch_registry','installation_archive','policy_generation_guard'):
                                        with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute(sql.SQL('DELETE FROM {} WHERE false').format(sql.Identifier('truss',table)))
                                    with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute('SELECT truss.runtime_issue_source_epoch(%s,%s,%s,%s,%s)',(selected.comparison.installation,selected.comparison.epoch,selected.comparison.incarnation,selected.comparison.profile,selected.comparison.evidence))
                                released.append(raw)
                            def selected_epoch_compiler(*args):
                                receipt=native_compiler(*args)
                                if label=='compiler-drift':receipt={**receipt,'output':receipt['output']+' '}
                                return receipt
                            result=native_read.publish_native_ontology_resource_read(caller,caller_tx,executor,executor_tx,request,bindings,receiver,compiler=selected_epoch_compiler,cut_issuer=cut_issuer,source_epoch=selected)
                            if label in ('current','advanced-current'):
                                self.assertIsInstance(result,Ok,str(executor._custody.last_attempt.error));self.assertEqual([r['key'][0]['string'] for r in json.loads(result.value)['rows']],['RB']);self.assertEqual(released,[result.value])
                                observations.append({'case':label,'resources':['RB'],'withheldSalary':True,'epochArchiveGuardCutsThroughReceiver':True,'ordinaryExecutorNoEpochUpdate':True})
                            else:
                                self.assertIsInstance(result,Error);self.assertEqual(released,[]);self.assertEqual(str(executor._custody.last_attempt.error),{'stale':'Original current graph source epoch required','advanced':'Original current graph source epoch required','guard-drift':'Original current graph authority guard required','archive-drift':'Original current graph source archive required','capsule-drift':'Original current graph source archive required','epoch-rls':'Original complete unfiltered graph epoch homes and cuts required','issuer-public':'Exact private graph epoch cut ACL required','compiler-drift':'Original current graph compiler source correspondence required','guard-writable':'Original private read-only graph epoch homes required','issuer-owner-member':'Original excluded privileged graph epoch cut owner required'}[label])
                                self.assertEqual(private.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,));observations.append({'case':label,'refusedBeforeRelease':True,'noRetainedCuts':True})
                            caller.detach();connection.rollback()
                        executor.detach();private.rollback()
                    if label=='issuer-owner-member':self.admin.execute(sql.SQL('REVOKE {} FROM {}').format(sql.Identifier(issuer_owner),sql.Identifier(private_executor)))
                    if label=='guard-writable':self.admin.execute(sql.SQL('REVOKE UPDATE(generation) ON truss.policy_generation_guard FROM {}').format(sql.Identifier(private_executor)))
                    if label=='guard-drift':self.admin.execute('UPDATE truss.policy_generation_guard SET generation=1')
                    if label=='archive-drift':self.admin.execute("UPDATE truss.installation_archive SET artifact_bytes=%s WHERE artifact_identity='graph:original-compiler-output'",(graph.original_response,))
                    if label=='capsule-drift':
                        from truss._security_guarded_source import capture_guarded_source_comparison
                        capsule=capture_guarded_source_comparison(graph.native_dependencies,graph.guarded_response)
                        self.admin.execute("UPDATE truss.installation_archive SET artifact_bytes=%s WHERE artifact_identity='graph:original-source-context'",(capsule.source_bytes,))
                    if label=='epoch-rls':self.admin.execute('ALTER TABLE truss.source_epoch_current DISABLE ROW LEVEL SECURITY')
                    if label=='issuer-public':self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.acquire_graph_epoch_read_cut() FROM PUBLIC')
                directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_EPOCH_READ_EVIDENCE')
                if directory:
                    folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
                    (folder/'ordinary-epoch-read.json').write_text(json.dumps({'observations':observations,'epoch':comparison.epoch,'advancedEpoch':advanced_epoch,'securityReady':False,'scope':'Selected actual ordinary epoch/archive/guard reads, trusted compiler/installer/routine/DDL/authentication custody; registered Subject issuer and public compiler admission pending.'},indent=2)+'\n')

            if os.environ.get('TRUSS_SECURITY_ONTOLOGY_REGISTERED_SUBJECT'):
                from truss._security_graph_subject_installation import bootstrap_graph_subjects_in_transaction,verify_graph_subject_issuer_with_cursor
                self.admin.execute("BEGIN;CREATE TEMP TABLE graph_subject_prior(value text);INSERT INTO graph_subject_prior VALUES('kept');SAVEPOINT before_graph_subject_registration;DROP TABLE truss.catalog_subject_map")
                registration_host=adopt_psycopg_host(self.admin,operation_timeout_ms=30000);registration_tx=registration_host.adopt_transaction().value
                self.addCleanup(registration_host.detach)
                role_bindings=tuple((roles[name],name) for name in ('Alice','Bob','Outsider'))
                missing=bootstrap_graph_subjects_in_transaction(registration_host,registration_tx,source=graph,bindings=((roles['Alice'],'missing-staff'),))
                self.assertIsInstance(missing,Error);self.assertEqual(str(registration_host._custody.last_attempt.error),'Unique original stored graph Staff identity required')
                self.assertEqual(self.admin.execute("SELECT count(*) FROM pg_catalog.pg_class WHERE oid=pg_catalog.to_regclass('truss.catalog_subject_map')").fetchone(),(0,))
                self.admin.execute(sql.SQL('REVOKE SELECT ON truss.object FROM {}').format(sql.Identifier(self.installation.owner_role)))
                refused=bootstrap_graph_subjects_in_transaction(registration_host,registration_tx,source=graph,bindings=role_bindings)
                self.assertIsInstance(refused,Error);self.assertEqual(str(registration_host._custody.last_attempt.error),'Original graph Subject owner read privileges required')
                self.admin.execute(sql.SQL('GRANT SELECT ON truss.object TO {}').format(sql.Identifier(self.installation.owner_role)))
                self.admin.execute(sql.SQL('REVOKE MAINTAIN,UPDATE,DELETE,TRUNCATE ON truss.object FROM {}').format(sql.Identifier(self.installation.owner_role)))
                refused=bootstrap_graph_subjects_in_transaction(registration_host,registration_tx,source=graph,bindings=role_bindings)
                self.assertIsInstance(refused,Error);self.assertEqual(str(registration_host._custody.last_attempt.error),'Original graph Subject owner SHARE privileges required')
                self.admin.execute(sql.SQL('GRANT MAINTAIN,UPDATE,DELETE,TRUNCATE ON truss.object TO {}').format(sql.Identifier(self.installation.owner_role)))
                self.admin.execute('SAVEPOINT graph_subject_installation')
                rolled=bootstrap_graph_subjects_in_transaction(registration_host,registration_tx,source=graph,bindings=role_bindings)
                self.assertIsInstance(rolled,Ok,str(registration_host._custody.last_attempt.error))
                self.admin.execute('ROLLBACK TO graph_subject_installation')
                self.assertEqual(self.admin.execute('TABLE graph_subject_prior').fetchall(),[('kept',)])
                self.assertEqual(self.admin.execute("SELECT pg_catalog.to_regclass('truss.catalog_subject_map')::text,pg_catalog.to_regclass('truss.catalog_graph_subject_profile')::text,pg_catalog.to_regprocedure('truss.graph_subject_current()')::text").fetchone(),(None,None,None))
                registered=bootstrap_graph_subjects_in_transaction(registration_host,registration_tx,source=graph,bindings=role_bindings)
                self.assertIsInstance(registered,Ok,str(registration_host._custody.last_attempt.error))
                subjects=registered.value
                self.assertIsInstance(bootstrap_graph_subjects_in_transaction(registration_host,registration_tx,source=graph,bindings=role_bindings),Error)
                with self.admin.cursor() as cursor:verify_graph_subject_issuer_with_cursor(cursor,subjects)
                # Commit only this disposable fixture's explicit fresh registration.
                registration_host.detach();self.admin.commit()
                own_subjects=[]
                for name in ('Alice','Bob','Outsider'):
                    parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=roles[name]
                    with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                        connection.execute('BEGIN')
                        self.assertEqual(connection.execute("SELECT pg_catalog.has_table_privilege('truss.catalog_subject_map','SELECT'),pg_catalog.has_table_privilege('truss.object','SELECT')").fetchone(),(False,False))
                        rows=connection.execute('SELECT * FROM truss.graph_subject_current()').fetchall()
                        oid=self.admin.execute('SELECT oid::text FROM pg_catalog.pg_roles WHERE rolname=%s',(roles[name],)).fetchone()[0]
                        db=self.admin.execute('SELECT oid::text FROM pg_catalog.pg_database WHERE datname=current_database()').fetchone()[0]
                        self.assertEqual(rows,[(name,self.installation.installation_id,db,oid,sha256(subjects.profile_bytes).hexdigest())])
                        self.assertEqual(connection.execute('SELECT SESSION_USER::text,CURRENT_USER::text').fetchone(),(roles[name],roles[name]))
                        connection.rollback();own_subjects.append({'principal':name,'subjectKey':name,'ownNativeSession':True,'rawReads':False})
                parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=roles['Unregistered']
                with psycopg.connect(**parameters,autocommit=True) as connection:
                    with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute('SELECT * FROM truss.graph_subject_current()')
                self.admin.execute('GRANT EXECUTE ON FUNCTION truss.graph_subject_current() TO PUBLIC')
                with self.admin.cursor() as cursor:
                    with self.assertRaisesRegex(ValueError,'Exact registered graph Subject issuer ACL required'):verify_graph_subject_issuer_with_cursor(cursor,subjects)
                self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.graph_subject_current() FROM PUBLIC')
                directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_REGISTERED_SUBJECT_EVIDENCE')
                if directory:
                    folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
                    (folder/'subject-profile.json').write_bytes(subjects.profile_bytes)
                    (folder/'native-subject-registration.json').write_text(json.dumps({'observations':own_subjects,'missingStaffNoEffects':True,'revokedOwnerSelectRefused':True,'revokedOwnerShareRefused':True,'rollbackPreservesPriorWork':True,'reuseRefused':True,'unregisteredExecuteRefused':True,'publicAclDriftRefused':True,'securityReady':False,'scope':'Source-validated fresh graph Subject registration and own-session metadata issuer in disposable full ontology fixture. Protected query composition/registered native compiler admission remain pending.'},indent=2)+'\n')

                if os.environ.get('TRUSS_SECURITY_ONTOLOGY_SUBJECT_COMPOSITION'):
                    self.admin.execute(sql.SQL('GRANT SELECT ON truss.catalog_subject_map,truss.catalog_graph_subject_profile TO {}').format(sql.Identifier(private_executor)))
                    self.admin.execute('CREATE TRIGGER fact_write_fence BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.catalog_subject_map FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_fence_authorization_fact_write();ALTER TABLE truss.catalog_subject_map ENABLE ALWAYS TRIGGER fact_write_fence')
                    new_facts=[]
                    for name in ('object','edge','catalog_subject_map'):
                        oid,owner=self.admin.execute('SELECT oid,relowner FROM pg_catalog.pg_class WHERE oid=%s::pg_catalog.regclass',('truss.'+name,)).fetchone()
                        cols=self.admin.execute('SELECT attname,attnum,atttypid,atttypmod,attnotnull,attcollation,attgenerated,attidentity FROM pg_catalog.pg_attribute WHERE attrelid=%s AND attnum>0 AND NOT attisdropped ORDER BY attnum',(oid,)).fetchall()
                        new_facts.append(_FactRelationComparison('truss',name,oid,owner,source.split('AS $$',1)[1].split('$$;',1)[0],tuple(_FactColumnComparison(*c) for c in cols)))
                    from truss._security_catalog_source_binding import derive_catalog_source_epoch_profile
                    from truss._psycopg_epoch_cut import _EpochComparison
                    new_profile=derive_catalog_source_epoch_profile(graph,tuple(new_facts),infrastructure.value.barrier,subject_source=inputs['subject_source'])
                    new_epoch=self.admin.execute('SELECT truss.runtime_issue_source_epoch(%s,%s,%s,%s,%s)',(comparison.installation,advanced_epoch,comparison.incarnation,new_profile,comparison.evidence)).fetchone()[0]
                    composed_context=replace(context,comparison=_EpochComparison(comparison.installation,new_epoch,comparison.incarnation,new_profile,comparison.evidence))
                    if guarded_binary:
                        from truss._security_guarded_source import capture_guarded_source_comparison
                        guarded_source=capture_guarded_source_comparison(graph.native_dependencies,graph.guarded_response)
                    composed=[]
                    for name,expected in (('Alice',[]),('Bob',['RB']),('Outsider',[]),*((('AliceGuarded',[]),('OutsiderGuarded',[]),('BobGuarded',['RB']),('BobGuardedId',['RB']),('BobGuardedCorrupt',None),('BobGuardedReceiptSwap',None)) if guarded_binary else ()),('BobMapColumnWrite',None),('BobProfileColumnWrite',None),('BobProfilePublicWrite',None),('AliceInheritedWrite',None),('BobPrivilegedRoles',['RB']),('AliceOtherRole',None),('BobSetRole',None),('BobOldSnapshot',None),('BobRevoked',[]),('BobReactivated',['RB']),('BobStreaming',None),('BobProfileDrift',None),('BobProfileRestored',['RB']),('BobPublicIssuer',None)):
                        if name in ('BobMapColumnWrite','BobProfileColumnWrite'):
                            writable_home,writable_column=('catalog_subject_map','staff_key') if name=='BobMapColumnWrite' else ('catalog_graph_subject_profile','profile_bytes')
                            self.admin.execute(sql.SQL('GRANT UPDATE({}) ON {} TO {}').format(sql.Identifier(writable_column),sql.Identifier('truss',writable_home),sql.Identifier(roles['Bob'])))
                        if name=='AliceInheritedWrite':
                            inherited_writer=private_executor+'_w'
                            self.admin.execute(sql.SQL('CREATE ROLE {} NOLOGIN').format(sql.Identifier(inherited_writer)))
                            self.admin.execute(sql.SQL('GRANT UPDATE(profile_bytes) ON truss.catalog_graph_subject_profile TO {}').format(sql.Identifier(inherited_writer)))
                            self.admin.execute(sql.SQL('GRANT {} TO {}').format(sql.Identifier(inherited_writer),sql.Identifier(roles['Alice'])))
                        if name=='BobProfilePublicWrite':self.admin.execute('GRANT UPDATE(profile_bytes) ON truss.catalog_graph_subject_profile TO PUBLIC')
                        if name=='AliceOtherRole':self.admin.execute(sql.SQL('GRANT {} TO {}').format(sql.Identifier(roles['Bob']),sql.Identifier(roles['Alice'])))
                        if name=='BobProfileDrift':self.admin.execute("UPDATE truss.catalog_graph_subject_profile SET document_revision='tampered'")
                        if name=='BobPublicIssuer':self.admin.execute('GRANT EXECUTE ON FUNCTION truss.graph_subject_current() TO PUBLIC')
                        with psycopg.connect(**private_parameters,autocommit=True,options='-c statement_timeout=10000') as private:
                            private.execute('BEGIN');executor=adopt_psycopg_host(private,statement_timeout_ms=10000,operation_timeout_ms=30000);executor_tx=executor.adopt_transaction().value
                            parameters=psycopg.conninfo.conninfo_to_dict(self.info.connection_uri);parameters['user']=roles['Alice' if name in ('AliceGuarded','AliceOtherRole','AliceInheritedWrite') else 'Outsider' if name=='OutsiderGuarded' else 'Bob' if name in ('BobPublicIssuer','BobMapColumnWrite','BobProfileColumnWrite','BobProfilePublicWrite','BobPrivilegedRoles','AliceOtherRole','BobSetRole','BobOldSnapshot','BobRevoked','BobReactivated','BobStreaming','BobProfileDrift','BobProfileRestored','BobGuarded','BobGuardedId','BobGuardedCorrupt','BobGuardedReceiptSwap') else name]
                            with psycopg.connect(**parameters,autocommit=True,options='-c statement_timeout=10000') as connection:
                                connection.execute('BEGIN ISOLATION LEVEL REPEATABLE READ' if name=='BobOldSnapshot' else 'BEGIN');caller=adopt_psycopg_host(connection,statement_timeout_ms=10000,operation_timeout_ms=30000);caller_tx=caller.adopt_transaction(isolation='repeatable_read' if name=='BobOldSnapshot' else 'read_committed').value;released=[]
                                if name=='AliceInheritedWrite':self.assertEqual(connection.execute("SELECT pg_catalog.has_any_column_privilege(CURRENT_USER,'truss.catalog_graph_subject_profile','UPDATE')").fetchone(),(True,))
                                if name=='BobPrivilegedRoles':
                                    for statement in ("UPDATE truss.catalog_subject_map SET staff_key='Outsider'","UPDATE truss.catalog_graph_subject_profile SET profile_bytes=pg_catalog.decode('00','hex')"):
                                        connection.execute('SAVEPOINT denied_subject_write')
                                        with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute(statement)
                                        connection.execute('ROLLBACK TO SAVEPOINT denied_subject_write');connection.execute('RELEASE SAVEPOINT denied_subject_write')
                                    for forbidden_role in (self.installation.owner_role,private_executor):
                                        for setter in ('SET LOCAL ROLE {}','SET LOCAL SESSION AUTHORIZATION {}'):
                                            connection.execute('SAVEPOINT denied_role')
                                            with self.assertRaises(psycopg.errors.InsufficientPrivilege):connection.execute(sql.SQL(setter).format(sql.Identifier(forbidden_role)))
                                            connection.execute('ROLLBACK TO SAVEPOINT denied_role');connection.execute('RELEASE SAVEPOINT denied_role')
                                            self.assertEqual(connection.execute("SELECT SESSION_USER::text,CURRENT_USER::text,pg_catalog.current_setting('role')").fetchone(),(roles['Bob'],roles['Bob'],'none'))
                                if name=='AliceOtherRole':
                                    connection.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(roles['Bob'])))
                                    self.assertEqual(connection.execute('SELECT SESSION_USER::text,CURRENT_USER::text').fetchone(),(roles['Alice'],roles['Bob']))
                                if name=='BobSetRole':
                                    connection.execute('SET LOCAL ROLE '+sql.Identifier(roles['Bob']).as_string(connection))
                                if name=='BobOldSnapshot':
                                    old_snapshot=connection.execute('SELECT pg_catalog.txid_current_snapshot()::pg_catalog.text').fetchone()[0]
                                    self.assertIsInstance(old_snapshot,str)
                                    self.admin.execute("UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s,'value'],'false'::pg_catalog.jsonb) WHERE id=%s",(active_property,identities['ba']))
                                    self.assertEqual(self.admin.execute("SELECT props->%s->>'value' FROM truss.object WHERE id=%s",(active_property,identities['ba'])).fetchone(),('false',))
                                def receiver(raw):
                                    with psycopg.connect(self.info.connection_uri,autocommit=True,options='-c lock_timeout=100ms') as writer:
                                        for table in ('catalog_subject_map','catalog_graph_subject_profile'):
                                            with self.assertRaises(psycopg.errors.LockNotAvailable):writer.execute(sql.SQL('DELETE FROM {} WHERE false').format(sql.Identifier('truss',table)))
                                    released.append(raw)
                                is_guarded_query=name.endswith('Guarded') or name.startswith('BobGuarded') or (name=='BobRevoked' and guarded_binary is not None)
                                selected_compiler=prepare_owned_graph_compiler(guarded_binary,str(Path(guarded_binary).with_name('security_guarded_result')),guarded=True,query_sql=('SELECT q.resourceId FROM Resource q' if name=='BobGuardedId' else 'SELECT q.resourceId, q.salary FROM Resource q'),source_comparison=guarded_source) if is_guarded_query else native_compiler
                                relational_binary=os.environ.get('TRUSS_SECURITY_RELATIONAL_COMPILER_BINARY')
                                if relational_binary and name in ('AliceGuarded','OutsiderGuarded','BobGuarded'):
                                    prior_compiler=selected_compiler
                                    def capture_then_direct(cursor,physical,before,subject,semantic):
                                        from security_ontology_compiled_read import _original_request
                                        from security_relational_capture import execute_relational_program
                                        from security_relational_codecs import prepare_owned_relational_codec_checker
                                        from truss._security_guarded_source import capture_guarded_source_comparison
                                        from truss._security_relational_source import capture_relational_source_comparison
                                        relational_request=_original_request(physical,before[0],"SELECT r.resourceId FROM Resource r WHERE r.resourceId = 'never'")
                                        produced=original_run([relational_binary],input=relational_request,capture_output=True,check=True,timeout=15).stdout
                                        self.assertEqual(capture_relational_source_comparison(relational_request,produced),guarded_source)
                                        inventory=json.loads(before[0])['inventory']
                                        staff_type=next(t['type_id'] for t in inventory['types'] if t['element']=='Staff' and t['retired_rev'] is None)
                                        staff_prop=next(p['prop_id'] for p in inventory['properties'] if p['type_id']==staff_type and p['element']=='staffId' and p['retired_rev'] is None)
                                        locators=[int(oid) for oid,tid,raw,root in before[1] if tid==str(staff_type) and root=='false' and json.loads(raw).get(str(staff_prop))=={'kind':'string','text':subject}]
                                        self.assertEqual(len(locators),1)
                                        checker=prepare_owned_relational_codec_checker(Path(relational_binary).with_name('security_postgresql_codecs'))
                                        from security_relational_inspection import prepare_owned_relational_inspector
                                        inspector=prepare_owned_relational_inspector(Path(relational_binary).with_name('security_relational_result'))
                                        relational_result=execute_relational_program(cursor,relational_request,produced,locators[0],checker,inspector)
                                        self.assertEqual(json.loads(relational_result['batch'])['rows'],[])
                                        captured=relational_result['operandBatch']
                                        scans=json.loads(captured)['scans'];self.assertEqual(len(scans),1)
                                        self.assertEqual(len(scans[0]['rows']),len(semantic['rows']))
                                        self.assertEqual(len(scans[0]['rows']),1 if subject=='Bob' else 0)
                                        self.assertEqual({r['nativeRowId'] for r in scans[0]['rows']},{str(identities['rb'])} if subject=='Bob' else set())
                                        matching_request=_original_request(physical,before[0],"SELECT r.resourceId FROM Resource r WHERE r.resourceId = 'RB'")
                                        matching_output=original_run([relational_binary],input=matching_request,capture_output=True,check=True,timeout=15).stdout
                                        self.assertEqual(capture_relational_source_comparison(matching_request,matching_output),guarded_source)
                                        matching=execute_relational_program(cursor,matching_request,matching_output,locators[0],checker,inspector)
                                        expected_cells=[[{'outcomeId':'original','disposition':'original','value':{'string':'RB'}}]] if subject=='Bob' else []
                                        self.assertEqual(json.loads(matching['batch'])['rows'],expected_cells)
                                        count_request=_original_request(physical,before[0],'SELECT COUNT(*) AS n FROM Resource r')
                                        count_output=original_run([relational_binary],input=count_request,capture_output=True,check=True,timeout=15).stdout
                                        self.assertEqual(capture_relational_source_comparison(count_request,count_output),guarded_source)
                                        counted=execute_relational_program(cursor,count_request,count_output,locators[0],checker,inspector)
                                        count_cells=json.loads(counted['batch'])['rows']
                                        self.assertEqual(count_cells,[[{'outcomeId':'computed','disposition':'computed','value':{'integerToken':str(len(semantic['rows']))}}]])
                                        return {'request':matching_request.decode(),'output':matching_output.decode(),'operandBatch':matching['operandBatch'].decode(),'batch':matching['batch'].decode(),'resultCheck':matching['inspection'].decode()}
                                    selected_compiler=capture_then_direct
                                if name=='BobGuardedReceiptSwap':
                                    original_selected_compiler=selected_compiler
                                    def swapped_receipt(*args):
                                        receipt=original_selected_compiler(*args)
                                        batch=json.loads(receipt['batch'])
                                        batch['rows'][0][0]['value']={'string':'RA'}
                                        receipt['batch']=json.dumps(batch,separators=(',',':'))
                                        return receipt
                                    selected_compiler=swapped_receipt
                                corruption=[]
                                def corrupt_guarded_check(*args,**kwargs):
                                    if args[0][0]==str(Path(guarded_binary).with_name('security_guarded_result')):
                                        checker_input=json.loads(kwargs['input']);batch=json.loads(checker_input['batchJson'])
                                        self.assertEqual(batch['rows'][0][1],{'outcomeId':'withheld','disposition':'withheld'})
                                        batch['rows'][0][1]['value']={'integerToken':'200'}
                                        checker_input['batchJson']=json.dumps(batch);kwargs['input']=json.dumps(checker_input).encode();corruption.append(True)
                                    return original_run(*args,**kwargs)
                                from contextlib import nullcontext
                                with patch.object(guarded.subprocess,'run',corrupt_guarded_check) if name=='BobGuardedCorrupt' else nullcontext():
                                    if name=='BobStreaming':
                                        def streaming_receiver(raw):
                                            released.append(raw)
                                            yield raw
                                        with self.assertRaisesRegex(ValueError,'Original synchronous private publisher required'):
                                            native_read.publish_native_ontology_resource_read(caller,caller_tx,executor,executor_tx,request,subjects.bindings,streaming_receiver,compiler=selected_compiler,cut_issuer=cut_issuer,source_epoch=composed_context,subject_registration=subjects)
                                        self.assertEqual(released,[])
                                        for session in (private,connection):self.assertEqual(session.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,))
                                        caller.detach();connection.rollback();executor.detach();private.rollback()
                                        composed.append({'principal':name,'outcome':'streamingRefusedBeforeOutput','released':False,'noRetainedCuts':True})
                                        continue
                                    result=native_read.publish_native_ontology_resource_read(caller,caller_tx,executor,executor_tx,request,subjects.bindings,receiver,compiler=selected_compiler,cut_issuer=cut_issuer,source_epoch=composed_context,subject_registration=subjects,query_results=is_guarded_query)
                                if expected is None:
                                    self.assertIsInstance(result,Error);self.assertEqual(released,[])
                                    if name in ('AliceOtherRole','BobSetRole'):
                                        for session in (private,connection):self.assertEqual(session.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,))
                                    elif name=='BobOldSnapshot':
                                        self.assertEqual(str(caller._custody.last_attempt.error),'Original fresh native ontology caller transaction required')
                                        for session in (private,connection):self.assertEqual(session.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,))
                                    elif name in ('BobMapColumnWrite','BobProfileColumnWrite','BobProfilePublicWrite','AliceInheritedWrite'):self.assertEqual(str(executor._custody.last_attempt.error),'Unmediated registered Subject writes refused')
                                    elif name=='BobGuardedReceiptSwap':self.assertEqual(str(executor._custody.last_attempt.error),'Original inspected query publication correspondence required')
                                    elif name!='BobProfileDrift':self.assertEqual(str(executor._custody.last_attempt.error),'Original graph compiler result contract refused' if name=='BobGuardedCorrupt' else 'Exact registered graph Subject issuer ACL required')
                                    if name=='BobProfileDrift':
                                        for session in (private,connection):self.assertEqual(session.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,))
                                    if name in ('BobGuardedCorrupt','BobGuardedReceiptSwap'):
                                        if name=='BobGuardedCorrupt':self.assertEqual(corruption,[True])
                                        for session in (private,connection):self.assertEqual(session.execute("SELECT count(*) FROM pg_catalog.pg_locks WHERE pid=pg_catalog.pg_backend_pid() AND mode='ShareLock' AND granted").fetchone(),(0,))
                                else:
                                    self.assertIsInstance(result,Ok,str(executor._custody.last_attempt.error));self.assertEqual(released,[result.value])
                                    if is_guarded_query:
                                        published=json.loads(result.value);self.assertEqual(published['version'],'truss.guarded-query-result/0.2-candidate' if relational_binary and name in ('AliceGuarded','OutsiderGuarded','BobGuarded') else 'truss.guarded-query-result/0.1-candidate')
                                        cells=json.loads(published['batchJson']);contract=json.loads(published['resultContractJson'])
                                        self.assertEqual(len(contract['columns']),1 if name=='BobGuardedId' or relational_binary and name in ('AliceGuarded','OutsiderGuarded','BobGuarded') else 2)
                                        expected_cells=[{'outcomeId':'original','disposition':'original','value':{'string':'RB'}}]
                                        if name=='BobGuarded' and not relational_binary:expected_cells.append({'outcomeId':'withheld','disposition':'withheld'})
                                        self.assertEqual(cells['rows'],[expected_cells] if expected else [])
                                    else:self.assertEqual([r['key'][0]['string'] for r in json.loads(result.value)['rows']],expected)
                                caller.detach();connection.rollback()
                            executor.detach();private.rollback()
                        if name in ('BobMapColumnWrite','BobProfileColumnWrite'):self.admin.execute(sql.SQL('REVOKE UPDATE({}) ON {} FROM {}').format(sql.Identifier(writable_column),sql.Identifier('truss',writable_home),sql.Identifier(roles['Bob'])))
                        if name=='AliceInheritedWrite':
                            self.admin.execute(sql.SQL('REVOKE {} FROM {}').format(sql.Identifier(inherited_writer),sql.Identifier(roles['Alice'])))
                            self.admin.execute(sql.SQL('REVOKE UPDATE(profile_bytes) ON truss.catalog_graph_subject_profile FROM {}').format(sql.Identifier(inherited_writer)))
                            self.admin.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(inherited_writer)))
                        if name=='BobProfilePublicWrite':self.admin.execute('REVOKE UPDATE(profile_bytes) ON truss.catalog_graph_subject_profile FROM PUBLIC')
                        if name=='AliceOtherRole':self.admin.execute(sql.SQL('REVOKE {} FROM {}').format(sql.Identifier(roles['Bob']),sql.Identifier(roles['Alice'])))
                        if name=='BobRevoked':self.admin.execute("UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s,'value'],'true'::pg_catalog.jsonb) WHERE id=%s",(active_property,identities['ba']))
                        if name=='BobProfileDrift':
                            document_revision=json.loads(graph.native_dependencies)['bindingJson']
                            document_revision=json.loads(document_revision)['physicalModule']['pin']['revision']
                            self.admin.execute('UPDATE truss.catalog_graph_subject_profile SET document_revision=%s',(document_revision,))
                        if name=='BobPublicIssuer':self.admin.execute('REVOKE EXECUTE ON FUNCTION truss.graph_subject_current() FROM PUBLIC')
                        composed.append({'principal':name,'outcome':('subjectWriteGrantRefused' if name in ('BobMapColumnWrite','BobProfileColumnWrite','BobProfilePublicWrite','AliceInheritedWrite') else 'otherPrincipalRoleRefused' if name=='AliceOtherRole' else 'setRoleRefused' if name=='BobSetRole' else 'oldSnapshotRefusedAfterRevocationAck' if name=='BobOldSnapshot' else 'inspectedBatchSubstitutionRefused' if name=='BobGuardedReceiptSwap' else 'guardedResultRefused' if name=='BobGuardedCorrupt' else 'subjectProfileRefused' if name=='BobProfileDrift' else 'issuerAclRefused'),'released':False} if expected is None else {'principal':name,'resources':expected,'queryCellsPublished':is_guarded_query,'ownSessionIssuerAndCurrentEpoch':True,'subjectProfileAndMapCutsThroughReceiver':True})
                    directory=os.environ.get('TRUSS_SECURITY_ONTOLOGY_SUBJECT_COMPOSITION_EVIDENCE')
                    if directory:
                        folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
                        (folder/'registered-subject-protected-read.json').write_text(json.dumps({'observations':composed,'epoch':new_epoch,'securityReady':False,'scope':'Actual own-session registered Subject + peer/role/source/fact/current epoch/compiler/result guarded buffered reads; complete native admission/lifetime and all132 remain pending.'},indent=2)+'\n')
