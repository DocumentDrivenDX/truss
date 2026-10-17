"""Private embedded owner host. No executable discovery or host JavaScript process.

This delivery boundary is replaceable by native UMF. Owner receipts and native
admission remain owned by their existing producers; this module grants neither.
"""
from functools import lru_cache
from hashlib import sha256
from importlib.resources import files
import json
import gzip
import struct
from subprocess import CompletedProcess
from threading import Lock
from time import monotonic

from ._current_query_pipe import CurrentQueryPipeError, _envelope


@lru_cache(maxsize=1)
def _assets():
    root = files('truss').joinpath('_embedded_js')
    from ._embedded_release import MANIFEST_SHA256
    raw_manifest=root.joinpath('manifest.json').read_bytes()
    if sha256(raw_manifest).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('Embedded owner manifest pin mismatch')
    manifest = json.loads(raw_manifest)
    if manifest['profile'] != 'truss.embedded-v8/1' or manifest['engine'] != 'mini-racer==0.14.1':
        raise ValueError('Qualified embedded owner profile required')
    values = {}
    for name, digest in manifest['files'].items():
        raw = root.joinpath(name).read_bytes()
        if sha256(raw).hexdigest() != digest:
            raise ValueError('Embedded owner asset digest mismatch')
        values[name] = (gzip.decompress(raw) if name.endswith('.gz') else raw).decode('utf8')
    values['archive']=json.loads(values['modules.json.gz'])
    return values


def _entry(path):
    value = str(path).replace('\\', '/')
    marker = '/truss/'
    if marker in value:
        value = value.rsplit(marker, 1)[1]
    if value.startswith('/') or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('Packaged owner entry required')
    return value


class OwnerVM:
    def __init__(self, entry, *, input_bytes=b'', args=(), extra=None, timeout=10):
        if type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError('Bounded embedded deadline required')
        self.end = monotonic() + timeout
        self.vm = None
        try:
            from importlib.metadata import version, PackageNotFoundError
            try:
                if version('mini-racer') != '0.14.1':
                    raise OSError('Qualified embedded engine required')
                from py_mini_racer import MiniRacer
            except (ImportError,PackageNotFoundError) as error:
                raise OSError('Qualified embedded engine unavailable') from error
            self.vm = MiniRacer()
            if self.vm.v8_version!='14.4.258.23':
                raise OSError('Qualified embedded V8 revision required')
            self.vm.set_hard_memory_limit(512 * 1024 * 1024)
            assets = _assets()
            self.eval(assets['runtime.js'])
            self.eval(assets['polyfills.js'])
            name=_entry(entry)
            cohort=name.split('/')[0]+'/'
            prefixes=(cohort,'_umf/') if cohort=='_umf_core08/' else (cohort,)
            archive={kind:{key:value for key,value in group.items() if key.startswith(prefixes)} for kind,group in assets['archive'].items()}
            if name not in archive['modules']:
                raise ValueError('Packaged owner entry required')
            self.eval('__install(' + json.dumps(archive,separators=(',',':')) + ',' + json.dumps(name) + ','
                      + json.dumps(input_bytes.hex()) + ',' + json.dumps(list(args)) + ','
                      + json.dumps(extra or {}) + ')')
        except BaseException:
            self.close()
            raise

    def remaining(self):
        remaining = self.end - monotonic()
        if remaining <= 0:
            raise TimeoutError('Embedded owner deadline expired')
        return remaining

    def eval(self, source):
        from py_mini_racer import JSEvalException
        try:
            return self.vm.eval(source, timeout_sec=self.remaining())
        except TimeoutError:
            raise
        except JSEvalException as error:
            raise ValueError('Embedded owner execution refused') from error

    def promise(self, source):
        try:
            return self.eval(source).get(timeout=self.remaining())
        except BaseException:
            self.close()
            raise

    def close(self):
        if self.vm is not None:
            self.vm.close()
            self.vm = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def capture(entry, *, input_bytes=b'', limit, timeout, args=(), extra=None):
    try:
        from py_mini_racer import JSPromiseError
    except ImportError as error:
        raise OSError('Qualified embedded engine unavailable') from error
    try:
        with OwnerVM(entry, input_bytes=input_bytes, args=args, extra=extra, timeout=timeout) as owner:
            result = json.loads(owner.promise('__result()'))
    except JSPromiseError as error:
        raise ValueError('Embedded owner output refused') from error
    stdout, stderr = bytes.fromhex(result['stdout']), bytes.fromhex(result['stderr'])
    if len(stdout) > limit:
        raise ValueError('Original owner output capacity exceeded')
    return CompletedProcess(('embedded-v8', _entry(entry)), result['code'], stdout, stderr)


class EmbeddedOwnerPipe:
    """One isolate, one shared deadline, original frames and permanent fencing."""
    def __init__(self, entry, *, timeout_seconds=5, disclosure=False):
        self._lock = Lock()
        self._seen = set()
        self._source_receipt = None
        self._closed = False
        self._cleanup_complete = False
        self._disclosure = disclosure
        self._owner = OwnerVM(entry, timeout=timeout_seconds)

    def _request_capacity(self, request):
        if not self._disclosure:
            return 4 * 1024 * 1024
        from ._current_disclosure_pipe import CurrentDisclosurePipe
        return CurrentDisclosurePipe._request_capacity(self, request)

    def exchange(self, request, *, source_receipt):
        if not self._lock.acquire(blocking=False):
            raise CurrentQueryPipeError('One original computation call at a time required')
        try:
            if self._closed:
                raise CurrentQueryPipeError('Original computation isolate is closed')
            if type(request) is not bytes or not 1 <= len(request) <= self._request_capacity(request):
                raise CurrentQueryPipeError('Bounded original computation request required')
            if (type(source_receipt) is not str or len(source_receipt) != 64
                    or any(c not in '0123456789abcdef' for c in source_receipt)):
                raise CurrentQueryPipeError('Original source receipt correlation required')
            if self._source_receipt is not None and self._source_receipt != source_receipt:
                raise CurrentQueryPipeError('Original computation source receipt changed')
            self._source_receipt = source_receipt
            envelope = _envelope(request)
            if 'sourceReceipt' in envelope and envelope['sourceReceipt'] != source_receipt:
                raise CurrentQueryPipeError('Original computation request source receipt changed')
            request_id = envelope['requestId']
            if request_id in self._seen or len(self._seen) >= 4098:
                raise CurrentQueryPipeError('Unique bounded computation calls required')
            self._seen.add(request_id)
            frame = struct.pack('>I', len(request)) + request
            result = bytes.fromhex(self._owner.promise('__feed(' + json.dumps(frame.hex()) + ')'))
            if len(result) < 4:
                raise CurrentQueryPipeError('Original response truncated')
            size = struct.unpack('>I', result[:4])[0]
            if not 1 <= size <= 16 * 1024 * 1024 or len(result) != size + 4:
                raise CurrentQueryPipeError('Bounded complete computation response required')
            response = result[4:]
            envelope = _envelope(response)
            if envelope['requestId'] != request_id or envelope.get('sourceReceipt') != source_receipt:
                raise CurrentQueryPipeError('Original computation response correlation changed')
            self._owner.remaining()
            return response
        except BaseException as error:
            self.close()
            if isinstance(error,(CurrentQueryPipeError,KeyboardInterrupt,SystemExit)):
                raise
            raise CurrentQueryPipeError('Original embedded computation unavailable') from error
        finally:
            self._lock.release()

    def close(self):
        self._closed = True
        self._owner.close()
        self._cleanup_complete = True

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
