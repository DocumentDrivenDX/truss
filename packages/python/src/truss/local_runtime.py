# SPDX-License-Identifier: MIT OR Apache-2.0
"""Explicit, retained-data pgserver lifecycle; no Truss install or migration."""
from dataclasses import dataclass
import hashlib
import importlib.metadata
import importlib.resources
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import threading
from urllib.parse import quote

from ._runtime_profile import RUNTIME_DISTRIBUTION, RUNTIME_VERSION, SERVER_VERSION


class LocalRuntimeError(RuntimeError):
    """Local profile unavailable or directory custody refused; no automatic retry."""


@dataclass(frozen=True)
class RuntimeInfo:
    connection_uri: str
    data_directory: Path
    server_version: str
    runtime_version: str = '0.1.4'
    truss_installation: str = 'not_checked'
    socket_directory: Path | None = None
    port: int = 5432


_active_directories: set[Path] = set()
_directory_lock = threading.Lock()
_PORT = 5432


def _private_environment() -> dict[str, str]:
    """Keep shell-provided libpq/PostgreSQL settings out of owned clusters."""
    environment = os.environ.copy()
    for name in tuple(environment):
        if name.startswith('PG'):
            environment.pop(name, None)
    return environment


def _runtime_root() -> Path:
    # Keep the socket path short enough for AF_UNIX even when the caller places
    # PGDATA inside a deeply nested checkout. /private/tmp is the real macOS
    # temporary directory; /tmp is used on other Unix platforms.
    if os.name == 'nt':
        raise LocalRuntimeError('The isolated local runtime requires Unix-domain sockets')
    base = Path('/private/tmp') if sys.platform == 'darwin' else Path('/tmp')
    return base / f'truss-pg18-{os.getuid()}'


def _owned_directory(path: Path, *, create: bool) -> None:
    if create:
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        details = path.lstat()
    except FileNotFoundError as error:
        raise LocalRuntimeError(f'Runtime directory is missing: {path}') from error
    if stat.S_ISLNK(details.st_mode) or not stat.S_ISDIR(details.st_mode):
        raise LocalRuntimeError(f'Runtime path must be a real directory: {path}')
    if hasattr(os, 'getuid') and details.st_uid != os.getuid():
        raise LocalRuntimeError(f'Runtime directory is owned by another user: {path}')
    if stat.S_IMODE(details.st_mode) != 0o700:
        try:
            path.chmod(0o700)
        except OSError as error:
            raise LocalRuntimeError(f'Runtime directory permissions must be 0700: {path}') from error
    if stat.S_IMODE(path.stat().st_mode) != 0o700:
        raise LocalRuntimeError(f'Runtime directory permissions must be 0700: {path}')


def _socket_directory(data_directory: Path) -> Path:
    root = _runtime_root()
    _owned_directory(root, create=True)
    identity = hashlib.sha256(os.fsencode(data_directory)).hexdigest()[:24]
    socket_directory = root / identity
    if not socket_directory.exists():
        try:
            socket_directory.mkdir(mode=0o700)
        except FileExistsError:
            # Another independent LocalPostgres may have created this exact
            # path at the same time. Ownership and mode are checked below.
            pass
    _owned_directory(socket_directory, create=False)
    return socket_directory


class LocalPostgres:
    """Own one isolated local cluster; connections and transactions belong to callers.

    Install ``truss-toolkit[local]``. Each data directory owns a PostgreSQL 18
    cluster and a private, short Unix-socket directory. The context stops the
    server and retains data; it never initializes or upgrades Truss. A context
    cannot be reentered or restarted; use a new context for restart.
    """

    def __init__(self, data_directory: str | Path):
        self._requested_directory = Path(data_directory).expanduser()
        self.directory = self._requested_directory.resolve()
        self._server_process = False
        self._lease = None
        self._info = None
        self._used = False
        self._registered = False
        self._startup_pending = False
        self._socket_directory: Path | None = None
        self._binary_directory: Path | None = None

    @property
    def info(self) -> RuntimeInfo:
        if self._info is None:
            raise LocalRuntimeError('Local PostgreSQL context is not running')
        return self._info

    @property
    def psql_path(self) -> Path:
        if self._binary_directory is None:
            return Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'
        return self._binary_directory / 'psql'

    def _run(self, command: str, *arguments: str, timeout: int = 60,
             check: bool = True) -> subprocess.CompletedProcess[str]:
        if self._binary_directory is None:
            raise LocalRuntimeError('PostgreSQL binaries are unavailable')
        executable = self._binary_directory / command
        if not executable.is_file():
            raise LocalRuntimeError(f'Pinned PostgreSQL binary is missing: {executable}')
        argv = [str(executable), *arguments]
        # pg_ctl can deadlock when stdout/stderr use pipes during daemon start;
        # file-backed streams are the supported pattern used by pgserver.
        with tempfile.TemporaryFile(mode='w+t') as stdout, tempfile.TemporaryFile(mode='w+t') as stderr:
            result = subprocess.run(argv, check=False, stdout=stdout, stderr=stderr,
                                    text=True, timeout=timeout, env=_private_environment())
            stdout.seek(0)
            stderr.seek(0)
            completed = subprocess.CompletedProcess(argv, result.returncode, stdout.read(), stderr.read())
        if check and completed.returncode:
            details = (completed.stderr or completed.stdout or '').strip()
            raise LocalRuntimeError(f'{command} failed: {details or completed.returncode}')
        return completed

    def _uri(self) -> str:
        assert self._socket_directory is not None
        host = quote(str(self._socket_directory), safe='')
        return f'postgresql://postgres@/postgres?host={host}&port={_PORT}'

    def __enter__(self):
        if self._used:
            raise LocalRuntimeError('Use a new LocalPostgres context for restart')
        self._used = True
        if self._requested_directory.is_symlink():
            raise LocalRuntimeError('Local PostgreSQL data directory must not be a symlink')
        try:
            import fasteners
            runtime_version = importlib.metadata.version(RUNTIME_DISTRIBUTION)
            if runtime_version != RUNTIME_VERSION:
                raise LocalRuntimeError(f'Expected pinned {RUNTIME_DISTRIBUTION}=={RUNTIME_VERSION}')
        except (ImportError, importlib.metadata.PackageNotFoundError) as error:
            raise LocalRuntimeError('Install truss-toolkit[local] for the local runtime') from error

        expected_major = SERVER_VERSION.split('.')[0]
        self.directory.parent.mkdir(parents=True, exist_ok=True)
        with _directory_lock:
            if self.directory in _active_directories:
                raise LocalRuntimeError('Local PostgreSQL directory is already in use')
            _active_directories.add(self.directory)
            self._registered = True
        try:
            self._lease = fasteners.InterProcessLock(str(self.directory) + '.truss-runtime.lock')
            if not self._lease.acquire(blocking=False):
                self._lease = None
                raise LocalRuntimeError('Local PostgreSQL directory is leased by another process')

            self._binary_directory = Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin'
            if not self._binary_directory.is_dir():
                raise LocalRuntimeError('Pinned PostgreSQL executable bundle is missing')
            if self.directory.exists():
                if not self.directory.is_dir():
                    raise LocalRuntimeError('Local PostgreSQL path must be a directory')
                if hasattr(os, 'getuid') and self.directory.stat().st_uid != os.getuid():
                    raise LocalRuntimeError('Local PostgreSQL data directory is owned by another user')
                version = self.directory / 'PG_VERSION'
                if any(self.directory.iterdir()) and not version.is_file():
                    raise LocalRuntimeError('Nonempty directory is not a PostgreSQL data directory')
                if version.is_file() and version.read_text().strip() != expected_major:
                    raise LocalRuntimeError(f'Local profile requires PostgreSQL{expected_major}; no automatic upgrade')
                if (self.directory / 'postmaster.pid').exists():
                    raise LocalRuntimeError('Existing postmaster custody requires explicit host recovery')
            else:
                self.directory.mkdir(mode=0o700)
            self.directory.chmod(0o700)
            self._socket_directory = _socket_directory(self.directory)

            if not (self.directory / 'PG_VERSION').is_file():
                self._startup_pending = True
                self._run('initdb', '-D', str(self.directory), '--auth=trust',
                          '--auth-local=trust', '--encoding=UTF8', '-U', 'postgres')

            self._startup_pending = True
            options = ' '.join((
                "-h ''",
                f'-k {shlex.quote(str(self._socket_directory))}',
                f'-p {_PORT}',
                f'-c data_directory={shlex.quote(str(self.directory))}',
                "-c unix_socket_permissions=0700",
            ))
            self._run('pg_ctl', '-D', str(self.directory), '-l', str(self.directory / 'log'),
                      '-o', options, '-w', '-t', '60', 'start')
            self._server_process = True
            self._startup_pending = False

            version = self._run('psql', self._uri(), '-X', '-A', '-t',
                                '-v', 'ON_ERROR_STOP=1', '-c', 'SHOW server_version').stdout.strip()
            if version != SERVER_VERSION:
                raise LocalRuntimeError(f'Unqualified bundled PostgreSQL version: {version}')
            actual_data_directory = self._run(
                'psql', self._uri(), '-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1',
                '-c', 'SHOW data_directory').stdout.strip()
            if Path(actual_data_directory).resolve() != self.directory:
                raise LocalRuntimeError('Started PostgreSQL does not use the owned data directory')
            actual_socket_directory = self._run(
                'psql', self._uri(), '-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1',
                '-c', 'SHOW unix_socket_directories').stdout.strip()
            if actual_socket_directory != str(self._socket_directory):
                raise LocalRuntimeError('Started PostgreSQL does not use the private Unix-socket directory')
            actual_listen_addresses = self._run(
                'psql', self._uri(), '-X', '-A', '-t', '-v', 'ON_ERROR_STOP=1',
                '-c', 'SHOW listen_addresses').stdout.strip()
            if actual_listen_addresses:
                raise LocalRuntimeError('Started PostgreSQL unexpectedly listens on TCP')
            self._server_process = True
            self._info = RuntimeInfo(self._uri(), self.directory, version, runtime_version,
                                     socket_directory=self._socket_directory, port=_PORT)
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        """Stop the owned server and retain data and custody when stop is uncertain."""
        self._info = None
        if self._server_process:
            if (self.directory / 'postmaster.pid').exists():
                try:
                    self._run('pg_ctl', '-D', str(self.directory), '-m', 'fast',
                              '-w', '-t', '60', 'stop')
                except Exception as error:
                    raise LocalRuntimeError('Local PostgreSQL cleanup failed; directory lease retained') from error
            if (self.directory / 'postmaster.pid').exists():
                raise LocalRuntimeError('Local PostgreSQL stop unconfirmed; directory lease retained')
            self._server_process = False
            self._startup_pending = False
        elif self._startup_pending:
            if (self.directory / 'postmaster.pid').exists():
                raise LocalRuntimeError('Local PostgreSQL startup stop unconfirmed; directory lease retained')
            self._startup_pending = False
        if self._lease is not None:
            self._lease.release()
            self._lease = None
        if self._registered:
            with _directory_lock:
                _active_directories.discard(self.directory)
            self._registered = False

    def __exit__(self, exc_type, exc, traceback):
        self.close()
