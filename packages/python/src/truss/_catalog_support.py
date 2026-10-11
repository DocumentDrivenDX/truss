"""Selected catalog metadata policy; incomplete support, never acceptance."""
import base64
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import _require_original_preparation
from ._catalog_owner_evidence import require_catalog_owner_evidence

POLICY_SHA256='d4abdcc3c8e42aac764ca7bb5f8875dcd7f230f0fa4d0dcead8cc91a62901c91'
PROFILE={'identity':'truss-fresh-catalog-support','version':'0.1.0','sha256':POLICY_SHA256}


def evaluate_catalog_support(prepared):
    """Evaluate only the exact selected policy before native catalog effects.

    Unregistered pins remain unavailable. No owner-known declaration is turned
    into value enforcement, complete assertion coverage or installation authority.
    """
    _require_original_preparation(prepared)
    choices=prepared.input()
    if choices['supportProfile']!=PROFILE:
        return {'state':'unavailable','reason':'unregistered_support_policy'}
    policy=files('truss').joinpath('_profiles/fresh-catalog-support.json').read_bytes()
    if not 1<=len(policy)<=4096 or sha256(policy).hexdigest()!=POLICY_SHA256:
        raise ValueError('Original selected catalog support policy required')
    if (choices['binding']!={'state':'absent'} or choices['transforms']
        or any(d['ingress']!={'kind':'native'} for d in choices['documents'])
        or any(d.observation()['source']['umf']!='0.7.0' for d in prepared.documents)):
        raise ValueError('Unselected catalog support source')
    evidence=json.loads(prepared.report_evidence_bytes)
    observations,coverage,core=require_catalog_owner_evidence(prepared,evidence)
    source_elements={}
    staged=set()
    unresolved=[]
    for document in prepared.documents:
        source=document.observation()['source']
        for module in source['modules']:
            for element in module['elements']:
                source_elements[(document.document.document_id,module['id'],element['id'])]=element
    for document in json.loads(prepared.declarations_bytes):
        for record in document['records']:
            if record['membership']!='declared':
                raise ValueError('Selected Record requires explicit original membership')
            for field in record['fields']:
                identity=(record['documentId'],field['fieldModule'],field['fieldId'])
                source=source_elements.get(identity)
                if source!=field['declaration']:
                    raise ValueError('Original staged Field source correspondence required')
                for name in ('name','kind','nullability','cardinality'):
                    if type(source.get(name)) is not str or not 1<=len(source[name].encode('utf8'))<=4096:
                        raise ValueError('Selected Field requires explicit authored metadata')
                staged.add(identity)
                if 'scalarType' not in source:
                    unresolved.append({'documentId':identity[0],'moduleId':identity[1],'elementId':identity[2],'duty':'value_family_unresolved'})
    required=[]
    retained=[]
    for observed in observations['observations']:
        operation=observed['operation'];identity=observed['identity']
        source=source_elements.get((observed['documentId'],identity.get('module'),identity.get('element')))
        if operation in ('schema_properties','referenceLinks') or (source and source.get('kind')=='group'):
            retained.append(observed['evidence'])
            continue
        if observed['basis']!='original' or observed['result']['state']!='observed':
            raise ValueError('Required original catalog interpretation unavailable')
        meaning=observed['result']['observation']['meaning']
        state=meaning['state']
        if operation=='kind':
            allowed=('known',)
        elif operation=='members' and source and source.get('kind')=='record':
            allowed=('known',)
        elif operation in ('nullability','cardinality') and (observed['documentId'],identity.get('module'),identity.get('element')) in staged:
            allowed=('known',)
        else:
            allowed=('known','missing','inapplicable')
        if state not in allowed or meaning.get('uninterpretedPaths'):
            raise ValueError('Required catalog meaning is unknown or incomplete')
        required.append(observed['evidence'])
    decision={'state':'evaluated','profile':dict(PROFILE),
            'supportedSubset':{'identity':'truss.fresh-catalog-support/0.1.0',
                'bytesBase64':base64.b64encode(policy).decode('ascii'),'sha256':POLICY_SHA256},
            'scope':'original_0.7_native_catalog_metadata_preflight_only',
            'requiredObservations':required,'retainedObservations':retained,
            'unresolvedValueFamilies':unresolved,
            'originalTransitions':[d.observation()['transition'] for d in prepared.documents],
            'originalDiagnostics':evidence['validation'],
            'retainedExtensions':evidence['retainedExtensions'],
            'observationCoverage':coverage,'assertionInventoryComplete':False,
            'enforcementQualified':False,'supportSemanticsQualified':False,
            'acceptedReportQualified':False}

    if len(json.dumps(decision,ensure_ascii=True,separators=(',',':')).encode('utf8'))>4194304:
        raise ValueError('Selected catalog support decision capacity exceeded')
    return decision
