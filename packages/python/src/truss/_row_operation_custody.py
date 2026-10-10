"""Private immutable custody-body decoding; no registry/profile/authority admission."""
import base64
from dataclasses import dataclass
from hashlib import sha256
import re
from ._acceptance_json import decode_row_operation_json, AcceptanceJsonError


@dataclass(frozen=True)
class Artifact:
    identity: str
    original: bytes
    sha256: str


@dataclass(frozen=True)
class Profile:
    identity: str
    version: str
    sha256: str


@dataclass(frozen=True)
class Operation:
    ordinal: str
    identity: str
    kind: str
    definition: Artifact
    input: Artifact
    prestate: Artifact
    candidate: Artifact
    group_identity: str
    obligation: Artifact


@dataclass(frozen=True)
class CustodyBody:
    original: bytes
    profile: Profile
    layout: Artifact
    home: Artifact
    owner_property: Artifact
    operations: tuple[Operation, ...]


def _closed(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ValueError('Closed custody object required')
    return value


def _text(value):
    if type(value) is not str or not value:
        raise ValueError('Custody identity required')
    return value


def _hash(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('Exact custody digest required')
    return value


def _artifact(value):
    o = _closed(value, ('identity', 'bytesBase64', 'sha256'))
    identity, digest = _text(o['identity']), _hash(o['sha256'])
    token = o['bytesBase64']
    if type(token) is not str or re.fullmatch(r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?', token) is None:
        raise ValueError('Custody artifact encoding refused')
    original = base64.b64decode(token, validate=True)
    if sha256(original).hexdigest() != digest:
        raise ValueError('Custody artifact digest mismatch')
    return Artifact(identity, original, digest)


def decode_row_operation_custody(original: bytes) -> CustodyBody:
    """Validate closed body and local ordering; retain the exact original bytes.

    A parsed identity/profile/hash grants no authority. Original native registry,
    artifact meaning, complete contributor coverage and resource-account custody
    must be independently admitted. Base64 spelling is retained in original JSON;
    no extra canonical spelling rule is imposed beyond the existing schema.
    """
    try:
        o = _closed(decode_row_operation_json(original), (
            'interfaceVersion', 'profile', 'originalLayout', 'originalHome',
            'originalOwnerProperty', 'operations', 'groupResolution',
            'completionEvidence', 'transactionAuthority'))
        constants = {'interfaceVersion': 'truss-row-operation-custody/0.1.0',
                     'groupResolution': 'original-native-effects-readiness-before-seal',
                     'completionEvidence': 'resolved-independently-not-embedded-future-digest',
                     'transactionAuthority': 'actual-native-touch-context-not-caller-manifest'}
        if any(o[k] != v for k, v in constants.items()):
            raise ValueError('Custody protocol mismatch')
        p = _closed(o['profile'], ('identity', 'version', 'sha256'))
        profile = Profile(_text(p['identity']), _text(p['version']), _hash(p['sha256']))
        rows = o['operations']
        if type(rows) is not list or not 1 <= len(rows) <= 1024:
            raise ValueError('Custody operation bound')
        operations, identities = [], set()
        for position, row in enumerate(rows):
            r = _closed(row, ('ordinal', 'operationIdentity', 'operationKind',
                'originalOperationDefinition', 'originalInput', 'originalPrestate',
                'admittedCandidate', 'nativeGroupCustodyIdentity', 'effectObligationDefinition'))
            identity = _text(r['operationIdentity'])
            if r['ordinal'] != str(position) or identity in identities:
                raise ValueError('Custody local order or identity mismatch')
            if type(r['operationKind']) is not str or r['operationKind'] not in (
                    'mutation', 'import', 'catalog-transform', 'catalog-acceptance',
                    'home-migration', 'administrative-repair'):
                raise ValueError('Custody operation kind refused')
            identities.add(identity)
            operations.append(Operation(r['ordinal'], identity, r['operationKind'],
                _artifact(r['originalOperationDefinition']), _artifact(r['originalInput']),
                _artifact(r['originalPrestate']), _artifact(r['admittedCandidate']),
                _text(r['nativeGroupCustodyIdentity']), _artifact(r['effectObligationDefinition'])))
        return CustodyBody(original, profile, _artifact(o['originalLayout']),
                          _artifact(o['originalHome']), _artifact(o['originalOwnerProperty']), tuple(operations))
    except AcceptanceJsonError:
        raise ValueError('Custody syntax refused') from None
