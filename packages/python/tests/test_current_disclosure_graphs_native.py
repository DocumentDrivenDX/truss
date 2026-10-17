"""Actual public population and native projection; source wrapper is diagnostic only.

No registration/native binding/authenticated protected release admission. The
source-provider substitution is explicit and does not stand in for those gates.
"""
import base64,copy,json,hashlib,struct,time,os,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import psycopg
from truss import Ok
from truss.contracts import MapValue,TextValue,BooleanValue,NullValue
from truss.groups import CreateObject,CreateEdge,RootlessOwnership,AuthoredValue,AliasObjectReference,StoredObjectReference,NullOrderKey,GroupSuccess
from truss._current_disclosure_facts import capture_current_disclosure_facts_with_cursor,verify_current_disclosure_capture_with_cursor
from truss._current_query_pipe import CurrentQueryPipe
from truss._security_catalog_assessment import capture_accepted_catalog
import test_group_create_native as base

PACKETS=json.loads((Path(__file__).parent/'fixtures/current-disclosure/native-graph-capture.json').read_bytes())
BUNDLE_SHA256='548b7ff64dabf3bc796afe99ecca265f5bcf242202e367ba7125e62c64f0a735'
_ENABLED=os.environ.get('TRUSS_GRAPH_CAPTURE_NATIVE_QUALIFICATION')=='1' and bool(os.environ.get('TRUSS_GRAPH_CAPTURE_UMF_CHILD'))
wire=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=True).encode()

def native_literal(value):
    """Fixture transport to public carriers; no domain or permission evaluator."""
    if value is None:return NullValue()
    if set(value)=={'boolean'}:return BooleanValue(value=value['boolean'])
    for member,kind in [('string','string'),('integerToken','integer'),('decimalToken','decimal')]:
        if set(value)=={member}:return TextValue(kind=kind,text=value[member])
    if set(value)=={'binaryHex'}:return TextValue(kind='binary',text=base64.b64encode(bytes.fromhex(value['binaryHex'])).decode())
    raise ValueError('Unsupported fixture literal')

class Deadline:
    def __init__(self):self.end=time.monotonic()+90
    def check(self):
        if time.monotonic()>self.end:raise TimeoutError('Native graph experiment deadline')
class NativeCursor:
    def __init__(self,connection):self.cursor=connection.cursor();self._deadline=Deadline()
    def execute(self,*args,**kwargs):self._deadline.check();return self.cursor.execute(*args,**kwargs)
    def fetchmany(self,n):self._deadline.check();return self.cursor.fetchmany(n)
    @property
    def description(self):return self.cursor.description

@unittest.skipUnless(_ENABLED,'requires explicit isolated graph native campaign and exact UMF child bundle')
class NativeGraphCaptureTests(base.PublicCreateGroupTests):
    for name in tuple(n for n in dir(base.PublicCreateGroupTests) if n.startswith('test_')):locals()[name]=None
    def test_actual_public_graph_capture_and_original_held_semantics(self):self._run_population(False)
    def test_actual_public_parallel_graph_and_original_held_semantics(self):self._run_population(True)
    def _create_public_population(self,parallel):
        bundle=Path(os.environ['TRUSS_GRAPH_CAPTURE_UMF_CHILD'])
        self.assertEqual(hashlib.sha256(bundle.read_bytes()).hexdigest(),BUNDLE_SHA256)
        output=Path(os.environ.get('TRUSS_GRAPH_CAPTURE_EVIDENCE',str(self.root/'evidence')));output.mkdir(parents=True,exist_ok=True)
        initial=copy.deepcopy(PACKETS['initialize']);document=initial['sources']['closure']['documents'][0]['document']
        def source(old):old.clear();old.update(copy.deepcopy(document))
        c,h,a,t=self.ready(source,document_ids=('adoc',))
        facts=PACKETS['packets'][0]['cut']['facts'];graphs=PACKETS['packets'][0]['cut']['graphs']
        aliases={};operations=[];field_names={x['id']:x['name'] for x in document['modules'][0]['elements'] if x['kind']=='field'}
        for i,fact in enumerate(facts):
            name=fact['type']['elementId'];alias='n'+str(i);aliases[(name,json.dumps(fact['key'],sort_keys=True))]=alias
            values=[]
            for cell in fact['fields']:
                literal=native_literal(cell['value'])
                values.append(AuthoredValue(name=field_names[cell['field']['elementId']],value=literal))
            operations.append(CreateObject(type_definition_pin=self.types[('adoc',name)].definition_pin,values=tuple(values),ownership=RootlessOwnership(),alias=alias))
        declarations={r['id']:r for r in document['modules'][0]['relationships']};refs={name:a.get_relationship_reference_in_transaction(t,document_id='adoc',module_id='m',relationship_id=name).value for name in declarations}
        expected_incidence=[]
        for graph in graphs:
            name=graph['relationship']['relationshipId'];decl=declarations[name];ends={e['role']:e['key'] for e in graph['endpoints']}
            src=aliases[(decl['source'][0]['element'],json.dumps(ends['source'],sort_keys=True))];dst=aliases[(decl['target'][0]['element'],json.dumps(ends['target'],sort_keys=True))]
            operations.append(CreateEdge(relationship_definition_pin=refs[name].definition_pin,source=AliasObjectReference(alias=src),target=AliasObjectReference(alias=dst),values=(),order_key=NullOrderKey()))
            expected_incidence.append((name,src,dst))
        context=a.group_context_in_transaction(t).value;result=self.apply(a,t,context.input(tuple(operations),MapValue(entries=())),context.request('graph-capture-native'))
        self.assertIsInstance(result,GroupSuccess);identities={x.alias:x.identity for x in result.response.semantic.aliases};h.detach();c.commit()
        if parallel:
            c,h,a,t=self.consumer();name,src,dst=next(x for x in expected_incidence if x[0]=='StaffAssignment')
            context=a.group_context_in_transaction(t).value
            edge=CreateEdge(relationship_definition_pin=refs[name].definition_pin,source=StoredObjectReference(identity=identities[src]),target=StoredObjectReference(identity=identities[dst]),values=(),order_key=NullOrderKey())
            duplicate=self.apply(a,t,context.input((edge,),MapValue(entries=())),context.request('graph-parallel-native'))
            self.assertIsInstance(duplicate,GroupSuccess);expected_incidence.append((name,src,dst));h.detach();c.commit()
        case='parallel' if parallel else 'base'
        original_document=self.documents[0];raw=original_document.content
        request=wire({'modules':[{'pin':{'documentId':'adoc','revision':original_document.document_revision,'umfVersion':'0.8.0','sha256':hashlib.sha256(raw).hexdigest()},'documentJson':raw.decode()}]})
        # The semantic closure must retain exact accepted revision and document.
        initial['sources']['closure']={'pins':[{'documentId':'adoc','revision':original_document.document_revision}],'documents':[{'revision':original_document.document_revision,'document':json.loads(raw)}]}
        initial['sources']['ontology']['documents']=[{'documentId':'adoc','revision':original_document.document_revision}]
        return initial,request,case,output,refs,identities,expected_incidence,bundle

    def _run_population(self,parallel):
        initial,request,case,output,refs,identities,expected_incidence,bundle=self._create_public_population(parallel)
        self.admin.execute('BEGIN')
        from truss._security_catalog_assessment import SOURCE_TABLES
        self.admin.execute('LOCK TABLE '+','.join('ONLY truss.'+name for name in SOURCE_TABLES)+' IN SHARE MODE NOWAIT')
        cursor=NativeCursor(self.admin)
        assessment=capture_accepted_catalog(cursor,request)
        supplied=SimpleNamespace(source_profile='truss-current-disclosure-sources/0.1-candidate',initialize_bytes=wire(initial),accepted_request_bytes=request,accepted_assessment_bytes=assessment)
        with patch('truss._current_disclosure_facts.capture_current_query_sources_with_cursor',return_value=supplied):captured=capture_current_disclosure_facts_with_cursor(cursor,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        self.assertEqual(len(json.loads(captured.facts_bytes)),14);self.assertEqual(len(captured.graph_rows),13 if parallel else 12);self.assertEqual(len(json.loads(captured.graph_coverage_bytes)),5)
        self.assertEqual(len(captured.rows),14)
        evidence=output/('native-inputs-'+case);evidence.mkdir(exist_ok=True)
        for name,data in [('accepted-request.json',request),('assessment.json',assessment),('initialize.json',wire(initial)),('facts.json',captured.facts_bytes),('coverage.json',captured.coverage_bytes),('graphs.json',captured.graphs_bytes),('graph-coverage.json',captured.graph_coverage_bytes)]:
            (evidence/name).write_bytes(data)
        (evidence/'native-locators.json').write_bytes(wire({'objects':[[*r[:3],*[b.hex() for b in r[3:]]] for r in captured.rows],'edges':captured.graph_rows}))
        actual=self.admin.execute('SELECT rel_type_id::text,source_id::text,target_id::text FROM truss.edge ORDER BY id').fetchall()
        self.assertEqual(actual,[(refs[n].relationship_id,identities[s].id,identities[d].id) for n,s,d in expected_incidence])
        lock_observations=[]
        def require_external_exclusion(stage):
            with psycopg.connect(self.info.connection_uri,autocommit=True) as writer:
                for name in ('object','object_key_bucket','edge'):
                    with self.assertRaises(psycopg.errors.LockNotAvailable):
                        with writer.transaction():writer.execute('LOCK TABLE ONLY truss.'+name+' IN ROW EXCLUSIVE MODE NOWAIT')
            lock_observations.append(stage)
        require_external_exclusion('captured')
        closing_observations=[]
        def require_closing(stage):
            with patch('truss._current_disclosure_facts.capture_current_query_sources_with_cursor',return_value=supplied):
                verify_current_disclosure_capture_with_cursor(cursor,captured,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
            closing_observations.append(stage)
        require_closing('original-capture')
        assignment_rows=[r for r in captured.graph_rows if r[1]==refs['StaffAssignment'].relationship_id]
        self.assertGreaterEqual(len(assignment_rows),2)
        native_inventory=json.loads(assessment)['inventory']
        active=next(p for p in native_inventory['properties'] if p['element']=='active' and p['retired_rev'] is None)
        assignment=next(r for r in captured.rows if r[1]==str(active['type_id']))
        mutations=[
            ('edge-deletion','DELETE FROM truss.edge WHERE id=%s',(captured.graph_rows[0][0],)),
            ('edge-version','UPDATE truss.edge SET ver=ver+1 WHERE id=%s',(captured.graph_rows[0][0],)),
            ('typed-endpoint','UPDATE truss.edge SET target_id=%s WHERE id=%s',(assignment_rows[1][5],assignment_rows[0][0])),
            ('object-version','UPDATE truss.object SET ver=ver+1 WHERE id=%s',(captured.rows[0][0],)),
            ('non-key-value',"UPDATE truss.object SET props=pg_catalog.jsonb_set(props,ARRAY[%s,'value'],pg_catalog.to_jsonb(NOT ((props->%s->>'value')::boolean))) WHERE id=%s",(str(active['prop_id']),str(active['prop_id']),assignment[0])),
        ]
        for label,statement,parameters in mutations:
            self.admin.execute('SAVEPOINT closing_population_control')
            self.admin.execute(statement,parameters)
            with patch('truss._current_disclosure_facts.capture_current_query_sources_with_cursor',return_value=supplied):
                with self.subTest(closing=label),self.assertRaisesRegex(ValueError,'changed before closing'):
                    verify_current_disclosure_capture_with_cursor(cursor,captured,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
            self.admin.execute('ROLLBACK TO SAVEPOINT closing_population_control')
            self.admin.execute('RELEASE SAVEPOINT closing_population_control')
            require_closing(label+':restored')
        # Native home refusal and complete empty graph coverage are separate
        # diagnostic savepoint controls; no altered bytes leave this experiment.
        self.admin.execute('SAVEPOINT graph_home_control')
        self.admin.execute('ALTER TABLE truss.edge ENABLE ROW LEVEL SECURITY')
        with patch('truss._current_disclosure_facts.capture_current_query_sources_with_cursor',return_value=supplied):
            with self.assertRaisesRegex(ValueError,'unfiltered native graph home'):capture_current_disclosure_facts_with_cursor(cursor,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        self.admin.execute('ROLLBACK TO SAVEPOINT graph_home_control')
        self.admin.execute('RELEASE SAVEPOINT graph_home_control')
        self.admin.execute('SAVEPOINT graph_empty_control')
        self.admin.execute('DELETE FROM truss.edge')
        with patch('truss._current_disclosure_facts.capture_current_query_sources_with_cursor',return_value=supplied):empty=capture_current_disclosure_facts_with_cursor(cursor,bun_executable=os.environ['TRUSS_BUN_EXECUTABLE'])
        self.assertEqual(empty.graphs_bytes,b'[]');self.assertEqual(len(json.loads(empty.graph_coverage_bytes)),5);self.assertNotEqual(empty.graphs_bytes,captured.graphs_bytes)
        self.admin.execute('ROLLBACK TO SAVEPOINT graph_empty_control');self.admin.execute('RELEASE SAVEPOINT graph_empty_control')
        observations=[]
        for staff,expected in [('Alice',['RA']),('Bob',['RB']),('Outsider',[])]:
            cut=copy.deepcopy(PACKETS['packets'][0]['cut']);cut.update(facts=json.loads(captured.facts_bytes),coverage=json.loads(captured.coverage_bytes),graphs=json.loads(captured.graphs_bytes),graphCoverage=json.loads(captured.graph_coverage_bytes),domains=initial['sources']['closure']['pins']);cut['subject']['key']=[{'string':staff}]
            (evidence/(staff+'-cut.json')).write_bytes(wire(cut))
            initial_raw=wire(initial);receipt=hashlib.sha256(struct.pack('>I',len(initial_raw))+initial_raw).hexdigest()
            with CurrentQueryPipe((os.environ['TRUSS_BUN_EXECUTABLE'],str(bundle)),timeout_seconds=20) as child:
                require_external_exclusion(staff+':initialize')
                init=json.loads(child.exchange(initial_raw,source_receipt=receipt));self.assertEqual(init['kind'],'initialized')
                result=json.loads(child.exchange(wire({'version':initial['version'],'kind':'evaluate-disclosure','requestId':'evaluate','sourceReceipt':receipt,'cut':cut}),source_receipt=receipt))
                self.assertEqual(result['kind'],'disclosure-evaluated');decision=result['result'];self.assertEqual(decision['status'],'rendered')
                self.assertEqual([r['key'][0]['string'] for r in decision['resources']],expected)
                require_external_exclusion(staff+':inspection')
                inspected=json.loads(child.exchange(wire({'version':initial['version'],'kind':'inspect-native-disclosure','requestId':'inspect','sourceReceipt':receipt,'batch':decision['batch']}),source_receipt=receipt));self.assertEqual(inspected['kind'],'native-disclosure-inspected')
            self.assertTrue(child._cleanup_complete)
            require_closing(staff+':after-original-inspection')
            observations.append({'subject':staff,'expected':expected,'decision':decision,'inspection':inspected})
        (output/('native-graph-capture-'+case+'-result.json')).write_bytes(wire({'scope':'Actual public population, native fact/key/graph projection and original held UMF semantics; substituted source wrapper is diagnostic, no source admission/current authority/guarded release or case promotion.','bundleSha256':BUNDLE_SHA256,'case':case,'serverVersion':self.admin.info.server_version,'serverBuild':self.admin.execute('SELECT version()').fetchone()[0],'facts':len(captured.rows),'graphs':len(captured.graph_rows),'heldFactLockChecks':lock_observations,'closingCaptureChecks':closing_observations,'closingMutationRefusals':[m[0] for m in mutations],'nativeControls':['edge-RLS-refusal','complete-empty-coverage','own-mutation-changes-recapture','savepoint-restoration'],'sourceAssessmentSha256':hashlib.sha256(assessment).hexdigest(),'observations':observations}))
        self.admin.rollback()
