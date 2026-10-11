"""Selected catalog metadata policy; incomplete support, never acceptance."""
import base64
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import _require_original_preparation
from ._catalog_owner_evidence import require_catalog_owner_evidence

POLICY_SHA256='1226bb636125567d1e628f5250655a615d104c401ba639f1c6b6031ba346bcdd'
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
            'acceptedReportQualified':False,
            'closedSourceInventory':_closed_source_inventory(prepared,observations,core)}

    if len(json.dumps(decision,ensure_ascii=True,separators=(',',':')).encode('utf8'))>4194304:
        raise ValueError('Selected catalog support decision capacity exceeded')
    return decision


def _closed_source_inventory(prepared, observations, core):
    """Complete source occurrence inventory for explicit scalar string Records.

    This proves source coverage, not value enforcement or accepted execution.
    Broader preparation remains intact and explicitly outside this branch.
    """
    unavailable={'state':'unavailable','reason':'outside_closed_scalar_record_subset'}
    expected={}
    kinds={}
    documents={d['documentId']:d['artifact'] for d in prepared.input()['documents']}
    for document in prepared.documents:
        source=document.observation()['source']
        if source['umf']!='0.7.0' or set(source)-{'umf','id','modules','vocabularies','extensions'}:
            return unavailable
        if source.get('vocabularies',{})!={} or source.get('extensions',{})!={}:
            return unavailable
        fields=set();owned=set()
        for mi,module in enumerate(source['modules']):
            if set(module)-{'id','namespace','elements','extensions'} or module.get('extensions',{})!={}:
                return unavailable
            for ei,element in enumerate(module['elements']):
                pointer=f'/modules/{mi}/elements/{ei}'
                kind=element.get('kind')
                kinds[(document.document.document_id,module['id'],element['id'])]=kind
                allowed=({'id','kind','members','extensions'} if kind=='record' else
                         {'id','kind','name','scalarType','nullability','cardinality','extensions'})
                if kind not in ('record','field') or set(element)-allowed or element.get('extensions',{})!={}:
                    return unavailable
                operations=['kind']
                if kind=='record':
                    if type(element.get('members')) is not list:
                        return unavailable
                    operations.append('members')
                    for index,member in enumerate(element['members']):
                        if type(member) is not dict or set(member)!={'module','element'}:
                            return unavailable
                        owned.add((member['module'],member['element']))
                        expected[(document.document.document_id,pointer+f'/members/{index}')]='core.members.member'
                else:
                    if (element.get('scalarType')!='string' or element.get('cardinality')!='one'
                        or element.get('nullability') not in ('required','absent-allowed')
                        or type(element.get('name')) is not str or not element['name']):
                        return unavailable
                    fields.add((module['id'],element['id']))
                    operations.extend(('nullability','cardinality','scalarType'))
                for operation in operations:
                    expected[(document.document.document_id,pointer+'/'+operation)]='core.'+operation
        if fields!=owned:
            return unavailable
    classifications=[]
    for observed in observations['observations']:
        operation=observed['operation'];identity=observed['identity']
        kind=kinds.get((observed['documentId'],identity.get('module'),identity.get('element')))
        if operation=='schema_properties':
            classification='reversible_target_retained_original_source_has_no_schema_properties'
        else:
            if observed['result']['state']!='observed' or observed['basis']!='original':
                raise ValueError('Original closed-source observation required')
            meaning=observed['result']['observation']['meaning']
            if operation in ('relationships','keys','referenceLinks') or (operation=='facets' and kind=='field'):
                expected_state='missing';classification='authored_absence'
            elif (kind=='record' and operation in ('nullability','cardinality','facets','scalarType')) or (kind=='field' and operation=='members'):
                expected_state='inapplicable';classification='inapplicable_to_source_kind'
            else:
                expected_state='known';classification='original_assertion'
            if meaning['state']!=expected_state or meaning.get('uninterpretedPaths'):
                raise ValueError('Exhaustive closed-source observation classification required')
        classifications.append({'evidence':observed['evidence'],'classification':classification})
    artifacts={o['evidence']['identity']:o['evidence'] for o in observations['observations']}
    entries=core.get('entries')
    if type(entries) is not list or len(entries)!=len(expected):
        raise ValueError('Complete closed-source assertion occurrence inventory required')
    seen=set()
    for entry in entries:
        assertion=entry['assertion']
        key=(assertion['owner']['documentId'],assertion['sourcePointer'])
        if key in seen or expected.get(key)!=entry['ruleName']:
            raise ValueError('Original closed-source assertion occurrence bijection required')
        seen.add(key)
        artifact=entry['ownerEvidence']
        if artifacts.get(artifact['identity'])!=artifact:
            raise ValueError('Original assertion owner evidence required')
        owner=json.loads(base64.b64decode(artifact['bytesBase64'],validate=True))
        observed=owner['result']['observation']
        path=observed['path']
        if (owner['documentId']!=key[0] or owner['basis']!='original'
            or observed['meaning']['state']!='known'
            or (path!=key[1] and not (entry['ruleName']=='core.members.member' and key[1].startswith(path+'/')))
            or entry['enforcement']!='none' or entry['reason']!='unqualified'
            or assertion['owner']!={'documentId':key[0],'moduleId':owner['identity']['module']}
            or assertion['sourceKind']!='umf_document' or assertion['kind']!='source'
            or assertion['sourceIdentityProfile']!=core['profile']
            or entry['ruleNameOrigin']!='profile_generated'
            or entry['source']!=documents[key[0]]
            or entry['ruleName'] not in ('core.'+owner['operation'],'core.members.member')
            or assertion['definitionPin']!=owner['contentSha256']
            or entry['source']['sha256']!=owner['contentSha256']):
            raise ValueError('Original closed-source meaning correspondence required')
    if seen!=set(expected):
        raise ValueError('Complete closed-source assertion occurrence coverage required')
    return {'state':'inventoried','scope':'original_0.7_explicit_scalar_string_records',
            'assertionOccurrenceCoverageComplete':True,'entries':entries,'extensions':[],
            'observationClassifications':classifications,
            'enforcementQualified':False,'acceptedReportQualified':False}
