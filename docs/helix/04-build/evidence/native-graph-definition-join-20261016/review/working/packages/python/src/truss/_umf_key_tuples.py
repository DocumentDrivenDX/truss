"""Original UMF string-key batch producer; no native uniqueness authority."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from importlib.resources import files
import json
import base64
import shutil
import subprocess
from time import monotonic
from .contracts import TextValue, BooleanValue
from .preparation import _capture
from ._owner_evidence_json import decode_owner_evidence_json
from ._umf_keys_release import MANIFEST_SHA256
from ._umf_keys08_release import MANIFEST_SHA256 as CORE08_MANIFEST_SHA256


@dataclass(frozen=True,slots=True)
class KeyTupleRequest:
    module_id: str
    record_id: str
    key_id: str
    values: tuple[str | TextValue | BooleanValue,...]


@dataclass(frozen=True,slots=True)
class OriginalKeyTuple:
    request: KeyTupleRequest
    document_sha256: str
    original_receipt_bytes: bytes
    tuple_bytes: bytes


def _same_json_meaning(left,right):
    # The owner's JSON parser may normalize 1.0 to 1, but boolean is never a
    # number. Original source bytes remain independently retained and hashed.
    if type(left) in (int,Decimal) and type(right) in (int,Decimal):return left==right
    if type(left) is not type(right):return False
    if type(left) is dict:return left.keys()==right.keys() and all(_same_json_meaning(left[key],right[key]) for key in left)
    if type(left) is list:return len(left)==len(right) and all(_same_json_meaning(a,b) for a,b in zip(left,right))
    return left==right


def key_value_from_cell(cell):
    """Carry native exact cells to UMF without interpreting numeric tokens."""
    if type(cell) is not dict:raise ValueError('Exact key cell required')
    if set(cell)=={'kind','value'} and cell['kind']=='boolean' and type(cell['value']) is bool:
        return BooleanValue(value=cell['value'])
    if set(cell)=={'kind','text'} and cell['kind'] in ('string','integer','decimal','binary') and type(cell['text']) is str:
        return TextValue(kind=cell['kind'],text=cell['text'])
    raise ValueError('Admitted exact key family required')


def _owner_key_value(value):
    if type(value) is str:return {'string':value}
    if type(value) is BooleanValue and type(value.value) is bool:return {'boolean':value.value}
    if type(value) is TextValue and type(value.text) is str:
        if value.kind=='string':return {'string':value.text}
        if value.kind=='integer':return {'integerToken':value.text}
        if value.kind=='decimal':return {'decimalToken':value.text}
        if value.kind=='binary':return {'binaryHex':base64.b64decode(value.text,validate=True).hex()}
    raise ValueError('Exact UMF key carrier required')


def encode_string_key_tuples(original_document: bytes,requests: tuple[KeyTupleRequest,...],*,bun_executable: str='bun',deadline=None) -> tuple[OriginalKeyTuple,...]:
    if type(requests) is not tuple or any(type(r) is not KeyTupleRequest or type(r.values) is not tuple or any(type(v) is not str for v in r.values) for r in requests):
        raise ValueError('Immutable string key requests required')
    return encode_key_tuples(original_document,requests,bun_executable=bun_executable,deadline=deadline)


def encode_key_tuples(original_document: bytes,requests: tuple[KeyTupleRequest,...],*,bun_executable: str='bun',deadline=None) -> tuple[OriginalKeyTuple,...]:
    if type(original_document) is not bytes or not 0<len(original_document)<=1048576:
        raise ValueError('Bounded original accepted document bytes required')
    source=decode_owner_evidence_json(original_document)
    if type(source) is not dict or source.get('umf') not in ('0.7.0','0.8.0'):raise ValueError('Selected UMF 0.7 or 0.8 original source required')
    if type(requests) is not tuple or not 1<=len(requests)<=512:raise ValueError('Bounded ordered key batch required')
    if len(original_document)*len(requests)>4194304:raise ValueError('Aggregate original source budget exceeded')
    wire=[]
    for request in requests:
        if type(request) is not KeyTupleRequest or type(request.values) is not tuple or not request.values:
            raise ValueError('Immutable string key request required')
        for value in (request.module_id,request.record_id,request.key_id):
            if type(value) is not str:raise ValueError('Exact string key identities and values required')
            value.encode('utf-8')
        if not all((request.module_id,request.record_id,request.key_id)) or any('\0' in value for value in (request.module_id,request.record_id,request.key_id)):
            raise ValueError('Qualified Record/Key identity required')
        wire.append({'identity':{'module':request.module_id,'element':request.record_id,'key':request.key_id},
            'values':[_owner_key_value(value) for value in request.values]})
    payload=json.dumps({'sourceText':original_document.decode('utf-8'),'requests':wire},ensure_ascii=True,separators=(',',':')).encode()
    if len(payload)>1048576:raise ValueError('Aggregate key input budget exceeded')
    current=source['umf']=='0.8.0'
    root=files('truss').joinpath('_umf_keys08' if current else '_umf_keys');manifest_bytes=root.joinpath('manifest.json').read_bytes()
    if sha256(manifest_bytes).hexdigest()!=(CORE08_MANIFEST_SHA256 if current else MANIFEST_SHA256):raise ValueError('Original key producer manifest required')
    manifest=json.loads(manifest_bytes)
    for name,digest in manifest['files'].items():
        if sha256(root.joinpath(name).read_bytes()).hexdigest()!=digest:raise ValueError('Original key producer assets required')
    executable=shutil.which(bun_executable)
    if executable is None:raise ValueError('Selected Bun runtime unavailable')
    def timeout(maximum):
        if deadline is None:return maximum
        deadline.check()
        return min(maximum,max(0.001,deadline.end-monotonic()))
    def capture(command,*,maximum,**kwargs):
        try:return _capture(command,timeout=timeout(maximum),**kwargs)
        except subprocess.TimeoutExpired:
            if deadline is not None:deadline.check()
            raise
    version=capture([executable,'--version'],limit=256,maximum=5)
    if version.returncode or version.stdout.strip().decode()!=manifest['runtimeVersion']:raise ValueError('Selected Bun runtime required')
    result=capture([executable,str(root.joinpath('bridge.mjs'))],input_bytes=payload,limit=8388608,maximum=10)
    if result.returncode:raise ValueError('Original key producer unavailable')
    response=decode_owner_evidence_json(result.stdout)
    if type(response) is not dict or set(response)!= {'status','receiptTexts'} or response['status']!='encoded' or type(response['receiptTexts']) is not list or len(response['receiptTexts'])!=len(requests):
        raise ValueError('UMF key tuple refused')
    outputs=[]
    for index,(request,expected) in enumerate(zip(requests,wire)):
        text=response['receiptTexts'][index]
        if type(text) is not str:raise ValueError('Original receipt text required')
        raw=text.encode('utf-8');receipt=decode_owner_evidence_json(raw)
        if type(receipt) is not dict or set(receipt)!={'operation','version','profile','source','identity','values','keyPath','bytesHex'}:
            raise ValueError('Complete original UMF key receipt required')
        if receipt['operation']!='encode-core-key-tuple' or receipt['version']!=('3.0.0' if current else '2.0.0') or receipt['profile']!='umf-key-tuple-v1':
            raise ValueError('Selected original UMF key receipt required')
        if receipt['identity']!=expected['identity'] or receipt['values']!=expected['values'] or not _same_json_meaning(receipt['source'],source):
            raise ValueError('Original source and ordered key correspondence required')
        key=bytes.fromhex(receipt['bytesHex'])
        if key.hex()!=receipt['bytesHex']:raise ValueError('Exact original tuple byte carrier required')
        outputs.append(OriginalKeyTuple(request,sha256(original_document).hexdigest(),raw,key))
    return tuple(outputs)


@dataclass(frozen=True,slots=True)
class OriginalLiteralKeyTuple:
    original_document: bytes
    identity: tuple[str,str,str]
    literal_texts: tuple[str,...]
    original_receipt_bytes: bytes
    tuple_bytes: bytes


def encode_literal_key_tuple(original_document:bytes,identity:tuple[str,str,str],literal_texts:tuple[str,...],*,bun_executable:str='bun')->OriginalLiteralKeyTuple:
    """Original Core0.8 parses/encodes values; output grants no native authority."""
    if type(original_document) is not bytes or not 1<=len(original_document)<=1048576:
        raise ValueError('Bounded original source required')
    source_text=original_document.decode('utf8',errors='strict')
    source=decode_owner_evidence_json(original_document)
    if type(source) is not dict or source.get('umf')!='0.8.0':raise ValueError('Original Core0.8 source required')
    if (type(identity) is not tuple or len(identity)!=3 or any(type(v) is not str or not 1<=len(v.encode('utf8'))<=4096 or '\0' in v for v in identity)
            or type(literal_texts) is not tuple or not 1<=len(literal_texts)<=32
            or any(type(v) is not str or not 1<=len(v.encode('utf8'))<=65536 for v in literal_texts)
            or sum(len(v.encode('utf8')) for v in literal_texts)>1048576):
        raise ValueError('Exact ordered original literal texts required')
    selected={'module':identity[0],'element':identity[1],'key':identity[2]}
    payload=json.dumps({'sourceText':source_text,'requests':[{'identity':selected,'literalTexts':literal_texts}]},ensure_ascii=True,separators=(',',':')).encode()
    if len(payload)>1048576:raise ValueError('Aggregate original key input budget exceeded')
    root=files('truss').joinpath('_umf_keys08');manifest_bytes=root.joinpath('manifest.json').read_bytes()
    if sha256(manifest_bytes).hexdigest()!=CORE08_MANIFEST_SHA256:raise ValueError('Original key producer manifest required')
    manifest=json.loads(manifest_bytes)
    for name,digest in manifest['files'].items():
        if sha256(root.joinpath(name).read_bytes()).hexdigest()!=digest:raise ValueError('Original key producer assets required')
    executable=shutil.which(bun_executable)
    if executable is None:raise ValueError('Selected Bun runtime unavailable')
    version=_capture([executable,'--version'],limit=256,timeout=5)
    if version.returncode or version.stdout.strip().decode()!=manifest['runtimeVersion']:raise ValueError('Selected Bun runtime required')
    result=_capture([executable,str(root.joinpath('bridge.mjs'))],input_bytes=payload,limit=8388608,timeout=10)
    if result.returncode:raise ValueError('Original key producer unavailable')
    response=decode_owner_evidence_json(result.stdout)
    if (type(response) is not dict or set(response)!={'status','receiptTexts'} or response['status']!='encoded'
            or type(response['receiptTexts']) is not list or len(response['receiptTexts'])!=1 or type(response['receiptTexts'][0]) is not str):
        raise ValueError('Original literal key refused')
    raw=response['receiptTexts'][0].encode('utf8');receipt=decode_owner_evidence_json(raw)
    if (type(receipt) is not dict or set(receipt)!={'operation','version','profile','source','identity','values','keyPath','bytesHex'}
            or receipt['operation']!='encode-core-key-tuple' or receipt['version']!='3.0.0' or receipt['profile']!='umf-key-tuple-v1'
            or receipt['identity']!=selected or not _same_json_meaning(receipt['source'],source)
            or type(receipt['values']) is not list or len(receipt['values'])!=len(literal_texts)
            or type(receipt['keyPath']) is not str or not receipt['keyPath']
            or type(receipt['bytesHex']) is not str or not 2<=len(receipt['bytesHex'])<=8388608):
        raise ValueError('Complete original source-bound key receipt required')
    key=bytes.fromhex(receipt['bytesHex'])
    if key.hex()!=receipt['bytesHex']:raise ValueError('Exact original key bytes required')
    # Original bridge verified the whole receipt with the original owner.
    return OriginalLiteralKeyTuple(original_document,identity,literal_texts,raw,key)
