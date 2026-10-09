"""Private original report-schema/byte candidate; no acceptance or effect authority."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from python_raw_json_candidate import JsonNumberToken, JsonObject, RetainedJson, parse_retained_json

PINS = MappingProxyType({
    'exact-value-v0.1.schema.json': '0c804796bfbf68339c299f0c55d24db58fcfcc929bffe2d5ffaf4a2f27e24880',
    'history-record-v0.1.schema.json': 'c35c1258028cc4c8c95dcd16b561caed4f2a347c086f72ebfc7bfc4f2dfcf2fe',
    'history-event-v0.1.schema.json': 'e42f9b48642528cabbb646ccb758eb12b7f030029b712cf5d6f5174cbd90bfa6',
    'acceptance-input-v0.1.schema.json': '0278cbbbde843091c005b688fd9c081a2fdff843b9adda006ba80fb87828d7cd',
    'acceptance-rejection-v0.1.schema.json': '98262b8d99fe0f87f752140a418a4e4f8751c4d28986457302586fee622258cf',
    'enforcement-report-v0.1.schema.json': '7af9c786a297583d6eb5489d85f33fb0a04b2c1d0b6551e6d107528cc15c4137',
    'direct-cursor-v0.1.schema.json': 'bff79ad2e5ccc1047b43bdbe6eeb51b597f098c881313fd980de01c1685b4942',
    'acceptance-report-v0.1.schema.json': 'ccdc9976de3c158fae0a14d6cc41685d5f5a289d67daeb86b5e998b4a611e902',
    'history-retain-payload-v0.1.proposal.schema.json': 'fc08e07a4b09636ac234737be9bb2cf3a9a3c26120baad612176574c17659605',
    'history-event-v0.2.proposal.schema.json': '714923be0f86bd3508a097cabfee63a180e03b19651ebbfa38844bb3e637b425',
    'acceptance-report-v0.3.proposal.schema.json': 'c54196f8b4324aec768a33eeeab89bc2615a954af0e45559ed2038ccad7f14bf',
})


@dataclass(frozen=True)
class ReportWire:
    original: RetainedJson
    scope: str = 'original_composed_report_schema_bytes_only'


class ReportWireCandidate:
    def __init__(self, directory: Path):
        schemas = {}
        for name, expected in PINS.items():
            original = (directory / name).read_bytes()
            if sha256(original).hexdigest() != expected:
                raise ValueError('Original report schema pin mismatch')
            schema = json.loads(original)
            Draft202012Validator.check_schema(schema)
            schemas[name] = schema
        # Explicit local registry; unavailable references do not trigger fetching.
        registry = Registry().with_resources((schema['$id'], Resource.from_contents(schema))
                                              for schema in schemas.values())
        self._validator = Draft202012Validator(
            schemas['acceptance-report-v0.3.proposal.schema.json'], registry=registry)

    def prepare(self, source: bytes | bytearray) -> ReportWire:
        retained = parse_retained_json(source, maximum_bytes=1048576,
                                       maximum_depth=128, maximum_nodes=100000,
                                       preserve_byte_document_nul=True, maximum_members=4096)

        def view(value):
            if isinstance(value, JsonNumberToken):
                raise ValueError('Outer report numeric node refused')
            if isinstance(value, JsonObject):
                return {key: view(child) for key, child in value.entries}
            if isinstance(value, tuple):
                return [view(child) for child in value]
            return value

        # Do not propagate jsonschema's instance-bearing exception to consumers.
        # This bounds the outward diagnostic, not internal validator allocations.
        if not self._validator.is_valid(view(retained.value)):
            raise ValueError('Original composed report schema refused')
        return ReportWire(retained)
