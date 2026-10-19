# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fixed reference domain, no original codec/facet authority."""
from test_numeric_row_image_native import NumericRowImageNativeTests,ROOT
class ReferenceDecimalNativeTests(NumericRowImageNativeTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass();c=cls.Connection(**cls.kwargs)
        try:c.run((ROOT/'packages/postgresql/native/row-image/reference-decimal.sql').read_text())
        finally:c.close()
    def coefficient(self,token):
        return self.connection.run('SELECT truss.reference_decimal_coefficient_original(:token)',token=token)[0][0]
    def test_reference_coefficients_and_zero_owner_order(self):
        for token,expected in [('9007199254740993.000','9007199254740993000'),('0.00','0'),
            ('-0.01','-10'),('1e2','100000'),('1.2300','1230'),
            ('-999999999999999999.999','-999999999999999999999'),
            ('0e'+'9'*33,'0'),('-0.000e'+'9'*1000,'0')]:
            self.assertEqual(self.coefficient(token),expected)
    def test_reference_domain_and_grammar_refusals(self):
        from pg8000.exceptions import DatabaseError
        for token in ('1e-4','1e18','+1','01','.1','1.','NaN','1e','1\n','1e'+'9'*33):
            with self.assertRaises(DatabaseError):self.coefficient(token)

    def test_reference_actual_images_preserve_zero_and_precision(self):
        for token,native in [('0e'+'9'*1000,'0'),
            ('999999999999999999.999','999999999999999999.999'),
            ('-999999999999999999.999','-999999999999999999.999'),
            ('1.2300','1.23')]:
            image=self.numeric_image('decimal',token,native)
            self.connection.run('SELECT truss.row_image_reference_decimal_original(:image)',image=image)
    def test_reference_actual_images_refuse_mismatch_and_domain_loss(self):
        from pg8000.exceptions import DatabaseError
        for token,native in [('1.2300','1.24'),('0.0001','0.0001'),
            ('1000000000000000000','1000000000000000000'),
            ('-1000000000000000000','-1000000000000000000'),('1e'+'0'*33,'1')]:
            image=self.numeric_image('decimal',token,native)
            with self.assertRaises(DatabaseError) as caught:
                self.connection.run('SELECT truss.row_image_reference_decimal_original(:image)',image=image)
            self.assertEqual(caught.exception.args[0]['C'],'54000' if len(token)>32 else '22023')

    def test_reference_images_require_complete_exclusive_carriers(self):
        from truss._row_image import decode_row_image
        from test_row_event_attribution import change
        from test_row_image_scalar_shape import null
        from pg8000.exceptions import DatabaseError
        import struct
        image=decode_row_image(self.numeric_image('decimal','1','1'))
        def missing(index):
            cell=image.cells[index]
            return image.original[:cell.offset-4]+struct.pack('!i',-1)+image.original[cell.offset+cell.length:]
        candidates=[null(image,5).original,null(image,6).original,
            missing(11),missing(12),
            change(image,11,b'').original,change(image,12,b'').original,
            change(image,2,b'integer').original,
            self.numeric_image('decimal','1','1',text_value='extra'),
            image.original[:-1],image.original+b'\x00',None]
        for candidate in candidates:
            with self.assertRaises(DatabaseError) as caught:
                self.connection.run('SELECT truss.row_image_reference_decimal_original(:image)',image=candidate)
            self.assertEqual(caught.exception.args[0]['C'],'22023')
