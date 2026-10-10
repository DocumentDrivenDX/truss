"""Private proposed group carrier projection; no native admission or authority."""
from dataclasses import dataclass
from ._acceptance_json import AcceptanceJsonError, decode_row_operation_json
from ._row_operation_address import OperationAddress, decode_row_operation_address
from ._row_operation_custody import Artifact, Profile, _artifact, _closed, _hash, _text


@dataclass(frozen=True)
class GroupCustody:
    original: bytes
    profile: Profile
    address: OperationAddress
    kind: str
    admission: Artifact


def decode_row_group_custody(original: bytes) -> GroupCustody:
    """Retain original bytes; check closed fields, exact artifact and address codec.

    Matching hashes establish byte correspondence only. The selected original
    profile, family meaning, installation, actual transaction and native registry
    must still be independently admitted. No future completion seal is accepted.
    """
    try:
        o = _closed(decode_row_operation_json(original), (
            'interfaceVersion', 'profile', 'addressDomain', 'operationIdentity',
            'operationKind', 'originalGroupAdmission', 'authority', 'completionEvidence'))
        constants = {
            'interfaceVersion': 'truss-row-group-custody/0.1.0',
            'addressDomain': 'truss-row-operation-address/0.1.0',
            'authority': 'actual-original-operation-admission-not-caller-address',
            'completionEvidence': 'resolved-independently-not-embedded-future-digest'}
        if any(o[key] != value for key, value in constants.items()):
            raise ValueError('Group custody protocol mismatch')
        p = _closed(o['profile'], ('identity', 'version', 'sha256'))
        profile = Profile(_text(p['identity']), _text(p['version']), _hash(p['sha256']))
        kind = _text(o['operationKind'])
        if kind not in ('mutation', 'import', 'catalog-transform', 'catalog-acceptance',
                        'home-migration', 'administrative-repair'):
            raise ValueError('Group custody operation kind refused')
        address = decode_row_operation_address(_text(o['operationIdentity']).encode('utf-8'))
        return GroupCustody(original, profile, address, kind, _artifact(o['originalGroupAdmission']))
    except AcceptanceJsonError:
        raise ValueError('Group custody syntax refused') from None
