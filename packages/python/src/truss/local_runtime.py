"""Explicit, retained-data pgserver lifecycle; no Truss install or migration."""
from dataclasses import dataclass
import importlib.metadata
import importlib.resources
from pathlib import Path
import subprocess
import threading


class LocalRuntimeError(RuntimeError):
    """Local profile unavailable or directory custody refused; no automatic retry."""


@dataclass(frozen=True)
class RuntimeInfo:
    connection_uri: str
    data_directory: Path
    server_version: str
    runtime_version: str = '0.1.4'
    truss_installation: str = 'not_checked'


_active_directories: set[Path] = set()
_directory_lock = threading.Lock()


class LocalPostgres:
    """Own a local development server for one context; connections belong to callers.

    Install truss-toolkit[local]. Existing running servers are refused. The context
    stops its server and retains data; it never initializes or upgrades Truss.
    A context cannot be reentered or restarted; use a new context for restart.
    """
    def __init__(self, data_directory: str | Path):
        self.directory = Path(data_directory).expanduser().resolve()
        self._server = None
        self._lease = None
        self._info = None
        self._used = False
        self._registered = False

    @property
    def info(self) -> RuntimeInfo:
        if self._info is None:
            raise LocalRuntimeError('Local PostgreSQL context is not running')
        return self._info

    @property
    def psql_path(self) -> Path:
        return Path(str(importlib.resources.files('pgserver'))) / 'pginstall/bin/psql'

    def __enter__(self):
        if self._used:
            raise LocalRuntimeError('Use a new LocalPostgres context for restart')
        self._used = True
        try:
            import pgserver
            import fasteners
            if importlib.metadata.version('pgserver') != '0.1.4':
                raise LocalRuntimeError('Expected pgserver0.1.4; install truss-toolkit[local]')
        except (ImportError, importlib.metadata.PackageNotFoundError) as error:
            raise LocalRuntimeError('Install truss-toolkit[local] for the local runtime') from error
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
            if self.directory.exists():
                if not self.directory.is_dir():
                    raise LocalRuntimeError('Local PostgreSQL path must be a directory')
                version = self.directory / 'PG_VERSION'
                if any(self.directory.iterdir()) and not version.is_file():
                    raise LocalRuntimeError('Nonempty directory is not a PostgreSQL data directory')
                if version.is_file() and version.read_text().strip() != '16':
                    raise LocalRuntimeError('Local profile requires PostgreSQL16; no automatic upgrade')
                if (self.directory / 'postmaster.pid').exists():
                    raise LocalRuntimeError('Existing postmaster custody requires explicit host recovery')
            self._server = pgserver.get_server(self.directory, cleanup_mode='stop')
            version = subprocess.check_output(
                [str(self.psql_path), self._server.get_uri(), '-X', '-A', '-t',
                 '-v', 'ON_ERROR_STOP=1', '-c', 'SHOW server_version'],
                text=True, timeout=30).strip()
            if version != '16.2':
                raise LocalRuntimeError(f'Unqualified bundled PostgreSQL version: {version}')
            self._info = RuntimeInfo(self._server.get_uri(), self.directory, version)
            return self
        except BaseException:
            self.close()
            raise

    def close(self):
        """Stop owned server; retain lease if cleanup fails or stop is unconfirmed.

        A later close is an explicit host recovery action, never an automatic retry.
        Connection information becomes unavailable as soon as close starts.
        """
        self._info = None
        if self._server is not None:
            try:
                self._server.cleanup()
            except Exception as error:
                raise LocalRuntimeError('Local PostgreSQL cleanup failed; directory lease retained') from error
            if (self.directory / 'postmaster.pid').exists():
                raise LocalRuntimeError('Local PostgreSQL stop unconfirmed; directory lease retained')
            self._server = None
        if self._lease is not None:
            self._lease.release()
            self._lease = None
        if self._registered:
            with _directory_lock:
                _active_directories.discard(self.directory)
            self._registered = False

    def __exit__(self, exc_type, exc, traceback):
        self.close()
