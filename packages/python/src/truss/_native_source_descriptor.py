"""Pure original-source structural correspondence; never a native permit."""
from dataclasses import dataclass
from hashlib import sha256
import json,re
from ._owner_evidence_json import decode_owner_evidence_json,same_owner_evidence

_ROLES=('accepted-request','accepted-assessment','runtime-release','native-inventory')


def _shape(value,keys):
    if type(value) is not dict or set(value)!=set(keys):raise ValueError('Closed native source identity required')


def _uint(value,bits,zero=False):
    if (type(value) is not str or re.fullmatch('0|[1-9][0-9]*',value) is None
            or len(value)>20 or not (0 if zero else 1)<=int(value)<2**bits):
        raise ValueError('Canonical native identity integer required')


def _name(value):
    if type(value) is not str or not value or '\0' in value or len(value.encode('utf8'))>63:
        raise ValueError('Exact bounded native name required')


def _inventory(value):
    _shape(value,('version','installationId','database','schema','release','relations'))
    if value['version']!='truss.native-source.inventory/0.1-candidate' or type(value['installationId']) is not str or not value['installationId']:
        raise ValueError('Original native source profile required')
    database=value['database'];_shape(database,('systemIdentifier','oid','name'))
    _uint(database['systemIdentifier'],64);_uint(database['oid'],32);_name(database['name'])
    schema=value['schema'];_shape(schema,('oid','name'));_uint(schema['oid'],32)
    if schema['name']!='truss':raise ValueError('Exact Truss schema required')
    _shape(value['release'],('id','sha256'))
    if (type(value['release']['id']) is not str or not value['release']['id']
            or type(value['release']['sha256']) is not str or re.fullmatch('[0-9a-f]{64}',value['release']['sha256']) is None):
        raise ValueError('Exact original release identity required')
    relations=value['relations']
    if type(relations) is not list or not 1<=len(relations)<=256:raise ValueError('Bounded native relation inventory required')
    oids=set();names=set()
    for relation in relations:
        _shape(relation,('oid','name','ownerOid','columns'))
        _uint(relation['oid'],32);_uint(relation['ownerOid'],32);_name(relation['name'])
        if relation['oid'] in oids or relation['name'] in names:raise ValueError('Distinct native relation identities required')
        oids.add(relation['oid']);names.add(relation['name'])
        columns=relation['columns'];positions=set();column_names=set()
        if type(columns) is not list or not 1<=len(columns)<=4096:raise ValueError('Bounded native column inventory required')
        for column in columns:
            _shape(column,('attnum','name','typeOid','typmod','collationOid','notNull','dropped','generated','identity'))
            position=column['attnum'];_name(column['name']);_uint(column['typeOid'],32);_uint(column['collationOid'],32,True)
            if (type(position) is not int or not 1<=position<=32767 or position in positions or column['name'] in column_names
                    or type(column['typmod']) is not int or not -(2**31)<=column['typmod']<2**31
                    or type(column['notNull']) is not bool or type(column['dropped']) is not bool
                    or column['generated'] not in ('','s','v') or column['identity'] not in ('','a','d')):
                raise ValueError('Exact distinct native column identities required')
            positions.add(position);column_names.add(column['name'])


@dataclass(frozen=True,slots=True)
class NativeSourceDescriptor:
    accepted_request:bytes
    accepted_assessment:bytes
    runtime_release:bytes
    native_inventory:bytes
    json:bytes


def prepare_native_source_descriptor(*,accepted_request,accepted_assessment,runtime_release,native_inventory):
    originals=(accepted_request,accepted_assessment,runtime_release,native_inventory)
    if any(type(raw) is not bytes or not 1<=len(raw)<=4_000_000 for raw in originals) or sum(map(len,originals))>16_000_000:
        raise ValueError('Bounded exact immutable native source originals required')
    decoded=[decode_owner_evidence_json(raw) for raw in originals]
    if any(type(value) is not dict for value in decoded):raise ValueError('Original source objects required')
    request,assessment,release,inventory=decoded;_inventory(inventory)
    if (assessment.get('version')!='truss.accepted-catalog-assessment/0.1' or assessment.get('securityReady') is not False
            or assessment.get('installationId')!=inventory['installationId'] or assessment.get('releaseId')!=release.get('releaseId')
            or inventory['release']!={'id':release.get('releaseId'),'sha256':sha256(runtime_release).hexdigest()}
            or assessment.get('releaseSha256')!=sha256(runtime_release).hexdigest()):
        raise ValueError('Exact original installed-source correspondence required')
    modules=request.get('modules');seen=set()
    if type(modules) is not list or not 1<=len(modules)<=256:raise ValueError('Complete original model pins required')
    for module in modules:
        if type(module) is not dict or type(module.get('pin')) is not dict or type(module.get('documentJson')) is not str:
            raise ValueError('Original accepted model required')
        pin=module['pin'];_shape(pin,('documentId','revision','umfVersion','sha256'))
        if (any(type(pin[k]) is not str or not pin[k] or len(pin[k].encode())>4096 for k in ('documentId','revision','umfVersion'))
                or type(pin['sha256']) is not str or re.fullmatch('[0-9a-f]{64}',pin['sha256']) is None):
            raise ValueError('Complete exact original model pin required')
        identity=pin['documentId']
        if (identity in seen or sha256(module['documentJson'].encode()).hexdigest()!=pin['sha256']):
            raise ValueError('Distinct exact original model source required')
        document=decode_owner_evidence_json(module['documentJson'].encode())
        if type(document) is not dict or document.get('id')!=identity or document.get('umf')!=pin['umfVersion']:
            raise ValueError('Strict original model object/identity correspondence required')
        seen.add(identity)
    if not same_owner_evidence(assessment.get('modelPins'),[m['pin'] for m in modules]):raise ValueError('Complete exact original model correspondence required')
    result={'version':'truss.native-source.descriptor/0.1-candidate','scope':'supplied-source-structural-correspondence',
        'complete':False,'authority':False,'securityReady':False,'nativeAdmission':'required',
        'sources':[{'role':role,'sha256':sha256(raw).hexdigest(),'utf8Bytes':len(raw)} for role,raw in zip(_ROLES,originals)],
        'unresolved':['actual native observation and source continuity','original UMF Field/Key/edge/codec mapping','original authenticated operation-held current authority witness','closing guards and guarded release']}
    return NativeSourceDescriptor(*originals,json.dumps(result,separators=(',',':'),ensure_ascii=True).encode())
