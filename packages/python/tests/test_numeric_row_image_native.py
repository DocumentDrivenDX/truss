# SPDX-License-Identifier: MIT OR Apache-2.0
"""Actual scalar composite image correspondence, not protected codec admission."""
from test_row_touch_observer_native import RowTouchObserverNativeTests, ROOT
import json

class NumericRowImageNativeTests(RowTouchObserverNativeTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:
            for name in ('numeric-witness','numeric-binary-witness','numeric-correspondence'):
                c.run((ROOT/f'packages/postgresql/native/row-image/{name}.sql').read_text())
        finally:c.close()
    def numeric_image(self,family,token,native,**extra):
        values=dict(state_id=1,node_id=10,scalar_kind=family,numeric_token=token,
                    codec_definition_bytes='\\x01',original_source_bytes='\\x02',**extra)
        return bytes(self.connection.run("""SELECT truss.row_image_scalar_original(
            jsonb_populate_record(NULL::truss.row_home_scalar,:value::jsonb ||
            jsonb_build_object('numeric_value',:native::numeric)))""",value=json.dumps(values),native=native)[0][0])
    def check(self,image):
        return self.connection.run('SELECT truss.row_image_numeric_correspondence_original(:image)',image=image)
    def test_actual_numeric_row_images(self):
        for family,token,native in [('integer','9007199254740993','9007199254740993'),
            ('decimal','1.2300e2','123.0000'),('decimal','-0.000','0.00'),
            ('integer','1.00e2','100'),('decimal','-0.0012300','-0.00123')]:
            image=self.numeric_image(family,token,native);self.check(image)
            cells=self.connection.run("SELECT truss.row_touch_image_cells_original('scalar',:image)",image=image)[0][0]
            self.assertEqual(bytes(cells[6]),token.encode())
    def test_native_mismatch_and_family_refusals(self):
        from pg8000.exceptions import DatabaseError
        for family,token,native,extra in [('integer','9007199254740993','9007199254740992',{}),
            ('integer','1.5','1.5',{}),('decimal','+0001.2300e+02','123',{}),
            ('decimal','0','NaN',{}),('decimal','1','1',dict(text_value='extra'))]:
            image=self.numeric_image(family,token,native,**extra)
            with self.assertRaises(DatabaseError) as caught:self.check(image)
            self.assertEqual(caught.exception.args[0]['C'],'22023')

    def test_missing_carriers_and_original_identity_refuse(self):
        from truss._row_image import decode_row_image
        from test_row_event_attribution import change
        from test_row_image_scalar_shape import null
        from pg8000.exceptions import DatabaseError
        import struct
        image=decode_row_image(self.numeric_image('decimal','1','1'))
        invalid=[null(image,5),null(image,6),change(image,6,b''),
                 change(image,11,b''),change(image,12,b''),
                 change(image,0,struct.pack('!q',0)),change(image,1,struct.pack('!q',-1)),
                 change(image,2,b'string')]
        for candidate in invalid:
            with self.assertRaises(DatabaseError) as caught:self.check(candidate.original)
            self.assertEqual(caught.exception.args[0]['C'],'22023')
        for candidate in (None,image.original[:-1],image.original+b'\x00'):
            with self.assertRaises(DatabaseError) as caught:self.check(candidate)
            self.assertEqual(caught.exception.args[0]['C'],'22023')
