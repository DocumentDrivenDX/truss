"""Private frame-payload accounting integration, not a qualified driver.

The trusted transport must implement synchronous recv_into. Payload charges cover
the header and mutable/immutable whole frame only: transport, object overhead,
views, pg8000 core copies and parsing still need original producer accounting.
All allocation custody stays charged; this component issues no release facts.
"""
import struct
from threading import Lock
from ._resource_account import BytePermitAccount


class AccountedReceiver:
    def __init__(self, transport, account, producer, *, frame_bytes,
                 total_bytes, messages, reads):
        if not isinstance(account, BytePermitAccount) or producer is None:
            raise ValueError('Original byte account and producer required')
        for value in (frame_bytes, total_bytes, messages, reads):
            if type(value) is not int or value < 1:
                raise ValueError('Positive exact bounds required')
        if frame_bytes < 5 or total_bytes < 5:
            raise ValueError('Header capacity required')
        account.snapshot(producer)  # Recognize original custody before ingress.
        self._transport, self._account, self._producer = transport, account, producer
        self._frame_bytes = frame_bytes
        self._remaining_bytes, self._messages, self._reads = total_bytes, messages, reads
        self._failed = False
        self._gate = Lock()

    def _fill(self, buffer, start=0):
        offset = start
        while offset < len(buffer):
            if self._reads == 0:
                raise ValueError('Read work capacity exhausted')
            self._reads -= 1
            view = memoryview(buffer)[offset:]
            try:
                count = self._transport.recv_into(view)
            finally:
                view.release()
            if type(count) is not int or not 0 < count <= len(buffer) - offset:
                raise ValueError('Incomplete or invalid transport read')
            offset += count

    def receive(self):
        return self._receive(False)

    def receive_parts(self):
        """Return the original header/body with their slice payloads charged."""
        return self._receive(True)

    def _receive(self, split):
        if not self._gate.acquire(blocking=False):
            raise ValueError('Concurrent or reentrant receive refused')
        try:
            if self._failed:
                raise ValueError('Failed receiver cannot be reused')
            if self._messages == 0 or self._remaining_bytes < 5:
                raise ValueError('Message/header capacity exhausted')
            # Admit maximum payload overlap before even the header read. A peer's
            # length cannot authorize a later unreserved allocation.
            # Header/body slices together require one additional whole-frame
            # payload. Reserve it before ingress, not after receiving the frame.
            permit = self._account.reserve(self._producer,
                5 + (3 if split else 2) * self._frame_bytes)
            self._messages -= 1
            self._remaining_bytes -= 5
            self._account.allocate(self._producer, permit, 5)
            header = bytearray(5)
            self._fill(header)
            size = struct.unpack_from('!i', header, 1)[0]
            if size < 4 or size + 1 > self._frame_bytes:
                raise ValueError('Invalid or oversized frame')
            body_size = size - 4
            if body_size > self._remaining_bytes:
                raise ValueError('Cumulative wire capacity exhausted')
            self._remaining_bytes -= body_size
            self._account.allocate(self._producer, permit, size + 1)
            source = bytearray(size + 1)
            source[:5] = header
            self._fill(source, 5)
            self._account.allocate(self._producer, permit, size + 1)
            result = bytes(source)
            if split:
                self._account.allocate(self._producer, permit, 5)
                original_header = result[:5]
                self._account.allocate(self._producer, permit, body_size)
                original_body = result[5:]
                result = (original_header, original_body)
            # This synchronous receive cannot consume more of its reservation.
            # No allocation charge is released, including local temporary bytes.
            self._account.terminate(self._producer, permit)
            return result
        except BaseException:
            self._failed = True
            self._account.close(self._producer)
            raise
        finally:
            self._gate.release()
