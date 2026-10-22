# SPDX-License-Identifier: MIT OR Apache-2.0
"""Original compiler packet custody. This module never executes lowered SQL.

The configured compiler is trusted engine code. Recording its claimed source
pin or output does not authenticate that code or admit a native program.
"""
from dataclasses import dataclass
from hashlib import sha256
import json
import re
from importlib.resources import files
from psycopg import sql
from ._action_store import _capture_action_store_context, verify_action_store_enrollment_context_with_cursor
from ._preparation_source_epoch import _context, _restore
from .psycopg_host import PsycopgHost
from .execution import Error, ExecutionFailure
from .weft import _decode



def _json(raw):
    if type(raw) is not bytes or not 1 <= len(raw) <= 8388608:
        raise ValueError('Bounded original program JSON required')
    return _decode(raw, 8388608, 'preparation_program')[1]


def _encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def _artifact(value):
    if (type(value) is not dict or set(value) != {'mediaType', 'utf8', 'sha256'}
            or value['mediaType'] != 'application/json' or type(value['utf8']) is not str):
        raise ValueError('Exact original JSON Artifact required')
    raw = value['utf8'].encode('utf-8')
    if sha256(raw).hexdigest() != value['sha256']:
        raise ValueError('Original program Artifact digest differs')
    return _json(raw)


@dataclass(frozen=True, slots=True)
class OriginalPreparationProgram:
    compiler_source_pin: str
    configuration: bytes
    request: bytes
    compile_response: bytes
    binding_artifact: bytes
    lowering: bytes


@dataclass(frozen=True, slots=True)
class PendingPreparationProgram:
    program_identity: bytes
    registration_key: bytes
    status: str = 'pending_commit'
    authority: bool = False


def compile_preparation_program(compiler_factory, *, compiler_source_pin,
                                configuration, request, binding_artifact, evidence):
    """Invoke the configured original compiler and renderer; retain their bytes.

    No precomputed lowering or caller-selected effective bound is accepted.
    Native source, permission and installed effect custody remain external.
    """
    if type(compiler_source_pin) is not str or not re.fullmatch('[0-9a-f]{40}', compiler_source_pin):
        raise ValueError('Explicit original compiler source pin required')
    config = _json(configuration); original_request = _json(request)
    binding = _json(binding_artifact); _artifact(binding)
    if (type(config) is not dict or type(original_request) is not dict
            or original_request.get('interfaceVersion') != 'weft-mutation-compile/0.1.0'
            or original_request.get('dialect') != 'weft-mutation/0.1.0'
            or type(evidence) is not tuple or not 1 <= len(evidence) <= 64
            or any(type(x) is not str or not 1 <= len(x.encode('utf-8')) <= 4096 for x in evidence)):
        raise ValueError('Original mutation request and source evidence required')
    model = original_request['model']; document = _artifact(model)
    if (type(original_request.get('modelPin')) is not dict
            or original_request['modelPin'].get('umfVersion') != '0.10.0'
            or type(document) is not dict or document.get('umf') != '0.10.0'):
        raise ValueError('Only current UMF 0.10.0 preparation programs are supported')
    compiler = compiler_factory(configuration.decode('utf-8'))
    response = compiler.compile_json(request.decode('utf-8'))
    if type(response) is not str:
        raise ValueError('Original synchronous compiler JSON required')
    response_raw = response.encode('utf-8'); compiled = _json(response_raw)
    if compiled.get('status') != 'compiled':
        raise ValueError('Original mutation compiler refused')
    plan = _artifact(compiled['plan'])
    if (plan.get('protocol') != 'umf.actions.plan/1'
            or plan.get('model') != original_request['modelPin']
            or plan.get('action') != original_request['action']
            or plan.get('target') != original_request['target']
            or plan.get('limits') != original_request['limits']):
        raise ValueError('Original compiled plan correspondence differs')
    _artifact(plan['selection']['artifact'])
    maximum = plan['limits']['maxItems']
    if type(maximum) is not int or not 1 <= maximum <= 10000:
        raise ValueError('Original bounded selection required')
    registration_raw = _encode({
        'model': model, 'modelPin': original_request['modelPin'],
        'binding': binding, 'evidence': list(evidence),
    })
    handle = compiler.register_truss_selection(registration_raw.decode('utf-8'))
    lowering_request_raw = _encode({
        'selection': plan['selection']['artifact'], 'model': model,
        'binding': binding, 'maxItems': maximum,
    })
    result = compiler.lower_selection_json(handle, lowering_request_raw.decode('utf-8'))
    if type(result) is not str:
        raise ValueError('Original synchronous lowering JSON required')
    lowering_raw = result.encode('utf-8'); lowering = _json(lowering_raw)
    if (lowering.get('status') != 'lowered'
            or lowering.get('bounds') != {'maxItems': maximum, 'fetchLimit': maximum + 1}):
        raise ValueError('Original selection bounds differ')
    invocation = _encode({'registrationRequest': registration_raw.decode('utf-8'),
                          'loweringRequest': lowering_request_raw.decode('utf-8'),
                          'response': result})
    if sum(map(len, (configuration, request, response_raw, binding_artifact, invocation))) > 16777216:
        raise ValueError('Original program packet exceeds private registration bound')
    return OriginalPreparationProgram(compiler_source_pin, configuration, request,
                                      response_raw, binding_artifact, invocation)


def register_preparation_program_in_transaction(host, transaction, *, store_context,
                                                registration_key, program):
    """Trusted quiescent administrative byte enrollment, never native admission.

    Caller owns COMMIT. Original artifacts are private immutable data, including
    SQL text; no helper executes them or grants an ordinary caller access.
    """
    try:
        context = _capture_action_store_context(store_context)
        if (type(host) is not PsycopgHost or type(program) is not OriginalPreparationProgram
                or type(registration_key) is not bytes or not 1 <= len(registration_key) <= 256
                or not re.fullmatch('[0-9a-f]{40}', program.compiler_source_pin)):
            raise ValueError('Original bounded registration required')
        packet = tuple(getattr(program, k) for k in
                       ('configuration', 'request', 'compile_response', 'binding_artifact', 'lowering'))
        for raw in packet: _json(raw)
        if sum(map(len, packet)) > 16777216:
            raise ValueError('Original packet exceeds registration bound')
    except (ValueError, TypeError):
        return Error(ExecutionFailure('execution_obligation', 'Original bounded preparation program required'))

    def register(cursor, observed):
        from ._installation_privileges import require_empty_managed_grants_with_cursor
        require_empty_managed_grants_with_cursor(cursor,'Preparation program registry')
        path, installation, owner, actor = _context(cursor)
        verify_action_store_enrollment_context_with_cursor(cursor, context, installation)
        binding = _artifact(_json(program.binding_artifact))
        if binding.get('installationId') != installation:
            raise ValueError('Original same-installation binding required')
        cursor.execute("SELECT control_id FROM ONLY truss.action_store_registration WHERE singleton AND initial_receipt_bytes=%s FOR SHARE NOWAIT", (context.receipt_bytes,), prepare=False)
        rows = cursor.fetchmany(2)
        if len(rows) != 1: raise ValueError('Original issued store required')
        store_id = rows[0][0]
        cursor.execute("SELECT pg_catalog.to_regclass('truss.preparation_program_registration')::oid", prepare=False)
        if cursor.fetchone() == (None,):
            raw = files('truss').joinpath('_security_bootstrap', 'preparation-program-storage.sql').read_bytes()
            cursor.execute(raw.decode('utf-8'), prepare=False)
            cursor.execute('SELECT rolname FROM pg_catalog.pg_roles WHERE oid=%s::oid', (owner,), prepare=False)
            name = cursor.fetchone()[0]
            for statement in ('ALTER TABLE truss.preparation_program_registration OWNER TO {}',
                              'ALTER SEQUENCE truss.preparation_program_registration_program_id_seq OWNER TO {}'):
                cursor.execute(sql.SQL(statement).format(sql.Identifier(name)), prepare=False)
        cursor.execute('LOCK TABLE ONLY truss.preparation_program_registration IN SHARE ROW EXCLUSIVE MODE NOWAIT', prepare=False)
        _verify_home(cursor, owner)
        columns = ('store_receipt_bytes,compiler_source_pin,original_configuration,original_request,'
                   'original_plan_artifact,original_binding_artifact,original_lowering')
        expected = (context.receipt_bytes, program.compiler_source_pin, *packet)
        cursor.execute('SELECT program_identity::text,' + columns + ' FROM ONLY truss.preparation_program_registration WHERE store_control_id=%s AND registration_key=%s FOR SHARE NOWAIT',
                       (store_id, registration_key), prepare=False)
        existing = cursor.fetchmany(2)
        if existing:
            if len(existing) != 1 or existing[0][1:] != expected:
                raise ValueError('Original program registration retry differs')
            identity = existing[0][0]
        else:
            cursor.execute('INSERT INTO truss.preparation_program_registration(store_control_id,registration_key,' + columns + ',issuer_xid,issuer_actor_oid,issued_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,pg_catalog.pg_current_xact_id(),%s::oid,pg_catalog.clock_timestamp()) RETURNING program_identity::text',
                           (store_id, registration_key, *expected, int(actor)), prepare=False)
            identity = cursor.fetchone()[0]
        _restore(cursor, path)
        return PendingPreparationProgram(_encode(identity), registration_key)
    return host._run_operation(transaction, register)


def _verify_home(cursor, owner):
    cursor.execute("SELECT c.relowner,c.relkind,c.relpersistence,c.relrowsecurity,c.relforcerowsecurity FROM pg_catalog.pg_class c WHERE c.oid='truss.preparation_program_registration'::regclass", prepare=False)
    if cursor.fetchmany(2) != [(owner, 'r', 'p', False, False)]:
        raise ValueError('Private original program storage required')
    cursor.execute("SELECT a.grantee,a.grantor,a.is_grantable FROM pg_catalog.pg_class c CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault(CASE WHEN c.relkind='S' THEN 's'::\"char\" ELSE 'r'::\"char\" END,c.relowner))) a WHERE c.oid IN ('truss.preparation_program_registration'::regclass,'truss.preparation_program_registration_program_id_seq'::regclass)", prepare=False)
    acl = cursor.fetchmany(32)
    if not acl or any(row != (owner, owner, False) for row in acl):
        raise ValueError('Original owner-only program storage required')
    cursor.execute("SELECT tgname,tgfoid::regprocedure::text,tgenabled,tgtype FROM pg_catalog.pg_trigger WHERE tgrelid='truss.preparation_program_registration'::regclass AND NOT tgisinternal", prepare=False)
    if cursor.fetchmany(2) != [('preparation_program_registration_immutable', 'truss.catalog_immutable()', 'A', 58)]:
        raise ValueError('Original immutable program storage required')
