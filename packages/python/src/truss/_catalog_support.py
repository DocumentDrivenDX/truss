from ._catalog_source_reference import REFERENCE08_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE,compact_catalog_sources,catalog_source_artifact,resolve_catalog_observation
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

RETAINED_METADATA_PROFILE={'identity':'truss-fresh-catalog-support','version':'0.6.0','sha256':'c188429e07667bd1ba6a13da5d89f9c584e517163b948e9ec4cf02810b420369'}

CORE08_PROFILE={'identity':'truss-fresh-catalog-support','version':'0.7.0','sha256':'a37ace85f20b58b82c06a174bcc30ad3fe69d26fc1fd77d52e4e0392c671338f'}

FACET07_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.8.0', 'sha256': '9fd5ab418905f95257563740528a6d80403ab154af8d1f6edfd28c93b7ae0620'}
FACET08_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.9.0', 'sha256': '12705eba231df82a2e0d1ae049d69e376819a78c895f6823e0154a36d0d614e9'}

CONTAINER07_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.10.0', 'sha256': '28c130f83be7b7ac6786759c1b625b0d316497104fc5f635a485f923e755758d'}
CONTAINER08_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.11.0', 'sha256': 'd6d7782d0d111876c1fa2102703cebc52de981c6b6c36cccd88fc2f6524fc60c'}

DECIMAL207_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.12.0', 'sha256': 'f2c2495fdfab81d555194e5a3dfafe1c7cf58e17035fe5b03698e2808d3b027f'}

DECIMAL208_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.13.0', 'sha256': 'd660fab21eabe2d52ef0609cafcea6112f506786e359424235714718f6c769a7'}

RECURSIVE07_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.15.0', 'sha256': 'a69a3035fcc0927730977ad05a1f60b0d10ec765413ab7c57d763f14d409c455'}

def evaluate_catalog_support(prepared):
    """Evaluate only the exact selected policy before native catalog effects.

    Unregistered pins remain unavailable. No owner-known declaration is turned
    into value enforcement, complete assertion coverage or installation authority.
    """
    _require_original_preparation(prepared)
    choices=prepared.input()
    selected=choices['supportProfile']
    if selected not in (PROFILE,RELATIONAL_PROFILE,SCALAR_PROFILE,NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE,RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE):
        return {'state':'unavailable','reason':'unregistered_support_policy'}
    decimal2=selected in (DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    containers=selected in (CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    current=selected in (CORE08_PROFILE,FACET08_PROFILE,CONTAINER08_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    faceted=selected in (FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    metadata=selected in (RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    inverse=selected in (NAMED_RELATIONSHIP_PROFILE,RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    named=selected in (NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE,RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    scalars=selected in (SCALAR_PROFILE,NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE,RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    relational=selected in (RELATIONAL_PROFILE,SCALAR_PROFILE,NAMED_SCALAR_PROFILE,NAMED_RELATIONSHIP_PROFILE,RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE,DECIMAL207_PROFILE,DECIMAL208_PROFILE,REFERENCE08_PROFILE,RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE)
    policy=files('truss').joinpath('_profiles/fresh-catalog-support-declarative08.json' if selected==DECLARATIVE08_PROFILE else '_profiles/fresh-catalog-support-recursive07.json' if selected==RECURSIVE07_PROFILE else '_profiles/fresh-catalog-support-recursive08.json' if selected==RECURSIVE08_PROFILE else '_profiles/fresh-catalog-support-references08.json' if selected==REFERENCE08_PROFILE else '_profiles/fresh-catalog-support-decimal208.json' if selected==DECIMAL208_PROFILE else '_profiles/fresh-catalog-support-decimal207.json' if selected==DECIMAL207_PROFILE else '_profiles/fresh-catalog-support-containers08.json' if selected==CONTAINER08_PROFILE else '_profiles/fresh-catalog-support-containers07.json' if selected==CONTAINER07_PROFILE else '_profiles/fresh-catalog-support-numeric08.json' if selected==FACET08_PROFILE else '_profiles/fresh-catalog-support-numeric07.json' if selected==FACET07_PROFILE else '_profiles/fresh-catalog-support-core08.json' if current else '_profiles/fresh-catalog-support-retained-metadata.json' if metadata else '_profiles/fresh-catalog-support-named-relationships.json' if inverse else '_profiles/fresh-catalog-support-named-scalars.json' if named else '_profiles/fresh-catalog-support-scalars.json' if scalars else '_profiles/fresh-catalog-support-relational.json' if relational else '_profiles/fresh-catalog-support.json').read_bytes()
    if not 1<=len(policy)<=4096 or sha256(policy).hexdigest()!=selected['sha256']:
        raise ValueError('Original selected catalog support policy required')
    if (choices['binding']!={'state':'absent'} or choices['transforms']
        or any(d['ingress']!={'kind':'native'} for d in choices['documents'])
        or any(d.observation()['source']['umf']!=('0.8.0' if current else '0.7.0') for d in prepared.documents)):
        raise ValueError('Unselected catalog support source')
    evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
    ordinary=evidence.get('interfaceVersion')=='truss-registration-preparation/1.0'
    if ordinary:
        expected=[{'documentId':d.document.document_id,
            'contentSha256':sha256(d.document.content).hexdigest(),
            'sourceValidation':d.observation()['sourceValidation'],
            'targetValidation':d.observation()['targetValidation']} for d in prepared.documents]
        if evidence!={'interfaceVersion':'truss-registration-preparation/1.0','documents':expected}:
            raise ValueError('Original registration validation results required')
    else:
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
            property_names=set()
            for field in record['fields']:
                identity=(record['documentId'],field['fieldModule'],field['fieldId'])
                source=source_elements.get(identity)
                if source!=field['declaration']:
                    raise ValueError('Original staged Field source correspondence required')
                for name in ('kind','nullability','cardinality'):
                    if type(source.get(name)) is not str or not 1<=len(source[name].encode('utf8'))<=4096:
                        raise ValueError('Selected Field requires explicit authored metadata')
                # A Truss property binding is distinct from the optional UMF name.
                # Preserve the declaration and bind unnamed fields by stable ID.
                property_name=source['name'] if 'name' in source else source['id']
                if (type(property_name) is not str or not 1<=len(property_name.encode('utf8'))<=4096
                        or '\0' in property_name):
                    raise ValueError('Valid Truss property name or field ID required')
                if property_name in property_names:
                    raise ValueError('Duplicate Truss property binding name')
                property_names.add(property_name)
                staged.add(identity)
                if 'scalarType' not in source:
                    unresolved.append({'documentId':identity[0],'moduleId':identity[1],'elementId':identity[2],'duty':'value_family_unresolved'})
    if ordinary:
        inventory=_closed_source_inventory(prepared,None,None,relational=relational,scalars=scalars,
            named=named,inverse=inverse,metadata=metadata,current=current,faceted=faceted,
            containers=containers,decimal2=decimal2,
            recursive=selected in (RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE),
            standalone_scalars=selected==DECLARATIVE08_PROFILE,ordinary=True)
        # Ordinary reports describe the actual native catalog capability. The
        # retained AcceptanceInput selector is not a claim that an older
        # experimental subset describes this release's complete storage API.
        profiles=json.loads(files('truss').joinpath('_catalog_runtime/capability-profiles.json').read_bytes())
        capability=next(entry for entry in profiles['profiles'] if entry['name']=='catalog')
        definition=capability['definition'].encode('utf8')
        if sha256(definition).hexdigest()!=capability['pin']['sha256']:
            raise ValueError('Original native catalog capability definition required')
        return {'state':'evaluated','profile':dict(selected),'registrationSummary':evidence,
            'supportedSubset':{'identity':capability['pin']['identity']+'/'+capability['pin']['version'],
                'bytesBase64':base64.b64encode(definition).decode('ascii'),
                'sha256':capability['pin']['sha256']},'closedSourceInventory':inventory}
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
            'scope':'original_0.8_native_catalog_metadata_preflight_only' if current else 'original_0.7_native_catalog_metadata_preflight_only',
            'requiredObservations':required,'retainedObservations':retained,
            'unresolvedValueFamilies':unresolved,
            'originalTransitions':[d.observation()['transition'] for d in prepared.documents],
            'originalDiagnostics':evidence['validation'],
            'retainedExtensions':evidence['retainedExtensions'],
            'observationCoverage':coverage,'assertionInventoryComplete':False,
            'enforcementQualified':False,'supportSemanticsQualified':False,
            'acceptedReportQualified':False,
            'closedSourceInventory':_closed_source_inventory(prepared,observations,core,relational=relational,scalars=scalars,named=named,inverse=inverse,metadata=metadata,current=current,faceted=faceted,containers=containers,decimal2=decimal2,recursive=selected in (RECURSIVE07_PROFILE,DECLARATIVE08_PROFILE,RECURSIVE08_PROFILE),standalone_scalars=selected==DECLARATIVE08_PROFILE)}

    if len(json.dumps(decision,ensure_ascii=True,separators=(',',':')).encode('utf8'))>4194304:
        raise ValueError('Selected catalog support decision capacity exceeded')
    return decision


def _closed_source_inventory(prepared, observations, core, *, relational=False,scalars=False,named=False,inverse=False,metadata=False,current=False,faceted=False,containers=False,decimal2=False,recursive=False,standalone_scalars=False,ordinary=False):
    """Complete source occurrence inventory for explicit scalar string Records.

    Profile 0.2 additionally covers known authored Keys and Relationships.
    Profile 0.17 permits otherwise-admitted standalone singular scalars only.
    This proves source coverage, not value enforcement or accepted execution.
    Broader preparation remains intact and explicitly outside this branch.
    """
    unavailable={'state':'unavailable','reason':'outside_closed_scalar_record_subset'}
    if metadata and not ordinary: verified_retained_metadata(prepared)
    expected={}
    kinds={}
    authored={}
    declaration_values={}
    documents={d['documentId']:catalog_source_artifact(prepared,d['documentId']) for d in prepared.input()['documents']}
    for document in prepared.documents:
        source=document.observation()['source']
        if source['umf']!=('0.8.0' if current else '0.7.0') or set(source)-({'umf','id','modules','vocabularies','extensions'}|({'title'} if compact_catalog_sources(prepared) else set())):
            return unavailable
        if not metadata and (source.get('vocabularies',{})!={} or source.get('extensions',{})!={}):
            return unavailable
        item_refs=set()
        fields=set();owned=set();singular_scalars=set()
        for mi,module in enumerate(source['modules']):
            if set(module)-(({'id','namespace','elements','extensions','relationships'} if relational else {'id','namespace','elements','extensions'}) | ({'actions'} if metadata else set())) or (not metadata and module.get('extensions',{})!={}):
                return unavailable
            for ei,element in enumerate(module['elements']):
                pointer=f'/modules/{mi}/elements/{ei}'
                kind=element.get('kind')
                kinds[(document.document.document_id,module['id'],element['id'])]=kind
                allowed=((({'id','kind','members','extensions','keys'} if relational else {'id','kind','members','extensions'}) | ({'name'} if named else set())) if kind=='record' else
                         {'id','kind','name','scalarType','nullability','cardinality','extensions'})
                if faceted and kind=='field':allowed=allowed|{'facets'}
                if containers and kind=='field':allowed=allowed|{'itemType'}
                if current:allowed=allowed|{'title','description','aliases','examples'}|({'facets','allowedValues','default'} if kind=='field' else set())
                if kind not in ('record','field') or set(element)-allowed or (not metadata and element.get('extensions',{})!={}):
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
                    container=containers and element.get('cardinality') in ('array','map')
                    if (element.get('nullability') not in ('required','absent-allowed') or ('name' in element and (type(element['name']) is not str or not element['name']))):return unavailable
                    if container:
                        ref=element.get('itemType')
                        if ('scalarType' in element or element.get('facets',{})!={} or type(ref) is not dict or set(ref)!={'module','element'}):return unavailable
                        seen=set()
                        while True:
                            if type(ref) is not dict or set(ref)!={'module','element'}:return unavailable
                            identity=(ref['module'],ref['element'])
                            if identity in seen or len(seen)>=32:return unavailable
                            seen.add(identity);item_refs.add(identity)
                            target=next((f for m in source['modules'] if m['id']==ref['module'] for f in m['elements'] if f['id']==ref['element']),None)
                            if target is None or target.get('kind')!='field' or target.get('nullability')!='required':return unavailable
                            if target.get('cardinality')=='one':
                                if target.get('scalarType') not in ('string','integer','decimal','boolean','timestamp','binary') or 'itemType' in target:return unavailable
                                break
                            if not recursive or target.get('cardinality') not in ('array','map') or 'scalarType' in target or target.get('facets',{})!={}:return unavailable
                            ref=target.get('itemType')
                    elif element.get('scalarType') not in (('string','integer','decimal','boolean','timestamp','binary') if scalars else ('string',)) or element.get('cardinality')!='one' or 'itemType' in element:return unavailable
                    fields.add((module['id'],element['id']))
                    if not container:singular_scalars.add((module['id'],element['id']))
                    operations.extend(('nullability','cardinality'))
                    if not container:operations.append('scalarType')
                    if faceted and 'facets' in element:
                        facet=element['facets'];family=element.get('scalarType')
                        signed=(family=='integer' and facet=={'integerWidth':{'bits':64,'signed':True}} and type(facet['integerWidth']['bits']) is int and type(facet['integerWidth']['signed']) is bool)
                        decimal=(family=='decimal' and facet in (({'precision':18,'scale':4},{'precision':18,'scale':2}) if decimal2 else ({'precision':18,'scale':4},)) and type(facet['precision']) is int and type(facet['scale']) is int)
                        if ordinary and family=='decimal' and facet=={'precision':12,'scale':2}:decimal=True
                        if facet!={} and not (signed or decimal):return unavailable
                    if (current or faceted) and 'facets' in element:
                        operations.append('facets');declaration_values[(document.document.document_id,'facets',module['id'],element['id'])]=element['facets']
                    if current:
                        for prop in ('allowedValues','default'):
                            if prop in element:expected[(document.document.document_id,pointer+'/'+prop)]='core.schema_properties.'+prop
                for operation in operations:
                    expected[(document.document.document_id,pointer+'/'+operation)]='core.'+operation
            if relational and 'relationships' in module:
                values=module['relationships']
                if type(values) is not list:return unavailable
                declaration_values[(document.document.document_id,'relationships',module['id'],None)]=values
                for ri,relation in enumerate(values):
                    if (type(relation) is not dict or set(relation)-({'id','name','source','target','sourceMultiplicity','targetMultiplicity','targetLifecycle','directed'}|({'inverse'} if inverse else set())|({'extensions'} if ordinary else set()))
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
        if not (owned | item_refs) <= fields or not (fields - (owned | item_refs)) <= (singular_scalars if standalone_scalars else set()):
            return unavailable
    if ordinary:
        # Storage support is decided from the validated original definitions.
        # This is not an exhaustive inspection/enforcement evidence inventory.
        return {'state':'supported','scope':'validated_original_storage_definitions'}
    classifications=[]
    for observed in observations['observations']:
        operation=observed['operation'];identity=observed['identity']
        kind=kinds.get((observed['documentId'],identity.get('module'),identity.get('element')))
        if operation=='schema_properties' and current:
            original=observed['result']
            if original['state']!='observed' or observed['basis']!='original':raise ValueError('Original current schema properties required')
            classification='original_current_properties_retained_no_native_enforcement'
        elif operation=='schema_properties':
            classification='reversible_target_retained_original_source_has_no_schema_properties'
        else:
            if observed['result']['state']!='observed' or observed['basis']!='original':
                raise ValueError('Original closed-source observation required')
            meaning=observed['result']['observation']['meaning']
            declaration=declaration_values.get((observed['documentId'],operation,identity.get('module'),identity.get('element')))
            if ((relational and operation in ('relationships','keys')) or ((current or faceted) and operation=='facets')) and declaration is not None:
                expected_state='known';classification='original_assertion'
                if not same_owner_evidence(meaning.get(operation),declaration):
                    raise ValueError('Original authored declaration meaning correspondence required')
            elif operation in ('relationships','keys','referenceLinks') or (operation=='facets' and kind=='field'):
                expected_state='missing';classification='authored_absence'
            elif (containers and kind=='field' and operation=='scalarType' and any(e.get('cardinality') in ('array','map') for d in prepared.documents if d.document.document_id==observed['documentId'] for m in d.observation()['source']['modules'] if m['id']==identity.get('module') for e in m['elements'] if e['id']==identity.get('element'))):
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
        observed=resolve_catalog_observation(prepared,owner)
        path=observed['path']
        authored_entry=key in authored
        descendant_rule=entry['ruleName'] in ('core.members.member','core.keys','core.relationships')
        schema_property=entry['ruleName'].removeprefix('core.schema_properties.')
        property_path=(current and owner['operation']=='schema_properties' and schema_property in ('default','allowedValues') and key[1]==path+'/'+schema_property and schema_property in observed['properties'])
        expected_kind='authored' if authored_entry else 'source'
        if (owner['documentId']!=key[0] or owner['basis']!='original'
            or (observed.get('meaning',{}).get('state')!='known' and not (current and owner['operation']=='schema_properties'))
            or (path!=key[1] and not (descendant_rule and key[1].startswith(path+'/')) and not property_path)
            or entry['enforcement']!='none' or entry['reason']!='unqualified'
            or assertion['owner']!={'documentId':key[0],'moduleId':owner['identity']['module']}
            or assertion['sourceKind']!='umf_document' or assertion['kind']!=expected_kind
            or (not authored_entry and assertion.get('sourceIdentityProfile')!=core['profile'])
            or (authored_entry and (assertion.get('authoredIdentity')!=authored[key] or 'sourceIdentityProfile' in assertion))
            or entry['ruleNameOrigin']!='profile_generated'
            or entry['source']!=documents[key[0]]
            or (entry['ruleName'] not in ('core.'+owner['operation'],'core.members.member') and not (current and owner['operation']=='schema_properties' and entry['ruleName'] in ('core.schema_properties.default','core.schema_properties.allowedValues')))
            or assertion['definitionPin']!=owner['contentSha256']
            or entry['source']['sha256']!=owner['contentSha256']):
            raise ValueError('Original closed-source meaning correspondence required')
    if seen!=set(expected):
        raise ValueError('Complete closed-source assertion occurrence coverage required')
    return {'state':'inventoried','scope':('original_0.8_explicit_exact_scalar_records_string_keys_relationships_and_known_facets' if current else 'original_0.7_explicit_exact_scalar_records_string_keys_relationships' if scalars else 'original_0.7_explicit_scalar_string_records_keys_relationships' if relational else 'original_0.7_explicit_scalar_string_records'),
            'assertionOccurrenceCoverageComplete':True,'entries':entries,'extensions':[],
            'observationClassifications':classifications,
            'enforcementQualified':False,'acceptedReportQualified':False}


def verified_retained_metadata(prepared):
    _require_original_preparation(prepared)
    evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
    documents={d['documentId']:d['artifact'] for d in prepared.input()['documents']}
    profiles={d['documentId']:d['umfProfile'] for d in prepared.input()['documents']}
    sources={d.document.document_id:d.observation()['source'] for d in prepared.documents}
    def read(artifact):
        raw=base64.b64decode(artifact['bytesBase64'],validate=True)
        if sha256(raw).hexdigest()!=artifact['sha256']:raise ValueError('Original retained artifact hash required')
        return decode_owner_evidence_json(raw)
    diagnostics={}
    for wrapper in evidence['validation']['diagnostics']:
        value=read(wrapper['diagnostic'])
        doc=value['documentId']
        if value['contentSha256']!=documents[doc]['sha256'] or wrapper['source']['artifact']!=documents[doc] or value['profile']!=wrapper['diagnosticProfile'] or value['producer']!=profiles[doc]:
            raise ValueError('Original diagnostic/source correspondence required')
        if value['basis']=='original':
            diagnostic=value['diagnostic']
            diagnostics[(doc,diagnostic['code'],diagnostic['path'])]=diagnostic
    expected={}
    escape=lambda value:value.replace('~','~0').replace('/','~1')
    for doc,source in sources.items():
        def add(node,path,owner,scope):
            for name,payload in node.get('extensions',{}).items():
                expected[(doc,path+'/extensions/'+escape(name))]={'owner':owner,'scope':scope,
                    'sourcePointer':path+'/extensions/'+escape(name),'extensionId':name,
                    'vocabulary':source['vocabularies'][name],'payload':payload,'source':documents[doc]}
        add(source,'',{'scope':'document','documentId':doc},'document')
        for mi,module in enumerate(source['modules']):
            owner={'documentId':doc,'moduleId':module['id']};path=f'/modules/{mi}'
            if 'actions' in module:
                warning=diagnostics.get((doc,'UNKNOWN_CORE_FIELD',path+'/actions'))
                if warning is None or warning.get('severity')!='warning':
                    raise ValueError('Original owner-uninterpreted module actions diagnostic required')
            add(module,path,owner,'module')
            for ei,element in enumerate(module['elements']):add(element,path+f'/elements/{ei}',owner,'element')
    artifacts=evidence['retainedExtensions']['extensions'];seen=set()
    for artifact in artifacts:
        value=read(artifact);source=value['source'];doc=next((d for d,a in documents.items() if a==source),None)
        key=(doc,value['sourcePointer'])
        if key in seen or key not in expected or set(value)!={'interfaceVersion','interpretation',*expected[key]} or value['interfaceVersion']!='truss-original-extension-occurrence/0.1.0' or value['interpretation']!='retained_uninterpreted':
            raise ValueError('Original extension occurrence bijection required')
        if not same_owner_evidence({k:value[k] for k in expected[key]},expected[key]):
            raise ValueError('Original extension payload/source correspondence required')
        seen.add(key)
    if seen!=set(expected):raise ValueError('Complete retained extension inventory required')
    return artifacts
