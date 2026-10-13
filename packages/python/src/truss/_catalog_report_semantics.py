"""Executable original report source inputs; installed issuance remains separate."""
import base64
from hashlib import sha256
from importlib.resources import files
import json
from .preparation import _require_original_preparation
from ._catalog_support import CONTAINER07_PROFILE,CONTAINER08_PROFILE,evaluate_catalog_support, verified_retained_metadata, RETAINED_METADATA_PROFILE, CORE08_PROFILE, FACET07_PROFILE, FACET08_PROFILE

PROFILE_SHA256='be634f1d1bdf8f096333e25d15597d2b81af4ace87c9216a8abf304797df2080'
PROFILE={'identity':'truss-catalog-report-semantic-inputs','version':'0.1.0','sha256':PROFILE_SHA256}
ENTRY_FIELDS=('assertion','source','ruleName','ruleNameOrigin','enforcement','reason')


def canonical_numeric_free(value):
    """CONTRACT-009 bytes with logical bounds, no native allocation claim."""
    output=bytearray();nodes=0
    def append(raw):
        if len(output)+len(raw)>4194304:raise ValueError('Canonical report byte capacity exceeded')
        output.extend(raw)
    def string(text):
        append(b'"')
        for character in text:
            code=ord(character)
            if 0xD800<=code<=0xDFFF:raise ValueError('Unicode scalar required')
            if code<32:append(('\\u00'+format(code,'02x')).encode('ascii'))
            elif character in ('"','\\'):append(('\\'+character).encode('ascii'))
            else:append(character.encode('utf8'))
        append(b'"')
    def emit(item,depth):
        nonlocal nodes
        nodes+=1
        if nodes>100000 or depth>128:raise ValueError('Canonical report tree capacity exceeded')
        if item is None:append(b'null')
        elif type(item) is bool:append(b'true' if item else b'false')
        elif type(item) is str:string(item)
        elif type(item) is list:
            if len(item)>4096:raise ValueError('Canonical report array capacity exceeded')
            append(b'[')
            for index,child in enumerate(item):
                if index:append(b',')
                emit(child,depth+1)
            append(b']')
        elif type(item) is dict:
            if len(item)>4096 or any(type(key) is not str for key in item):raise ValueError('Canonical report object required')
            try:keys=sorted(item,key=lambda key:key.encode('utf8'))
            except UnicodeError as error:raise ValueError('Unicode scalar key required') from error
            append(b'{')
            for index,key in enumerate(keys):
                if index:append(b',')
                string(key);append(b':');emit(item[key],depth+1)
            append(b'}')
        else:raise ValueError('Numeric-free canonical report tree required')
    emit(value,0)
    return bytes(output)


def compose_original_catalog_report_semantics(prepared,support):
    _require_original_preparation(prepared)
    if support!=evaluate_catalog_support(prepared):raise ValueError('Original evaluated report support required')
    inventory=support.get('closedSourceInventory',{})
    if inventory.get('state')!='inventoried':
        return {'state':'unavailable','reason':'complete_closed_source_inventory_required'}
    policy=files('truss').joinpath('_profiles/catalog-report-semantic-inputs.json').read_bytes()
    if not 1<=len(policy)<=4096 or sha256(policy).hexdigest()!=PROFILE_SHA256:
        raise ValueError('Original report semantic projection profile required')
    entries=[{key:entry[key] for key in ENTRY_FIELDS} for entry in inventory['entries']]
    def order(entry):
        assertion=entry['assertion'];owner=assertion['owner']
        return tuple(value.encode('utf8') for value in (owner['documentId'],owner['moduleId'],assertion['sourcePointer'],entry['ruleName']))
    entries.sort(key=order)
    canonical=canonical_numeric_free(entries)
    digest=sha256(b'truss-canonical/0.1.0\ntruss-catalog-assertion-inventory/0.1.0\n'+canonical).hexdigest()
    groups=[]
    for document in prepared.input()['documents']:
        membership={'version':next(d.observation()['source']['umf'] for d in prepared.documents if d.document.document_id==document['documentId']),'interpretationProfile':document['umfProfile'],
                    'supportedSubset':support['supportedSubset']}
        group=next((group for group in groups if group['umf']==membership),None)
        if group is None:
            group={'umf':membership,'documentIds':[]};groups.append(group)
        group['documentIds'].append(document['documentId'])
    return {'state':'source_fields_ready','projectionProfile':dict(PROFILE),
            'projectionArtifact':{'identity':'truss.catalog-report-semantic-inputs/0.1.0',
                'bytesBase64':base64.b64encode(policy).decode('ascii'),'sha256':PROFILE_SHA256},
            'umf':[group['umf'] for group in groups],'umfMembership':groups,'extensions':verified_retained_metadata(prepared) if support['profile'] in (RETAINED_METADATA_PROFILE,CORE08_PROFILE,FACET07_PROFILE,FACET08_PROFILE,CONTAINER07_PROFILE,CONTAINER08_PROFILE) else [],
            'assertionEntries':entries,'canonicalAssertionBytesBase64':base64.b64encode(canonical).decode('ascii'),
            'assertionInventorySha256':digest,
            'unresolvedBindings':['installedLayoutProfile','enforcementReportProfile','originalExecution','acceptanceReportProfile'],
            'acceptedReportQualified':False}


def compose_catalog_report_semantics(prepared,support,revision):
    """Join the actual native revision to the original revision-free sources."""
    result=compose_original_catalog_report_semantics(prepared,support)
    if result['state']!='source_fields_ready':return result
    if (type(revision) is not str or not revision.isascii() or not revision.isdecimal()
        or str(int(revision))!=revision or not 0<int(revision)<=2147483647):
        raise ValueError('Canonical native catalog revision required')
    return {**result,'catalogRevision':revision}
