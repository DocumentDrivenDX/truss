"""Closed catalog response custody; provisional native effects only."""
from dataclasses import dataclass
import re
from ._native_admission_capture import NativeAdmissionCapture
from ._native_result_custody import NativeTextLimits
from ._native_pg8000 import NativeBoundaryRefusal, NativeCall
from ._acceptance_json import decode_acceptance_json
from ._native_catalog_report_sources import CapturedReportSources, compose_captured_catalog_sources


CATALOG_LIMITS = NativeTextLimits(columns=5, rows=1, cell_bytes=262144,
    result_bytes=294912, frame_bytes=307200, wire_bytes=614400,
    payload_capacity=33554432, cumulative_payload=33554432)
# Maximum cells: 20+19+8192+262144+20=270395; DataRow adds27.
# Nonrewinding ingress/decoder reservations fit21*(wire+frame)+5<32MiB.
# These are selected payload bounds, not full heap/work qualification.

def _integer(value, minimum=0, maximum=9223372036854775807):
    return (type(value) is str and len(value)<=20
        and re.fullmatch(r'0|[1-9][0-9]*',value) is not None
        and minimum<=int(value)<=maximum)

def _result_shape(result):
    fields={'interfaceVersion','revision','writerXid','ordinal','effectGeneration',
            'accepted','inventory','documents','counts','reportSources'}
    if (set(result)!=fields or not _integer(result['revision'],1,2147483647)
            or not _integer(result['effectGeneration'])
            or type(result['inventory']) is not list or len(result['inventory'])>16384
            or type(result['documents']) is not list or not 1<=len(result['documents'])<=512
            or type(result['counts']) is not dict):return False
    families={'type':4,'property':4,'key':3,'relationship':4,'endpoint':3}
    integer_positions={'type':(0,),'property':(0,1),'key':(0,2),
                       'relationship':(0,),'endpoint':(0,1,2)}
    seen=set();counts={f:0 for f in families}
    for item in result['inventory']:
        if type(item) is not dict or set(item)!={'family','identity'}:return False
        family=item['family'];identity=item['identity']
        if (type(family) is not str or family not in families
                or type(identity) is not list or len(identity)!=families[family]
                or any(type(v) is not str or not 1<=len(v.encode('utf8'))<=65536 for v in identity)
                or any(not _integer(identity[i],1,2147483647) for i in integer_positions[family])):return False
        if family=='key' and not _integer(identity[2],1,32767):return False
        key=(family,tuple(identity))
        if key in seen:return False
        seen.add(key);counts[family]+=1
    count_names=dict(zip(families,('types_added','properties_added','keys_added','relationships_added','endpoints_added')))
    if set(result['counts'])!=set(count_names.values())|{'elements_retired'}:return False
    if any(not _integer(v,0,16384) for v in result['counts'].values()):return False
    if result['counts']['elements_retired']!='0':return False
    if any(result['counts'][name]!=str(counts[f]) for f,name in count_names.items()):return False
    ids=set()
    for position,doc in enumerate(result['documents']):
        if (type(doc) is not dict or set(doc)!={'doc_id','doc_revision','content_sha256','ord'}
                or type(doc['doc_id']) is not str or not 1<=len(doc['doc_id'].encode('utf8'))<=4096 or doc['doc_id'] in ids
                or type(doc['doc_revision']) is not str or not 1<=len(doc['doc_revision'].encode('utf8'))<=4096
                or type(doc['content_sha256']) is not str
                or re.fullmatch(r'[0-9a-f]{64}',doc['content_sha256']) is None
                or doc['ord']!=str(position)):return False
        ids.add(doc['doc_id'])
    return True


@dataclass(frozen=True, slots=True)
class NativeCatalogStageObservation:
    original_call: NativeCall
    writer_xid: str
    ordinal: str
    original_context: bytes
    original_provisional_result: bytes
    original_report_source_snapshot: bytes | None = None
    original_report_assembly: bytes | None = None
    scope: str = 'provisional_native_catalog_effects_only'


class NativeCatalogCapture(NativeAdmissionCapture):
    NAMES = (b'writer_xid', b'ordinal', b'context_hex',
             b'provisional_result_hex', b'actual_writer_xid')

    def __init__(self, session, *, entry, expected_documents, encoded):
        if (type(expected_documents) is not tuple or not 1<=len(expected_documents)<=512
                or any(type(d) is not tuple or len(d)!=4 or any(type(v) is not str for v in d)
                       for d in expected_documents)):
            raise NativeBoundaryRefusal('Original expected document tuple required')
        self.encoded=encoded
        self.expected_documents=expected_documents
        self.original_observation = None
        super().__init__(session, CATALOG_LIMITS, entry=entry)

    def _produce_observation(self, call, writer, ordinal, context, row):
        encoded = row[3]
        if (type(encoded) is not str or not 2<=len(encoded)<=262144
                or len(encoded)%2 or re.fullmatch(r'[0-9a-f]+', encoded) is None):
            raise NativeBoundaryRefusal('Exact bounded original catalog response required')
        original = bytes.fromhex(encoded)
        result = decode_acceptance_json(original)
        if (type(result) is not dict
                or result.get('interfaceVersion')!='truss-native-provisional-catalog/0.2'
                or result.get('writerXid')!=writer or result.get('ordinal')!=ordinal
                or result.get('accepted') is not False or not _result_shape(result)):
            raise NativeBoundaryRefusal('Original provisional operation correspondence required')
        actual=tuple((d['doc_id'],d['doc_revision'],d['content_sha256'],d['ord']) for d in result['documents'])
        if actual!=self.expected_documents:
            raise NativeBoundaryRefusal('Original prepared document response correspondence required')
        # Preserve original native sources even if Python composition refuses.
        self.original_observation=NativeCatalogStageObservation(call,writer,ordinal,context,original)
        try:
            snapshot=compose_captured_catalog_sources(self.encoded,result,context)
        except ValueError as error:
            raise NativeBoundaryRefusal('Original report source correspondence required') from error
        if type(snapshot) is not CapturedReportSources:
            raise NativeBoundaryRefusal('Original report source result required')
        observation = NativeCatalogStageObservation(call, writer, ordinal, context, original,
            snapshot.snapshot_bytes,snapshot.assembly_bytes)
        # Retain before publishing to the caller, including lost return replies.
        self.original_observation = observation
        return observation
