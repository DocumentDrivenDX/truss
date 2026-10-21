# SPDX-License-Identifier: MIT OR Apache-2.0
from ._catalog_source_reference import DATE10_PROFILE
"""Selected catalog metadata policy; incomplete support, never acceptance."""
import base64
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import _require_original_preparation
from ._owner_evidence_json import decode_owner_evidence_json

def evaluate_catalog_support(prepared):
    """Evaluate only the exact selected policy before native catalog effects.

    Unregistered pins remain unavailable. No owner-known declaration is turned
    into value enforcement, complete assertion coverage or installation authority.
    """
    _require_original_preparation(prepared)
    choices=prepared.input()
    selected=choices['supportProfile']
    if selected!=DATE10_PROFILE:
        return {'state':'unavailable','reason':'unregistered_support_policy'}
    policy=files('truss').joinpath('_profiles/fresh-catalog-support-current010.json').read_bytes()
    if not 1<=len(policy)<=4096 or sha256(policy).hexdigest()!=selected['sha256']:
        raise ValueError('Original selected catalog support policy required')
    if (choices['binding']!={'state':'absent'} or choices['transforms']
        or any(d['ingress']!={'kind':'native'} for d in choices['documents'])
        or any(d.source()['umf']!='0.10.0' for d in prepared.documents)):
        raise ValueError('Unselected catalog support source')
    evidence=decode_owner_evidence_json(prepared.report_evidence_bytes)
    if evidence.get('interfaceVersion')!='truss-registration-preparation/2.0':
        raise ValueError('Current registration validation results required')
    expected=[{'documentId':d.document.document_id,
        'contentSha256':sha256(d.document.content).hexdigest(),
        'validation':entry['validation'],**({'dddProfile':entry['dddProfile'],'dddValidation':entry['dddValidation']}
            if 'dddProfile' in entry else {})} for d,entry in zip(prepared.documents,evidence['documents'])]
    if evidence!={'interfaceVersion':'truss-registration-preparation/2.0','documents':expected}:
        raise ValueError('Original registration validation results required')
    source_elements={}
    staged=set()
    unresolved=[]
    for document in prepared.documents:
        source=document.source()
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
    inventory=_storage_support(prepared)
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


def _whole_number(value):
    return type(value) is int or type(value) is float and value.is_integer()


def _storage_support(prepared):
    """Check storage capabilities once over the validated current schema."""
    unavailable={'state':'unavailable','reason':'unsupported_storage_definition'}
    scalar_families={'string','integer','decimal','boolean','timestamp','binary','date'}
    annotations={'title','description','aliases','examples','semanticTypes'}
    for document in prepared.documents:
        source=document.source()
        if source['umf']!='0.10.0' or set(source)-{'umf','id','modules','vocabularies','extensions','title'}:
            return unavailable
        elements={(m['id'],e['id']):e for m in source['modules'] for e in m['elements']}
        fields=set();owned=set();item_refs=set()
        for module in source['modules']:
            if set(module)-{'id','namespace','elements','extensions','relationships','actions'}:return unavailable
            for element in module['elements']:
                kind=element.get('kind')
                if kind=='record':
                    if set(element)-({'id','kind','name','members','extensions','keys'}|annotations):return unavailable
                    if type(element.get('members')) is not list:return unavailable
                    for member in element['members']:
                        if set(member)!={'module','element'}:return unavailable
                        owned.add((member['module'],member['element']))
                    for key in element.get('keys',[]):
                        if set(key)-{'id','name','fields','primary'}:return unavailable
                        if any(set(ref)!={'module','element'} for ref in key['fields']):return unavailable
                elif kind=='field':
                    if set(element)-({'id','kind','name','scalarType','nullability','cardinality','extensions','facets','allowedValues','default','itemType'}|annotations):return unavailable
                    if element.get('nullability') not in ('required','absent-allowed'):return unavailable
                    fields.add((module['id'],element['id']))
                    if element.get('cardinality') in ('array','map'):
                        if 'scalarType' in element or element.get('facets',{})!={}:return unavailable
                        ref=element.get('itemType');seen=set()
                        while True:
                            if type(ref) is not dict or set(ref)!={'module','element'}:return unavailable
                            identity=(ref['module'],ref['element'])
                            if identity in seen or len(seen)>=32:return unavailable
                            seen.add(identity);item_refs.add(identity);target=elements.get(identity)
                            if target is None or target.get('kind')!='field' or target.get('nullability')!='required':return unavailable
                            if target.get('cardinality')=='one':
                                if target.get('scalarType') not in scalar_families or 'itemType' in target:return unavailable
                                break
                            if target.get('cardinality') not in ('array','map') or 'scalarType' in target or target.get('facets',{})!={}:return unavailable
                            ref=target.get('itemType')
                    elif element.get('cardinality')!='one' or element.get('scalarType') not in scalar_families or 'itemType' in element:return unavailable
                    facet=element.get('facets',{});family=element.get('scalarType')
                    if facet:
                        signed=family=='integer' and facet=={'integerWidth':{'bits':64,'signed':True}} and _whole_number(facet['integerWidth']['bits']) and type(facet['integerWidth']['signed']) is bool
                        decimal=family=='decimal' and type(facet) is dict and set(facet)=={'precision','scale'} and _whole_number(facet['precision']) and _whole_number(facet['scale']) and 1<=facet['precision']<=2147483647 and 0<=facet['scale']<=facet['precision']
                        length_facet=facet.get('length') if type(facet) is dict and set(facet)=={'length'} else None
                        length=(type(length_facet) is dict and set(length_facet)=={'max','unit'}
                            and type(length_facet['max']) is not bool and _whole_number(length_facet['max'])
                            and 0<=length_facet['max']<=9007199254740991
                            and ((family=='string' and length_facet['unit']=='unicode-scalar')
                                or (family=='binary' and length_facet['unit']=='byte')))
                        if not (signed or decimal or length):return unavailable
                else:return unavailable
            for relation in module.get('relationships',[]):
                if set(relation)-{'id','name','source','target','sourceMultiplicity','targetMultiplicity','targetLifecycle','directed','inverse','extensions'}:return unavailable
                if relation.get('targetLifecycle') not in ('owned','independent','unspecified'):return unavailable
                if 'inverse' in relation and (type(relation['inverse']) is not str or not 1<=len(relation['inverse'].encode('utf8'))<=4096):return unavailable
                for side in ('source','target'):
                    refs=relation[side];multiplicity=relation[side+'Multiplicity']
                    if any(set(ref)!=({'module','element'} if side=='source' else {'module','element','key'}) for ref in refs):return unavailable
                    if set(multiplicity)!={'min','max'} or not _whole_number(multiplicity['min']) or not 0<=multiplicity['min']<=2147483647:return unavailable
                    if multiplicity['max']!='*' and not (_whole_number(multiplicity['max']) and multiplicity['min']<=multiplicity['max']<=2147483647):return unavailable
        if not (owned|item_refs)<=fields:return unavailable
        # Unowned declarations are metadata only; only singular scalars have a storage meaning.
        if any(elements[identity].get('cardinality')!='one' for identity in fields-(owned|item_refs)):return unavailable
    return {'state':'supported','scope':'validated_original_storage_definitions'}
