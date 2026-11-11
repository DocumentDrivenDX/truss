# SPDX-License-Identifier: MIT OR Apache-2.0
"""Qualification-only exact-case results and stop-before-delete custody.

No application runtime, admission, codec or dependency-selection behavior lives
here. Existing test methods and native initializer bytes execute unchanged.
"""
from contextlib import ExitStack, contextmanager
from pathlib import Path
from hashlib import sha256
import json
import os
import shutil
import stat
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch


def flatten(suite):
    for item in suite:
        if isinstance(item,unittest.TestSuite):yield from flatten(item)
        else:yield item


def collect_exact(selectors):
    if type(selectors) is not list or not selectors or len(set(selectors))!=len(selectors):
        raise ValueError('Nonempty unique exact case IDs required')
    loader=unittest.TestLoader();cases=[]
    for selector in selectors:
        suite=loader.loadTestsFromName(selector);loaded=list(flatten(suite))
        if loader.errors or len(loaded)!=1 or loaded[0].id()!=selector:
            raise ValueError('Exactly the named real case must collect: '+selector+' '+repr(loader.errors))
        cases.extend(loaded)
    return unittest.TestSuite(cases)


def strict_result(result,expected,observed,*,inventory_verified,cleanup_confirmed):
    counts={'testsRun':0 if result is None else result.testsRun,
        'skips':0 if result is None else len(result.skipped),
        'expectedFailures':0 if result is None else len(result.expectedFailures),
        'unexpectedSuccesses':0 if result is None else len(result.unexpectedSuccesses),
        'failures':0 if result is None else len(result.failures),'errors':0 if result is None else len(result.errors),
        'wasSuccessful':False if result is None else result.wasSuccessful(),
        'inventoryVerified':inventory_verified,'cleanupConfirmed':cleanup_confirmed}
    counts['passed']=bool(expected and len(set(expected))==len(expected) and observed==expected
        and counts['testsRun']==len(expected) and counts['wasSuccessful']
        and not any(counts[k] for k in ('skips','expectedFailures','unexpectedSuccesses','failures','errors'))
        and inventory_verified is True and cleanup_confirmed is True)
    return counts


class RecordedResult(unittest.TextTestResult):
    """Retain exact cases/subcases and original exception class/SQLSTATE."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.started_ids=[];self.observations=[]
    def startTest(self,test):
        self.started_ids.append(test.id());super().startTest(test)
    def event(self,test,status,error=None):
        value={'id':test.id(),'status':status}
        if error is not None:
            value.update(errorClass=error[0].__module__+'.'+error[0].__qualname__,sqlState=getattr(error[1],'sqlstate',None))
        self.observations.append(value)
    def addSuccess(self,test):self.event(test,'passed');super().addSuccess(test)
    def addFailure(self,test,error):self.event(test,'failed',error);super().addFailure(test,error)
    def addError(self,test,error):self.event(test,'error',error);super().addError(test,error)
    def addSkip(self,test,reason):self.event(test,'skipped');super().addSkip(test,reason)
    def addExpectedFailure(self,test,error):self.event(test,'expectedFailure',error);super().addExpectedFailure(test,error)
    def addUnexpectedSuccess(self,test):self.event(test,'unexpectedSuccess');super().addUnexpectedSuccess(test)
    def addSubTest(self,test,subtest,error):
        self.event(subtest,'subcase-passed' if error is None else 'subcase-failed',error)
        super().addSubTest(test,subtest,error)


@contextmanager
def _open_directory(path):
    # Anchor every component. Do not follow an intermediate or final symlink.
    if path.anchor != '/' or '..' in path.parts:
        raise ValueError(f'Expected canonical absolute directory: {path}')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _cleanup_path(path):
    if path.anchor != '/' or '..' in path.parts:
        raise ValueError(f'Ambiguous PostgreSQL cleanup path: {path}')
    if sys.platform != 'darwin':
        return path
    # macOS supplies these two root-owned aliases to native fixtures.
    for prefix, link, real in (
            (Path('/tmp'), Path('/tmp'), Path('/private/tmp')),
            (Path('/var/folders'), Path('/var'), Path('/private/var/folders'))):
        if path.is_relative_to(prefix):
            before = link.lstat()
            expected = str(Path('/private') / link.name)
            if (not stat.S_ISLNK(before.st_mode) or before.st_uid != 0
                    or os.readlink(link) not in (expected, expected.lstrip('/'))):
                raise ValueError(f'Unexpected platform temporary alias: {link}')
            actual = prefix.stat()
            after = link.lstat()
            if ((before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                    or [actual.st_dev, actual.st_ino] != _directory_identity(real)):
                raise ValueError(f'Platform temporary alias identity differs: {link}')
            return real / path.relative_to(prefix)
    return path


def _directory_identity(path):
    with _open_directory(path) as fd:
        details = os.fstat(fd)
        return [details.st_dev, details.st_ino]


def _regular_file(path, limit):
    # O_NONBLOCK also avoids blocking on a substituted FIFO.
    with _open_directory(path.parent) as parent:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(path.name, flags, dir_fd=parent), 'rb') as stream:
            details = os.fstat(stream.fileno())
            if not stat.S_ISREG(details.st_mode) or details.st_size > limit:
                raise ValueError(f'Expected bounded regular PostgreSQL file: {path}')
            data = stream.read(limit + 1)
            after = os.fstat(stream.fileno())
            current = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            def identity(st):
                return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]
            if len(data) != details.st_size or identity(details) != identity(after) or identity(after) != identity(current):
                raise ValueError(f'PostgreSQL file changed during read: {path}')
            return data, [*identity(details), sha256(data).hexdigest()]


def _canonical_oid(name):
    return (0 < len(name) <= 10 and name.isascii() and name.isdecimal()
            and name[0] != '0' and int(name) <= 4294967295)


def _crc32c(data):
    crc = 0xffffffff
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0x82f63b78 if crc & 1 else 0)
    return crc ^ 0xffffffff


def _database_layout(directory, major):
    if not _canonical_oid(directory.name):
        raise ValueError(f'Noncanonical database OID: {directory}')
    identity = _directory_identity(directory)
    marker, marker_identity = _regular_file(directory / 'PG_VERSION', 16)
    if marker != major:
        raise ValueError(f'Database and cluster major versions differ: {directory}')
    mapping, mapping_identity = _regular_file(directory / 'pg_filenode.map', 524)
    # PostgreSQL 18 RelMapFile: magic, entry count, 64 pairs, and CRC.
    # Require a real mapped relation file as well as the relation map shape.
    if len(mapping) != 524:
        raise ValueError(f'Invalid PostgreSQL relation map size: {directory}')
    magic, count, relation, filenode = struct.unpack_from('=4I', mapping)
    if (magic != 0x592717 or not 1 <= count <= 64 or not relation or not filenode
            or _crc32c(mapping[:-4]) != struct.unpack_from('=I', mapping, 520)[0]):
        raise ValueError(f'Invalid PostgreSQL relation map header: {directory}')
    with _open_directory(directory) as fd:
        catalog = os.stat(str(filenode), dir_fd=fd, follow_symlinks=False)
    if not stat.S_ISREG(catalog.st_mode) or not catalog.st_size:
        raise ValueError(f'Missing mapped PostgreSQL relation: {directory}')
    if _directory_identity(directory) != identity:
        raise ValueError(f'Database directory changed during read: {directory}')
    return {'directory': identity, 'marker': marker_identity, 'relationMap': mapping_identity,
            'mappedRelation': [catalog.st_dev, catalog.st_ino]}


_DATABASE_MEMBERSHIP_SQL = """
SELECT pg_catalog.json_build_object(
    'data', pg_catalog.current_setting('data_directory'),
    'socket', pg_catalog.current_setting('unix_socket_directories'),
    'port', pg_catalog.current_setting('port'),
    'listen', pg_catalog.current_setting('listen_addresses'),
    'unix', pg_catalog.inet_server_addr() IS NULL,
    'version', pg_catalog.current_setting('server_version_num'),
    'oids', COALESCE((
        SELECT pg_catalog.json_agg(m.oid ORDER BY m.oid)
        FROM (
            SELECT d.oid::pg_catalog.text AS oid
            FROM pg_catalog.pg_database AS d
            JOIN pg_catalog.pg_tablespace AS t ON t.oid = d.dattablespace
            WHERE t.spcname = 'pg_default'
            ORDER BY d.oid LIMIT 1025
        ) AS m
    ), '[]'::pg_catalog.json)
)
"""


def _socket_identity(socket, port):
    with _open_directory(socket) as fd:
        endpoint = os.stat(f'.s.PGSQL.{port}', dir_fd=fd, follow_symlinks=False)
        if not stat.S_ISSOCK(endpoint.st_mode) or endpoint.st_uid != os.getuid():
            raise ValueError(f'Expected owned Unix socket: {socket}')
        return [endpoint.st_dev, endpoint.st_ino]


def _database_membership(data, binary, socket, pid_lines):
    if not isinstance(socket, Path) or len(pid_lines) < 5:
        raise ValueError(f'Owned Unix socket authority unavailable: {data}')
    socket = _cleanup_path(socket)
    port = pid_lines[3].decode('ascii')
    recorded_socket = Path(os.fsdecode(pid_lines[4]))
    if (not _canonical_oid(port) or int(port) > 65535 or not recorded_socket.is_absolute()
            or _cleanup_path(recorded_socket) != socket):
        raise ValueError(f'Postmaster socket or port differs from lifecycle custody: {data}')
    lock = socket / f'.s.PGSQL.{port}.lock'
    endpoint = _socket_identity(socket, port)
    lock_text, lock_identity = _regular_file(lock, 4096)
    if lock_text.splitlines()[:5] != pid_lines[:5]:
        raise ValueError(f'Unix socket lock does not bind the original postmaster: {socket}')
    environment = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
    environment.update(PGCONNECT_TIMEOUT='5',
                       PGOPTIONS='-c default_transaction_read_only=on -c statement_timeout=5000')
    result = subprocess.run(
        [str(binary / 'psql'), '-X', '-A', '-t', '-w', '-v', 'ON_ERROR_STOP=1',
         '-h', str(socket), '-p', port, '-U', 'postgres', '-d', 'postgres',
         '-c', _DATABASE_MEMBERSHIP_SQL],
        capture_output=True, text=True, timeout=10, env=environment)
    if result.returncode or result.stderr or len(result.stdout) > 16384:
        raise ValueError(f'Owned database membership query refused: {data}')
    result = json.loads(result.stdout)
    if isinstance(result, dict):
        for field in ('data', 'socket'):
            if isinstance(result.get(field), str) and Path(result[field]).is_absolute():
                result[field] = str(_cleanup_path(Path(result[field])))
    expected = {'data': str(data), 'socket': str(socket), 'port': port,
                'listen': '', 'unix': True, 'version': '180006'}
    if not isinstance(result, dict) or any(result.get(k) != v for k, v in expected.items()):
        raise ValueError(f'Owned database membership endpoint mismatch: {data}')
    oids = result.get('oids')
    if (not isinstance(oids, list) or not 0 < len(oids) <= 1024
            or any(not isinstance(oid, str) or not _canonical_oid(oid) for oid in oids)
            or len(set(oids)) != len(oids)):
        raise ValueError(f'Invalid owned database OID inventory: {data}')
    if _regular_file(lock, 4096)[1] != lock_identity:
        raise ValueError(f'Unix socket lock changed during membership query: {socket}')
    if _socket_identity(socket, port) != endpoint:
        raise ValueError(f'Unix socket changed during membership query: {socket}')
    return {'endpoint': expected, 'oids': oids, 'socketLock': lock_identity,
            'socketIdentity': endpoint}


def _owned_layout(data, pid_file, pid, binary, socket):
    base = data / 'base'
    try:
        base_identity = _directory_identity(base)
    except FileNotFoundError:
        return None
    # This exception covers the exact PostgreSQL 18 default tablespace only.
    major, marker = _regular_file(data / 'PG_VERSION', 16)
    pid_text, pid_identity = _regular_file(pid_file, 4096)
    lines = pid_text.splitlines()
    if (major != b'18\n' or len(lines) < 2 or lines[0] != str(pid).encode('ascii')
            or not Path(os.fsdecode(lines[1])).is_absolute()
            or _cleanup_path(Path(os.fsdecode(lines[1]))) != data):
        raise ValueError(f'Unverified PostgreSQL 18 data directory and PID binding: {data}')
    # Capture the layout only during the original live postmaster custody.
    os.kill(pid, 0)
    membership = _database_membership(data, binary, socket, lines)
    global_identity = _directory_identity(data / 'global')
    control, control_identity = _regular_file(data / 'global/pg_control', 8192)
    if len(control) != 8192:
        raise ValueError(f'Invalid PostgreSQL control file: {data}')
    databases = {}
    with _open_directory(base) as fd:
        for name in os.listdir(fd):
            child = base / name
            details = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if stat.S_ISLNK(details.st_mode):
                raise ValueError(f'Symbolic link in PostgreSQL base directory: {child}')
            if not stat.S_ISDIR(details.st_mode):
                continue
            with _open_directory(child) as child_fd:
                try:
                    os.stat('PG_VERSION', dir_fd=child_fd, follow_symlinks=False)
                except FileNotFoundError:
                    continue
            if name not in membership['oids']:
                raise ValueError(f'Unregistered PostgreSQL database directory: {child}')
            databases[name] = _database_layout(child, major)
    os.kill(pid, 0)
    if (_directory_identity(base) != base_identity
            or _regular_file(pid_file, 4096) != (pid_text, pid_identity)):
        raise ValueError(f'PostgreSQL layout changed during PID capture: {data}')
    if set(databases) != set(membership['oids']):
        raise ValueError(f'PostgreSQL database membership and layout differ: {data}')
    return {'base': base_identity, 'marker': marker, 'global': global_identity,
            'controlFile': control_identity[:3], 'databases': databases,
            'membership': membership, 'pidFile': pid_identity}


def _walk_error(error):
    raise error


class OwnedNativeCleanup:
    """Observe existing isolated fixture lifecycle; never change its initializer.

    Class setup/local startup records the ORIGINAL PID before test cleanup. A
    scoped rmtree gate requires pg_ctl==3 and that PID absent BEFORE deletion.
    Unknown PG data is retained. This wrapper adds no permission or data grants.
    """
    def __init__(self,classes,output,*,only_runtime=None):
        self.classes=classes;self.output=Path(output);self.records={};self.uncertain=[];self.cleanup_errors=[];self.stack=ExitStack()
        self.only_runtime = only_runtime
        self._runtime_data = _cleanup_path(only_runtime.directory) if only_runtime is not None else None
        self._remove_tree = None
    def save(self):
        self.output.write_text(json.dumps({'scope':'Owned isolated test cluster cleanup only; not native profile admission',
            'clusters':list(self.records.values()),'uncertainPaths':self.uncertain,'cleanupErrors':self.cleanup_errors},indent=2)+'\n')
    def capture(self,data,binary,*,socket=None):
        if not isinstance(data,Path) or not isinstance(binary,Path):return
        data = _cleanup_path(data)
        if self._runtime_data is not None and data != self._runtime_data:
            raise ValueError('Another data directory is outside scoped cleanup')
        pid_file = data / 'postmaster.pid'
        if str(data) in self.records:return
        # Class attributes can name paths before startup, so only a directory
        # that PostgreSQL has initialized is an owned cluster. Once PG_VERSION
        # exists, however, a missing/malformed PID is uncertainty, never a
        # successful no-op: preserve the data and its diagnostics.
        try:
            directory_identity = _directory_identity(data)
            _, marker_identity = _regular_file(data / 'PG_VERSION', 16)
        except FileNotFoundError:
            return
        except (OSError, ValueError) as error:
            self.uncertain.append({'dataDirectory': str(data), 'reason': str(error)})
            self.save()
            raise RuntimeError('Owned PostgreSQL root is uncertain; retain data') from error
        try:
            pid_text, pid_identity = _regular_file(pid_file, 4096)
            first = pid_text.decode('ascii').splitlines()[0].strip()
            if not first.isascii() or not first.isdecimal():raise ValueError('PID is not an ASCII integer')
            pid=int(first)
        except (OSError,IndexError,ValueError) as error:
            self.uncertain.append({'dataDirectory':str(data),'reason':'owned postmaster.pid unreadable or malformed: '+str(error)})
            self.save()
            raise RuntimeError('Original owned postmaster PID invalid; retain data') from error
        if pid<=0:
            self.uncertain.append({'dataDirectory':str(data),'reason':'owned postmaster PID must be positive'})
            self.save()
            raise RuntimeError('Positive original owned postmaster PID required; retain data')
        self.records[str(data)]={'dataDirectory':str(data),'pgCtl':str(binary/'pg_ctl'),
            'originalPostmasterPid':pid,'originalPidFileIdentity':pid_identity,
            'confirmed':False,'dataDeleted':False}
        record = self.records[str(data)]
        try:
            record['directoryIdentity'] = directory_identity
            record['rootMarkerIdentity'] = marker_identity
            self._check_owned_root(record)
            layout = _owned_layout(data, pid_file, pid, binary, socket)
            if layout is not None:
                record['databaseLayout'] = layout
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            self._retain_layout(record, error)
        self.save()

    def _retain_layout(self, record, error):
        record['layoutUncertain'] = str(error)
        self.uncertain.append({'dataDirectory': record['dataDirectory'], 'reason': str(error)})
        self.save()

    def _refresh_runtime_layout(self, runtime, record):
        old = record.get('databaseLayout')
        if old is None or record.get('layoutUncertain'):
            return
        data = Path(record['dataDirectory'])
        try:
            pid_file = data / 'postmaster.pid'
            if _regular_file(pid_file, 4096)[1] != old['pidFile']:
                raise ValueError(f'Original postmaster lock changed before close: {data}')
            info = runtime.info
            new = _owned_layout(data, pid_file, record['originalPostmasterPid'],
                                runtime.psql_path.parent, info.socket_directory)
            if (new is None or any(old[k] != new[k] for k in
                                   ('base', 'marker', 'global', 'controlFile', 'pidFile'))
                    or any(new['databases'].get(oid) != identity
                           for oid, identity in old['databases'].items())):
                raise ValueError(f'Original PostgreSQL layout changed before close: {data}')
            record['databaseLayout'] = new
            self.save()
        except (OSError, ValueError, subprocess.TimeoutExpired) as error:
            # Membership uncertainty cannot authorize deletion. Still let the
            # original lifecycle stop the proven owner.
            self._retain_layout(record, error)

    def _capture_runtime(self, runtime):
        info = getattr(runtime, '_info', None)
        self.capture(runtime.directory, runtime.psql_path.parent,
                     socket=getattr(info, 'socket_directory', None))

    def capture_class(self,cls):
        runtime=getattr(cls,'runtime',None)
        if runtime is not None:
            self._capture_runtime(runtime)
        self.capture(getattr(cls,'data',None),getattr(cls,'pgbin',None),
                     socket=getattr(cls,'socket',None))
    def _check_owned_root(self, record):
        data = Path(record['dataDirectory'])
        if 'directoryIdentity' in record and _directory_identity(data) != record['directoryIdentity']:
            raise ValueError(f'Owned PostgreSQL directory identity changed: {data}')
        if 'rootMarkerIdentity' in record and _regular_file(data / 'PG_VERSION', 16)[1] != record['rootMarkerIdentity']:
            raise ValueError(f'Owned PostgreSQL root marker changed: {data}')

    def _original_pid_file_present(self, record):
        pid_file = Path(record['dataDirectory']) / 'postmaster.pid'
        try:
            raw, identity = _regular_file(pid_file, 4096)
        except FileNotFoundError:
            return False
        lines = raw.splitlines()
        expected = record.get('originalPidFileIdentity')
        if expected is not None and identity != expected:
            raise ValueError(f'Original postmaster lock changed: {pid_file}')
        if not lines or lines[0] != str(record['originalPostmasterPid']).encode('ascii'):
            raise ValueError(f'Original postmaster PID changed: {pid_file}')
        return True

    def confirm(self, record, *, refresh=False):
        if record['confirmed'] and not refresh:
            return
        self._check_owned_root(record)
        data=Path(record['dataDirectory'])
        if not data.exists():raise RuntimeError('Owned data deleted before native stop proof')
        status=subprocess.run([record['pgCtl'],'-D',str(data),'status'],capture_output=True,text=True,timeout=15)
        absent=False
        try:os.kill(record['originalPostmasterPid'],0)
        except ProcessLookupError:absent=True
        except PermissionError:pass
        record.update(pgCtlStatus=status.returncode,originalPostmasterPidAbsent=absent,
            pgCtlStdout=status.stdout,pgCtlStderr=status.stderr,
            confirmed=status.returncode == 3 and absent)
        self.save()
        if not record['confirmed']:raise RuntimeError('Owned native stop uncertain; retain data')
    def _deletion_roots(self, root):
        relevant = {}
        for record in self.records.values():
            data = Path(record['dataDirectory'])
            if record['dataDeleted']:
                continue
            if root != data and root.is_relative_to(data):
                raise ValueError(f'Partial PostgreSQL data deletion refused: {root}')
            if data.is_relative_to(root):
                if any(data.is_relative_to(other) or other.is_relative_to(data) for other in relevant):
                    raise ValueError(f'Ambiguous nested owned PostgreSQL directories: {data}')
                relevant[data] = record
        return relevant

    def _check_physical_overlap(self, root, root_identity):
        active = [record for record in self.records.values() if not record['dataDeleted']]
        if not active:
            return
        requested = [(root, root_identity)]
        requested.extend((parent, _directory_identity(parent)) for parent in root.parents)
        for record in active:
            data = Path(record['dataDirectory'])
            owned_identity = record.get('directoryIdentity')
            if owned_identity is None:
                owned_identity = _directory_identity(data)
            for ancestor, identity in requested:
                if identity == owned_identity and ancestor != data:
                    raise ValueError(f'Physical alias of owned PostgreSQL directory: {ancestor}')
            for ancestor in (data, *data.parents):
                if ancestor == root:
                    continue
                try:
                    identity = _directory_identity(ancestor)
                except FileNotFoundError:
                    # The captured leaf identity is still checked above.
                    continue
                if identity == root_identity:
                    raise ValueError(f'Physical alias enclosing owned PostgreSQL directory: {root}')

    def _check_deletion_tree(self, root, relevant):
        allowed_markers = set()
        for data, record in relevant.items():
            if record.get('layoutUncertain'):
                raise ValueError(record['layoutUncertain'])
            self._check_owned_root(record)
            allowed_markers.add(data / 'PG_VERSION')
            layout = record.get('databaseLayout')
            if layout is None:
                continue
            # Shutdown updates pg_control in place. Bind its file identity
            # and extent, while the version markers and relation maps are immutable.
            if (_directory_identity(data / 'base') != layout['base']
                    or _regular_file(data / 'PG_VERSION', 16)[1] != layout['marker']
                    or _directory_identity(data / 'global') != layout['global']
                    or _regular_file(data / 'global/pg_control', 8192)[1][:3] != layout['controlFile']):
                raise ValueError(f'Owned PostgreSQL base, marker or control identity changed: {data}')
            for name, identity in layout['databases'].items():
                directory = data / 'base' / name
                if _database_layout(directory, b'18\n') != identity:
                    raise ValueError(f'PostgreSQL database layout changed: {directory}')
                allowed_markers.add(directory / 'PG_VERSION')

        with _open_directory(root) as fd:
            for parent, dirs, files, directory_fd in os.fwalk(
                    '.', dir_fd=fd, follow_symlinks=False, onerror=_walk_error):
                directory = root / parent
                for name in dirs + files:
                    entry = directory / name
                    details = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
                    if stat.S_ISLNK(details.st_mode):
                        if relevant or name in ('PG_VERSION', 'postmaster.pid', 'postmaster.opts',
                                                'pg_control', 'global'):
                            raise ValueError(f'Symbolic link in PostgreSQL deletion evidence: {entry}')
                        # rmtree unlinks ordinary links without traversing them.
                        continue
                    if name == 'PG_VERSION':
                        if entry not in allowed_markers or not stat.S_ISREG(details.st_mode):
                            raise ValueError(f'Unobserved PG marker: {entry}')
                    elif (name in ('postmaster.pid', 'postmaster.opts', 'postgresql.conf',
                                  'postgresql.auto.conf', 'pg_hba.conf', 'pg_ident.conf')
                          and directory not in relevant):
                        raise ValueError(f'Unobserved PG cluster evidence: {entry}')
                    elif name == 'pg_control' and directory.name == 'global' and directory.parent not in relevant:
                        raise ValueError(f'Unobserved PG control evidence: {entry}')

    def finish_runtime(self, runtime, root, *, remove=True):
        """Close the one monitored runtime and use the active shared deletion gate."""
        try:
            if self._remove_tree is None or runtime is not self.only_runtime:
                raise ValueError('One active scoped cleanup runtime required')
            data = _cleanup_path(runtime.directory)
            root = _cleanup_path(root)
            if data != root / 'data' or set(self.records) != {str(data)}:
                raise ValueError('Exactly one captured original owned cluster required')
            # This is the wrapped close. It verifies ownership before the
            # original stop and refreshes the live database membership.
            runtime.close()
            record = self.records[str(data)]
            if 'databaseLayout' not in record and not record.get('layoutUncertain'):
                self._retain_layout(record, ValueError('Authoritative runtime database layout unavailable'))
            if remove and not self.uncertain and not self.cleanup_errors:
                self._remove_tree(root)
        except BaseException as error:
            self.cleanup_errors.append(type(error).__name__ + ': ' + str(error))
        self.save()

    def __enter__(self):
        from truss import LocalPostgres
        original_enter=LocalPostgres.__enter__;original_close=LocalPostgres.close;original_rmtree=shutil.rmtree
        def entered(runtime):
            if self.only_runtime is not None and runtime is not self.only_runtime:
                raise RuntimeError('Another LocalPostgres owner is outside scoped cleanup')
            try:return original_enter(runtime)
            finally:self._capture_runtime(runtime)
        def closed(runtime):
            if self.only_runtime is not None and runtime is not self.only_runtime:
                raise RuntimeError('Another LocalPostgres owner is outside scoped cleanup')
            self._capture_runtime(runtime)
            record = self.records.get(str(_cleanup_path(runtime.directory)))
            if record is not None:
                self._check_owned_root(record)
                if self._original_pid_file_present(record):
                    self._refresh_runtime_layout(runtime, record)
            result=original_close(runtime)
            if record is not None:self.confirm(record)
            return result
        def removed(path,*args,**kwargs):
            root = Path(path)
            ordinary_rmtree = False
            try:
                if kwargs.get('dir_fd') is not None:
                    raise ValueError(f'Ambiguous descriptor-relative deletion path: {root}')
                root = _cleanup_path(root)
                relevant = self._deletion_roots(root)
                try:
                    with _open_directory(root.parent) as parent:
                        details = os.stat(root.name, dir_fd=parent, follow_symlinks=False)
                        if not relevant and stat.S_ISLNK(details.st_mode):
                            # The standard symlink-resistant rmtree rejects a
                            # final link itself, without inspecting its target.
                            ordinary_rmtree = True
                            return original_rmtree(root.name, *args, dir_fd=parent,
                                                   **{k: v for k, v in kwargs.items() if k != 'dir_fd'})
                    deletion_identity = _directory_identity(root)
                except FileNotFoundError:
                    if relevant:
                        raise
                    # Preserve ordinary missing-path callbacks and ignore_errors.
                    ordinary_rmtree = True
                    return original_rmtree(path, *args, **kwargs)
                self._check_physical_overlap(root, deletion_identity)
                self._check_deletion_tree(root, relevant)
            except (OSError, ValueError) as error:
                if ordinary_rmtree:
                    raise
                self.uncertain.append({'deletionRoot': str(root), 'reason': str(error)})
                self.save()
                raise RuntimeError(f'Unobserved PG or uncertain deletion tree retained: {error}') from error
            for record in relevant.values():
                self.confirm(record, refresh=record['confirmed'])
            try:
                self._check_physical_overlap(root, deletion_identity)
                self._check_deletion_tree(root, relevant)
                for record in relevant.values():
                    if self._original_pid_file_present(record):
                        raise ValueError(f"Postmaster PID file present after stop proof: {record['dataDirectory']}")
                if _directory_identity(root) != deletion_identity:
                    raise ValueError(f'Requested deletion directory changed: {root}')
            except (OSError, ValueError) as error:
                self.uncertain.append({'deletionRoot': str(root), 'reason': str(error)})
                self.save()
                raise RuntimeError(f'PostgreSQL deletion readback failed; retain data: {error}') from error
            if not original_rmtree.avoids_symlink_attacks:
                raise RuntimeError('Symlink-resistant rmtree required; retain data')
            # Anchor the delete under a nonsymlink parent, just as the tree
            # scan is anchored. The caller cannot supply a different dir_fd.
            options = dict(kwargs)
            options.pop('dir_fd', None)
            with _open_directory(root.parent) as parent:
                details = os.stat(root.name, dir_fd=parent, follow_symlinks=False)
                if not stat.S_ISDIR(details.st_mode) or [details.st_dev, details.st_ino] != deletion_identity:
                    self.uncertain.append({'deletionRoot': str(root), 'reason': 'directory changed before removal'})
                    self.save()
                    raise RuntimeError(f'Requested deletion directory changed; retain data: {root}')
                result = original_rmtree(root.name, *args, dir_fd=parent, **options)
            for record in relevant.values():
                record['dataDeleted'] = not Path(record['dataDirectory']).exists()
            self.save();return result
        self.stack.enter_context(patch.object(LocalPostgres,'__enter__',entered))
        self.stack.enter_context(patch.object(LocalPostgres,'close',closed))
        self.stack.enter_context(patch.object(shutil,'rmtree',removed))
        self._remove_tree = removed
        for cls in self.classes:
            original=cls.setUpClass
            def setup(selected,original=original):
                try:return original()
                finally:self.capture_class(selected)
            self.stack.enter_context(patch.object(cls,'setUpClass',classmethod(setup)))
        return self
    def _check_scoped_retry(self, record):
        layout = record.get('databaseLayout')
        if layout is None:
            raise ValueError('Captured original socket custody required for scoped stop retry')
        membership = layout['membership']
        endpoint = membership['endpoint']
        socket, port = Path(endpoint['socket']), endpoint['port']
        lock = socket / f'.s.PGSQL.{port}.lock'
        if (_socket_identity(socket, port) != membership['socketIdentity']
                or _regular_file(lock, 4096)[1] != membership['socketLock']):
            raise ValueError('Original socket custody changed before scoped stop retry')
        os.kill(record['originalPostmasterPid'], 0)
        if not self._original_pid_file_present(record):
            raise ValueError('Original postmaster lock vanished before scoped stop retry')

    def __exit__(self,*args):
        try:
            # Drain every original callback even when a previous one failed;
            # never let an exception skip stopping a known owned postmaster.
            for cls in self.classes:
                try:
                    cls.doClassCleanups()
                    self.cleanup_errors.extend(str(error[1]) for error in cls.tearDown_exceptions)
                except BaseException as error:self.cleanup_errors.append(type(error).__name__+': '+str(error))
            for record in self.records.values():
                if not record['confirmed']:
                    try:
                        self._check_owned_root(record)
                        if self._original_pid_file_present(record):
                            if self.only_runtime is not None:
                                self._check_scoped_retry(record)
                            status=subprocess.run([record['pgCtl'],'-D',record['dataDirectory'],'-m','fast','-w','-t','30','stop'],
                                capture_output=True,text=True,timeout=35)
                            record['finalStopReturncode']=status.returncode
                        self.confirm(record)
                    except BaseException as error:self.cleanup_errors.append(type(error).__name__+': '+str(error))
            self.save()
            if self.cleanup_errors:raise RuntimeError('Owned native cleanup uncertain: '+repr(self.cleanup_errors))
        finally:
            self._remove_tree = None
            self.stack.close()
    @property
    def confirmed(self):
        return bool(self.records) and not self.uncertain and not self.cleanup_errors and all(r['confirmed'] and r['dataDeleted'] for r in self.records.values())


# Deliberate parallel planner documents are not executable qualification inputs.
_PLANNER_PATHS={
 'docs/helix/02-design/contracts/CONTRACT-010-exact-value-transport.md',
 'docs/helix/02-design/contracts/CONTRACT-012-weft-storage-handoff.md',
 'docs/helix/03-test/test-plan.md','docs/helix/04-build/temporal-current-baseline-plan.md',
 *('docs/helix/04-build/'+name for name in ('embedder-temporal-delivery-plan.md',
 'temporal-coherent-source-integration-plan.md','temporal-dependency-cohort-plan.md',
 'temporal-interface-freeze.md','temporal-native-qualification-plan.md','temporal-public-values-addendum.md'))}
_JH_INPUTS=(
 'packages/python/src/truss/_initialization_custody.py',
 'packages/python/src/truss/_catalog_runtime/initialization-custody.sql',
 'packages/python/src/truss/_catalog_runtime/initialization-custody.schema.json',
 'packages/python/src/truss/_catalog_runtime/groups.sql',
 'packages/python/src/truss/_catalog_runtime/manifest.json',
 'packages/python/src/truss/catalog_runtime.py',
 'packages/python/src/truss/_installation_privileges.py',
 'packages/python/src/truss/_migration_verify.py','packages/python/src/truss/_migration_recipe.py',
 'packages/python/src/truss/migrations.py',
 'scripts/capture-temporal-native-inventory.py','scripts/assemble-temporal-native-baseline.py',
 'scripts/qualify-temporal-native.py','scripts/temporal-native-case-ledger.json',
 'scripts/temporal_qualification_support.py','scripts/check-module-boundaries.py',
 'packages/python/tests/test_initialization_custody.py',
 'packages/python/tests/test_initialization_custody_native.py',
 'packages/python/tests/test_initialization_custody_derivation_native.py',
 'packages/python/tests/test_temporal_public055_refusal_native.py',
 'packages/python/tests/public055_seed_fixture.py',
 'packages/python/tests/fixtures/temporal/public055-provenance.json',
 'packages/python/tests/fixtures/temporal/public055-isolated-runtime-constraints.txt',
 'scripts/retain-temporal-carrier-input.py','.github/workflows/temporal-input-retention.yml',
 '.github/workflows/python-runtime.yml',
 'docs/helix/02-design/contracts/journal-horizon-initialization-custody.md',
 'docs/helix/02-design/contracts/journal-horizon-initialization-custody-0.1.schema.json',
 'docs/helix/04-build/journal-horizon-custody-plan.md',
 'docs/helix/02-design/contracts/CONTRACT-008-layout-bootstrap.md',
 'docs/helix/02-design/contracts/CONTRACT-002-journal.md',
 'docs/helix/03-test/test-plans/STP-045-bootstrap-the-internal-layout-from-umf.md',
 'docs/helix/04-build/temporal-native-qualification-plan.md',
 'docs/helix/04-build/temporal-current-baseline-plan.md')


def journal_custody_inputs(root,commit):
    root=Path(root);result={}
    for name in _JH_INPUTS:
        original=_git(root,'show',commit+':'+name);actual=(root/name).read_bytes()
        if actual!=original:raise ValueError('Custody code/schema/governance differs from actual committed source: '+name)
        result[name]=sha256(original).hexdigest()
    return result


_INPUT_ROOTS=('packages/python/src/truss','packages/python/tests','scripts','.github/workflows','docs/helix/03-test','tests')
_MIGRATIONS='packages/python/src/truss/_migrations/'
_SEAL='scripts/truss-release-cohort.json'


def _git(root,*args):
    return subprocess.check_output(['git',*args],cwd=root)


def commit_tree(root,commit):
    import re
    if type(commit) is not str or re.fullmatch('[0-9a-f]{40}',commit) is None:
        raise ValueError('Exact admitted commit required')
    if _git(root,'rev-parse',commit+'^{commit}').decode().strip()!=commit:
        raise ValueError('Exact original commit required')
    return _git(root,'rev-parse',commit+'^{tree}').decode().strip()


def assert_qualification_checkout(root,commit,tree,*,evidence_roots=()):
    """Bind HEAD/TREE and reject staged, unstaged, untracked/ignored inputs.

    Evidence roots are explicit, separate directories below design-audit or
    outside this checkout. They never authorize changes to tracked input bytes.
    """
    root=Path(root).resolve()
    jh=(root/'packages/python/src/truss/_initialization_custody.py').is_file()
    actual=_git(root,'rev-parse','HEAD').decode().strip()
    actual_tree=commit_tree(root,actual)
    if actual!=commit or actual_tree!=tree:raise ValueError('Actual admitted qualification commit/tree differs')
    outputs=[];checkout_outputs=[]
    for selected in evidence_roots:
        # Preserve lexical location BEFORE resolving symlinks. External output
        # roots are recorded but never exempt an input located in this checkout.
        lexical=Path(os.path.abspath(selected));resolved=lexical.resolve()
        for path in (lexical,resolved):
            if root.is_relative_to(path):raise ValueError('Evidence output cannot contain the qualification checkout')
            if path.is_relative_to(root):
                relative=path.relative_to(root)
                base=Path('docs/helix/04-build/evidence/design-audit')
                if relative==base or not relative.is_relative_to(base):
                    raise ValueError('Evidence output must be separately scoped below design-audit')
        if lexical.is_relative_to(root):
            if not resolved.is_relative_to(root/'docs/helix/04-build/evidence/design-audit'):
                raise ValueError('Checkout evidence root must resolve within design-audit')
            checkout_outputs.append((lexical,resolved))
        outputs.append(resolved)
    changed=set(_git(root,'diff','--name-only','-z','HEAD','--').decode().split('\0'))
    changed.update(_git(root,'diff','--cached','--name-only','-z','HEAD','--').decode().split('\0'))
    dirty=sorted(p for p in changed if p and (p not in _PLANNER_PATHS or jh and p in _JH_INPUTS))
    if dirty:raise ValueError('Dirty tracked qualification inputs versus admitted HEAD: '+repr(dirty))
    # All untracked files, plus ignored files under executable/data input roots.
    untracked=set(_git(root,'ls-files','--others','--exclude-standard','-z').decode().split('\0'))
    untracked.update(_git(root,'ls-files','--others','--ignored','--exclude-standard','-z','--',*_INPUT_ROOTS,*(_JH_INPUTS if jh else ())).decode().split('\0'))
    unknown=[]
    for name in sorted(untracked-{''}):
        path=Path(name)
        if (name in _PLANNER_PATHS and not (jh and name in _JH_INPUTS)) or name.startswith('docs/helix/04-build/evidence/temporal-completion-current-owner-audit-20261102/'):continue
        if '__pycache__' in path.parts and path.suffix=='.pyc':continue
        lexical=root/path;resolved=lexical.resolve()
        if any(lexical.is_relative_to(location) and resolved.is_relative_to(target) for location,target in checkout_outputs):continue
        unknown.append(name)
    if unknown:raise ValueError('Uncommitted qualification inputs outside scoped evidence: '+repr(unknown))
    return {'commit':actual,'tree':actual_tree,'qualificationInputsClean':True,'generatedEvidenceRoots':[str(p) for p in outputs]}


def validate_capture_transition(root,receipt,final_commit,final_tree,*,native_digest,nonmigration_payload):
    """Preserve original capture provenance; allow reviewed fresh-artifact descendants only."""
    root=Path(root).resolve();capture=receipt.get('sourceCommit');tree=receipt.get('sourceTree')
    identity=receipt.get('sourceIdentity',{})
    jh=(root/'packages/python/src/truss/_initialization_custody.py').is_file()
    if jh or receipt.get('journalCustodyInputs') is not None:
        original_inputs=journal_custody_inputs(root,capture)
        if receipt.get('journalCustodyInputs')!=original_inputs or journal_custody_inputs(root,final_commit)!=original_inputs:
            raise ValueError('Custody code/schema/plan changes require a new original capture')
    if identity.get('commit')!=capture or identity.get('tree')!=tree or identity.get('qualificationInputsClean') is not True:
        raise ValueError('Original capture must attest clean qualification inputs at its own commit/tree')
    if commit_tree(root,capture)!=tree or commit_tree(root,final_commit)!=final_tree:
        raise ValueError('Original capture/final commit tree correspondence required')
    if receipt.get('runtimeManifestSha256')!=native_digest or receipt.get('nonMigrationPackageFiles')!=nonmigration_payload:
        raise ValueError('Complete non-migration payload and native manifest must equal original capture')
    producer=_git(root,'show',capture+':scripts/capture-temporal-native-inventory.py')
    from hashlib import sha256
    if sha256(producer).hexdigest()!=receipt.get('producerSha256'):
        raise ValueError('Original capture producer commit/blob differs')
    ancestor=subprocess.run(['git','merge-base','--is-ancestor',capture,final_commit],cwd=root,capture_output=True)
    if ancestor.returncode:raise ValueError('Reviewed final commit must descend from original capture')
    # Inspect EVERY intervening commit, including merge-parent diffs, so a
    # non-migration change subsequently reverted cannot masquerade as equality.
    changed=set(_git(root,'log','--format=','--name-only','-m','--full-history',capture+'..'+final_commit,
                     '--','packages/python',_SEAL,*(_JH_INPUTS if jh else ())).decode().splitlines())-{''}
    manifest=json.loads(_git(root,'show',final_commit+':'+_MIGRATIONS+'manifest.json'))
    if (manifest.get('target')!=native_digest or manifest.get('targetRelease')!='truss-catalog-runtime/0.76-temporal-candidate'
            or not manifest.get('baseline') or manifest.get('sources')!=[] or manifest.get('edges')!=[] or manifest.get('sourceWheels')!={}):
        raise ValueError('Reviewed descendant must select genuine fresh-only native baseline')
    allowed={_MIGRATIONS+'manifest.json'}|{_MIGRATIONS+name for name in manifest['files'] if Path(name).name==name and name.endswith('.json')}
    for name in changed:
        if name not in allowed:raise ValueError('Intervening package/enrollment/seal change requires a new source capture: '+name)
        if name!=_MIGRATIONS+'manifest.json':
            exists=subprocess.run(['git','cat-file','-e',capture+':'+name],cwd=root,capture_output=True)
            if exists.returncode==0:raise ValueError('Frozen migration artifact changed after capture: '+name)
            body=_git(root,'show',final_commit+':'+name)
            if sha256(body).hexdigest()!=manifest['files'][name.removeprefix(_MIGRATIONS)]:
                raise ValueError('Fresh descendant artifact differs from reviewed final manifest')
    return {'captureCommit':capture,'captureTree':tree,'finalCommit':final_commit,'finalTree':final_tree,
            'interveningPackagePaths':sorted(changed),'nativeManifestSha256':native_digest,'nonMigrationPayloadEqual':True}
