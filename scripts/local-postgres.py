#!/usr/bin/env python3
"""Pinned pgserver development launcher; does not install or upgrade Truss."""
import argparse
import importlib.metadata
import importlib.resources
import json
from pathlib import Path
import signal
import subprocess
import threading


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', required=True, type=Path)
    parser.add_argument('--probe', action='store_true', help='Verify readiness, then stop; retain data')
    args = parser.parse_args()
    import pgserver
    if importlib.metadata.version('pgserver') != '0.1.4':
        parser.error('Install packages/python/local-runtime-requirements.txt in your Python environment')
    directory = args.data_dir.expanduser().resolve()
    directory.parent.mkdir(parents=True, exist_ok=True)
    stop = threading.Event()
    for name in ('SIGINT', 'SIGTERM'):
        signal.signal(getattr(signal, name), lambda *_: stop.set())
    server = pgserver.get_server(directory, cleanup_mode='stop')
    try:
        # Use argv, not the upstream convenience method's shell interpolation.
        psql = Path(str(importlib.resources.files('pgserver'))) / 'pginstall' / 'bin' / 'psql'
        version = subprocess.check_output(
            [str(psql), server.get_uri(), '-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1',
             '-c', 'SHOW server_version'], text=True, timeout=30).strip()
        print(json.dumps({'runtime': 'pgserver', 'runtimeVersion': '0.1.4',
                          'serverVersion': version, 'dataDirectory': str(directory),
                          'connectionUri': server.get_uri(), 'trussInstallation': 'not_checked',
                          'scope': 'local_postgresql_only'}), flush=True)
        if not args.probe:
            stop.wait()
    finally:
        server.cleanup()


if __name__ == '__main__':
    main()
