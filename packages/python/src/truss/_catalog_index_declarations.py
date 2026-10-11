"""Original selected immutable index declarations; never installed readiness."""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
import weakref
from .preparation import _require_original_preparation

POLICY_SHA256='332591930fb0f8a370b24e9607ef1f126f1e53ada88cdfed193c848078b31d8d'
SCOPE='original_absent_binding_index_declarations_only'
_issued={}

def _policy_bytes():
    original=files('truss').joinpath('_profiles/absent-binding-index-declarations.json').read_bytes()
    if not 1<=len(original)<=4096 or sha256(original).hexdigest()!=POLICY_SHA256:
        raise ValueError('Original selected index declaration policy required')
    return original

@dataclass(frozen=True,slots=True,weakref_slot=True)
class CatalogIndexDeclarations:
    original_bytes: bytes
    scope: str = SCOPE

def _collect(connection,prepared,revision,cut,policy):
    _require_original_preparation(prepared)
    if (type(revision) is not str or not 1<=len(revision)<=10
        or not revision.isascii() or not revision.isdecimal()
        or str(int(revision))!=revision or not 1<=int(revision)<=2147483647
        or type(cut) is not tuple or len(cut)!=3
        or any(type(v) is not str or not 1<=len(v)<=20 or not v.isascii() or not v.isdecimal()
               or str(int(v))!=v for v in cut)):
        raise ValueError('Original index declaration revision/cut required')
    choices=prepared.input()
    if (choices['binding']!={'state':'absent'} or choices['transforms']!=[]
        or any(d['ingress']!={'kind':'native'} for d in choices['documents'])):
        raise ValueError('Unselected index declaration source requires its original producer')
    rows=connection.run("SELECT truss.runtime_collect_absent_binding_index_declarations(:w,:o,:g,CAST(:rev AS pg_catalog.int4),pg_catalog.decode(:policy,'hex'))::pg_catalog.text",
        w=cut[0],o=cut[1],g=cut[2],rev=revision,policy=policy.hex())
    if len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:
        raise ValueError('Complete native index declaration response required')
    original=rows[0][0].encode('utf8')
    if len(original)>4194304:raise ValueError('Index declaration retention bound exceeded')
    value=json.loads(original)
    expected={'scope':SCOPE,'policyHex':policy.hex(),'policySha256':POLICY_SHA256,
        'inputHex':prepared.input_bytes.hex(),'writerXid':cut[0],
        'operationOrdinal':cut[1],'effectGeneration':cut[2],'revision':revision,
        'declaredJobs':[],'installedProfileQualified':False,'readinessQualified':False,
        'documents':[{'doc_id':d['documentId'],'doc_revision':d['documentRevision'],
            'content_sha256':d['artifact']['sha256'],'ord':str(i)}
            for i,d in enumerate(choices['documents'])]}
    if type(value) is not dict or value.keys()!=expected.keys() or any(
        type(value[k]) is not type(v) or value[k]!=v for k,v in expected.items()):
        raise ValueError('Original index declaration policy/input/source correspondence required')
    return original

def collect_catalog_index_declarations(connection,prepared,revision,cut):
    policy=_policy_bytes()
    original=_collect(connection,prepared,revision,cut,policy)
    result=CatalogIndexDeclarations(original);key=id(result)
    _issued[key]=(weakref.ref(result,lambda ref:_issued.pop(key,None)),connection,
                  prepared,revision,cut,policy,original)
    return result

def require_current_catalog_index_declarations(result,connection,prepared):
    original=_issued.get(id(result))
    if (type(result) is not CatalogIndexDeclarations or original is None
        or original[0]() is not result or original[1] is not connection
        or original[2] is not prepared or type(result.original_bytes) is not bytes
        or result.original_bytes!=original[6] or type(result.scope) is not str
        or result.scope!=SCOPE or _policy_bytes()!=original[5]):
        raise ValueError('Original bound index declaration evidence required')
    if _collect(connection,prepared,original[3],original[4],original[5])!=original[6]:
        raise ValueError('Current original index declaration evidence differs')
