# SPDX-License-Identifier: MIT OR Apache-2.0
"""Executable original report source inputs; installed issuance remains separate."""
from .preparation import _require_original_preparation
from ._catalog_support import evaluate_catalog_support


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
    if inventory.get('state')!='supported':
        return {'state':'unavailable','reason':'unsupported_storage_definition'}
    memberships=[]
    for document in prepared.input()['documents']:
        membership={'version':next(d.source()['umf'] for d in prepared.documents
            if d.document.document_id==document['documentId']),
            'interpretationProfile':document['umfProfile'],'supportedSubset':support['supportedSubset']}
        if membership not in memberships:memberships.append(membership)
    return {'state':'source_fields_ready','sourceFormat':'truss-registration-summary/2.0',
        'umf':memberships,'documentValidations':support['registrationSummary']['documents']}


def compose_catalog_report_semantics(prepared,support,revision):
    """Join the actual native revision to the original revision-free sources."""
    result=compose_original_catalog_report_semantics(prepared,support)
    if result['state']!='source_fields_ready':return result
    if (type(revision) is not str or not revision.isascii() or not revision.isdecimal()
        or str(int(revision))!=revision or not 0<int(revision)<=2147483647):
        raise ValueError('Canonical native catalog revision required')
    return {**result,'catalogRevision':revision}
