"""Existing numeric-free wire → native tagged-tree protocol; no report authority."""
from dataclasses import dataclass
import json
from ._acceptance_json import decode_acceptance_json


@dataclass(frozen=True,slots=True)
class CanonicalWireTree:
    original_utf8_hex: str
    native_tree_text: str
    native_task_count: str
    scope: str = 'original_numeric_free_wire_codec_handoff_only'


def prepare_canonical_wire_tree(original, *, maximum_carrier_bytes=4194304):
    if type(maximum_carrier_bytes) is not int or not 1<=maximum_carrier_bytes<=4194304:
        raise ValueError('Bounded native carrier capacity required')
    value=decode_acceptance_json(original)
    pending=[value];steps=0;length=0
    while pending:
        node=pending.pop();steps+=1
        if node is None:length+=len('{"kind":"null"}')
        elif type(node) is bool:length+=len('{"kind":"boolean","value":true}')+(not node)
        elif type(node) is str:length+=len('{"kind":"string","utf8Hex":""}')+2*len(node.encode('utf8'))
        else:
            children=node if type(node) is list else list(node.values())
            steps+=len(children)+1+(0 if type(node) is list else 2*len(children))
            length+=len('{"kind":"array","items":[]}' if type(node) is list
                        else '{"kind":"object","members":[]}')+max(0,len(children)-1)
            if type(node) is dict:
                length+=sum(len('{"keyUtf8Hex":"","node":}')+2*len(key.encode('utf8')) for key in node)
            pending.extend(children)
        if steps>32768:raise ValueError('Native canonical tree task capacity exceeded')
        if length>maximum_carrier_bytes:raise ValueError('Native canonical tree carrier capacity exceeded')
    def entries(node):
        # ECMAScript Object.entries orders array-index keys first. Preserve the
        # owner protocol even though the native codec independently sorts UTF-8.
        indexes=[key for key in node if len(key)<=10 and key.isascii() and key.isdecimal()
                 and str(int(key))==key and int(key)<4294967295]
        return [(key,node[key]) for key in sorted(indexes,key=int)]+[
            (key,child) for key,child in node.items() if key not in indexes]
    def encode(node):
        if node is None:return {'kind':'null'}
        if type(node) is bool:return {'kind':'boolean','value':node}
        if type(node) is str:return {'kind':'string','utf8Hex':node.encode('utf8').hex()}
        if type(node) is list:return {'kind':'array','items':[encode(child) for child in node]}
        return {'kind':'object','members':[{'keyUtf8Hex':key.encode('utf8').hex(),'node':encode(child)}
                                         for key,child in entries(node)]}
    text=json.dumps(encode(value),ensure_ascii=True,separators=(',',':'))
    if len(text)!=length:raise ValueError('Native carrier preflight correspondence failed')
    return CanonicalWireTree(original.hex(),text,str(steps))
