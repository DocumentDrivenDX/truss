"""Original CQP -> original UMF computation inside the held native operation."""
from hashlib import sha256
import json
from time import monotonic
from ._current_query_computation import open_current_query_computation
from ._current_query_pipe import _envelope
from ._owner_evidence_json import decode_owner_evidence_json


class CurrentQueryLimit(ValueError):
    pass


def wire(value):
    return json.dumps(value,separators=(',',':'),ensure_ascii=True).encode()


def ref(identity):
    return {'documentId':identity['documentId'],'moduleId':identity['module'],'elementId':identity['element']}


def identity(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True)


def evaluate_current_query(cursor,captured,subject,*,sql,parameters,document_ids,bun_executable):
    sources=captured.sources
    if sources.query_originals is None:
        raise ValueError('Complete registered query originals required')
    request=decode_owner_evidence_json(sources.accepted_request_bytes)
    if set(document_ids)!={m['pin']['documentId'] for m in request['modules']}:
        raise ValueError('Complete selected query model closure required')
    opaque=decode_owner_evidence_json(sources.query_originals.opaque_sources_bytes)
    original={r['role']:decode_owner_evidence_json(r['utf8'].encode()) for r in opaque}
    modules=[dict(m,selectedModuleIds=[x['id'] for x in json.loads(m['documentJson'])['modules']]) for m in request['modules']]
    typed={}
    for name,value in parameters.items():
        if (type(name) is not str or not 1<=len(name.encode())<=4096 or '\0' in name
                or type(value) not in (str,int)
                or type(value) is str and (len(value.encode())>1048576 or '\0' in value)):
            raise ValueError('Exact String/signed64 query parameters required')
        if type(value) is int and not -(2**63)<=value<2**63:
            raise ValueError('Exact signed64 parameter required')
        typed[name]={'family':'integer' if type(value) is int else 'string','value':str(value)}
    raw=wire({'interfaceVersion':'weft-application-lineage/0.2-candidate','modules':modules,
              'sql':sql,'parameters':typed,'opaqueSources':opaque})
    if len(raw)>4194304:raise CurrentQueryLimit('Bounded original current-query request required')
    import weft.weft as native
    cursor._deadline.check()
    parent=native.prepare_application_lineage(raw.decode())
    current=parent.prepare_current_query()
    # Invoke the actual native descriptors, never a caller's replacement packet.
    packet=decode_owner_evidence_json(native.CurrentQueryPreparation.native_request_json(current).encode())
    designation_raw=native.CurrentQueryPreparation.designation_json(current).encode()
    designation=decode_owner_evidence_json(designation_raw)
    cursor._deadline.check()
    if (packet['authority'] is not False or packet['securityReady'] is not False
            or packet['sourceRequestSha256']!=sha256(parent.source_request_json().encode()).hexdigest()
            or packet['designationSha256']!=sha256(designation_raw).hexdigest()
            or packet['primaryAction']!=original['owner']['disclosure']['readAction']
            or packet['binding']!=original['query-designation']['binding']
            or packet['modelPins']!=[m['pin'] for m in modules]):
        raise ValueError('Original CQP/source correspondence required')
    facts=json.loads(captured.facts_bytes)
    generation=cursor.execute('SELECT pg_catalog.pg_current_xact_id()::pg_catalog.text',prepare=False).fetchone()[0]
    initial=decode_owner_evidence_json(sources.initialize_bytes)['sources']
    owner=original['owner']
    cut={'version':'umf.security.logical-facts/0.1','trusted':True,
         'generation':generation,'expectedGeneration':generation,
         'policy':{'id':initial['policy']['id'],'revision':initial['policy']['revision']},
         'ontology':initial['policy']['ontology'],
         'protection':None if initial['catalog'] is None else {'id':initial['catalog']['id'],'revision':initial['catalog']['revision']},
         'domains':initial['closure']['pins'],'owner':{'id':owner['id'],'revision':owner['revision']},
         'subject':{'type':initial['ontology']['subject'],'key':[{'string':subject.key}]},
         'facts':facts,'graphs':[],'coverage':json.loads(captured.coverage_bytes),'graphCoverage':[],
         'context':[],'valueProfiles':[],'maxFacts':10000,'maxSteps':1000000}
    routes=[{'id':'route'+str(n),'use':r} for n,r in enumerate(packet['routes'])]
    receipt=sources.source_receipt
    with open_current_query_computation(bun_executable=bun_executable,
            timeout_seconds=min(20,cursor._deadline.end-monotonic())) as child:
        def exchange(value):
            cursor._deadline.check()
            result=_envelope(child.exchange(wire(value),source_receipt=receipt))
            cursor._deadline.check()
            return result
        initialized=_envelope(child.exchange(sources.initialize_bytes,source_receipt=receipt))
        if initialized['kind']!='initialized':raise ValueError('Original UMF initialization refused')
        inspected=exchange({'kind':'inspect-routes','requestId':'inspect','sourceReceipt':receipt,'owner':owner,'routes':routes})
        if (inspected['kind']!='routes-inspected'
                or [r['id'] for r in inspected['routeResults']]!=[r['id'] for r in routes]):
            raise ValueError('Original complete route inspection required')
        operations=[]
        for scan in packet['scans']:
            fields=[]
            def add(field):
                if field not in fields:fields.append(field)
            for projection in packet['projections']:
                if projection['scan']==scan['scan']:add(ref(projection['field']))
            for inspection,route in zip(inspected['routeResults'],packet['routes'],strict=True):
                result=inspection['result']
                if (result['status']!='inspected' or result['authority'] is not False
                        or result['use']!=route or result['sources']['readAction']!=packet['primaryAction']):
                    raise ValueError('Original route/source inspection refused')
                if route['scan']==scan['scan'] and not all(x['mode']=='original-authorized' for x in result['sources']['baseConstraints']):
                    add(route['field'])
            operations.extend([{'id':scan['scan']+'-rules','kind':'read-rules','selection':{'type':scan['type']}},
                               {'id':scan['scan']+'-cells','kind':'scan','selection':{'type':scan['type'],'fields':fields}}])
        for n,route in enumerate(packet['routes']):
            uses=[u for u in designation['uses'] if (u['scan'],u['path'])==(route['scan'],route['path'])]
            operands=[x['input'] for operation in packet['operations'] for x in operation['operands'] if x['path']==route['path']]
            if len(uses)!=1 or len(operands)!=1 or uses[0]['originalAction']!=operands[0]['originalAction']:
                raise ValueError('Exact original action designation required')
            if uses[0]['originalAction'] is not None:
                resources=[{'type':f['type'],'key':f['key']} for f in facts if f['type']==route['type']]
                operations.append({'id':'action'+str(n),'kind':'action','request':{
                    'action':uses[0]['originalAction'],'resources':resources,'targets':[route['type']],'fields':[]}})
        evaluated=exchange({'kind':'evaluate','requestId':'evaluate','sourceReceipt':receipt,'owner':owner,
                            'cut':cut,'operations':operations,'routes':routes})
    if (evaluated['kind']!='evaluation' or evaluated['batch']['status']!='completed'
            or evaluated['batch']['authority'] is not False
            or [(x['id'],x['kind']) for x in evaluated['batch']['operations']]!=[(x['id'],x['kind']) for x in operations]
            or [r['id'] for r in evaluated['routeResults']]!=[r['id'] for r in routes]):
        raise ValueError('Original complete policy evaluation required')
    return native,current,packet,designation,evaluated,owner,modules
