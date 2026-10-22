# SPDX-License-Identifier: MIT OR Apache-2.0
"""Pinned pgserver development launcher with fresh current Truss installation."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import threading


@contextmanager
def _without_postgres_environment():
    """Keep inherited libpq defaults from changing the owned install session."""
    saved = {name: value for name, value in os.environ.items() if name.startswith('PG')}
    for name in saved:
        os.environ.pop(name, None)
    try:
        yield
    finally:
        os.environ.update(saved)


class _InstallRefusalError(RuntimeError):
    """A typed, contained refusal from the fresh-install operation."""

    def __init__(self, refusal):
        self.refusal = refusal
        super().__init__(refusal.code)

    def payload(self):
        refusal = self.refusal
        result = {'outcome': 'refused', 'code': refusal.code}
        for field in ('role_name', 'object_class', 'phase'):
            value = getattr(refusal, field)
            if value is not None:
                result[field] = value
        return result


def _required(result, *, install_result=False):
    from truss import InstallRefused, Ok
    if not isinstance(result, Ok):
        raise RuntimeError(f'Truss installation/status refused: {result!r}')
    if isinstance(result.value, InstallRefused):
        if install_result:
            raise _InstallRefusalError(result.value)
        raise RuntimeError('Truss installation/status refused: InstallRefused')
    return result.value


def _installation(connection_uri, tolerated_grantees=()):
    """The CLI owns fresh installation and status-confirmation settlement."""
    import psycopg
    from truss import (CatalogRuntimeConfiguration, CatalogRuntimeStatus,
                       adopt_psycopg_host, create_reference_assembly)

    # The URI carries the owned socket/database/user; the CLI has removed
    # inherited PG* settings for this one-shot connection.
    with psycopg.connect(connection_uri, autocommit=True,
                         options='-c statement_timeout=10000') as connection:
        pending = None
        with connection.transaction():
            host = adopt_psycopg_host(connection, statement_timeout_ms=10000,
                                     operation_timeout_ms=30000)
            try:
                tx = _required(host.adopt_transaction())
                assembly = _required(create_reference_assembly(CatalogRuntimeConfiguration(), host))
                before = _required(assembly.status_in_transaction(tx))
                if type(before) is not CatalogRuntimeStatus:
                    raise RuntimeError('Exact public installation status required')
                if before.installed is False:
                    pending = _required(assembly.install_in_transaction(
                        tx, tolerated_grantees=tuple(tolerated_grantees)), install_result=True)
                    identity = pending.installation_id
                elif before.installed is True:
                    if tolerated_grantees:
                        raise RuntimeError(
                            '--tolerated-grantee applies only to a fresh installation; '
                            'the existing installation policy is retained')
                    identity = before.installation_id
                else:
                    raise RuntimeError('Exact installed status required')
            finally:
                host.detach()
        # The first caller transaction committed. Confirm through a fresh one.
        with connection.transaction():
            host = adopt_psycopg_host(connection, statement_timeout_ms=10000,
                                     operation_timeout_ms=30000)
            try:
                tx = _required(host.adopt_transaction())
                assembly = _required(create_reference_assembly(CatalogRuntimeConfiguration(), host))
                confirmed = _required(assembly.status_in_transaction(tx))
                if type(confirmed) is not CatalogRuntimeStatus or confirmed.installed is not True or not identity or confirmed.installation_id != identity:
                    raise RuntimeError('Committed installation status did not confirm the original identity')
                expected_release = pending.release_id if pending else before.release_id
                if not confirmed.release_id or not confirmed.release_sha256 or confirmed.layout_profile is None or confirmed.release_id != expected_release:
                    raise RuntimeError('Committed release status did not confirm the original target')
            finally:
                host.detach()
        result = {'action': 'created' if pending else 'status_confirmed',
                  'installationId': identity, 'catalogRevision': confirmed.revision,
                  'releaseId': confirmed.release_id, 'releaseSha256': confirmed.release_sha256,
                  'layoutProfile': {'identity': confirmed.layout_profile.identity,
                                    'version': confirmed.layout_profile.version,
                                    'sha256': confirmed.layout_profile.sha256}}
        if pending:
            result.update(ownerRole=pending.owner_role, registrarRole=pending.registrar_role)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--probe', action='store_true', help='Verify readiness, then stop; retain data')
    parser.add_argument('--install', action='store_true',
                        help='Explicitly install fresh Truss or confirm current status; never upgrade')
    parser.add_argument('--tolerated-grantee', action='append', default=[], metavar='ROLE',
                        help='On a fresh install, retain existing grants to this exact PostgreSQL role name; repeat as needed')
    args = parser.parse_args()
    if args.tolerated_grantee and not args.install:
        parser.error('--tolerated-grantee requires --install')
    stop = threading.Event()
    previous = {}
    for name in ('SIGINT', 'SIGTERM'):
        signum = getattr(signal, name)
        previous[signum] = signal.signal(signum, lambda *_: stop.set())
    try:
        from truss import LocalPostgres
        with LocalPostgres(args.data_dir) as runtime:
            info = runtime.info
            if args.install:
                # This executable handles a single owned server in its own
                # process, so temporarily remove libpq's process environment
                # while creating its explicit host connection.
                try:
                    with _without_postgres_environment():
                        installation = _installation(info.connection_uri, args.tolerated_grantee)
                except _InstallRefusalError as error:
                    print(json.dumps(error.payload()), flush=True)
                    raise SystemExit(1)
            else:
                installation = None
            output = {'runtime': 'pgserver', 'runtimeVersion': info.runtime_version,
                              'serverVersion': info.server_version, 'dataDirectory': str(info.data_directory),
                              'socketDirectory': str(info.socket_directory), 'port': info.port,
                              'connectionUri': info.connection_uri, 'trussInstallation': 'installed' if installation else info.truss_installation,
                              'scope': 'local_truss_candidate' if installation else 'local_postgresql_only'}
            if installation is not None:
                output['installation'] = installation
            print(json.dumps(output), flush=True)
            if not args.probe:
                stop.wait()
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


if __name__ == '__main__':
    main()


def migrate_main():
    """Explicit migration commands; never start an application or reset a database."""
    import os
    import psycopg
    from dataclasses import asdict
    from truss.migrations import RuntimeMigrations
    from truss.recovery_registry import HostRecoveryRegistry
    parser=argparse.ArgumentParser(description=migrate_main.__doc__)
    parser.add_argument('action',choices=('status','verify','backup-metadata','prepare','apply','reconcile','receipt'))
    parser.add_argument('--registry',required=True,type=Path,help='Host-owned restart-durable recovery registry')
    parser.add_argument('--reference',help='Original reference returned by prepare; retain it across restarts')
    args=parser.parse_args()
    uri=os.environ.get('TRUSS_DATABASE_URI')
    if not uri:parser.error('Set TRUSS_DATABASE_URI to the administrative connection URI')
    if args.action in ('apply','reconcile','receipt') and not args.reference:parser.error('Original --reference required')
    tool=RuntimeMigrations(lambda:psycopg.connect(uri,autocommit=True,options='-c statement_timeout=10000'),HostRecoveryRegistry(args.registry))
    try:
        result=getattr(tool,args.action)(args.reference) if args.action in ('apply','reconcile','receipt') else getattr(tool,args.action.replace('-','_'))()
        value=result if isinstance(result,dict) else asdict(result)
    except Exception as error:
        print(json.dumps({'outcome':'refused','detail':str(error)}));raise SystemExit(1)
    print(json.dumps(value))
    if value.get('outcome') in ('rolled_back','commit_unknown','recovery_required','committed_unverified'):raise SystemExit(1)
