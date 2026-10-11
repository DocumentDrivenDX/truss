"""Private original catalog request; not accepted registration or authority."""
from dataclasses import dataclass
import re
from .preparation import PreparedAcceptance, _require_original_preparation
from ._acceptance_json import decode_acceptance_json
from ._catalog_support import evaluate_catalog_support
from ._native_pg8000 import NativeBoundaryRefusal
from ._catalog_lifecycle import _policy_bytes as lifecycle_policy_bytes
from ._catalog_index_declarations import _policy_bytes as index_policy_bytes


@dataclass(frozen=True, slots=True)
class NativeCatalogStageInput:
    prepared: PreparedAcceptance
    origin: bytes
    definition: bytes
    obligations: bytes
    group: bytes


@dataclass(frozen=True, slots=True)
class EncodedCatalogStage:
    original_input: NativeCatalogStageInput
    ordinal: str
    sql: str
    encoded_bytes: int
    expected_documents: tuple[tuple[str, str, str, str], ...]
    lifecycle_policy: bytes
    index_policy: bytes


def encode_catalog_stage(value, ordinal):
    if type(value) is not NativeCatalogStageInput:
        raise NativeBoundaryRefusal('Original catalog stage input required')
    _require_original_preparation(value.prepared)
    decision = evaluate_catalog_support(value.prepared)
    if decision['state'] != 'evaluated':
        raise NativeBoundaryRefusal('Selected catalog support policy unavailable')
    if (type(ordinal) is not str or len(ordinal)>19
            or re.fullmatch(r'0|[1-9][0-9]*', ordinal) is None
            or int(ordinal)>9223372036854775807):
        raise NativeBoundaryRefusal('Canonical original operation ordinal required')
    p = value.prepared
    if len(p.input_bytes)>16384:
        raise NativeBoundaryRefusal('Selected report input capacity exceeded')
    lifecycle_policy=lifecycle_policy_bytes()
    index_policy=index_policy_bytes()
    artifacts = (value.definition, p.input_bytes, p.declarations_bytes,
                 value.obligations, value.group, p.archive_documents_bytes,
                 p.declarations_bytes, value.origin)
    if any(type(b) is not bytes or not 1<=len(b)<=1048576 for b in artifacts):
        raise NativeBoundaryRefusal('Bounded exact original catalog bytes required')
    if sum(map(len, artifacts))>4194304:
        raise NativeBoundaryRefusal('Catalog artifact aggregate capacity exceeded')
    if type(decode_acceptance_json(value.origin)) is not dict:
        raise NativeBoundaryRefusal('Original numeric-free origin object required')
    prefix = ('SELECT writer_xid, ordinal, context_hex, provisional_result_hex '
              'FROM truss.runtime_stage_catalog_issued(')
    fixed = prefix+ordinal+'::pg_catalog.int8,'+','.join(
        "pg_catalog.decode('','hex')" for _ in artifacts)+')'
    size = len(fixed)+2*sum(map(len, artifacts))
    wrapper = ('SELECT admitted.writer_xid, admitted.ordinal, admitted.context_hex, '
               'admitted.provisional_result_hex, pg_catalog.pg_current_xact_id()::pg_catalog.text '
               'AS actual_writer_xid FROM (')
    if size+len(wrapper)+len(') AS admitted')+6>1048576:
        raise NativeBoundaryRefusal('Complete catalog SQL Q capacity exceeded')
    sql = prefix+ordinal+'::pg_catalog.int8,'+','.join(
        "pg_catalog.decode('"+b.hex()+"','hex')" for b in artifacts)+')'
    expected=tuple((d['documentId'],d['documentRevision'],d['artifact']['sha256'],str(position))
        for position,d in enumerate(p.input()['documents']))
    _require_original_preparation(p)
    return EncodedCatalogStage(value, ordinal, sql, size, expected,lifecycle_policy,index_policy)
