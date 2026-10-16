"""Pinned pgserver development launcher with explicit Truss installation/migration."""
import argparse
import json
from pathlib import Path
import signal
import threading


def _installation(connection_uri, *, upgrade=False):
    """The CLI owns settlement; upgrading requires its explicit caller option."""
    import psycopg
    from truss import (CatalogRuntimeConfiguration, CatalogRuntimeStatus, PendingRuntimeUpgrade, Ok,
                       adopt_psycopg_host, create_reference_assembly)

    def required(result):
        if not isinstance(result, Ok):
            raise RuntimeError(f'Truss installation/status refused: {result!r}')
        return result.value

    with psycopg.connect(connection_uri, autocommit=True,
                         options='-c statement_timeout=10000') as connection:
        pending = None
        upgraded = None
        with connection.transaction():
            host = adopt_psycopg_host(connection, statement_timeout_ms=10000,
                                     operation_timeout_ms=30000)
            try:
                tx = required(host.adopt_transaction())
                assembly = required(create_reference_assembly(CatalogRuntimeConfiguration(), host))
                if upgrade:
                    upgraded = required(assembly.upgrade_in_transaction(tx))
                    if type(upgraded) is not PendingRuntimeUpgrade:
                        raise RuntimeError('Exact public runtime upgrade result required')
                    identity = upgraded.installation_id
                else:
                    before = required(assembly.status_in_transaction(tx))
                    if type(before) is not CatalogRuntimeStatus:
                        raise RuntimeError('Exact public installation status required')
                    if before.installed is False:
                        pending = required(assembly.install_in_transaction(tx))
                        identity = pending.installation_id
                    elif before.installed is True:
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
                tx = required(host.adopt_transaction())
                assembly = required(create_reference_assembly(CatalogRuntimeConfiguration(), host))
                confirmed = required(assembly.status_in_transaction(tx))
                if type(confirmed) is not CatalogRuntimeStatus or confirmed.installed is not True or not identity or confirmed.installation_id != identity:
                    raise RuntimeError('Committed installation status did not confirm the original identity')
                expected_release = upgraded.release_id if upgraded else pending.release_id if pending else before.release_id
                if not confirmed.release_id or not confirmed.release_sha256 or confirmed.layout_profile is None or confirmed.release_id != expected_release:
                    raise RuntimeError('Committed release status did not confirm the original target')
            finally:
                host.detach()
        result = {'action': upgraded.outcome if upgraded else 'created' if pending else 'status_confirmed',
                  'installationId': identity, 'catalogRevision': confirmed.revision,
                  'releaseId': confirmed.release_id, 'releaseSha256': confirmed.release_sha256,
                  'layoutProfile': {'identity': confirmed.layout_profile.identity,
                                    'version': confirmed.layout_profile.version,
                                    'sha256': confirmed.layout_profile.sha256}}
        if pending:
            result.update(ownerRole=pending.owner_role, registrarRole=pending.registrar_role)
        if upgraded:
            result.update(previousReleaseId=upgraded.previous_release_id)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--probe', action='store_true', help='Verify readiness, then stop; retain data')
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument('--install', action='store_true',
                        help='Explicitly install fresh Truss or confirm current status; never upgrade')
    operation.add_argument('--upgrade', action='store_true',
                        help='Explicitly apply supported candidate migration; never install or repair')
    args = parser.parse_args()
    stop = threading.Event()
    previous = {}
    for name in ('SIGINT', 'SIGTERM'):
        signum = getattr(signal, name)
        previous[signum] = signal.signal(signum, lambda *_: stop.set())
    try:
        from truss import LocalPostgres
        with LocalPostgres(args.data_dir) as runtime:
            info = runtime.info
            installation = _installation(info.connection_uri, upgrade=args.upgrade) if args.install or args.upgrade else None
            output = {'runtime': 'pgserver', 'runtimeVersion': info.runtime_version,
                              'serverVersion': info.server_version, 'dataDirectory': str(info.data_directory),
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
