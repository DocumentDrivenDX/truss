"""Exact original owner-artifact coverage diagnostics, never policy interpretation.

The expected artifact digest is an independently selected comparison premise,
not caller authentication. A complete declaration still cannot qualify producers
or activate a protected profile. All semantic traversal stays with UMF.
"""
from dataclasses import dataclass
import hashlib,json

@dataclass(frozen=True)
class _FactBindingDeclaration:
    kind: str
    reference: tuple
    producer: str

@dataclass(frozen=True)
class _FactCoverage:
    required: tuple
    missing: tuple
    bindings: tuple
    # Declared coverage cannot issue native authority.
    admitted: bool = False


def _inspect_fact_coverage(original_bytes, expected_sha256, declarations):
    if (type(original_bytes) is not bytes or not 1<=len(original_bytes)<=1048576
            or type(expected_sha256) is not str or len(expected_sha256)!=64
            or hashlib.sha256(original_bytes).hexdigest()!=expected_sha256):
        raise ValueError('Original owner requirement artifact comparison required')
    def unique(pairs):
        result={}
        for k,v in pairs:
            if k in result:raise ValueError('Duplicate owner artifact field')
            result[k]=v
        return result
    artifact=json.loads(original_bytes,object_pairs_hook=unique)
    if (type(artifact) is not dict or set(artifact)!= {'kind','policySha256','resolutionSha256','dependencies'}
            or artifact['kind']!='truss-security-fact-requirements-fixture/0.1'):
        raise ValueError('Closed original fixture requirement envelope required')
    for key in ('policySha256','resolutionSha256'):
        value=artifact[key]
        if type(value) is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Original source digest required')
    dependencies=artifact['dependencies']
    if type(dependencies) is not dict or set(dependencies)!={'fields','associations'}:raise ValueError('Complete owner dependency lists required')
    required=[]
    for category,kind in (('fields','field'),('associations','association')):
        values=dependencies[category]
        if type(values) is not list or len(values)>4096:raise ValueError('Bounded original dependency list required')
        for ref in values:
            if type(ref) is not dict or set(ref)!={'documentId','moduleId','elementId'}:raise ValueError('Exact qualified dependency reference required')
            reference=tuple(ref[k] for k in ('documentId','moduleId','elementId'))
            if any(type(v) is not str or not 1<=len(v.encode('utf8'))<=4096 for v in reference):raise ValueError('Original opaque reference components required')
            required.append((kind,reference))
    required_set=set(required)
    if len(required_set)!=len(required):raise ValueError('Duplicate original dependency')
    if type(declarations) is not tuple or len(declarations)>8192:raise ValueError('Bounded exact binding declarations required')
    selected={}
    for entry in declarations:
        if type(entry) is not _FactBindingDeclaration:raise ValueError('Exact binding declaration required')
        kind,reference,producer=entry.kind,entry.reference,entry.producer
        if type(kind) is not str or kind not in ('field','association') or type(reference) is not tuple or len(reference)!=3:
            raise ValueError('Exact qualified binding identity required')
        if any(type(v) is not str or not 1<=len(v.encode('utf8'))<=4096 for v in reference) or type(producer) is not str or not 1<=len(producer.encode('utf8'))<=4096:
            raise ValueError('Bounded exact provider declaration required')
        key=(kind,reference)
        if key not in required_set or key in selected:raise ValueError('Foreign or repeated binding declaration')
        selected[key]=producer
    ordered=tuple(required)  # Preserve original owner enumeration, without normalization.
    return _FactCoverage(ordered,tuple(k for k in ordered if k not in selected),tuple((k,selected[k]) for k in ordered if k in selected))
