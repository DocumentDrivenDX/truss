"""Original reference [module,action] family codec; no registry or authority.

Preserves UTF-16 identity, including NUL, pairs and lone surrogates, through
well-formed JSON UTF-8 bytes. Store scope and revision binding stay separate.
"""
import json


def _bounded_string(value):
    if (type(value) is not str or not value
            or len(value.encode('utf-16-le', errors='surrogatepass')) > 512):
        raise ValueError('Original bounded action identity string required')
    # JS strings contain UTF-16 units. Combine a valid explicit pair while
    # retaining unmatched units for JSON.stringify's escaped representation.
    normalized = value.encode('utf-16-le', errors='surrogatepass').decode(
        'utf-16-le', errors='surrogatepass')
    quoted = json.dumps(normalized, ensure_ascii=False, separators=(',', ':'))
    return ''.join('\\u%04x' % ord(c) if 0xD800 <= ord(c) <= 0xDFFF else c
                   for c in quoted).encode('utf-8')


def encode_action_family(module, action):
    return b'[' + _bounded_string(module) + b',' + _bounded_string(action) + b']'


def encode_action_role(role):
    return _bounded_string(role)


def encode_action_store_identity(store):
    """Original JSON string codec; first native profile bounds 256 UTF-16 units."""
    return _bounded_string(store)


def encode_action_tenant_identity(tenant):
    return _bounded_string(tenant)


def encode_action_namespace_epoch(epoch):
    return _bounded_string(epoch)
