# SPDX-License-Identifier: MIT OR Apache-2.0
"""Synthetic frame controls: no native/provider/authentication qualification."""
import struct
import unittest
from types import SimpleNamespace
from pg8000.converters import string_in
from truss._native_source_census import NativeSourceCensusCapture,CENSUS_LIMITS,CHUNK_BYTES
from truss._native_arbitration import NativeOperationSession
from truss._native_result_custody import NativeTextLimits
from truss._native_pg8000 import NativeBoundaryRefusal

def descriptor(names=(b'ordinal',b'total_bytes',b'chunk_hex'),oid=25):
    return struct.pack('!H',3)+b''.join(n+b'\0'+struct.pack('!IhIhih',0,0,oid,-1,-1,0) for n in names)
def row(cells):
    return struct.pack('!H',len(cells))+b''.join(struct.pack('!i',-1) if c is None else struct.pack('!i',len(c))+c for c in cells)
def gate():
    g=object.__new__(NativeSourceCensusCapture)
    g.boundary=SimpleNamespace(_connection=SimpleNamespace(_client_encoding='utf8'),_active_control=None)
    g.session=SimpleNamespace(cleanup_calls=())
    g.limits=CENSUS_LIMITS;g.stage=0;g.chunk_count=0;g.image=None;g.offset=0
    g.unavailable=False;g.frames=[];g.census_context=SimpleNamespace(input_funcs=[string_in]*3)
    g.rows_seen=0;g.bytes_seen=0;g.cleanup_rows_seen=0;g.cleanup_bytes_seen=0;g.expected_command='SELECT'
    return g
def feed(g,code,data):g._validate(code,data,g.census_context)
def pieces(image):
    return [(str(i).encode(),str(len(image)).encode(),image[i*CHUNK_BYTES:(i+1)*CHUNK_BYTES].hex().encode()) for i in range((len(image)+CHUNK_BYTES-1)//CHUNK_BYTES)]
class NativeSourceCensusFrameTests(unittest.TestCase):
    def test_selected_profile_does_not_modify_defaults(self):
        self.assertEqual(NativeTextLimits().wire_bytes,1048576)
        self.assertEqual(CENSUS_LIMITS.frame_bytes,65536)
        self.assertEqual(CENSUS_LIMITS.cell_bytes,8192)
    def test_native_descriptor_bounds(self):
        for data in (descriptor((b'wrong',b'total_bytes',b'chunk_hex')),descriptor(oid=23)):
            with self.subTest(data=data[:30]),self.assertRaises(NativeBoundaryRefusal):feed(gate(),b'T',data)
    def test_complete_boundaries_and_unicode(self):
        for image in (b'a',b'a'*4095,b'a'*4096,b'a'*4097,b'a'*4095+'🙂é'.encode()):
            g=gate();feed(g,b'T',descriptor())
            for p in pieces(image):feed(g,b'D',row(p))
            feed(g,b'C',b'SELECT '+str(g.chunk_count).encode()+b'\0');self.assertEqual(g.stage,2)
            feed(g,b'Z',b'T');self.assertEqual(g.stage,3);self.assertEqual(bytes(g.image),image)
    def test_exact_maximum_image(self):
        image=b"a"*16777216;g=gate();feed(g,b"T",descriptor())
        for p in pieces(image):feed(g,b"D",row(p))
        feed(g,b"C",b"SELECT 4096\0");feed(g,b"Z",b"T")
        self.assertEqual(bytes(g.image),image)
    def test_constructor_rejects_unselected_session(self):
        for source in ("", "x"*32769):
            with self.assertRaises(NativeBoundaryRefusal):NativeSourceCensusCapture(object.__new__(NativeOperationSession),source)
    def test_changed_decoder_refused(self):
        g=gate();feed(g,b"T",descriptor());g.census_context.input_funcs=[str]*3
        with self.assertRaises(NativeBoundaryRefusal):feed(g,b"D",row((b"0",b"1",b"61")))
    def test_invalid_chunk_shapes(self):
        for cells in [(b'1',b'1',b'61'),(b'00',b'1',b'61'),(b'0',b'01',b'61'),(b'0',b'0',b'61'),
                      (b'0',b'16777217',b'61'),(b'0',b'4097',b'61'),(b'0',b'1',b'6G'),
                      (b'0',b'1',b'6A'),(b'0',b'1',None)]:
            g=gate();feed(g,b'T',descriptor())
            with self.subTest(cells=cells),self.assertRaises(NativeBoundaryRefusal):feed(g,b'D',row(cells))
    def test_missing_prefix_or_terminal_and_count(self):
        g=gate();feed(g,b'T',descriptor());feed(g,b'D',row(pieces(b'a'*4097)[0]))
        with self.assertRaises(NativeBoundaryRefusal):feed(g,b'C',b'SELECT 1\0')
        for code,data in ((b'Z',b'T'),(b'C',b'SELECT 2\0'),(b'D',row((b'0',b'1',b'61')))):
            g=gate();feed(g,b'T',descriptor());feed(g,b'D',row((b'0',b'1',b'61')))
            with self.assertRaises(NativeBoundaryRefusal):feed(g,code,data)
    def test_complete_null_is_unavailable_not_partial_image(self):
        g=gate();feed(g,b'T',descriptor());feed(g,b'D',row((None,None,None)))
        feed(g,b'C',b'SELECT 1\0');feed(g,b'Z',b'T')
        self.assertTrue(g.unavailable);self.assertIsNone(g.image);self.assertEqual(g.stage,3)
    def test_closed_response_inventory(self):
        for code,data in ((b'T',descriptor()),(b'N',b'SNOTICE\0C00000\0\0'),(b'Z',b'I')):
            g=gate();feed(g,b'T',descriptor())
            with self.assertRaises(NativeBoundaryRefusal):feed(g,code,data)
    def test_shape_only_can_capture_forged_bytes(self):
        g=gate();feed(g,b'T',descriptor());feed(g,b'D',row((b'0',b'6',b'forged'.hex().encode())))
        feed(g,b'C',b'SELECT 1\0');feed(g,b'Z',b'T');self.assertEqual(bytes(g.image),b'forged')
        # Synthetic complete framing is not actual NativeCall/session custody.
