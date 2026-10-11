"""Private POSIX directory resource resolver; explicit start/close, no fallback."""
import os
import stat
from threading import Lock
from ._installation_resources import ResourceEntry


class DirectoryResourceResolver:
    def __init__(self):
        self._root = None
        self._closed = False
        self._lock = Lock()

    def start(self, path):
        with self._lock:
            if self._closed or self._root is not None:
                raise ValueError('Original unstarted resolver required')
            if os.open not in os.supports_dir_fd or not all(hasattr(os, n) for n in ('O_NOFOLLOW', 'O_DIRECTORY', 'O_NONBLOCK')):
                raise ValueError('POSIX descriptor-relative containment unavailable')
            self._root = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def resolve(self, entry):
        if type(entry) is not ResourceEntry:
            raise ValueError('Original admitted resource entry required')
        segments = entry.path.split('/')
        if '\\' in entry.path or ':' in entry.path or any(s in ('', '.', '..') or '\0' in s for s in segments):
            raise ValueError('Relative resource path required')
        return _DirectoryResource(self, tuple(segments))

    def _open(self, segments, mode):
        if mode != 'rb':
            raise ValueError('Read-only binary resource required')
        with self._lock:
            if self._closed or self._root is None:
                raise ValueError('Original open resolver required')
            parent = os.dup(self._root)
            leaf = None
            try:
                for segment in segments[:-1]:
                    child = os.open(segment, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                    os.close(parent)
                    parent = child
                leaf = os.open(segments[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                observed = os.fstat(leaf)
                if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
                    raise ValueError('Single-link regular resource file required')
                stream = os.fdopen(leaf, 'rb')
                leaf = None
                return stream
            finally:
                if leaf is not None: os.close(leaf)
                os.close(parent)

    def close(self):
        with self._lock:
            self._closed = True
            if self._root is not None:
                os.close(self._root)
                self._root = None


class _DirectoryResource:
    def __init__(self, resolver, segments):
        self._resolver = resolver
        self._segments = segments

    def open(self, mode):
        return self._resolver._open(self._segments, mode)
