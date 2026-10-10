"""Private pinned resource capture; not complete index or installer admission.

Only a trusted registered resource handle supplies open/read. This component
charges the declared read bound, not actual interpreter/decoder/hash workspace.
"""
from dataclasses import dataclass
from hashlib import sha256
from ._resource_account import ByteAllocation, BytePermitAccount


@dataclass(frozen=True, eq=False)
class ResourceCapture:
    original: bytes
    allocation: ByteAllocation
    account: BytePermitAccount


def capture_resource(resource, expected_length, expected_sha256, maximum_length,
                     account, producer):
    """Read once through a complete bounded binary-read handle, retaining bytes.

    The independently selected entry/profile supplies lengths and digest. No
    path lookup, package index selection, database submission or retry occurs.
    On read/close/correspondence failure, quarantine the original charge.
    """
    if (type(expected_length) is not int or type(maximum_length) is not int
            or expected_length < 0 or maximum_length < 0
            or expected_length > maximum_length):
        raise ValueError('Selected exact resource length bound required')
    if (type(expected_sha256) is not str or len(expected_sha256) != 64
            or any(c not in '0123456789abcdef' for c in expected_sha256)):
        raise ValueError('Independent exact resource digest required')
    # One sentinel byte distinguishes exact EOF from an appended payload.
    bound = expected_length + 1
    permit = account.reserve(producer, bound)
    allocation = account.allocate(producer, permit, bound)
    try:
        with resource.open('rb') as stream:
            original = stream.read(bound)
        if type(original) is not bytes or len(original) != expected_length:
            raise ValueError('Resource byte length mismatch')
        if sha256(original).hexdigest() != expected_sha256:
            raise ValueError('Resource digest mismatch')
        account.terminate(producer, permit)
        return ResourceCapture(original, allocation, account)
    except BaseException:
        # Error/close/termination does not establish safe release of all views.
        account.close(producer)
        raise


@dataclass(frozen=True)
class ResourceEntry:
    id: str
    path: str
    role: str
    byte_length: int
    sha256: str


def decode_resource_index(original, expected_sha256, expected_release,
                          expected_entries, maximum_index_bytes,
                          maximum_entries, maximum_total_bytes):
    """Pure correspondence gate; does not meter JSON heap/work or select files.

    Expected entries and pins come from independent trusted release registration.
    Returned immutable entries preserve original ordered inventory membership.
    """
    import json
    for bound in (maximum_index_bytes, maximum_entries, maximum_total_bytes):
        if type(bound) is not int or bound < 0:
            raise ValueError('Selected exact index bounds required')
    if type(original) is not bytes or len(original) > maximum_index_bytes:
        raise ValueError('Original bounded index bytes required')
    if not _digest(expected_sha256) or sha256(original).hexdigest() != expected_sha256:
        raise ValueError('Independent index pin mismatch')
    if not _text(expected_release) or type(expected_entries) is not tuple:
        raise ValueError('Original release registration required')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate index member')
            result[key] = value
        return result

    def no_float(value):
        raise ValueError('Index numeric carrier unsupported')

    def integer(value):
        if len(value) > max(1, len(str(maximum_total_bytes))) + 1:
            raise ValueError('Index integer exceeds selected bound')
        return int(value)

    try:
        document = json.loads(original.decode('utf-8'), object_pairs_hook=pairs,
                              parse_int=integer, parse_float=no_float,
                              parse_constant=no_float)
    except (UnicodeError, RecursionError) as error:
        raise ValueError('Invalid index encoding or nesting') from error
    if (type(document) is not dict or set(document) != {'interface', 'releaseId', 'entries'}
            or document['interface'] != 'truss-python-resources/0.1.0'
            or document['releaseId'] != expected_release
            or type(document['entries']) is not list
            or len(document['entries']) > maximum_entries):
        raise ValueError('Closed release index mismatch')
    entries = []; ids = set(); paths = set(); total = 0
    for item in document['entries']:
        if type(item) is not dict or set(item) != {'id', 'path', 'role', 'byteLength', 'sha256'}:
            raise ValueError('Closed resource entry required')
        if not all(_text(item[key]) for key in ('id', 'path', 'role')) or not _digest(item['sha256']):
            raise ValueError('Invalid resource identity or digest')
        path = item['path']
        if '\\' in path or ':' in path or any(segment in ('', '.', '..') for segment in path.split('/')):
            raise ValueError('Relative POSIX resource path required')
        length = item['byteLength']
        if type(length) is not int or length < 0 or total + length > maximum_total_bytes:
            raise ValueError('Selected aggregate resource byte bound exceeded')
        if item['id'] in ids or path in paths:
            raise ValueError('Duplicate resource identity or path')
        ids.add(item['id']); paths.add(path); total += length
        entries.append(ResourceEntry(item['id'], path, item['role'], length, item['sha256']))
    result = tuple(entries)
    if any(type(entry) is not ResourceEntry for entry in expected_entries) or result != expected_entries:
        raise ValueError('Complete registered resource membership mismatch')
    return result


def _text(value):
    return (type(value) is str and bool(value)
            and not any(ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value))


def _digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)
