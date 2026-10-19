# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private original catalog request; not accepted registration or authority."""
from dataclasses import dataclass
from ._catalog_candidate import encode_original_catalog_candidate
from ._catalog_report_semantics import canonical_numeric_free
import re
from .preparation import PreparedAcceptance, _require_original_preparation
from ._acceptance_json import decode_acceptance_json
from ._catalog_support import evaluate_catalog_support
from ._native_pg8000 import NativeBoundaryRefusal
from ._catalog_lifecycle import _policy_bytes as lifecycle_policy_bytes
from ._catalog_index_declarations import _policy_bytes as index_policy_bytes


@dataclass(frozen=True, slots=True)
class ConfiguredCatalogSelection:
    installation: str
    source_epoch: str
    incarnation: str
    capture_profile: bytes
    configuration_profile: bytes


@dataclass(frozen=True, slots=True)
class NativeCatalogStageInput:
    prepared: PreparedAcceptance
    origin: bytes
    definition: bytes
    obligations: bytes
    group: bytes
    configuration: ConfiguredCatalogSelection | None = None


@dataclass(frozen=True, slots=True)
class EncodedCatalogStage:
    original_input: NativeCatalogStageInput
    ordinal: str
    sql: str
    encoded_bytes: int
    expected_documents: tuple[tuple[str, str, str, str], ...]
    lifecycle_policy: bytes
    index_policy: bytes
    original_configuration: bytes | None = None


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
    if type(value.origin) is not bytes or not 1<=len(value.origin)<=1048576:
        raise NativeBoundaryRefusal('Bounded exact original origin bytes required')
    selection=value.configuration
    captured=None
    if selection is not None:
        if type(selection) is not ConfiguredCatalogSelection:
            raise NativeBoundaryRefusal('Exact original configuration selection required')
        text=[]
        for name,maximum in (('installation',1024),('source_epoch',256),('incarnation',1024)):
            item=getattr(selection,name)
            if type(item) is not str or not item or '\0' in item:
                raise NativeBoundaryRefusal('Bounded scalar original configuration identity required')
            try:raw=item.encode('utf8')
            except UnicodeError as error:raise NativeBoundaryRefusal('Lossless original configuration identity required') from error
            if len(raw)>maximum:raise NativeBoundaryRefusal('Original configuration identity capacity')
            text.append(raw)
        for item in (selection.capture_profile,selection.configuration_profile):
            if type(item) is not bytes or not 1<=len(item)<=65536:
                raise NativeBoundaryRefusal('Bounded original configuration profile required')
        identity_context_bytes=sum(len(canonical_numeric_free(getattr(selection,name)))
            for name in ('installation','source_epoch','incarnation'))
        if 2*(len(value.origin)+len(selection.capture_profile))+identity_context_bytes>3000:
            raise NativeBoundaryRefusal('Selected reduced configured context capacity')
        captured=canonical_numeric_free({'installation':selection.installation,'sourceEpoch':selection.source_epoch,
            'incarnation':selection.incarnation,'captureProfileHex':selection.capture_profile.hex(),
            'configurationProfileHex':selection.configuration_profile.hex(),'originHex':value.origin.hex()})
    candidate=p.declarations_bytes if selection is None else encode_original_catalog_candidate(p)
    artifacts = (value.definition, p.input_bytes, candidate,
                 value.obligations, value.group, p.archive_documents_bytes,
                 p.declarations_bytes, value.origin)
    if any(type(b) is not bytes or not 1<=len(b)<=1048576 for b in artifacts):
        raise NativeBoundaryRefusal('Bounded exact original catalog bytes required')
    if sum(map(len, artifacts))>4194304:
        raise NativeBoundaryRefusal('Catalog artifact aggregate capacity exceeded')
    if type(decode_acceptance_json(value.origin)) is not dict:
        raise NativeBoundaryRefusal('Original numeric-free origin object required')
    arguments=[('binary',b) for b in artifacts]
    function='runtime_stage_catalog_issued'
    if selection is not None:
        function='runtime_stage_catalog_configured'
        arguments.extend([('binary',selection.capture_profile),*(('text',b) for b in text),
                          ('binary',selection.configuration_profile)])
        if sum(len(b) for kind,b in arguments if kind=='binary')>4194304:
            raise NativeBoundaryRefusal('Configured catalog aggregate capacity')
    prefix='SELECT writer_xid, ordinal, context_hex, provisional_result_hex FROM truss.'+function+'('
    def encoded(kind,raw):
        binary="pg_catalog.decode('"+raw.hex()+"','hex')"
        return binary if kind=='binary' else "pg_catalog.convert_from("+binary+",'UTF8')"
    def size(kind,raw):
        binary=len("pg_catalog.decode('','hex')")+2*len(raw)
        return binary if kind=='binary' else len("pg_catalog.convert_from(,'UTF8')")+binary
    total=len(prefix)+len(ordinal+'::pg_catalog.int8')+sum(1+size(k,b) for k,b in arguments)+1
    wrapper=('SELECT admitted.writer_xid, admitted.ordinal, admitted.context_hex, '
             'admitted.provisional_result_hex, pg_catalog.pg_current_xact_id()::pg_catalog.text '
             'AS actual_writer_xid FROM (')
    if total+len(wrapper)+len(') AS admitted')+6>1048576:
        raise NativeBoundaryRefusal('Complete catalog SQL Q capacity exceeded')
    sql=prefix+ordinal+'::pg_catalog.int8,'+','.join(encoded(k,b) for k,b in arguments)+')'
    if len(sql)!=total:raise NativeBoundaryRefusal('Original catalog SQL size correspondence required')
    expected=tuple((d['documentId'],d['documentRevision'],d['artifact']['sha256'],str(position))
        for position,d in enumerate(p.input()['documents']))
    _require_original_preparation(p)
    return EncodedCatalogStage(value, ordinal, sql, total, expected,lifecycle_policy,index_policy,captured)
