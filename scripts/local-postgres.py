#!/usr/bin/env python3
"""Pinned pgserver development launcher; does not install or upgrade Truss."""
import argparse
import json
from pathlib import Path
import signal
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--probe', action='store_true', help='Verify readiness, then stop; retain data')
    args = parser.parse_args()
    stop = threading.Event()
    for name in ('SIGINT', 'SIGTERM'):
        signal.signal(getattr(signal, name), lambda *_: stop.set())
    from truss import LocalPostgres
    with LocalPostgres(args.data_dir) as runtime:
        info = runtime.info
        print(json.dumps({'runtime': 'pgserver', 'runtimeVersion': info.runtime_version,
                          'serverVersion': info.server_version, 'dataDirectory': str(info.data_directory),
                          'connectionUri': info.connection_uri, 'trussInstallation': info.truss_installation,
                          'scope': 'local_postgresql_only'}), flush=True)
        if not args.probe:
            stop.wait()


if __name__ == '__main__':
    main()
