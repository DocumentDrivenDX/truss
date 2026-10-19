# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exercise the actual private receiver parser; no native/authentication claim."""
from pathlib import Path
import base64
import hashlib
import json
import platform
import uuid
import security_owned_receiver as receiver


def main():
    root = Path(__file__).resolve().parent.parent
    paths = ['scripts/check-security-owned-receiver-grammar.py', 'scripts/security_owned_receiver.py']
    sources = {name: (root / name).read_bytes() for name in paths}
    request = b'{"interfaceVersion":"truss-owned-decision-request/0.1","operation":"read"}'
    cases = [('canonical', request, True), ('empty', b'', False)]
    # Independent expected observations for every single byte outside the JSON document.
    for byte in range(256):
        allowed = byte in (9, 10, 13, 32)
        cases.append((f'prefix-{byte:02x}', bytes([byte]) + request, allowed))
        cases.append((f'suffix-{byte:02x}', request + bytes([byte]), allowed))
    cases.extend([
        ('exact-limit', request + b' ' * (1024 - len(request)), True),
        ('over-limit', request + b' ' * (1025 - len(request)), False),
        ('escaped-key', request.replace(b'operation', b'oper\\u0061tion'), True),
        ('escaped-value', request.replace(b'read', b'r\\u0065ad'), True),
        ('reordered', b'{"operation":"read","interfaceVersion":"truss-owned-decision-request/0.1"}', True),
        ('duplicate', request[:-1] + b',"operation":"read"}', False),
        ('escaped-duplicate', request[:-1] + b',"oper\\u0061tion":"read"}', False),
        ('duplicate-version', request[:-1] + b',"interfaceVersion":"truss-owned-decision-request/0.1"}', False),
        ('extra-sql', request[:-1] + b',"sql":"select 1"}', False),
        ('extra-actor', request[:-1] + b',"actor":"admin"}', False),
        ('extra-subject', request[:-1] + b',"subject":true}', False),
        ('explain', request.replace(b'read', b'explain'), False),
        ('null-operation', request.replace(b'"read"', b'null'), False),
        ('array-operation', request.replace(b'"read"', b'["read"]'), False),
        ('nan-operation', request.replace(b'"read"', b'NaN'), False),
        ('infinite-operation', request.replace(b'"read"', b'Infinity'), False),
        ('lone-surrogate', request.replace(b'read', b'\\ud800'), False),
        ('invalid-utf8', request.replace(b'read', b'\xff'), False),
        ('utf8-bom', b'\xef\xbb\xbf' + request, False),
        ('two-documents', request + request, False),
        ('trailing-comma', request[:-1] + b',}', False),
        ('nested-document', b'[' * 450 + request + b']' * 450, False),
        ('bytearray', bytearray(request), False),
        ('memoryview', memoryview(request), False),
        ('string', request.decode(), False),
        ('null-carrier', None, False),
    ])
    scope = tuple(object() for _ in range(7))
    selected = object.__new__(receiver._OwnedDecisionReceiver)
    selected._OwnedDecisionReceiver__scope = scope
    calls = []
    marker = object()
    original = receiver.run_delegated_owned_identity_read

    def dispatch(*args):
        assert all(a is b for a, b in zip(args, scope)) and len(args) == len(scope)
        calls.append(args)
        return marker

    def observe(function, value):
        before = len(calls)
        try:
            result = function(value)
        except ValueError as error:
            assert str(error) == 'Owned semantic request refused'
            assert len(calls) == before
            return False
        assert result is marker and len(calls) == before + 1
        return True

    receiver.run_delegated_owned_identity_read = dispatch
    observations = []
    try:
        for name, value, expected in cases:
            observed = observe(selected.dispatch, value)
            assert observed == expected, (name, expected, observed)
            observations.append({'id': name, 'expectedDispatch': expected, 'observedDispatch': observed,
                                 'carrierType': type(value).__name__,
                                 'bytesBase64': base64.b64encode(bytes(value)).decode() if isinstance(value, (bytes, bytearray, memoryview)) else None})
        # Deliberately weaken the parser: the suite must detect each distinct regression.
        def weakened(value):
            parsed = json.loads(value)
            if parsed['interfaceVersion'] != 'truss-owned-decision-request/0.1' or parsed['operation'] != 'read':
                raise ValueError('Owned semantic request refused')
            return dispatch(*scope)
        controls = []
        for name in ('duplicate', 'escaped-duplicate', 'extra-sql', 'over-limit', 'bytearray'):
            value = next(value for case, value, _ in cases if case == name)
            assert observe(weakened, value)
            controls.append({'id': name, 'weakenedParserDispatched': True, 'suiteWouldReject': True})
    finally:
        receiver.run_delegated_owned_identity_read = original
    assert all((root / name).read_bytes() == raw for name, raw in sources.items())
    out = root / 'docs/helix/04-build/evidence/security-owned-receiver-grammar' / str(uuid.uuid4())
    out.mkdir(parents=True)
    for name, raw in sources.items():
        target = out / 'preimages' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    receipt = {'status': 'parser-component-passed', 'python': platform.python_version(),
               'sourceDigests': {name: hashlib.sha256(raw).hexdigest() for name, raw in sources.items()},
               'cases': observations, 'negativeControls': controls,
               'scope': 'Actual receiver dispatch parser with isolated original-scope sentinel; constructor and delegated native evaluation excluded.',
               'limitations': ['Finite adversarial corpus, not universal parser refinement',
                               'No native, credentials, authentication, route closure or backend profile admission',
                               'Private fixed read spike does not restrict the full Weft query surface'],
               'acceptancePrerequisites': ['TD-056 C03', 'STP-056 B10/B12', 'US-056 AC9/AC10']}
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'], 'cases': len(cases), 'negativeControls': len(controls), 'evidence': str(out)}))


if __name__ == '__main__':
    main()
