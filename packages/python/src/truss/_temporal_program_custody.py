# SPDX-License-Identifier: MIT OR Apache-2.0
"""F6 checker dispatch and complete response custody, without native admission."""
from ._owner_evidence_json import decode_owner_evidence_json


class TemporalProgramUnavailable(RuntimeError):
    def __init__(self, operation: str) -> None:
        self.operation = operation
        super().__init__('Temporal program checker unavailable: ' + operation)


class TemporalProgramRefused(ValueError):
    def __init__(self, original: object, *, parsed: object = None) -> None:
        self.original = original
        self.parsed = parsed
        super().__init__('Temporal program checker response refused')


def _checker(compiler, operation):
    checker = getattr(compiler, operation, None)
    if not callable(checker):
        raise TemporalProgramUnavailable(operation)
    return checker


def _checked_program(original):
    if type(original) is not str:
        raise TemporalProgramRefused(original)
    try:
        parsed = decode_owner_evidence_json(original.encode('utf-8'))
    except (ValueError, UnicodeError) as error:
        raise TemporalProgramRefused(original) from error
    if (type(parsed) is not dict or set(parsed) != {'status', 'program'}
            or parsed['status'] != 'checked' or type(parsed['program']) is not dict):
        raise TemporalProgramRefused(original, parsed=parsed)
    return parsed['program']


def check_shape(compiler, program_json, original_request_json, *, page) -> dict:
    """Check original read/initial-page custody using the selected F6 checker."""
    if (type(page) is not bool or type(program_json) is not str
            or type(original_request_json) is not str):
        raise ValueError('Boolean route and original JSON text strings required')
    operation = ('check_engine_temporal_page_shape_json' if page
                 else 'check_engine_temporal_read_shape_json')
    checked = _checker(compiler, operation)(program_json, original_request_json)
    return _checked_program(checked)


def check_current(compiler, original_program_json, current_request_json, *,
                  page, after_json='null') -> dict:
    """Return the complete checked current program; shape grants no authority."""
    if (type(page) is not bool or type(original_program_json) is not str
            or type(current_request_json) is not str or page and type(after_json) is not str):
        raise ValueError('Boolean route and original JSON text strings required')
    operation = ('check_engine_temporal_page_json' if page
                 else 'check_engine_temporal_read_json')
    checker = _checker(compiler, operation)
    if page:
        checked = checker(original_program_json, current_request_json, after_json)
    else:
        checked = checker(original_program_json, current_request_json)
    return _checked_program(checked)
