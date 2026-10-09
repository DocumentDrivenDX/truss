"""Experimental compiler boundary. No database execution or authority issuance.

The trusted host supplies the original Weft compile_json function. The frozen
source/build must be verified separately; a callable or artifact cannot prove it.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import hashlib
import json
from threading import Lock
from types import MappingProxyType
from typing import Callable, Mapping

WEFT_SOURCE = 'f05f2df09e9c2494ac8c6d703dfe38413dbc4181'


class CompileRefusal(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _refuse(code, message):
    raise CompileRefusal(code, message)


def _decode(original, maximum, code):
    if type(original) is not bytes or len(original) > maximum:
        _refuse(code, 'Bounded immutable UTF-8 bytes required')
    try:
        text = original.decode('utf-8', errors='strict')
        # Admit bounded nesting before recursive JSON materialization. Original
        # owner grammar remains Rust's responsibility; this is no SQL parser.
        depth = 0
        quoted = escaped = False
        for character in text:
            if quoted:
                if escaped:
                    escaped = False
                elif character == '\\':
                    escaped = True
                elif character == '"':
                    quoted = False
            elif character == '"':
                quoted = True
            elif character in '[{':
                depth += 1
                if depth > 128:
                    _refuse(code, 'JSON nesting outside compiler boundary')
            elif character in ']}':
                depth -= 1
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    _refuse(code, 'Duplicate JSON member')
                key.encode('utf-8', errors='strict')
                result[key] = value
            return result
        value = json.loads(text, object_pairs_hook=pairs, parse_float=Decimal,
                           parse_constant=lambda _: _refuse(code, 'Nonfinite JSON number'))
        def unicode_values(item):
            if isinstance(item, str):
                item.encode('utf-8', errors='strict')
            elif isinstance(item, dict):
                for child in item.values(): unicode_values(child)
            elif isinstance(item, list):
                for child in item: unicode_values(child)
        unicode_values(value)
        return text, value
    except CompileRefusal:
        raise
    except (UnicodeError, ValueError, RecursionError, InvalidOperation) as error:
        raise CompileRefusal(code, 'Invalid compiler JSON transport') from error


def _freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(child) for key, child in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(child) for child in value)
    return value


@dataclass(frozen=True)
class CompiledQuery:
    original_request: bytes
    original_response: bytes
    artifact: Mapping


class CompilerBoundary:
    """Synchronous embedded compiler; no SQL execution, retry or native permit.

    Input is the complete original owner request, not a Python model translation.
    The original callback is captured once. Disposal withholds pending publication.
    Compiler response limits are component bounds, not original operation-account
    or native heap qualification. Do not turn a CompiledQuery into a SQL authority.
    """
    def __init__(self, compile_json: Callable[[str], str]):
        if not callable(compile_json):
            _refuse('compiler', 'Original compiler function required')
        self._compile = compile_json
        self._disposed = False
        self._busy = False
        self._lock = Lock()

    def dispose(self):
        with self._lock:
            self._disposed = True

    def compile_request(self, original_request: bytes) -> CompiledQuery:
        with self._lock:
            if self._disposed: _refuse('disposed', 'Compiler boundary disposed')
            if self._busy: _refuse('busy', 'Compiler invocation already active')
            self._busy = True
        try:
            text, request = _decode(original_request, 16 * 1024 * 1024, 'input')
            if not isinstance(request, dict) or request.get('interfaceVersion') != 'weft-compile/0.2.0' or request.get('dialect') != 'weft-sql/0.2.0':
                _refuse('input_version', 'Explicit frozen Weft0.2 request required')
            target = request.get('target')
            modules = request.get('modules')
            if not isinstance(target, dict) or target.get('backendId') != 'truss.postgresql' or not isinstance(modules, list):
                _refuse('input', 'Original Truss target and modules required')
            if any(type(target.get(key)) is not str or not target[key] for key in ('backendVersion','targetProfile','bindingJson','bindingSha256')):
                _refuse('input', 'Complete explicit target pins required')
            if hashlib.sha256(target['bindingJson'].encode('utf-8', errors='strict')).hexdigest() != target['bindingSha256']:
                _refuse('binding_pin', 'Original binding bytes/hash mismatch')
            if not 1 <= len(modules) <= 32: _refuse('model', 'Model bundle outside bounds')
            for module in modules:
                if (not isinstance(module, dict) or type(module.get('documentJson')) is not str
                    or not isinstance(module.get('pin'), dict)
                    or hashlib.sha256(module['documentJson'].encode('utf-8', errors='strict')).hexdigest() != module['pin'].get('sha256')):
                    _refuse('model_pin', 'Original model bytes/hash mismatch')
            with self._lock:
                if self._disposed: _refuse('disposed', 'Compiler boundary disposed')
            raw = self._compile(text)
            with self._lock:
                if self._disposed: _refuse('disposed', 'Compiler boundary disposed')
            if type(raw) is not str:
                _refuse('compiler', 'Original compiler must return UTF-8 text')
            try: response_bytes = raw.encode('utf-8', errors='strict')
            except UnicodeError as error:
                raise CompileRefusal('compiler', 'Invalid compiler text') from error
            _, artifact = _decode(response_bytes, 8 * 1024 * 1024, 'compiler')
            if not isinstance(artifact, dict): _refuse('compiler', 'Compiler object required')
            if artifact.get('status') != 'compiled': _refuse('compiler_blocked', raw)
            backend = artifact.get('backend')
            if (artifact.get('interfaceVersion') != 'weft-compile/0.2.0'
                or artifact.get('dialect') != 'weft-sql/0.2.0'
                or not isinstance(backend, dict)
                or backend.get('interfaceVersion') != 'weft-backend/0.2.0'
                or any(backend.get(key) != target.get(key) for key in ('backendId','backendVersion','targetProfile'))
                or artifact.get('bindingSha256') != target.get('bindingSha256')
                or any(not isinstance(module, dict) or 'pin' not in module for module in modules)
                or artifact.get('modelPins') != [module['pin'] for module in modules]):
                _refuse('artifact_pin', 'Compiler artifact context drift')
            if (type(artifact.get('sql')) is not str
                or any(type(artifact.get(key)) is not list for key in ('parameters','columns','obligations'))):
                _refuse('compiler', 'Incomplete compiler artifact')
            if (any(isinstance(column, dict) and 'carrierName' in column for column in artifact['columns'])
                or any(isinstance(o, dict) and o.get('id') == 'weft.output.positioned' for o in artifact['obligations'])):
                _refuse('artifact_version', 'Positional output requires an admitted Weft0.3 profile')
            for position, parameter in enumerate(artifact['parameters'], 1):
                if (not isinstance(parameter, dict) or type(parameter.get('position')) is not int
                    or parameter['position'] != position or type(parameter.get('value')) is not str):
                    _refuse('parameter', 'Exact ordered parameter text required')
            frozen = _freeze(artifact)
            with self._lock:
                if self._disposed: _refuse('disposed', 'Compiler boundary disposed')
                return CompiledQuery(original_request, response_bytes, frozen)
        finally:
            with self._lock:
                self._busy = False
