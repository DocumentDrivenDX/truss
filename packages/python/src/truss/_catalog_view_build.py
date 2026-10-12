"""Compose a complete view from the protected, verified native catalog basis."""
import base64
from dataclasses import fields, is_dataclass
from hashlib import sha256
import json
from .contracts import ProfilePin, QualifiedOwner, ExactArtifact
from .catalog_view import (CatalogDefinitionReference, CatalogDocumentProvenance,
    CatalogDefinitionEntry, CatalogView)
from ._catalog_definition_source import extract_definition
from ._owner_evidence_json import decode_owner_evidence_json

_EXTRACTION_RULE=b'UTF-8 JSON value slice at RFC6901 pointer; exclude surrounding whitespace; preserve original tokens; v1'
EXTRACTION_PROFILE=ProfilePin(identity='truss-original-json-definition',version='0.1',sha256=sha256(_EXTRACTION_RULE).hexdigest())
_VIEW_RULE=b"""truss-complete-catalog-view/0.1
Supported accepted revision: 1. Complete scope only. Maximum definitions65536, bytes16777216.
Hash serialization: json.dumps(ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8'). SHA256 lowercase hex.
Definition pin input array: [document.rev integer,document.ord integer,original document SHA256 string,authored JSON pointer string,extraction profile wire object,exact value-slice SHA256 string]. Artifact identity equals definition pin.
Inventory hash input: exact ordered definition-entry wire array, including artifacts, provenance and dependency references.
Consistency hash input object: installationId,releaseId,releaseSha256,revision,registrationId,reportSha256; each value exact native text.
Inventory order: type numeric type_id; property numeric prop_id; key numeric(type_id,key_num); relationship numeric rel_type_id.
Type dependencies: authored Record.members order. Property dependencies: owning Record. Key dependencies: owning Record then authored ordered fields. Relationship dependencies: authored source types then each authored target type and its type-local key. Preserve repeated dependencies, including self endpoints.
Key pointers use authored keys array position, not native key_num. Property source owner module is declaration_module. Relationship identity is numeric rel_type_id.
Complete encoded-byte budget includes all view fields. Internal native basis has a separate16MiB bound. No truncation.
"""
VIEW_PROFILE=ProfilePin(identity='truss-complete-catalog-view',version='0.1',sha256=sha256(_VIEW_RULE).hexdigest())


def wire(value):
    if is_dataclass(value):
        result={}
        for item in fields(value):
            if item.name=='original_bytes':continue
            child=getattr(value,item.name)
            if child is None:continue
            parts=item.name.split('_');name=parts[0]+''.join(part.title() for part in parts[1:])
            result[name]=wire(child)
        return result
    if type(value) is tuple:return [wire(item) for item in value]
    return value


def encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')


def build_catalog_view(basis,layout_profile):
    if basis['revision']!='1':raise ValueError('Retained accepted revision required')
    archives={};occurrences={}
    for document in basis['documents']:
        original=document['document'].encode('utf-8')
        if sha256(original).hexdigest()!=document['content_sha256']:raise ValueError('Original archive digest required')
        parsed=decode_owner_evidence_json(original)
        if parsed['id']!=document['doc_id']:raise ValueError('Original archive identity required')
        archives[document['doc_id']]=(document,original)
        for mi,module in enumerate(parsed['modules']):
            for ei,element in enumerate(module['elements']):
                address=(document['doc_id'],module['id'],element['id'])
                if address in occurrences:raise ValueError('Unique source definition required')
                occurrences[address]=(element,f'/modules/{mi}/elements/{ei}')
            for ri,rel in enumerate(module.get('relationships',[])):
                address=(document['doc_id'],module['id'],'relationship',rel['id'])
                if address in occurrences:raise ValueError('Unique source relationship required')
                occurrences[address]=(rel,f'/modules/{mi}/relationships/{ri}')
    entries=[];references={};sources={};native={}
    def add(kind,row,address,identity,**ids):
        source,pointer=occurrences[address]
        doc,original=archives[address[0]]
        if row['definition_document_id']!=address[0] or row['definition_doc_ord']!=doc['ord'] or row['definition_rev']!=doc['rev']:
            raise ValueError('Accepted native source provenance required')
        fragment=extract_definition(original,pointer)
        digest=sha256(fragment).hexdigest()
        pin=sha256(encoded([doc['rev'],doc['ord'],doc['content_sha256'],pointer,wire(EXTRACTION_PROFILE),digest])).hexdigest()
        reference=CatalogDefinitionReference(kind=kind,definition_pin=pin,
            owner=QualifiedOwner(document_id=address[0],module_id=address[1]),authored_identity=identity,**ids)
        provenance=CatalogDocumentProvenance(accepted_catalog_revision=str(doc['rev']),document_ordinal=str(doc['ord']),
            document_revision=doc['doc_revision'],accepted_document_sha256=doc['content_sha256'],
            authored_pointer=pointer,extraction_profile=EXTRACTION_PROFILE)
        key=(kind,tuple(ids.items()))
        if key in references:raise ValueError('Unique native definition reference required')
        references[key]=reference;sources[key]=source;native[key]=row
        entries.append((key,reference,ExactArtifact(identity=pin,bytes_base64=base64.b64encode(fragment).decode(),sha256=digest),provenance))
        return reference
    type_refs={};prop_refs={};key_refs={};type_source={}
    for row in basis['types']:
        address=(row['document_id'],row['module'],row['element'])
        ref=add('type',row,address,row['element'],type_id=str(row['type_id']))
        type_refs[address]=ref;type_source[row['type_id']]=address
    for row in basis['properties']:
        address=(row['definition_document_id'],row['declaration_module'],row['element'])
        ref=add('property',row,address,row['element'],type_id=str(row['type_id']),property_id=str(row['prop_id']))
        prop_refs[(row['type_id'],address[1],address[2])]=ref
    for row in basis['keys']:
        address=type_source[row['type_id']];record,record_pointer=occurrences[address]
        matches=[(i,key) for i,key in enumerate(record.get('keys',[])) if key['id']==row['key_id']]
        if len(matches)!=1:raise ValueError('Exact authored key occurrence required')
        index,key=matches[0];key_address=(*address,'key',key['id'])
        occurrences[key_address]=(key,record_pointer+f'/keys/{index}')
        ref=add('key',row,key_address,key['id'],type_id=str(row['type_id']),key_number=str(row['key_num']))
        key_refs[(row['type_id'],key['id'])]=ref
    for row in basis['relationships']:
        add('relationship',row,(row['document_id'],row['module'],'relationship',row['rel_id']),row['rel_id'],relationship_id=str(row['rel_type_id']))
    definitions=[]
    for key,reference,artifact,provenance in entries:
        source=sources[key];row=native[key];dependencies=[]
        if reference.kind=='type':
            dependencies=[prop_refs[(row['type_id'],member['module'],member['element'])] for member in source['members']]
        elif reference.kind=='property':
            dependencies=[type_refs[type_source[row['type_id']]]]
        elif reference.kind=='key':
            dependencies=[type_refs[type_source[row['type_id']]]]
            components=[prop_refs[(row['type_id'],member['module'],member['element'])] for member in source['fields']]
            if [int(member.property_id) for member in components]!=row['prop_ids']:raise ValueError('Ordered native key components required')
            dependencies.extend(components)
        else:
            source_ids=[];target_ids=[]
            for member in source['source']:
                endpoint=type_refs[(reference.owner.document_id,member['module'],member['element'])]
                dependencies.append(endpoint);source_ids.append(int(endpoint.type_id))
            for member in source['target']:
                endpoint=type_refs[(reference.owner.document_id,member['module'],member['element'])]
                dependencies.extend((endpoint,key_refs[(int(endpoint.type_id),member['key'])]));target_ids.append(int(endpoint.type_id))
            expected={(row['rel_type_id'],s,t) for s in source_ids for t in target_ids}
            actual={(e['rel_type_id'],e['source_type'],e['target_type']) for e in basis['endpoints'] if e['rel_type_id']==row['rel_type_id']}
            if actual!=expected:raise ValueError('Complete relationship endpoints required')
        definitions.append(CatalogDefinitionEntry(reference=reference,
            lifecycle='retired' if row['retired_rev'] is not None else 'active',
            resolution='provisional' if row.get('provisional',False) else 'defined',
            definition=artifact,provenance=provenance,dependencies=tuple(dependencies)))
    inventory=sha256(encoded([wire(entry) for entry in definitions])).hexdigest()
    evidence=sha256(encoded({key:basis[key] for key in ('installationId','releaseId','releaseSha256','revision','registrationId','reportSha256')})).hexdigest()
    view=CatalogView(catalog_revision='1',layout_profile=layout_profile,view_profile=VIEW_PROFILE,
        consistency_evidence_sha256=evidence,definitions=tuple(definitions),inventory_sha256=inventory,original_bytes=b'')
    from dataclasses import replace
    return replace(view,original_bytes=encoded(wire(view)))
