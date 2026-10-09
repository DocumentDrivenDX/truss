"""Private raw receive candidate; not a driver, account issuer or settlement proof.

Bounds cover raw frame bytes, message attempts and recv_into calls only. Python,
transport/TLS/backing, retained immutable copies and decoder allocations still
require the original complete operation account. Failure permanently closes this
receiver; it does not prove native termination or authorize connection reuse.
"""
import struct


class Receiver:
    def __init__(self, transport, *, frame_bytes, total_bytes, messages, reads):
        for value in (frame_bytes, total_bytes, messages, reads):
            if type(value) is not int or value < 1:
                raise ValueError('Positive integer candidate bounds required')
        if frame_bytes < 5 or total_bytes < 5:
            raise ValueError('Header capacity required')
        self.transport = transport
        self.frame_bytes = frame_bytes
        self.remaining_bytes = total_bytes
        self.remaining_messages = messages
        self.remaining_reads = reads
        self.failed = False

    def _fill(self, buffer, start=0):
        offset = start
        while offset < len(buffer):
            if self.remaining_reads == 0:
                raise ValueError('Read work capacity')
            self.remaining_reads -= 1
            view = memoryview(buffer)[offset:]
            try:
                count = self.transport.recv_into(view)
            finally:
                view.release()
            if type(count) is not int or not 0 < count <= len(buffer) - offset:
                raise ValueError('Incomplete or invalid transport read')
            offset += count

    def receive(self):
        if self.failed:
            raise ValueError('Failed receiver cannot be reused')
        try:
            # Reserve the message and header before the first ingress call.
            if self.remaining_messages == 0 or self.remaining_bytes < 5:
                raise ValueError('Message/header capacity')
            self.remaining_messages -= 1
            self.remaining_bytes -= 5
            header = bytearray(5)
            self._fill(header)
            size = struct.unpack_from('!i', header, 1)[0]
            if size < 4 or size + 1 > self.frame_bytes:
                raise ValueError('Frame capacity or invalid length')
            body_size = size - 4
            if body_size > self.remaining_bytes:
                raise ValueError('Cumulative body capacity')
            self.remaining_bytes -= body_size
            # Whole-frame storage is allocated only after complete length admission.
            source = bytearray(size + 1)
            source[:5] = header
            self._fill(source, 5)
            return bytes(source)
        except BaseException:
            self.failed = True
            raise
