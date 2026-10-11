"""Pure composition of sources captured at one original NativeCall.

This snapshot confers neither current-state revalidation nor accepted authority.
"""
import json
from dataclasses import dataclass
from hashlib import sha256
from .preparation import _require_original_preparation
from ._acceptance_json import decode_acceptance_json
from ._catalog_lifecycle import validate_catalog_source as validate_lifecycle
from ._catalog_index_declarations import validate_catalog_source as validate_indexes
from ._catalog_owner_evidence import require_catalog_owner_evidence
from ._catalog_support import evaluate_catalog_support
from ._catalog_report_assembly import assemble_catalog_report_sources, validate_configured_catalog_sources, require_configuration_profile_source
from ._catalog_report_semantics import canonical_numeric_free, compose_catalog_report_semantics
from ._native_catalog_metadata import validate_configured_metadata, require_compact_metadata_correspondence, validate_catalog_resource_selection

MISSING_FIELDS=('interfaceVersion','reportProfile','originalExecution','umf','assertions','extensions')


@dataclass(frozen=True,slots=True)
class CapturedReportSources:
    snapshot_bytes: bytes
    assembly_bytes: bytes


def compose_captured_catalog_sources(encoded, result, original_context=None):
    prepared=encoded.original_input.prepared
    _require_original_preparation(prepared)
    sources=result['reportSources']
    configured=result.get('interfaceVersion')=='truss-native-provisional-catalog/0.4'
    if configured != (encoded.original_configuration is not None):
        raise ValueError('Original configured request and response version correspondence required')
    if configured:
        selection=decode_acceptance_json(encoded.original_configuration)
        context=decode_acceptance_json(original_context)
        if type(context) is not dict:
            raise ValueError('Original configured context object required')
        require_configuration_profile_source(selection['configurationProfileHex'])
        pairs={'installation':'installationId','sourceEpoch':'sourceEpoch','incarnation':'targetIncarnation',
               'captureProfileHex':'assertedOriginCaptureProfileHex','originHex':'assertedOriginUtf8Hex'}
        if any(selection[k]!=context.get(v) for k,v in pairs.items()):
            raise ValueError('Original configured selection and context correspondence required')
    required={'start','end','lifecycle','indexDeclarations'}|({'catalogRelease','catalogResources'} if configured else set())
    if type(sources) is not dict or set(sources)!=required:
        raise ValueError('Closed original catalog source snapshot required')
    start=sources['start'];end=sources['end']
    cut_names={'writer_xid','operation_ordinal','effect_generation','empty_scope'}|({'metadata_source'} if configured else set())
    if (type(start) is not dict or type(end) is not dict
            or set(start)!=cut_names or set(end)!=cut_names
            or any(type(v) is not str for cut in (start,end) for v in cut.values())
            or start['effect_generation']!='0'
            or start['writer_xid']!=result['writerXid']
            or start['operation_ordinal']!=result['ordinal']
            or end['writer_xid']!=start['writer_xid']
            or end['operation_ordinal']!=start['operation_ordinal']
            or end['effect_generation']!=result['effectGeneration']
            or end['empty_scope']!=start['empty_scope']):
        raise ValueError('Original pre-effect and final source cuts required')
    scope=decode_acceptance_json(start['empty_scope'].encode('utf8'))
    expected=['object','edge','edge_limit','key_tombstone','record_source',
        'feed_consumer','journal','row_home_journal_stage','row_home_state','row_home_node',
        'row_home_scalar','row_home_touch','row_home_capacity','key_bucket_guard',
        'object_key_bucket','object_key_reservation_bucket','feed_tx','feed_member',
        'feed_prerequisite','feed_configuration_prerequisite','complete_feed_consumer',
        'complete_feed_administration_receipt','complete_feed_seed_attempt',
        'complete_feed_seed_artifact','key_lifecycle_history','key_migration_receipt',
        'request_receipt_route_guard','request_receipt','request_receipt_protection','schema_change']
    if encoded.original_configuration is None:
        if scope!=expected and scope!=expected+['source_epoch_registry','source_epoch_current']:
            raise ValueError('Selected complete empty graph scope required')
    else:
        if (type(scope) is not dict or set(scope)!={'interfaceVersion','businessRelations','metadataUtf8Hex'}
                or scope['interfaceVersion']!='truss-configured-empty-graph/0.1'
                or scope['businessRelations']!=expected or type(scope['metadataUtf8Hex']) is not str):
            raise ValueError('Selected configured empty graph scope required')
        from ._native_catalog_metadata import _hex
        validate_configured_metadata(encoded,original_context,result['writerXid'],result['ordinal'],
                                    _hex(scope['metadataUtf8Hex'],32768))

    cut=(end['writer_xid'],end['operation_ordinal'],end['effect_generation'])
    validate_lifecycle(sources['lifecycle'],prepared,result['revision'],cut,encoded.lifecycle_policy)
    validate_indexes(sources['indexDeclarations'],prepared,result['revision'],cut,encoded.index_policy)
    evidence=json.loads(prepared.report_evidence_bytes)
    owners,coverage,assertions=require_catalog_owner_evidence(prepared,evidence)
    support=evaluate_catalog_support(prepared)
    payload={'scope':'original_catalog_report_sources_at_native_call_only',
        'revision':result['revision'],'nativeSources':sources,
        'nativeInventory':result['inventory'],'nativeDocuments':result['documents'],
        'nativeCounts':result['counts'],'acceptedInput':prepared.input(),
        'ownerEvidenceHex':prepared.report_evidence_bytes.hex(),
        'ownerObservations':owners,'observationCoverage':coverage,
        'coreAssertionIdentities':assertions,'supportPolicyDecision':support,
        'semanticSourceFields':compose_catalog_report_semantics(prepared,support,result['revision']),
        'missingFields':list(MISSING_FIELDS),'acceptedReportQualified':False,
        'currentStateRevalidated':False}
    if configured:
        payload['configuredReleaseCandidate']=validate_configured_catalog_sources(
            start,end,sources['catalogRelease'],original_context,result)
        validate_catalog_resource_selection(sources['catalogResources'],result,sources['catalogRelease'],
            _hex(scope['metadataUtf8Hex'],32768))
        require_compact_metadata_correspondence(_hex(scope['metadataUtf8Hex'],32768),
            payload['configuredReleaseCandidate']['metadata'])
    assembly=assemble_catalog_report_sources(prepared,result,payload['semanticSourceFields'])
    assembly_bytes=canonical_numeric_free(assembly)
    payload['reportAssembly']={'state':assembly['state'],
        'requiredSources':assembly['requiredSources'],'completeReportBytes':None,
        'originalAssemblySha256':sha256(assembly_bytes).hexdigest()}
    _require_original_preparation(prepared)
    return CapturedReportSources(canonical_numeric_free(payload),assembly_bytes)
