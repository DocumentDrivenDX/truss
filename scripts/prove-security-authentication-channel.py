# SPDX-License-Identifier: MIT OR Apache-2.0
"""Conditional authentication/endpoint laws; no native refinement or authority."""
from pathlib import Path
import hashlib
import json
import sys
import uuid
import z3

root = Path.cwd()
native = Path(sys.argv[1])
assert native.is_relative_to(Path('docs/helix/04-build/evidence/security-native-authentication'))
assert json.loads(native.read_text())['status'] == 'authentication-component-passed'
paths = [Path(__file__).relative_to(root), Path('scripts/check-security-native-authentication.py'), native]
out = root / 'docs/helix/04-build/evidence/security-authentication-channel-formal' / str(uuid.uuid4())
out.mkdir(parents=True)
pins = {}
for path in paths:
    raw = path.read_bytes()
    pins[str(path)] = hashlib.sha256(raw).hexdigest()
    target = out / 'preimages' / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
required0, required1, credential0, credential1 = z3.Bools('required_at_login required_at_new_login credential_at_login credential_at_new_login')
accepted0, accepted1, authenticated0, authenticated1, session_end = z3.Bools('accepted_original accepted_new authenticated_original authenticated_new original_session_authentication_end')
subject_bound, target_bound = z3.Bools('independent_ontology_subject_binding independent_target_authentication')
protocol = z3.And(accepted0 == z3.Or(z3.Not(required0), credential0),
                  accepted1 == z3.Or(z3.Not(required1), credential1),
                  authenticated0 == z3.And(required0, credential0),
                  authenticated1 == z3.And(required1, credential1), session_end == authenticated0)
other_required, other_credential = z3.Bools('second_route_required second_route_credential')
other_accepted = z3.Or(z3.Not(other_required), other_credential)
other_authenticated = z3.And(other_required, other_credential)
queries = [
    ('required_credential_excludes_uncredentialed_startup', 'unsat', [protocol, required1, z3.Not(credential1), accepted1]),
    ('authenticated_session_survives_endpoint_weakening', 'sat', [protocol, required0, credential0, z3.Not(required1), z3.Not(credential1), session_end, accepted1, z3.Not(authenticated1)]),
    ('matching_role_without_challenge_does_not_authenticate', 'sat', [protocol, z3.Not(required1), accepted1, z3.Not(authenticated1)]),
    ('native_authentication_does_not_bind_ontology_subject', 'sat', [protocol, authenticated0, z3.Not(subject_bound)]),
    ('native_authentication_does_not_authenticate_target', 'sat', [protocol, authenticated0, z3.Not(target_bound)]),
    ('both_required_routes_authenticate_each_accepted_startup', 'unsat', [protocol, required1, other_required, z3.Or(z3.And(accepted1, z3.Not(authenticated1)), z3.And(other_accepted, z3.Not(other_authenticated)))]),
    ('unknown_alternate_route_defeats_known_route_authentication', 'sat', [protocol, required1, credential1, authenticated1, z3.Not(other_required), other_accepted, z3.Not(other_authenticated)]),
]
results = []
for name, expected, clauses in queries:
    solver = z3.Solver()
    solver.set(timeout=10000)
    solver.add(*clauses)
    smt = solver.to_smt2()
    (out / (name + '.smt2')).write_text(smt)
    observed = str(solver.check())
    context = z3.Context()
    replay = z3.Solver(ctx=context)
    replay.set(timeout=10000)
    replay.add(z3.parse_smt2_string(smt, ctx=context))
    replayed = str(replay.check())
    assert observed == expected and replayed == expected, name
    results.append({'id': name, 'expected': expected, 'observed': observed, 'freshContextReplay': replayed,
                    'smt2Sha256': hashlib.sha256(smt.encode()).hexdigest(),
                    'model': str(solver.model()) if observed == 'sat' else None})
assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in pins.items())
receipt = {'status': 'conditional-model-passed', 'solver': z3.get_version_string(), 'sourceDigests': pins,
           'queries': results, 'nativePacket': str(native),
           'scope': 'Two declared connection routes, original session authentication and one endpoint policy transition.',
           'limitations': ['Credential challenge and immutable original-session identity are explicit premises',
                           'Faithful PostgreSQL/Psycopg/HBA mapping and complete route inventory are not proved by this Boolean model',
                           'Native packet is a separately scoped owned fixture; no proof of Python/native protocol refinement',
                           'No production subject/target/issuer/credentials/writer closure or backend admission'],
           'acceptancePrerequisites': ['TD-056 C01/C02/C04', 'STP-056 B05/B10/B11/B12']}
(out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': receipt['status'], 'queries': len(results), 'evidence': str(out)}))
