import json
from pathlib import Path
import struct
import unittest
from truss._row_image import decode_row_image
from truss._row_image_scalar_shape import check_scalar_shape
from test_row_event_attribution import change

ROOT = Path(__file__).resolve().parents[3]


def scalar_samples():
    receipt = json.loads((ROOT / 'docs/helix/04-build/evidence/design-audit/row-image-tree-native.json').read_text())
    return [decode_row_image(bytes.fromhex(o['originalImageHex']))
            for o in receipt['observations'] if o.get('originalEvent', [None])[0] == 'row_home_scalar']


def null(image, index):
    cell = image.cells[index]
    return decode_row_image(image.original[:cell.offset-4] + struct.pack('!i', -1) +
                            image.original[cell.offset+(cell.length or 0):])


class ScalarShapeTests(unittest.TestCase):
    def test_all_original_native_families(self):
        samples = scalar_samples()
        self.assertEqual({bytes(i.payload(2)) for i in samples},
                         {b'string', b'boolean', b'integer', b'decimal', b'binary', b'timestamp', b'opaque'})
        for image in samples: self.assertIs(check_scalar_shape(image), image)

    def test_missing_and_extra_selected_payloads(self):
        for image in scalar_samples():
            required = next(i for i in range(3, 11) if image.payload(i) is not None)
            with self.assertRaisesRegex(ValueError, 'row-image-scalar-shape:unavailable'):
                check_scalar_shape(null(image, required))
            extra = 4 if image.payload(4) is None else 3
            with self.assertRaises(ValueError): check_scalar_shape(change(image, extra, b'\x01' if extra == 4 else b'extra'))

    def test_unknown_family_empty_token_and_original_carriers(self):
        for image in scalar_samples():
            with self.assertRaises(ValueError): check_scalar_shape(change(image, 2, b'unknown'))
            for i in (11, 12):
                with self.assertRaises(ValueError): check_scalar_shape(change(image, i, b''))
            if bytes(image.payload(2)) in (b'integer', b'decimal'):
                with self.assertRaises(ValueError): check_scalar_shape(change(image, 6, b''))

    def test_optional_timestamp_projection_and_present_empty_values(self):
        for image in scalar_samples():
            if bytes(image.payload(2)) == b'timestamp': check_scalar_shape(null(image, 9))
            if bytes(image.payload(2)) == b'string': check_scalar_shape(change(image, 3, b''))
            if bytes(image.payload(2)) == b'binary': check_scalar_shape(change(image, 7, b''))
            if bytes(image.payload(2)) == b'opaque': check_scalar_shape(change(image, 10, b''))
