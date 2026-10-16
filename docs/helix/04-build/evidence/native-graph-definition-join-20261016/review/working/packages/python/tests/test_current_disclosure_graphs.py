"""Physical mapping controls; supplied catalog/cursor fixtures are not native evidence."""
import copy,hashlib,itertools,json,unittest
from types import SimpleNamespace
from truss._current_disclosure_facts import _graph_recipes,_capture_graphs

ref=lambda name:{'documentId':'d','moduleId':'m','elementId':name}
relationship={'documentId':'d','moduleId':'m','relationshipId':'WorksOn'}

def fixture():
    core={'umf':'0.8.0','id':'d','modules':[{'id':'m','elements':[], 'relationships':[{'id':'WorksOn','directed':True,'source':[{'module':'m','element':'Staff'}],'target':[{'module':'m','element':'Project','key':'pk'}],'sourceMultiplicity':{'min':0,'max':'*'},'targetMultiplicity':{'min':0,'max':'*'},'targetLifecycle':'independent'}]}]}
    encoded=json.dumps(core,separators=(',',':'));pin={'documentId':'d','revision':'1','umfVersion':'0.8.0','sha256':hashlib.sha256(encoded.encode()).hexdigest()}
    association={'kind':'core-relationship','relationship':relationship,'witness':{'kind':'opaque-existential'},'endpoints':[{'role':'worker','side':'source','target':ref('Staff'),'keyId':'pk'},{'role':'project','side':'target','target':ref('Project'),'keyId':'pk'}]}
    ontology={'entities':[{'type':ref(name),'keyId':'pk'} for name in ('Staff','Project')],'associations':[association]}
    source={'ontology':ontology,'closure':{'pins':[{'documentId':'d','revision':'1'}],'documents':[{'revision':'1','document':core}]}}
    native={'document_id':'d','module':'m','rel_id':'WorksOn','rel_type_id':31,'retired_rev':None,'directed':True,'assoc_type_id':None,'source_min':0,'source_max':None,'target_min':0,'target_max':None,'lifecycle':'independent','composition':False,'inverse':None,'target_key':'pk'}
    inventory={'relationships':[native],'endpoints':[{'rel_type_id':31,'source_type':11,'target_type':12}]}
    sources=SimpleNamespace(initialize_bytes=json.dumps({'kind':'initialize','requestId':'initialize','sources':source}).encode(),accepted_request_bytes=json.dumps({'modules':[{'pin':pin,'documentJson':encoded}]}).encode(),accepted_assessment_bytes=json.dumps({'inventory':inventory}).encode())
    records=[(11,ref('Staff'),[],{'key_id':'pk'},b''),(12,ref('Project'),[],{'key_id':'pk'},b'')]
    facts=[{'type':ref('Staff'),'key':[{'string':'Alice'}]},{'type':ref('Project'),'key':[{'string':'A'}]},{'type':ref('Project'),'key':[{'string':'B'}]}]
    private=[('1','11','1',b'',b'',b''),('2','12','1',b'',b'',b''),('3','12','1',b'',b'',b'')]
    return sources,records,facts,private

class Cursor:
    def __init__(self,rows=()):self.rows=list(rows);self.queries=[];self.home=[('r','p','false','false','true','false')];self.count=len(rows);self.props='false';self._deadline=SimpleNamespace(check=lambda:None)
    def execute(self,sql,parameters=(),**kwargs):
        self.queries.append((sql,parameters));self.description=[SimpleNamespace(type_code=25)]
        if sql.startswith('LOCK'):self.response=[]
        elif 'FROM pg_catalog.pg_class' in sql:self.response=self.home
        elif 'count(*)' in sql:self.response=[(str(self.count),str(self.count*2),self.props)];self.description*=3
        else:self.response=self.rows;self.description*=7
        if self.response and len(self.response[0])==6:self.description*=6
    def fetchmany(self,limit):return self.response[:limit]

class GraphCaptureTests(unittest.TestCase):
    def test_complete_parallel_typed_identity_projection(self):
        sources,records,facts,private=fixture();rows=[('90','31','1','1','11','2','12'),('91','31','7','1','11','2','12'),('92','31','1','1','11','3','12')]
        cursor=Cursor(rows);raw,covered,retained=_capture_graphs(cursor,sources,records,facts,private)
        projected=json.loads(raw);self.assertEqual([r['witness']['id'] for r in projected],['90','91','92'])
        self.assertEqual(projected[0]['endpoints'],[{'role':'worker','key':[{'string':'Alice'}]},{'role':'project','key':[{'string':'A'}]}]);self.assertEqual(projected[2]['endpoints'][1]['key'],[{'string':'B'}]);self.assertEqual(retained,tuple(rows))
        self.assertEqual(json.loads(covered),[{'relationship':relationship,'complete':True,'roles':['worker','project'],'fields':[]}])
        self.assertTrue(any(q.startswith('LOCK TABLE ONLY truss.edge IN SHARE MODE NOWAIT') for q,_ in cursor.queries));self.assertTrue(all('WHERE rel_type_id=ANY' in q for q,_ in cursor.queries if 'FROM ONLY truss.edge' in q))
    def test_projection_preserves_typed_composite_keys_and_occurrences_under_permutation(self):
        sources,records,facts,private=fixture()
        initial=json.loads(sources.initialize_bytes)
        core=initial['sources']['closure']['documents'][0]['document']
        second=copy.deepcopy(core['modules'][0]['relationships'][0]);second['id']='Reviews'
        core['modules'][0]['relationships'].append(second)
        association=copy.deepcopy(initial['sources']['ontology']['associations'][0])
        association['relationship']['relationshipId']='Reviews'
        initial['sources']['ontology']['associations'].append(association)
        encoded=json.dumps(core,separators=(',',':'))
        accepted=json.loads(sources.accepted_request_bytes)
        accepted['modules'][0]['documentJson']=encoded
        accepted['modules'][0]['pin']['sha256']=hashlib.sha256(encoded.encode()).hexdigest()
        sources.accepted_request_bytes=json.dumps(accepted).encode()
        sources.initialize_bytes=json.dumps(initial).encode()
        assessment=json.loads(sources.accepted_assessment_bytes)
        native=copy.deepcopy(assessment['inventory']['relationships'][0]);native.update(rel_id='Reviews',rel_type_id=32)
        assessment['inventory']['relationships'].append(native)
        assessment['inventory']['endpoints'].append({'rel_type_id':32,'source_type':11,'target_type':12})
        sources.accepted_assessment_bytes=json.dumps(assessment).encode()
        # Equal tuples across distinct Record types must retain their typed roles.
        composite=[{'integerToken':'9007199254740993'},{'decimalToken':'1.00'},
                   {'binaryHex':'00ff'},{'boolean':False},{'string':'a\u0000b'}]
        facts[0]['key']=copy.deepcopy(composite);facts[1]['key']=copy.deepcopy(composite)
        rows=[('90','31','1','1','11','2','12'),('91','31','2','1','11','2','12'),
              ('92','32','1','1','11','3','12')]
        expected={edge: {'relationship':dict(relationship,relationshipId=rel),
                         'witness':{'kind':'opaque-existential','id':edge},
                         'endpoints':[{'role':'worker','key':composite},
                                      {'role':'project','key':key}]}
                  for edge,rel,key in [('90','WorksOn',composite),('91','WorksOn',composite),
                                       ('92','Reviews',facts[2]['key'])]}
        for permutation in itertools.permutations(range(len(facts))):
            ordered_facts=[facts[i] for i in permutation];ordered_private=[private[i] for i in permutation]
            for ordered_rows in itertools.permutations(rows):
                with self.subTest(facts=permutation,edges=[r[0] for r in ordered_rows]):
                    raw,covered,retained=_capture_graphs(Cursor(ordered_rows),sources,records,ordered_facts,ordered_private)
                    result=json.loads(raw)
                    self.assertEqual(result,[expected[r[0]] for r in ordered_rows])
                    self.assertEqual(retained,ordered_rows)
                    self.assertEqual(len(json.loads(covered)),2)

    def test_empty_population_keeps_complete_graph_coverage(self):
        raw,covered,rows=_capture_graphs(Cursor(),*fixture());self.assertEqual(raw,b'[]');self.assertEqual(rows,());self.assertTrue(json.loads(covered)[0]['complete'])
    def test_no_graph_selection_performs_no_edge_query(self):
        sources,records,facts,private=fixture();initial=json.loads(sources.initialize_bytes);initial['sources']['ontology']['associations']=[];sources.initialize_bytes=json.dumps(initial).encode();cursor=Cursor();self.assertEqual(_capture_graphs(cursor,sources,records,facts,private),(b'[]',b'[]',()));self.assertEqual(cursor.queries,[])
    def test_source_and_native_correspondence_mutants_refuse_even_empty(self):
        for label,mutate in [
            ('retired',lambda x:x['relationships'][0].update(retired_rev=2)),('wrong-type',lambda x:x['endpoints'][0].update(target_type=11)),
            ('extra-alternative',lambda x:x['endpoints'].append({'rel_type_id':31,'source_type':11,'target_type':11})),
            ('duplicate-definition',lambda x:x['relationships'].append(copy.deepcopy(x['relationships'][0]))),
            ('direction',lambda x:x['relationships'][0].update(directed=False)),('attributes',lambda x:x['relationships'][0].update(assoc_type_id=13)),
            ('multiplicity',lambda x:x['relationships'][0].update(source_max=1)),('lifecycle',lambda x:x['relationships'][0].update(lifecycle='dependent')),
            ('target-key',lambda x:x['relationships'][0].update(target_key='other')),('composition',lambda x:x['relationships'][0].update(composition=True))]:
            with self.subTest(label=label):
                sources,records,_,_=fixture();assessment=json.loads(sources.accepted_assessment_bytes);mutate(assessment['inventory']);sources.accepted_assessment_bytes=json.dumps(assessment).encode()
                with self.assertRaises(ValueError):_graph_recipes(sources,records)
        for label,mutate in [('record-witness',lambda x:x.update(witness={'kind':'record-key','type':ref('Assignment'),'keyId':'pk'})),('reversed',lambda x:x['endpoints'][0].update(side='target')),('wrong-key',lambda x:x['endpoints'][0].update(keyId='wrong')),('duplicate-role',lambda x:x['endpoints'][0].update(role='project')),('foreign-target',lambda x:x['endpoints'][0]['target'].update(documentId='foreign'))]:
            with self.subTest(label=label):
                sources,records,_,_=fixture();initial=json.loads(sources.initialize_bytes);mutate(initial['sources']['ontology']['associations'][0]);sources.initialize_bytes=json.dumps(initial).encode()
                with self.assertRaises(ValueError):_graph_recipes(sources,records)
    def test_explicit_authored_target_key_required_before_empty_coverage(self):
        for value in ('missing',None,'',False,0):
            sources,records,facts,private=fixture()
            initial=json.loads(sources.initialize_bytes)
            core=initial['sources']['closure']['documents'][0]['document']
            target=core['modules'][0]['relationships'][0]['target'][0]
            if value=='missing':target.pop('key')
            else:target['key']=value
            encoded=json.dumps(core,separators=(',',':'))
            accepted=json.loads(sources.accepted_request_bytes)
            accepted['modules'][0]['documentJson']=encoded
            accepted['modules'][0]['pin']['sha256']=hashlib.sha256(encoded.encode()).hexdigest()
            sources.accepted_request_bytes=json.dumps(accepted).encode()
            sources.initialize_bytes=json.dumps(initial).encode()
            assessment=json.loads(sources.accepted_assessment_bytes)
            assessment['inventory']['relationships'][0]['target_key']=None if value=='missing' else value
            sources.accepted_assessment_bytes=json.dumps(assessment).encode()
            cursor=Cursor()
            with self.subTest(value=value),self.assertRaises(ValueError):
                _capture_graphs(cursor,sources,records,facts,private)
            self.assertEqual(cursor.queries,[])

    def test_native_population_and_census_faults_refuse(self):
        good=('90','31','1','1','11','2','12')
        for label,rows in [('missing-endpoint',[good[:5]+('8','12')]),('wrong-endpoint-type',[good[:4]+('12',)+good[5:]]),('duplicate-edge',[good,good]),('foreign-relation',[(good[0],'32',*good[2:])]),('invalid-id',[('00',*good[1:])]),('overflow-id',[(str(2**63),*good[1:])])]:
            with self.subTest(label=label),self.assertRaises(ValueError):_capture_graphs(Cursor(rows),*fixture())
        for label,change in [('census',lambda c:setattr(c,'count',2)),('too-many',lambda c:setattr(c,'count',10000)),('omitted-attributes',lambda c:setattr(c,'props','true')),('rls',lambda c:setattr(c,'home',[('r','p','true','false','true','false')])),('inherited',lambda c:setattr(c,'home',[('r','p','false','false','true','true')]))]:
            cursor=Cursor([good]);change(cursor)
            with self.subTest(label=label),self.assertRaises(ValueError):_capture_graphs(cursor,*fixture())
    def test_repeated_large_endpoint_keys_refuse_before_unbounded_join(self):
        sources,records,facts,private=fixture();facts[0]['key']=[{'string':'s'*65536}];facts[1]['key']=[{'string':'p'*65536}]
        rows=[(str(90+i),'31','1','1','11','2','12') for i in range(128)]
        with self.assertRaisesRegex(ValueError,'graph output exceeds'):_capture_graphs(Cursor(rows),sources,records,facts,private)
    def test_expired_operation_refuses_without_partial_graph_output(self):
        cursor=Cursor([('90','31','1','1','11','2','12')])
        def expired():raise TimeoutError('fixture operation expired')
        cursor._deadline.check=expired
        with self.assertRaises(TimeoutError):_capture_graphs(cursor,*fixture())
    def test_private_endpoint_bag_must_be_complete_distinct_and_typed(self):
        for label,change in [('missing',lambda p:p.pop()),('duplicate',lambda p:p.__setitem__(1,p[0])),('wrong-type',lambda p:p.__setitem__(0,('1','12','1',b'',b'',b'')))]:
            sources,records,facts,private=fixture();change(private)
            with self.subTest(label=label),self.assertRaises(ValueError):_capture_graphs(Cursor(),sources,records,facts,private)

if __name__=='__main__':unittest.main()
