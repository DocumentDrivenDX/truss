"""Original catalog sources retained before admission; no installed authority."""
import json
from dataclasses import asdict
from .preparation import _require_original_preparation
from ._acceptance_json import decode_row_operation_json
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
