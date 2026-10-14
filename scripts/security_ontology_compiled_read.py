"""Original Weft graph query under the existing owned native graph cut.

Diagnostic composition only: trusted compiler binary/source, registration and
native source custody are premises. Candidate hashes do not authorize SQL.
Public/native compiler admission remains required by the original producer.
"""
from pathlib import Path
from hashlib import sha256
import json,subprocess
from truss._owner_evidence_json import decode_owner_evidence_json

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/helix/04-build/evidence/security-named-source-profile'
BINDING=ROOT/'docs/helix/04-build/evidence/security-ontology-shared-policy-20261014/binding-correspondence.json'


def _original_request(physical_request,assessment,query_sql=None):
    logical=decode_owner_evidence_json((BASE/'mapping-request.json').read_bytes())
    if query_sql is not None and (type(query_sql) is not str or not 1<=len(query_sql.encode())<=4000000):raise ValueError('Bounded original graph query required')
    logical['sql']='SELECT r.resourceId, r.salary FROM Resource r' if query_sql is None else query_sql
    native=decode_owner_evidence_json(assessment)
    physical=decode_owner_evidence_json(physical_request)
    if len(physical['modules'])!=1:raise ValueError('Original single physical graph source required')
    correspondence=decode_owner_evidence_json(BINDING.read_bytes())
    # Preserve the original authored pin; native revision is a separate carrier.
    inventory=json.dumps(native,sort_keys=True,separators=(',',':'))
    correspondence['inventorySha256']=sha256(inventory.encode()).hexdigest()
    source={'version':'weft.truss.security.graph-source/0.1-candidate',
            'nativeSchemaRevision':native['revision'],'physicalModule':{**physical['modules'][0],'selectedModuleIds':['m']},
            'inventoryJson':inventory,'correspondenceJson':json.dumps(correspondence,separators=(',',':')),
            'logicalResolutionJson':(BASE/'resolution.json').read_text(),
            'logicalTransportJson':(BASE/'transport.json').read_text()}
    binding=json.dumps(source,separators=(',',':'));logical['bindingJson']=binding
    profile=json.loads(logical['queryProfileJson']);profile['binding']['sha256']=sha256(binding.encode()).hexdigest()
    logical['queryProfileJson']=json.dumps(profile,separators=(',',':'))
    raw=json.dumps(logical,separators=(',',':')).encode()
    if len(raw)>4000000:raise ValueError('Bounded original graph compiler request required')
    return raw


def _text_result(cursor,statement,params=()):
    cursor.execute(statement,params,prepare=False,binary=False)
    if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=25:
        raise ValueError('Exact original graph compiler TEXT result required')
    rows=cursor.fetchmany(101)
    if len(rows)>100 or any(len(r)!=1 or type(r[0]) is not str or len(r[0].encode())>65536 for r in rows):
        raise ValueError('Bounded complete original graph compiler result required')
    return rows


def prepare_owned_graph_compiler(binary,result_binary,*,guarded=False,query_sql=None,source_comparison=None):
    """Pin original trusted producer; no path/hash-based authority issuance."""
    if type(guarded) is not bool or (not guarded and query_sql is not None):raise ValueError('Distinct original guarded compiler mode required')
    if guarded:
        from truss._security_guarded_source import snapshot_guarded_source_comparison
        source_comparison=snapshot_guarded_source_comparison(source_comparison)
    elif source_comparison is not None:raise ValueError('Distinct original guarded source comparison required')
    binary=Path(binary).resolve();original=binary.read_bytes()
    if not original or len(original)>64000000:raise ValueError('Bounded original graph compiler binary required')
    digest=sha256(original).digest()
    result_binary=Path(result_binary).resolve();result_original=result_binary.read_bytes()
    if not result_original or len(result_original)>64000000:raise ValueError('Bounded original graph result checker binary required')
    result_digest=sha256(result_original).digest()
    files=(Path(__file__),BINDING,BASE/'mapping-request.json',BASE/'resolution.json',BASE/'transport.json')
    pins=tuple((p,sha256(p.read_bytes()).digest()) for p in files)
    def execute(cursor,physical_request,before,subject,semantic):
        request=_original_request(physical_request,before[0],query_sql)
        compiled=subprocess.run([str(binary)],input=request,capture_output=True,timeout=15)
        if compiled.returncode:
            raise ValueError('Original graph compiler lowering refused: '+compiled.stderr.decode(errors='replace')[:1024])
        if len(compiled.stdout)>16000000:raise ValueError('Original graph compiler lowering output exceeded')
        output=decode_owner_evidence_json(compiled.stdout)
        if guarded:
            from truss._security_guarded_source import require_same_guarded_source
            require_same_guarded_source(source_comparison,request,compiled.stdout)
            context_sha=output['queryContextSha256']
            graph_sha=output['query']['graphSourceSha256']
        else:
            if (output['version']!='weft.truss.security.graph-lowering/0.1-candidate' or output['securityReady'] is not False
                    or output['sourceRequestSha256']!=sha256(request).hexdigest()
                    or output['bindingSha256']!=sha256(json.loads(request)['bindingJson'].encode()).hexdigest()):
                raise ValueError('Original graph compiler source correspondence required')
            context_sha=output['contextSha256'];graph_sha=output['graph']['graphSourceSha256']
        query=output['query'];execution=query['execution'];slot=execution['subjectSlot']
        if (query['version']!='weft.truss.security.graph-query/0.1-candidate' or query['securityReady'] is not False
                or query['nativeAdmission']!='required' or query['contextSha256']!=context_sha
                or query['graphSourceSha256']!=graph_sha
                or execution['policyParameterTypes']!=['boolean'] or type(execution['policyParameters']) is not list
                or len(execution['policyParameters'])!=1 or execution['policyParameters'][0] is not True
                or type(slot['ordinal']) is not int or slot['ordinal']!=2 or type(slot['nativeTypeId']) is not int or slot['physicalType']!='int8'
                or slot['logicalSubject']!={'documentId':'domain','moduleId':'m','elementId':'Staff'}
                or slot['supplier']!='original_authenticated_guarded_host_only'):
            raise ValueError('Original selected graph compiler query context required')
        inventory=json.loads(before[0])['inventory'];staff=[t for t in inventory['types'] if (t['document_id'],t['module'],t['element'])==('adoc','m','Staff') and t['retired_rev'] is None]
        if len(staff)!=1 or slot['nativeTypeId']!=staff[0]['type_id']:raise ValueError('Original compiled native Staff home required')
        props=[p for p in inventory['properties'] if p['type_id']==staff[0]['type_id'] and p['element']=='staffId' and p['retired_rev'] is None]
        if len(props)!=1:raise ValueError('Original compiled native Staff key required')
        identities=[]
        for oid,tid,raw,root in before[1]:
            if tid==str(staff[0]['type_id']) and root=='false' and json.loads(raw)[str(props[0]['prop_id'])]=={'kind':'string','text':subject}:identities.append(oid)
        if len(identities)!=1:raise ValueError('Original authenticated captured Staff locator required')
        # SQL is original trusted owner output. PREPARE retains native $ ordinals;
        # runtime values are supplied separately with stock driver parameters.
        from psycopg import sql
        import uuid
        def run(statement,parameterized):
            if type(statement) is not str or not 1<=len(statement.encode())<=4000000:raise ValueError('Bounded original compiled graph SQL required')
            if not parameterized:return _text_result(cursor,statement)
            name='graph_'+uuid.uuid4().hex
            cursor.execute(sql.SQL('PREPARE {}(pg_catalog.bool,pg_catalog.int8) AS ').format(sql.Identifier(name))+sql.SQL(statement),prepare=False)
            try:return _text_result(cursor,sql.SQL('EXECUTE {}({},{})').format(sql.Identifier(name),sql.Literal(True),sql.Literal(int(identities[0]))))
            finally:cursor.execute(sql.SQL('DEALLOCATE {}').format(sql.Identifier(name)),prepare=False)
        guards=query['integrityChecks']
        if type(guards) is not list or len(guards)!=4:raise ValueError('Original complete graph endpoint guards required')
        for guard in guards:
            if run(guard['sql'],False)!=[('0',)]:raise ValueError('Original compiled graph endpoint integrity refused')
        for guard in (query['subjectCheck'],query['truthCheck']):
            if run(guard['sql'],True)!=[('0',)]:raise ValueError('Original compiled graph subject/truth refused')
        rows=run(execution['sql'],True)
        cells=[decode_owner_evidence_json(r[0].encode()) for r in rows]
        expected=[]
        for row in semantic['rows']:
            if len(row['output'])!=1 or row['output'][0]['disposition']!='withheld' or 'value' in row['output'][0]:
                raise ValueError('Original semantic salary withholding required')
            original_cells={'resourceId':{'outcomeId':'original','disposition':'original','value':{'string':row['key'][0]['string']}},'salary':{'outcomeId':'withheld','disposition':'withheld'}}
            if guarded:
                columns=query['resultContract']['columns']
                if type(columns) is not list or not 1<=len(columns)<=100:raise ValueError('Bounded original guarded projection required')
                projected=[]
                for position,column in enumerate(columns,1):
                    fields=column['sourceFields']
                    if column['position']!=position or type(fields) is not list or len(fields)!=1 or fields[0] not in [dict(documentId='domain',module='m',element=f,revision='named-schema-1') for f in original_cells]:raise ValueError('Original supported semantic projection required')
                    projected.append(original_cells[fields[0]['element']])
                expected.append(projected)
            else:expected.append([original_cells['resourceId'],original_cells['salary']])
        if sorted(json.dumps(r,sort_keys=True) for r in cells)!=sorted(json.dumps(r,sort_keys=True) for r in expected):
            raise ValueError('Original compiler projected bag differs from shared semantic oracle')
        batch=json.dumps({'version':'weft.security.cells/0.1.0','resultContractSha256':query['resultContractSha256'],'rows':cells},separators=(',',':'))
        check_input=json.dumps({'version':('weft.truss.security.guarded-result/0.1-candidate' if guarded else 'weft.truss.security.graph-result/0.1-candidate'),'sourceRequestJson':request.decode(),'sourceOutputJson':compiled.stdout.decode(),'batchJson':batch}).encode()
        checked=subprocess.run([str(result_binary)],input=check_input,capture_output=True,timeout=15)
        if checked.returncode or len(checked.stdout)>65536:raise ValueError('Original graph compiler result contract refused')
        result_check=decode_owner_evidence_json(checked.stdout)
        expected_check={'version':('weft.truss.security.guarded-result/0.1-candidate' if guarded else 'weft.truss.security.graph-result/0.1-candidate'),'status':'inspected','securityReady':False,
                'sourceRequestSha256':sha256(request).hexdigest(),'sourceOutputSha256':sha256(compiled.stdout).hexdigest(),
                'batchSha256':sha256(batch.encode()).hexdigest()}
        if guarded:expected_check.update(sourceContextSha256=output['sourceContextSha256'],queryContextSha256=output['queryContextSha256'])
        if type(result_check) is not dict or result_check!=expected_check:
            raise ValueError('Original graph result checker correspondence required')
        if (sha256(binary.read_bytes()).digest()!=digest or sha256(result_binary.read_bytes()).digest()!=result_digest
                or any(sha256(p.read_bytes()).digest()!=d for p,d in pins)):raise ValueError('Original graph compiler sources changed')
        return {'request':request.decode(),'output':compiled.stdout.decode(),'cells':cells,'batch':batch,'resultCheck':checked.stdout.decode(),'binarySha256':digest.hex(),'resultBinarySha256':result_digest.hex()}
    return execute
