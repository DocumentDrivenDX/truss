"""Exact original-source framing, never UMF meaning or native authority.

Raw JSON source values are spliced unchanged. In particular arbitrary unknown
numeric extension tokens never pass through binary floats or a replacement
semantic serializer. The old native registration receipt remains separate.
"""
from hashlib import sha256
from decimal import Decimal
import json
import struct
from ._owner_evidence_json import decode_owner_evidence_json
from ._current_query_sources import _initialize
from ._current_disclosure_pipe import VERSION


def frame_digest(raw):
    if type(raw) is not bytes or not 1<=len(raw)<=16*1024*1024:
        raise ValueError('Bounded original disclosure frame required')
    return sha256(struct.pack('>I',len(raw))+raw).hexdigest()


def object_members(raw):
    # Existing duplicate/Unicode/tree/number bounds apply before slicing.
    value=decode_owner_evidence_json(raw)
    if type(value) is not dict:
        raise ValueError('Original source object required')
    text=raw.decode('utf8');decoder=json.JSONDecoder(parse_float=Decimal)
    def skip(index):
        while index<len(text) and text[index] in ' \t\r\n':index+=1
        return index
    index=skip(0)
    if text[index]!='{':raise ValueError('Original source object required')
    index=skip(index+1);members={}
    while text[index]!='}':
        name,end=decoder.raw_decode(text,index);index=skip(end)
        if type(name) is not str or text[index]!=':':raise ValueError('Original source member required')
        start=skip(index+1);_,end=decoder.raw_decode(text,start)
        members[name]=text[start:end].encode('utf8');index=skip(end)
        if text[index]=='}':break
        if text[index]!=',':raise ValueError('Original source member required')
        index=skip(index+1)
    if set(members)!=set(value):raise ValueError('Exact original source member census required')
    return members


def disclosure_initializer(registered_initialize,owner_raw,selection):
    registered_receipt=_initialize(registered_initialize)
    initialize=object_members(registered_initialize)
    sources=object_members(initialize['sources'])
    if set(sources)!={'policy','catalog','closure','ontology','associationBindings','extensionSelection'}:
        raise ValueError('Complete original registered source fields required')
    if type(decode_owner_evidence_json(owner_raw)) is not dict:
        raise ValueError('Original owner source object required')
    selected=json.dumps(selection,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
    # extensionSelection belongs to the old native registration. It is not a
    # field of the new producer's source envelope, and is never silently added.
    new_sources=b'{'+b','.join(json.dumps(key).encode()+b':'+sources[key] for key in (
        'policy','catalog','closure','ontology','associationBindings'))+b'}'
    raw=(b'{"version":'+json.dumps(VERSION).encode()+b',"kind":"initialize","requestId":"init",'
         b'"sources":'+new_sources+b',"owner":'+owner_raw+b',"selection":'+selected+b'}')
    if len(raw)>4*1024*1024:raise ValueError('Bounded disclosure initialization required')
    decode_owner_evidence_json(raw)
    return raw,registered_receipt,frame_digest(raw)


def array_members(raw):
    value=decode_owner_evidence_json(raw)
    if type(value) is not list:
        raise ValueError('Original source array required')
    text=raw.decode('utf8');decoder=json.JSONDecoder(parse_float=Decimal)
    def skip(index):
        while index<len(text) and text[index] in ' \t\r\n':index+=1
        return index
    index=skip(0)+1;index=skip(index);members=[]
    while text[index]!=']':
        start=index;_,end=decoder.raw_decode(text,start);members.append(text[start:end].encode());index=skip(end)
        if text[index]==']':break
        if text[index]!=',':raise ValueError('Original source array required')
        index=skip(index+1)
    if len(members)!=len(value):raise ValueError('Exact original source array census required')
    return members


def disclosure_fact_cut(metadata, *, facts, coverage, graphs, graph_coverage):
    """Transport all captured populations unchanged; never infer completeness."""
    populations={'facts':facts,'coverage':coverage,'graphs':graphs,'graphCoverage':graph_coverage}
    if type(metadata) is not dict or set(metadata)&set(populations):
        raise ValueError('Distinct original cut metadata required')
    for raw in populations.values():
        if type(raw) is not bytes or type(decode_owner_evidence_json(raw)) is not list:
            raise ValueError('Complete original captured population arrays required')
    prefix=json.dumps(metadata,ensure_ascii=True,separators=(',',':'),allow_nan=False).encode()
    return prefix[:-1]+(b',' if metadata else b'')+b','.join(
        json.dumps(name).encode()+b':'+raw for name,raw in populations.items())+b'}'
