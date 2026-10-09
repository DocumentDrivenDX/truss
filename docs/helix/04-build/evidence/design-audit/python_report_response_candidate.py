"""Private response-only codec candidate; no issuer or complete account authority.

The legacy request/input codec is unchanged. Limits here cover source/structure,
not parser/schema heap, aggregate work, transport or simultaneous-copy custody.
"""
import json
from python_report_wire_candidate import ReportWireCandidate, ReportWire
from python_raw_json_candidate import JsonNumberToken, JsonObject, parse_retained_json


class ResponseWireError(ValueError):
    def __init__(self, reason):
        self.reason = reason
        super().__init__('Response wire refused: ' + reason)


class ReportResponseCandidate(ReportWireCandidate):
    def prepare(self, source):
        if type(source) not in (bytes, bytearray):
            raise ResponseWireError('wire')
        reason = None
        try:
            retained = parse_retained_json(source, maximum_bytes=4194304,
                                           maximum_depth=128, maximum_nodes=100000,
                                           preserve_byte_document_nul=True, maximum_members=4096)
        except UnicodeError:
            reason = 'unicode'
        except json.JSONDecodeError:
            reason = 'grammar'
        except ValueError as error:
            resource_messages = {
                'Original bytes and explicit finite candidate bounds required',
                'Selected JSON container member count exceeded before parsing',
                'Selected JSON node count exceeded before parsing',
                'Selected JSON depth exceeded before parsing',
                'Selected JSON node count exceeded',
            }
            reason = 'resource' if str(error) in resource_messages else 'grammar'
        # Raise outside the handler: no instance-bearing cause/context escapes.
        if reason is not None:
            raise ResponseWireError(reason)

        def view(value):
            if isinstance(value, JsonNumberToken):
                raise ValueError('Outer report numeric node refused')
            if isinstance(value, JsonObject):
                return {key: view(child) for key, child in value.entries}
            if isinstance(value, tuple):
                return [view(child) for child in value]
            return value

        if not self._validator.is_valid(view(retained.value)):
            raise ValueError('Original composed report schema refused')
        return ReportWire(retained, scope='response_schema_bytes_only_without_account_admission')

    def prepare_native(self, source):
        raise ValueError('Response native carrier/account profile remains unadmitted')
