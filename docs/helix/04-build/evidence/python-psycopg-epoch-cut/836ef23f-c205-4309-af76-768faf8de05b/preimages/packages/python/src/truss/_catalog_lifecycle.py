"""Original fresh lifecycle fields; no accepted publication authority."""
from dataclasses import dataclass
from hashlib import sha256
from importlib.resources import files
import json
import weakref
from .preparation import _require_original_preparation

POLICY_SHA256='b477ea156c92210be27b118e1ecbda90dc459795dcecea7b010252fd44cffada'
SCOPE='original_fresh_catalog_lifecycle_only'
_issued={}
_starts={}
class LifecycleStart:
    __slots__=('__weakref__',)

def _validate_cut(cut,length):
    if (type(cut) is not tuple or len(cut)!=length
        or any(type(v) is not str for v in cut)
        or any(not 1<=len(v)<=20 or not v.isascii() or not v.isdecimal()
               or str(int(v))!=v or int(v)>9223372036854775807 for v in cut[:3])
        or (length==4 and not 1<=len(cut[3])<=16384)):
        raise ValueError('Exact bounded original lifecycle cut required')

def begin_catalog_lifecycle(connection,prepared,cut):
    _require_original_preparation(prepared)
    _validate_cut(cut,4)
    if cut[2]!='0':raise ValueError('Original pre-effect lifecycle start required')
    connection.run('SELECT truss.runtime_require_catalog_lifecycle_observers()')
    rows=connection.run('SELECT * FROM truss.runtime_collect_empty_catalog_graph()')
    if type(rows) is not list or len(rows)!=1 or type(rows[0]) not in (list,tuple):
        raise ValueError('Original native lifecycle start required')
    native=tuple(rows[0])
    _validate_cut(native,4)
    if native!=cut:
        raise ValueError('Original pre-effect lifecycle start required')
    result=LifecycleStart();key=id(result)
    _starts[key]=(weakref.ref(result,lambda ref:_starts.pop(key,None)),connection,prepared,cut)
    return result

def _require_start(start,connection,prepared,cut):
    _validate_cut(cut,3)
    original=_starts.get(id(start))
    if (type(start) is not LifecycleStart or original is None or original[0]() is not start
        or original[1] is not connection or original[2] is not prepared
        or original[3][2]!='0' or original[3][:2]!=cut[:2]):
        raise ValueError('Original pre-effect lifecycle custody required')


def _policy_bytes():
    original=files('truss').joinpath('_profiles/fresh-catalog-lifecycle.json').read_bytes()
    if not 1<=len(original)<=4096 or sha256(original).hexdigest()!=POLICY_SHA256:
        raise ValueError('Original selected lifecycle policy required')
    return original

@dataclass(frozen=True,slots=True,weakref_slot=True)
class CatalogLifecycle:
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
        raise ValueError('Original lifecycle revision/cut required')
    choices=prepared.input()
    if (choices['binding']!={'state':'absent'} or choices['transforms']!=[]
        or any(d['ingress']!={'kind':'native'} for d in choices['documents'])):
        raise ValueError('Unselected lifecycle source requires its original producer')
    rows=connection.run("SELECT truss.runtime_collect_fresh_catalog_lifecycle(:w,:o,:g,CAST(:rev AS pg_catalog.int4),pg_catalog.decode(:policy,'hex'))::pg_catalog.text",
        w=cut[0],o=cut[1],g=cut[2],rev=revision,policy=policy.hex())
    if len(rows)!=1 or len(rows[0])!=1 or type(rows[0][0]) is not str:
        raise ValueError('Complete native lifecycle response required')
    original=rows[0][0].encode('utf8')
    if len(original)>4194304:raise ValueError('Lifecycle retention bound exceeded')
    value=json.loads(original)
    validate_catalog_source(value,prepared,revision,cut,policy)
    return original

def validate_catalog_source(value,prepared,revision,cut,policy):
    _require_original_preparation(prepared)
    choices=prepared.input()
    expected={'scope':SCOPE,'policyHex':policy.hex(),'inputHex':prepared.input_bytes.hex(),
        'writerXid':cut[0],'operationOrdinal':cut[1],'effectGeneration':cut[2],
        'revision':revision,'expectedInsertEvents':cut[2],
        'lifecycleProfile':{'identity':'truss-fresh-catalog-lifecycle','version':'0.1.0','sha256':POLICY_SHA256},
        'reactivations':[],'acceptedReportQualified':False}
    if type(value) is not dict or value.keys()!=expected.keys() or any(
        type(value[k]) is not type(v) or value[k]!=v for k,v in expected.items()):
        raise ValueError('Original lifecycle policy/input/source correspondence required')

def collect_catalog_lifecycle(connection,prepared,revision,cut,start):
    _require_start(start,connection,prepared,cut)
    policy=_policy_bytes()
    original=_collect(connection,prepared,revision,cut,policy)
    result=CatalogLifecycle(original);key=id(result)
    _issued[key]=(weakref.ref(result,lambda ref:_issued.pop(key,None)),connection,
                  prepared,revision,cut,policy,original,start)
    return result

def require_current_catalog_lifecycle(result,connection,prepared):
    original=_issued.get(id(result))
    if (type(result) is not CatalogLifecycle or original is None
        or original[0]() is not result or original[1] is not connection
        or original[2] is not prepared or type(result.original_bytes) is not bytes
        or result.original_bytes!=original[6] or type(result.scope) is not str
        or result.scope!=SCOPE or _policy_bytes()!=original[5]):
        raise ValueError('Original bound lifecycle evidence required')
    _require_start(original[7],connection,prepared,original[4])
    if _collect(connection,prepared,original[3],original[4],original[5])!=original[6]:
        raise ValueError('Current original lifecycle evidence differs')
