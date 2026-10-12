"""Private candidate locator decoder, not receipt/commit/visibility authority."""
import base64
import binascii
from dataclasses import dataclass
import json
import re
from ._acceptance_json import decode_acceptance_json


@dataclass(frozen=True)
class PositionProfile:
    identity: str
    version: str
    sha256: str


@dataclass(frozen=True)
class ReceiptPositionLocator:
    position_profile: PositionProfile
    installation_id: str
    source_epoch: str
    receipt_storage_row_id: str
    writer_xid: str
    original_bytes: bytes


def _object(value, fields):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError('Closed locator required')
    return value


def _text(value, maximum):
    if type(value) is not str or not value or len(value) > maximum or '\0' in value:
        raise ValueError('Bounded locator text required')
    if len(value.encode('utf-8', errors='strict')) > maximum:
        raise ValueError('Locator byte bound')
    return value


def _integer(value, maximum, positive):
    if type(value) is not str or len(value) > 20 or not re.fullmatch(r'0|[1-9][0-9]*', value):
        raise ValueError('Canonical integer text required')
    integer = int(value)
    if integer > maximum or positive and integer == 0:
        raise ValueError('Locator integer domain')
    return value


def decode_receipt_position(token: str) -> ReceiptPositionLocator:
    """Validate syntax only; original resolver must independently admit all facts."""
    if type(token) is not str or not 1 <= len(token) <= 16384 or not re.fullmatch('[A-Za-z0-9_-]+', token):
        raise ValueError('Canonical bounded base64url required')
    try:
        original = base64.b64decode(token + '=' * (-len(token) % 4), altchars=b'-_', validate=True)
    except binascii.Error as error:
        raise ValueError('Invalid base64url') from error
    if base64.urlsafe_b64encode(original).decode('ascii').rstrip('=') != token:
        raise ValueError('Noncanonical base64url')
    value = _object(decode_acceptance_json(original), ('interfaceVersion', 'positionProfile', 'installationId', 'sourceEpoch', 'receiptStorageRowId', 'writerXid'))
    if value['interfaceVersion'] != 'truss-receipt-position/0.1.0':
        raise ValueError('Unsupported locator wire')
    profile = _object(value['positionProfile'], ('identity', 'version', 'sha256'))
    identity, version = _text(profile['identity'], 256), _text(profile['version'], 256)
    digest = profile['sha256']
    if type(digest) is not str or not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('Exact profile digest required')
    installation, epoch = _text(value['installationId'], 1024), _text(value['sourceEpoch'], 256)
    row = _integer(value['receiptStorageRowId'], 9223372036854775807, True)
    xid = _integer(value['writerXid'], 18446744073709551615, False)
    ordered = dict(interfaceVersion='truss-receipt-position/0.1.0', positionProfile=dict(identity=identity, version=version, sha256=digest), installationId=installation, sourceEpoch=epoch, receiptStorageRowId=row, writerXid=xid)
    canonical = json.dumps(ordered, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    if canonical != original:
        raise ValueError('Noncanonical locator bytes')
    return ReceiptPositionLocator(PositionProfile(identity, version, digest), installation, epoch, row, xid, original)
