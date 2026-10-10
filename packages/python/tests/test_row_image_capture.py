from dataclasses import FrozenInstanceError
import unittest
from unittest.mock import patch
from truss._row_image_capture import COLUMNS, decode_row_image_capture
from test_row_event_attribution import originals


def rows():return [(image.kind,image.original) for image in originals()]

def capture(values,**changes):
    options=dict(columns=COLUMNS,rows=values,command='SELECT',affected_rows=str(len(values)),maximum_rows=10,maximum_bytes=100000)
    options.update(changes)
    return decode_row_image_capture(**options)


class RowImageCaptureTests(unittest.TestCase):
    def test_original_cells_retained_after_input_container_change(self):
        source=rows();result=capture(source)
        for image,(_,raw) in zip(result.images,result.original_rows):self.assertIs(image.original,raw)
        source.clear()
        self.assertEqual(len(result.images),3)
        with self.assertRaises(FrozenInstanceError):result.command='UPDATE'
        exact=sum(len(kind)+len(raw) for kind,raw in result.original_rows)
        self.assertEqual(capture(list(result.original_rows),maximum_rows=3,maximum_bytes=exact).original_rows,result.original_rows)

    def test_descriptor_completion_and_bounds_refuse(self):
        source=rows()
        for options in ({'columns':('image_kind',)}, {'columns':('original_image','image_kind')}, {'command':'UPDATE'}, {'affected_rows':'02'}, {'affected_rows':'4'}, {'affected_rows':3}, {'maximum_rows':2}, {'maximum_bytes':1}, {'maximum_rows':True}, {'maximum_bytes':-1}):
            with self.subTest(options=options),self.assertRaisesRegex(ValueError,'row-image-capture:unavailable'):capture(source,**options)

    def test_all_input_preflight_precedes_decode(self):
        source=rows();source[-1]=('scalar',bytearray(source[-1][1]))
        with patch('truss._row_image_capture.decode_row_image',side_effect=AssertionError('No partial decode')) as decode:
            with self.assertRaisesRegex(ValueError,'row-image-capture:unavailable'):capture(source)
            decode.assert_not_called()

    def test_kind_correspondence_and_malformed_frame_refuse(self):
        source=rows()
        for values in ([('state',source[-1][1])],[('unknown',source[0][1])],[('state',None)],[('state',b'bad')],[('state',source[0][1],b'extra')]):
            with self.subTest(values=values),self.assertRaisesRegex(ValueError,'row-image-capture:unavailable'):capture(values)

    def test_duplicate_original_identity_refuses(self):
        source=rows()
        with self.assertRaisesRegex(ValueError,'row-image-capture:unavailable'):capture([*source,source[0]])
        # Empty completion alone never authenticates an absent selected scope.
        self.assertEqual(capture([]).images,())
