"""Select exact UTF-8 definition bytes from an accepted JSON archive.

JSON interpretation remains with the owner. This helper only locates a source
slice at an explicit JSON pointer after strict archive validation.
"""
import json
from decimal import Decimal
from ._owner_evidence_json import decode_owner_evidence_json


def extract_definition(original: bytes,pointer: str) -> bytes:
    decode_owner_evidence_json(original)
    if type(pointer) is not str or (pointer and not pointer.startswith('/')):
        raise ValueError('An explicit JSON pointer is required')
    tokens=[]
    for encoded in pointer.split('/')[1:] if pointer else ():
        index=0
        while index<len(encoded):
            if encoded[index]=='~':
                if index+1==len(encoded) or encoded[index+1] not in '01':
                    raise ValueError('Invalid JSON pointer escape')
                index+=1
            index+=1
        tokens.append(encoded.replace('~1','/').replace('~0','~'))
    text=original.decode('utf-8')
    decoder=json.JSONDecoder(parse_float=Decimal)
    def skip(index):
        while index<len(text) and text[index] in ' \r\n\t':index+=1
        return index
    start=skip(0)
    for token in tokens:
        cursor=skip(start+1)
        selected=None
        if text[start]=='{':
            while text[cursor]!='}':
                name,cursor=decoder.raw_decode(text,cursor)
                cursor=skip(cursor)
                if text[cursor]!=':':raise ValueError('Invalid archived object')
                value_start=skip(cursor+1)
                _,end=decoder.raw_decode(text,value_start)
                if name==token:selected=value_start;break
                cursor=skip(end)
                if text[cursor]=='}':break
                cursor=skip(cursor+1)
        elif text[start]=='[':
            if not token.isascii() or not token.isdecimal() or (len(token)>1 and token[0]=='0'):
                raise ValueError('Exact array index required')
            ordinal=0
            while text[cursor]!=']':
                _,end=decoder.raw_decode(text,cursor)
                if str(ordinal)==token:selected=cursor;break
                ordinal+=1;cursor=skip(end)
                if text[cursor]==']':break
                cursor=skip(cursor+1)
        if selected is None:raise ValueError('Definition pointer does not resolve')
        start=selected
    _,end=decoder.raw_decode(text,start)
    return text[start:end].encode('utf-8')


def extract_definitions(original: bytes, pointers) -> dict[str, bytes]:
    """Locate requested exact slices in one walk of a strictly validated archive."""
    decode_owner_evidence_json(original)
    requested={}
    prefixes={()}
    for pointer in pointers:
        if type(pointer) is not str or (pointer and not pointer.startswith('/')):
            raise ValueError('An explicit JSON pointer is required')
        tokens=[]
        for encoded in pointer.split('/')[1:] if pointer else ():
            index=0
            while index<len(encoded):
                if encoded[index]=='~':
                    if index+1==len(encoded) or encoded[index+1] not in '01':
                        raise ValueError('Invalid JSON pointer escape')
                    index+=1
                index+=1
            tokens.append(encoded.replace('~1','/').replace('~0','~'))
        path=tuple(tokens)
        requested.setdefault(path,[]).append(pointer)
        prefixes.update(path[:i] for i in range(len(path)+1))
    text=original.decode('utf-8')
    decoder=json.JSONDecoder(parse_float=Decimal)
    result={}
    def skip(index):
        while index<len(text) and text[index] in ' \r\n\t':index+=1
        return index
    def visit(start,path):
        if path not in prefixes or text[start] not in '{[':
            _,end=decoder.raw_decode(text,start)
        else:
            cursor=skip(start+1)
            closing='}' if text[start]=='{' else ']'
            ordinal=0
            while text[cursor]!=closing:
                if closing=='}':
                    token,cursor=decoder.raw_decode(text,cursor)
                    cursor=skip(cursor)
                    if text[cursor]!=':':raise ValueError('Invalid archived object')
                    cursor=skip(cursor+1)
                else:token=str(ordinal)
                cursor=skip(visit(cursor,path+(token,)))
                ordinal+=1
                if text[cursor]==closing:break
                cursor=skip(cursor+1)
            end=cursor+1
        for pointer in requested.get(path,()):
            result[pointer]=text[start:end].encode('utf-8')
        return end
    visit(skip(0),())
    if len(result)!=len(set(pointer for values in requested.values() for pointer in values)):
        raise ValueError('Definition pointer does not resolve')
    return result
