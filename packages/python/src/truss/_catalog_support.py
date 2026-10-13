"""Selected catalog metadata policy; incomplete support, never acceptance."""
import base64
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import _require_original_preparation
from ._catalog_owner_evidence import require_catalog_owner_evidence
from ._owner_evidence_json import decode_owner_evidence_json, same_owner_evidence

POLICY_SHA256='1226bb636125567d1e628f5250655a615d104c401ba639f1c6b6031ba346bcdd'
PROFILE={'identity':'truss-fresh-catalog-support','version':'0.1.0','sha256':POLICY_SHA256}
RELATIONAL_POLICY_SHA256='bc7aa15a3c2ab55368a3eb7fc2c4c18c8a316cc8ac7c783930c38a2ba825f557'
RELATIONAL_PROFILE={'identity':'truss-fresh-catalog-support','version':'0.2.0','sha256':RELATIONAL_POLICY_SHA256}
SCALAR_PROFILE={'identity':'truss-fresh-catalog-support','version':'0.3.0','sha256':'aec460c192bd831ed713f9bc8e42f2c31a99adfdf1cfcf4edecff8cd8f047b9f'}

NAMED_SCALAR_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.4.0', 'sha256': '82934e8b77e9c2fabf1095a119429842a5a38dd90e47ea8cf85867cb27b1952d'}

NAMED_RELATIONSHIP_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.5.0', 'sha256': '8358f0e885a88231bcad1bd6952efcbcfec8ba970c983a5e63e5ea4873757213'}

def evaluate_catalog_support(prepared):
    """Evaluate only the exact selected policy before native catalog effects.

    Unregistered pins remain unavailable. No owner-known declaration is turned
    into value enforcement, complete assertion coverage or installation authority.
    """
    _require_original_preparation(prepared)
    choices=prepared.input()
    selected=choices['supportProfile']
    if selected not in (PROFILE,RELATIONAL_PROFILE,SCALAR_PROFILE,NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE):
        return {'state':'unavailable','reason':'unregistered_support_policy'}
    inverse=selected==NAMED_RELATIONSHIP_PROFILE
    named=selected in (NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE)
    scalars=selected in (SCALAR_PROFILE,NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE)
    relational=selected in (RELATIONAL_PROFILE,SCALAR_PROFILE,NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE)
    policy=files('truss').joinpath('_profiles/fresh-catalog-support-named-relationships.json' if inverse else '_profiles/fresh-catalog-support-named-scalars.json' if named else '_profiles/fresh-catalog-support-scalars.json' if scalars else '_profiles/fresh-catalog-support-relational.json' if relational else '_profiles/fresh-catalog-support.json').read_bytes()
    if not 1<=len(policy)<=4096 or sha256(policy).hexdigest()!=selected['sha256']:
        raise ValueError('Original selected catalog support policy required')
    if (choices['binding']!={'state':'absent'} or choices['transforms']
        or any(d['ingress']!={'kind':'native'} for d in choices['documents'])
        or any(d.observation()['source']['umf']!='0.7.0' for d in prepared.documents)):
        raise ValueError('Unselected catalog support source')
    evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
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
    decision={'state':'evaluated','profile':dict(selected),
            'supportedSubset':{'identity':'truss.fresh-catalog-support/'+selected['version'],
                'bytesBase64':base64.b64encode(policy).decode('ascii'),'sha256':selected['sha256']},
            'scope':'original_0.7_native_catalog_metadata_preflight_only',
            'requiredObservations':required,'retainedObservations':retained,
            'unresolvedValueFamilies':unresolved,
            'originalTransitions':[d.observation()['transition'] for d in prepared.documents],
            'originalDiagnostics':evidence['validation'],
            'retainedExtensions':evidence['retainedExtensions'],
            'observationCoverage':coverage,'assertionInventoryComplete':False,
            'enforcementQualified':False,'supportSemanticsQualified':False,
            'acceptedReportQualified':False,
            'closedSourceInventory':_closed_source_inventory(prepared,observations,core,relational=relational,scalars=scalars,named=named,inverse=inverse)}

    if len(json.dumps(decision,ensure_ascii=True,separators=(',',':')).encode('utf8'))>4194304:
        raise ValueError('Selected catalog support decision capacity exceeded')
    return decision


def _closed_source_inventory(prepared, observations, core, *, relational=False,scalars=False,named=False,inverse=False):
    """Complete source occurrence inventory for explicit scalar string Records.

    Profile 0.2 additionally covers known authored Keys and Relationships.
    This proves source coverage, not value enforcement or accepted execution.
    Broader preparation remains intact and explicitly outside this branch.
    """
    unavailable={'state':'unavailable','reason':'outside_closed_scalar_record_subset'}
    expected={}
    kinds={}
    authored={}
    declaration_values={}
    documents={d['documentId']:d['artifact'] for d in prepared.input()['documents']}
    for document in prepared.documents:
        source=document.observation()['source']
        if source['umf']!='0.7.0' or set(source)-{'umf','id','modules','vocabularies','extensions'}:
            return unavailable
        if source.get('vocabularies',{})!={} or source.get('extensions',{})!={}:
            return unavailable
        fields=set();owned=set()
        for mi,module in enumerate(source['modules']):
            if set(module)-({'id','namespace','elements','extensions','relationships'} if relational else {'id','namespace','elements','extensions'}) or module.get('extensions',{})!={}:
                return unavailable
            for ei,element in enumerate(module['elements']):
                pointer=f'/modules/{mi}/elements/{ei}'
                kind=element.get('kind')
                kinds[(document.document.document_id,module['id'],element['id'])]=kind
                allowed=((({'id','kind','members','extensions','keys'} if relational else {'id','kind','members','extensions'}) | ({'name'} if named else set())) if kind=='record' else
                         {'id','kind','name','scalarType','nullability','cardinality','extensions'})
                if kind not in ('record','field') or set(element)-allowed or element.get('extensions',{})!={}:
                    return unavailable
                operations=['kind']
                if kind=='record':
                    if 'name' in element and (type(element['name']) is not str or not element['name'] or '\0' in element['name']):return unavailable
                    if type(element.get('members')) is not list:
                        return unavailable
                    operations.append('members')
                    if relational and 'keys' in element:
                        values=element['keys']
                        if type(values) is not list or not values:return unavailable
                        declaration_values[(document.document.document_id,'keys',module['id'],element['id'])]=values
                        for ki,key in enumerate(values):
                            if (type(key) is not dict or set(key)-{'id','name','fields','primary'}
                                or not {'id','name','fields'}<=set(key)
                                or type(key['id']) is not str or type(key['name']) is not str
                                or ('primary' in key and type(key['primary']) is not bool)
                                or type(key['fields']) is not list
                                or any(type(ref) is not dict or set(ref)!={'module','element'} for ref in key['fields'])):
                                return unavailable
                            address=(document.document.document_id,pointer+f'/keys/{ki}')
                            expected[address]='core.keys';authored[address]=key['id']
                    for index,member in enumerate(element['members']):
                        if type(member) is not dict or set(member)!={'module','element'}:
                            return unavailable
                        owned.add((member['module'],member['element']))
                        expected[(document.document.document_id,pointer+f'/members/{index}')]='core.members.member'
                else:
                    if (element.get('scalarType') not in (('string','integer','decimal','boolean','timestamp','binary') if scalars else ('string',)) or element.get('cardinality')!='one'
                        or element.get('nullability') not in ('required','absent-allowed')
                        or type(element.get('name')) is not str or not element['name']):
                        return unavailable
                    fields.add((module['id'],element['id']))
                    operations.extend(('nullability','cardinality','scalarType'))
                for operation in operations:
                    expected[(document.document.document_id,pointer+'/'+operation)]='core.'+operation
            if relational and 'relationships' in module:
                values=module['relationships']
                if type(values) is not list:return unavailable
                declaration_values[(document.document.document_id,'relationships',module['id'],None)]=values
                for ri,relation in enumerate(values):
                    if (type(relation) is not dict or set(relation)-({'id','name','source','target','sourceMultiplicity','targetMultiplicity','targetLifecycle','directed'}|({'inverse'} if inverse else set()))
                        or not {'id','name','source','target','sourceMultiplicity','targetMultiplicity','targetLifecycle','directed'}<=set(relation)
                        or type(relation['id']) is not str or type(relation['name']) is not str
                        or type(relation['directed']) is not bool
                        or relation['targetLifecycle'] not in ('owned','independent','unspecified')):
                        return unavailable
                    if 'inverse' in relation and (type(relation['inverse']) is not str or not 1<=len(relation['inverse'].encode('utf8'))<=4096):return unavailable
                    for side in ('source','target'):
                        refs=relation[side];multiplicity=relation[side+'Multiplicity']
                        if (type(refs) is not list or any(type(ref) is not dict or set(ref)!=({'module','element'} if side=='source' else {'module','element','key'}) for ref in refs)
                            or type(multiplicity) is not dict or set(multiplicity)!={'min','max'}
                            or type(multiplicity['min']) is not int or not 0<=multiplicity['min']<=2147483647
                            or not (multiplicity['max']=='*' or (type(multiplicity['max']) is int and multiplicity['min']<=multiplicity['max']<=2147483647))):
                            return unavailable
                    address=(document.document.document_id,f'/modules/{mi}/relationships/{ri}')
                    expected[address]='core.relationships';authored[address]=relation['id']
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
            declaration=declaration_values.get((observed['documentId'],operation,identity.get('module'),identity.get('element')))
            if relational and operation in ('relationships','keys') and declaration is not None:
                expected_state='known';classification='original_assertion'
                if not same_owner_evidence(meaning.get(operation),declaration):
                    raise ValueError('Original authored declaration meaning correspondence required')
            elif operation in ('relationships','keys','referenceLinks') or (operation=='facets' and kind=='field'):
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
        owner=decode_owner_evidence_json(base64.b64decode(artifact['bytesBase64'],validate=True))
        observed=owner['result']['observation']
        path=observed['path']
        authored_entry=key in authored
        descendant_rule=entry['ruleName'] in ('core.members.member','core.keys','core.relationships')
        expected_kind='authored' if authored_entry else 'source'
        if (owner['documentId']!=key[0] or owner['basis']!='original'
            or observed['meaning']['state']!='known'
            or (path!=key[1] and not (descendant_rule and key[1].startswith(path+'/')))
            or entry['enforcement']!='none' or entry['reason']!='unqualified'
            or assertion['owner']!={'documentId':key[0],'moduleId':owner['identity']['module']}
            or assertion['sourceKind']!='umf_document' or assertion['kind']!=expected_kind
            or (not authored_entry and assertion.get('sourceIdentityProfile')!=core['profile'])
            or (authored_entry and (assertion.get('authoredIdentity')!=authored[key] or 'sourceIdentityProfile' in assertion))
            or entry['ruleNameOrigin']!='profile_generated'
            or entry['source']!=documents[key[0]]
            or entry['ruleName'] not in ('core.'+owner['operation'],'core.members.member')
            or assertion['definitionPin']!=owner['contentSha256']
            or entry['source']['sha256']!=owner['contentSha256']):
            raise ValueError('Original closed-source meaning correspondence required')
    if seen!=set(expected):
        raise ValueError('Complete closed-source assertion occurrence coverage required')
    return {'state':'inventoried','scope':('original_0.7_explicit_exact_scalar_records_string_keys_relationships' if scalars else 'original_0.7_explicit_scalar_string_records_keys_relationships' if relational else 'original_0.7_explicit_scalar_string_records'),
            'assertionOccurrenceCoverageComplete':True,'entries':entries,'extensions':[],
            'observationClassifications':classifications,
            'enforcementQualified':False,'acceptedReportQualified':False}
