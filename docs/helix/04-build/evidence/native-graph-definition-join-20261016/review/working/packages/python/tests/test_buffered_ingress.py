"""Original buffered order and raw-stream visit accounting."""
import io
import unittest
from truss._native_result_custody import _BufferedIngress
from truss._native_pg8000 import NativeBoundaryRefusal

class ChunkedRaw(io.RawIOBase):
    def __init__(self, chunks):
        super().__init__(); self.chunks=list(chunks); self.visits=0
    def readable(self): return True
    def readinto(self, target):
        self.visits += 1
        if not self.chunks: return 0
        chunk=self.chunks.pop(0)
        count=min(len(target),len(chunk)); target[:count]=chunk[:count]
        if count < len(chunk): self.chunks.insert(0,chunk[count:])
        return count

class BufferedIngressTests(unittest.TestCase):
    def stream(self, chunks):
        raw=ChunkedRaw(chunks)
        stream=io.BufferedRWPair(raw,io.BytesIO(),8)
        self.addCleanup(stream.close)
        return raw,stream,_BufferedIngress(stream)
    def test_one_raw_call_per_partial_visit(self):
        raw,stream,ingress=self.stream([b'ab',b'cd',b'ef'])
        target=bytearray(6)
        self.assertEqual(ingress.recv_into(target),2)
        self.assertEqual(raw.visits,1)
        self.assertEqual(target[:2],b'ab')
        self.assertEqual(ingress.recv_into(memoryview(target)[2:]),2)
        self.assertEqual(raw.visits,2)
        self.assertEqual(ingress.recv_into(memoryview(target)[4:]),2)
        self.assertEqual(raw.visits,3)
        self.assertEqual(target,b'abcdef')
    def test_prefetched_bytes_keep_order_without_new_raw_call(self):
        raw,stream,ingress=self.stream([b'abcdefgh',b'ij'])
        target=bytearray(3)
        self.assertEqual(ingress.recv_into(target),3)
        self.assertEqual(target,b'abc'); self.assertEqual(raw.visits,1)
        self.assertEqual(ingress.recv_into(target),3)
        self.assertEqual(target,b'def'); self.assertEqual(raw.visits,1)
        self.assertEqual(ingress.recv_into(target),2)
        self.assertEqual(target[:2],b'gh'); self.assertEqual(raw.visits,1)
        self.assertEqual(ingress.recv_into(target),2)
        self.assertEqual(target[:2],b'ij'); self.assertEqual(raw.visits,2)
    def test_unsupported_stream_refuses_without_read(self):
        class Unsupported:
            def readinto(self, target): raise AssertionError('Must not read')
        with self.assertRaises(NativeBoundaryRefusal): _BufferedIngress(Unsupported())
    def test_subclass_cannot_substitute_receive(self):
        class Substitute(io.BufferedRWPair):
            def readinto1(self, target): raise AssertionError('Foreign receive')
        stream=Substitute(ChunkedRaw([]),io.BytesIO())
        self.addCleanup(stream.close)
        with self.assertRaises(NativeBoundaryRefusal): _BufferedIngress(stream)
    def test_eof_is_one_raw_visit(self):
        raw,stream,ingress=self.stream([])
        self.assertEqual(ingress.recv_into(bytearray(1)),0)
        self.assertEqual(raw.visits,1)
