"""Private PostgreSQL frame limits; no allocation or copy accounting."""
import struct
from threading import Lock


class BoundedReceiver:
    def __init__(self, transport, *, frame_bytes,
                 total_bytes, messages, reads):
        for value in (frame_bytes, total_bytes, messages, reads):
            if type(value) is not int or value < 1:
                raise ValueError('Positive exact bounds required')
        if frame_bytes < 5 or total_bytes < 5:
            raise ValueError('Header capacity required')
        self._transport = transport
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
        """Return bounded original header and body bytes."""
        return self._receive(True)

    def _receive(self, split):
        if not self._gate.acquire(blocking=False):
            raise ValueError('Concurrent or reentrant receive refused')
        try:
            if self._failed:
                raise ValueError('Failed receiver cannot be reused')
            if self._messages == 0 or self._remaining_bytes < 5:
                raise ValueError('Message/header capacity exhausted')
            self._messages -= 1
            self._remaining_bytes -= 5
            header = bytearray(5)
            self._fill(header)
            size = struct.unpack_from('!i', header, 1)[0]
            if size < 4 or size + 1 > self._frame_bytes:
                raise ValueError('Invalid or oversized frame')
            body_size = size - 4
            if body_size > self._remaining_bytes:
                raise ValueError('Cumulative wire capacity exhausted')
            self._remaining_bytes -= body_size
            source = bytearray(size + 1)
            source[:5] = header
            self._fill(source, 5)
            result = bytes(source)
            if split:
                original_header = result[:5]
                original_body = result[5:]
                result = (original_header, original_body)
            return result
        except BaseException:
            self._failed = True
            raise
        finally:
            self._gate.release()
