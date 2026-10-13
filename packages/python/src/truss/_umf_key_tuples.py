"""Original UMF string-key batch producer; no native uniqueness authority."""
from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
from importlib.resources import files
import json
import shutil
from .preparation import _capture
from ._owner_evidence_json import decode_owner_evidence_json
from ._umf_keys_release import MANIFEST_SHA256
from ._umf_keys08_release import MANIFEST_SHA256 as CORE08_MANIFEST_SHA256


@dataclass(frozen=True,slots=True)
class KeyTupleRequest:
    module_id: str
    record_id: str
    key_id: str
    values: tuple[str,...]


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


def encode_string_key_tuples(original_document: bytes,requests: tuple[KeyTupleRequest,...],*,bun_executable: str='bun') -> tuple[OriginalKeyTuple,...]:
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
        for value in (request.module_id,request.record_id,request.key_id,*request.values):
            if type(value) is not str:raise ValueError('Exact string key identities and values required')
            value.encode('utf-8')
        if not all((request.module_id,request.record_id,request.key_id)) or any('\0' in value for value in (request.module_id,request.record_id,request.key_id)):
            raise ValueError('Qualified Record/Key identity required')
        wire.append({'identity':{'module':request.module_id,'element':request.record_id,'key':request.key_id},
            'values':[{'string':value} for value in request.values]})
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
    version=_capture([executable,'--version'],limit=256,timeout=5)
    if version.returncode or version.stdout.strip().decode()!=manifest['runtimeVersion']:raise ValueError('Selected Bun runtime required')
    result=_capture([executable,str(root.joinpath('bridge.mjs'))],input_bytes=payload,limit=8388608,timeout=10)
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
