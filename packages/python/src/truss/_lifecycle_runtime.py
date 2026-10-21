# SPDX-License-Identifier: MIT OR Apache-2.0
"""Private adapters for person-minimal runtime status and admin recovery."""
from __future__ import annotations

import json
from typing import Any

from .execution import Error, Ok
from .lifecycle import (AdminInstallRecovery, LifecycleRefused,
                        PersonRuntimeStatus)


def _unique_object(pairs):
    value = {}
    for key, child in pairs:
        if key in value:
            raise ValueError('Duplicate native lifecycle member')
        value[key] = child
    return value


def _no_numbers(_token):
    raise ValueError('Numeric native lifecycle token')


def _json(raw: bytes):
    if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
        raise ValueError('Bounded native lifecycle response required')
    return json.loads(raw, object_pairs_hook=_unique_object, parse_int=_no_numbers,
                      parse_float=_no_numbers, parse_constant=_no_numbers)


def _decode_status(raw: bytes) -> PersonRuntimeStatus:
    value = _json(raw)
    if (type(value) is not dict or set(value) != {'outcome', 'installation', 'catalog'}
            or value['outcome'] != 'status'
            or value['installation'] not in ('compatible', 'incompatible')
            or value['catalog'] not in ('empty', 'accepted', 'unknown')
            or value['installation'] == 'incompatible' and value['catalog'] != 'unknown'
            or value['installation'] == 'compatible' and value['catalog'] == 'unknown'):
        raise ValueError('Exact minimal runtime status required')
    return PersonRuntimeStatus(installation=value['installation'], catalog=value['catalog'])


def _decode_recovery(raw: bytes) -> AdminInstallRecovery:
    value = _json(raw)
    if (type(value) is not dict or set(value) != {'outcome', 'ownerRole', 'registrarRole'}
            or value['outcome'] != 'recovered'
            or any(type(value[key]) is not str or not value[key]
                   for key in ('ownerRole', 'registrarRole'))
            or value['ownerRole'] == value['registrarRole']):
        raise ValueError('Exact separate administrator role recovery required')
    return AdminInstallRecovery(owner_role=value['ownerRole'],
                                registrar_role=value['registrarRole'])


def _catalog_reason(error: Error) -> str | None:
    if error.error.code != 'execution_obligation':
        return None
    return {'42501': 'unauthorized', '0A000': 'profile', '55P03': 'observation',
            '54000': 'observation', '22023': 'observation', '3F000': 'installation',
            '42883': 'installation'}.get(error.error.sql_state)


def person_runtime_status(host, transaction, manifest: dict[str, Any], digest: str,
                          pin_cursor) -> Ok | Error:
    from .psycopg_host import PsycopgHost
    if type(host) is not PsycopgHost or type(manifest) is not dict or type(digest) is not str:
        return Ok(LifecycleRefused(reason='observation'))

    def observe(cursor, _observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.person_runtime_status(%s,%s,%s::jsonb)',
            (manifest['releaseId'], digest, json.dumps(manifest['layoutProfile'],
             sort_keys=True, separators=(',', ':'))), prepare=False)
        return _decode_status(bytes(cursor.fetchone()[0]))

    result = host._run_operation(transaction, observe, function_call=True)
    if (isinstance(result, Error) and result.error.code == 'execution_obligation'
            and result.error.sql_state in ('3F000', '42883')):
        def absent(cursor, _observed):
            pin_cursor(cursor)
            cursor.execute("SELECT pg_catalog.to_regnamespace('truss') IS NULL", prepare=False)
            return cursor.fetchone()[0]
        check = host._run_operation(transaction, absent)
        if isinstance(check, Ok):
            if check.value:
                return Ok(PersonRuntimeStatus(installation='absent', catalog='unknown'))
            return Ok(LifecycleRefused(reason='installation'))
        return check
    reason = _catalog_reason(result) if isinstance(result, Error) else None
    return Ok(LifecycleRefused(reason=reason)) if reason else result


def admin_install_recovery(host, transaction, pin_cursor) -> Ok | Error:
    from .psycopg_host import PsycopgHost
    if type(host) is not PsycopgHost:
        return Ok(LifecycleRefused(reason='observation'))

    def recover(cursor, _observed):
        pin_cursor(cursor)
        cursor.execute('SELECT truss.admin_install_recovery()', prepare=False)
        return _decode_recovery(bytes(cursor.fetchone()[0]))

    result = host._run_operation(transaction, recover, function_call=True)
    reason = _catalog_reason(result) if isinstance(result, Error) else None
    return Ok(LifecycleRefused(reason=reason)) if reason else result
