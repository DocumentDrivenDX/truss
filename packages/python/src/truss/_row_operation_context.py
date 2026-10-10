"""Private original-context projection and correspondence; never native authority."""
from dataclasses import dataclass
from ._acceptance_json import AcceptanceJsonError, decode_row_operation_json
from ._row_operation_address import OperationAddress, decode_row_operation_address, encode_row_operation_address
from ._row_operation_custody import Artifact, CustodyBody, Profile, _artifact, _closed, _hash, _text
from ._row_group_custody import GroupCustody

ARTIFACT_FIELDS = ('originalInstallation', 'originalLayout', 'originalResourceProfile',
    'originalOperationDefinition', 'originalExecutionContext', 'originalActingRoleContext',
    'originalCatalogAuthorityCut', 'originalOwnerUnion', 'originalGroupAdmission')


@dataclass(frozen=True)
class OperationContext:
    original: bytes
    profile: Profile
    address: OperationAddress
    artifacts: tuple[Artifact, ...]


def decode_row_operation_context(original: bytes) -> OperationContext:
    """Decode the complete context, preserving each exact original artifact.

    Native address range checks refine the schema's decimal-text shape. Artifact
    correspondence is not admission of its semantics or its asserted authority.
    """
    try:
        o = _closed(decode_row_operation_json(original), (
            'interfaceVersion', 'profile', 'installationIdentity', 'originalWriterXid',
            'operationOrdinal', 'addressDomain', 'authority', 'durability', *ARTIFACT_FIELDS))
        constants = {'interfaceVersion':'truss-row-operation-context/0.1.0',
            'addressDomain':'truss-row-operation-address/0.1.0',
            'authority':'actual-protected-native-registry-correspondence',
            'durability':'transaction-local-until-original-commit-observation'}
        if any(o[key] != value for key,value in constants.items()):
            raise ValueError('Operation context protocol mismatch')
        p = _closed(o['profile'], ('identity','version','sha256'))
        profile = Profile(_text(p['identity']),_text(p['version']),_hash(p['sha256']))
        address = decode_row_operation_address(encode_row_operation_address(
            o['installationIdentity'],o['originalWriterXid'],o['operationOrdinal']))
        return OperationContext(original,profile,address,tuple(_artifact(o[key]) for key in ARTIFACT_FIELDS))
    except AcceptanceJsonError:
        raise ValueError('Operation context syntax refused') from None


def check_context_group_manifest(context, group, body, local_position):
    """Pure byte correspondence; inputs do not authenticate a native registry row.

    Full original scope/registry admission must precede use of this projection.
    Complete contributor/cohort coverage, readiness and settlement remain outside
    this component. Local manifest position is distinct from the native ordinal.
    """
    if (type(context) is not OperationContext or type(group) is not GroupCustody
            or type(body) is not CustodyBody or type(local_position) is not int
            or not 0 <= local_position < len(body.operations)):
        raise ValueError('Original correspondence projections required')
    operation = body.operations[local_position]
    if (context.profile != group.profile or context.profile != body.profile
            or context.address.original != group.address.original
            or operation.identity.encode('utf-8') != context.address.original
            or operation.group_identity != operation.identity or operation.kind != group.kind
            or context.artifacts[1] != body.layout
            or context.artifacts[3] != operation.definition
            or context.artifacts[8] != group.admission):
        raise ValueError('Original context/group/manifest mismatch')
    return context.address
