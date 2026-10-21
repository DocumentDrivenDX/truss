# SPDX-License-Identifier: MIT OR Apache-2.0
"""Bounded pure compiler results. Contains no connection or authorization state."""
from collections import OrderedDict
import json
import sys
from threading import RLock

MAX_ENTRIES = 64
MAX_BYTES = 16 * 1024 * 1024
_entries = OrderedDict()
_bytes = 0
_lock = RLock()
_bundles = OrderedDict()
_bundle_bytes = 0


def binding_hint(key):
    """A non-authoritative prior response; the native observer must validate it."""
    with _lock:
        entry = _bundles.get(key)
        if entry is not None:
            _bundles.move_to_end(key)
            return entry[:2]
    return None


def remember_binding(key, validator, raw):
    global _bundle_bytes
    size = sys.getsizeof(raw) + sys.getsizeof(validator) + sys.getsizeof(key)
    if size > MAX_BYTES:
        return
    with _lock:
        old = _bundles.pop(key, None)
        if old is not None:
            _bundle_bytes -= old[2]
        while _bundles and (len(_bundles) >= 2 or _bundle_bytes + size > MAX_BYTES):
            _, (_, _, removed) = _bundles.popitem(last=False)
            _bundle_bytes -= removed
        _bundles[key] = (validator, raw, size)
        _bundle_bytes += size


def compile_response(compiler, request, page_size=None, after=None):
    """Exact inputs include model bytes/pins, binding, values, profiles and limits.

    Retain serialized successes only; every caller receives a fresh decoded
    artifact. Changing compiler identity or any input misses. Native scope and
    engine-program correspondence are still checked by the execution boundary.
    """
    global _bytes
    key = (compiler, request, page_size, None if after is None else tuple(after))
    with _lock:
        entry = _entries.get(key)
        if entry is not None:
            _entries.move_to_end(key)
            return json.loads(entry[0])
    raw = compiler(request) if page_size is None else compiler(request, page_size, after)
    result = json.loads(raw)
    if result.get('status') != 'compiled':
        return result
    size = sys.getsizeof(request) + sys.getsizeof(raw) + sys.getsizeof(key)
    if after is not None:
        size += sys.getsizeof(key[3]) + sum(sys.getsizeof(value) for value in key[3])
    if size <= MAX_BYTES:
        with _lock:
            if key not in _entries:
                while _entries and (len(_entries) >= MAX_ENTRIES or _bytes + size > MAX_BYTES):
                    _, (_, removed) = _entries.popitem(last=False)
                    _bytes -= removed
                _entries[key] = (raw, size)
                _bytes += size
    return result
