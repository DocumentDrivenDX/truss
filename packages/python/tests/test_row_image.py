from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import struct
import unittest
from truss._row_image import decode_row_image, MAXIMUM_BYTES

RECEIPT=Path(__file__).resolve().parents[3]/'docs/helix/04-build/evidence/design-audit/row-image-preflight-native.json'


def samples():
    return [(v['id'],bytes.fromhex(v['originalHex'])) for v in json.loads(RECEIPT.read_text())['observations'] if 'originalHex' in v]


class NativeRowImageTests(unittest.TestCase):
    def test_all_retained_native_images_and_readonly_original_spans(self):
        values=samples();self.assertEqual(len(values),10)
        for name,raw in values:
            with self.subTest(nativeObservation=name):
                image=decode_row_image(raw);self.assertIs(image.original,raw)
                self.assertEqual(len(image.cells),10 if image.kind=='node' else 13)
                for i,cell in enumerate(image.cells):
                    payload=image.payload(i)
                    if cell.length is None:self.assertIsNone(payload)
                    else:
                        self.assertTrue(payload.readonly);self.assertIs(payload.obj,raw)
                        self.assertEqual(len(payload),cell.length)
                with self.assertRaises(FrozenInstanceError):image.cells[0].type_oid=25
        images={name:decode_row_image(raw) for name,raw in values}
        self.assertEqual(bytes(images['scalar-decimal'].payload(6)),b'0012345678901234567890.1234')
        self.assertEqual(bytes(images['scalar-decimal'].payload(5)),struct.pack('!hhhh6h',6,4,0,4,1234,5678,9012,3456,7890,1234))
        self.assertEqual(bytes(images['scalar-temporal'].payload(9)),b'\0'*8)
        self.assertEqual(bytes(images['scalar-temporal'].payload(8)),b'1999-12-31 19:00:00-05')
        self.assertIsNone(images['scalar-lexical-only-temporal'].payload(9))
        self.assertEqual(bytes(images['scalar-false'].payload(4)),b'\0')
        self.assertEqual(bytes(images['scalar-empty-binary'].payload(7)),b'')
        self.assertIsNone(images['scalar-empty-binary'].payload(3))

    def test_complete_domain_count_oid_null_length_and_trailing_refusals(self):
        raw=samples()[0][1];image=decode_row_image(raw)
        header=image.cells[0].offset-8;count=header-4
        controls=[b'',bytearray(raw),raw.replace(b'/0.1',b'/0.2'),raw[:count],
            raw[:count]+struct.pack('!i',12)+raw[count+4:],
            raw[:header]+struct.pack('!I',25)+raw[header+4:],
            raw[:header+4]+struct.pack('!i',-1)+raw[header+8:],
            raw[:header+4]+struct.pack('!i',-2)+raw[header+8:],
            raw[:header+4]+struct.pack('!i',2147483647)+raw[header+8:],raw[:-1],raw+b'\0']
        for i,value in enumerate(controls):
            with self.subTest(control=i),self.assertRaises(ValueError):decode_row_image(value)

    def test_primitive_boolean_and_text_refusals(self):
        values=dict(samples())
        for name,index,bad in [('scalar-false',4,b'\x02'),('scalar-string',3,b'\xff\xff'),('scalar-string',3,b'\0\0')]:
            raw=values[name];cell=decode_row_image(raw).cells[index]
            self.assertEqual(len(bad),cell.length)
            changed=raw[:cell.offset]+bad+raw[cell.offset+cell.length:]
            with self.assertRaises(ValueError):decode_row_image(changed)
        raw=values['scalar-false'];cell=decode_row_image(raw).cells[4]
        changed=raw[:cell.offset-4]+struct.pack('!i',0)+raw[cell.offset+1:]
        with self.assertRaises(ValueError):decode_row_image(changed)

    def test_complete_byte_ceiling_and_invalid_cell_index(self):
        raw=dict(samples())['complete-stored-scalar'];cell=decode_row_image(raw).cells[3]
        extra=MAXIMUM_BYTES-len(raw);new_length=cell.length+extra
        bounded=raw[:cell.offset-4]+struct.pack('!i',new_length)+b'a'*new_length+raw[cell.offset+cell.length:]
        self.assertEqual(len(bounded),MAXIMUM_BYTES)
        self.assertEqual(decode_row_image(bounded).cells[3].length,new_length)
        with self.assertRaises(ValueError):decode_row_image(bounded+b'a')
        for index in (-1,13,True,'0'):
            with self.assertRaises(ValueError):decode_row_image(raw).payload(index)


if __name__=='__main__':unittest.main()
