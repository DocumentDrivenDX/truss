"""Original catalog sources retained before admission; no installed authority."""
import json
from dataclasses import asdict
from .preparation import _require_original_preparation
from ._acceptance_json import decode_row_operation_json, decode_acceptance_json
from ._catalog_support import evaluate_catalog_support
from ._catalog_owner_evidence import require_catalog_owner_evidence
from ._catalog_report_semantics import (canonical_numeric_free,
    compose_original_catalog_report_semantics)
from ._canonical_wire_tree import prepare_canonical_wire_tree

INTERFACE='truss-catalog-source-candidate/0.1'
SOURCE_FIELDS=('umf','diagnostics','documentInterpretations','losses','extensions',
               'transformRegistrations','assertionEntries')


def encode_original_catalog_candidate(prepared):
    """Bind exact declarations/evidence and freshly derived source-only fields.

    Native-owned revision, identities, execution, counts and profile selection
    cannot be supplied here. The tagged source tree preserves all UTF-8 bytes,
    including NUL, without requiring PostgreSQL text to hold logical strings.
    """
    _require_original_preparation(prepared)
    hex_length=2*(len(prepared.declarations_bytes)+len(prepared.report_evidence_bytes))
    if hex_length>1048576:raise ValueError('Catalog candidate capacity exceeded')
    support=evaluate_catalog_support(prepared)
    evidence=decode_row_operation_json(prepared.report_evidence_bytes)
    require_catalog_owner_evidence(prepared,evidence)
    semantics=compose_original_catalog_report_semantics(prepared,support)
    if semantics['state']!='source_fields_ready':
        raise ValueError('Complete original closed report source inventory required')
    sources={'umf':semantics['umf'],
        'diagnostics':evidence['validation']['diagnostics'],
        'documentInterpretations':evidence['validation']['documentInterpretations'],
        'losses':evidence['ingress']['basis']['losses'],
        'extensions':semantics['extensions'],
        'transformRegistrations':evidence['ingress']['basis']['transformRegistrations'],
        'assertionEntries':semantics['assertionEntries']}
    provenance=asdict(prepared.provenance)
    fixed=len(canonical_numeric_free({'interfaceVersion':INTERFACE,
        'declarationsUtf8Hex':'','reportEvidenceUtf8Hex':'',
        'preparationProvenance':provenance,'hostSources':{}}))-2
    remaining=1048576-fixed-hex_length
    if remaining<1:raise ValueError('Catalog candidate capacity exceeded')
    carrier=prepare_canonical_wire_tree(canonical_numeric_free(sources),maximum_carrier_bytes=remaining)
    envelope={'interfaceVersion':INTERFACE,
        'declarationsUtf8Hex':prepared.declarations_bytes.hex(),
        'reportEvidenceUtf8Hex':prepared.report_evidence_bytes.hex(),
        'preparationProvenance':provenance,
        'hostSources':json.loads(carrier.native_tree_text)}
    original=canonical_numeric_free(envelope)
    if len(original)>1048576:
        raise ValueError('Catalog candidate capacity exceeded')
    _require_original_preparation(prepared)
    return original


# Pending private facade ABI: native body and result grammar are not implemented.
# Validate the exact native result columns when connecting execution.
FRESH_CATALOG_DISPATCH_SQL = (
    'SELECT * FROM truss.runtime_accept_fresh_catalog_session_candidate('
    '%s::pg_catalog.int8,%s::pg_catalog.bytea,%s::pg_catalog.bytea,'
    '%s::pg_catalog.bytea,%s::pg_catalog.bytea,%s::pg_catalog.bytea)'
)


def encode_fresh_catalog_dispatch_parameters(prepared, ordinal, origin_bytes):
    """Immediate trusted SDK input for the protected catalog facade.

    Invoke inside the semantic host operation with its reserved ordinal. This
    tuple supplies only original semantic input; actor, configuration, epoch,
    prestate, operation recipe, effect plan and group custody are native-owned.
    No registry, authority token, execution or accepted result is produced here.
    The selected origin grammar is an exact numeric-free JSON object.
    """
    _require_original_preparation(prepared)
    if (type(ordinal) is not str or not 1 <= len(ordinal) <= 19
            or not ordinal.isascii() or not ordinal.isdecimal()
            or str(int(ordinal)) != ordinal or int(ordinal) > 9223372036854775807):
        raise ValueError('Canonical host-issued ordinal required')
    if type(origin_bytes) is not bytes or not 1 <= len(origin_bytes) <= 131072:
        raise ValueError('Bounded original asserted origin required')
    if type(decode_acceptance_json(origin_bytes)) is not dict:
        raise ValueError('Original asserted origin object required')
    originals = (prepared.input_bytes, prepared.archive_documents_bytes,
                 prepared.declarations_bytes)
    if any(not 1 <= len(raw) <= 1048576 for raw in originals):
        raise ValueError('Original catalog dispatch capacity exceeded')
    candidate = encode_original_catalog_candidate(prepared)
    parameters = (ordinal, prepared.input_bytes, candidate,
                  prepared.archive_documents_bytes, prepared.declarations_bytes,
                  origin_bytes)
    if sum(len(raw) for raw in parameters) > 4194304:
        raise ValueError('Catalog dispatch aggregate capacity exceeded')
    _require_original_preparation(prepared)
    return parameters
