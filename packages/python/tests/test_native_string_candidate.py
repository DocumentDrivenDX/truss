"""Selected JSON string source correspondence; no full scope or installation authority."""
from test_native_connected_string_writer import installation_sql
import json
from test_native_dependent_owner import NativeDependentOwnerTests

class NativeStringCandidateTests(NativeDependentOwnerTests):
    def setUp(self):
        super().setUp()
        self.connection.run(installation_sql('packages/postgresql/native/row-image/prestate.sql'))
        self.connection.run(installation_sql('packages/postgresql/native/row-image/string-candidate.sql'))

    def _scalar(self,**fields):
        fields.setdefault('12',"decode('2276616c756522','hex')")
        return super()._scalar(**fields)

    def _candidate(self,replacement="'new value'",source="decode('226e65772076616c756522','hex')",state=None,node=None,scalar=None):
        state=state or self._value();node=node or self._node();scalar=scalar or self._scalar()
        arguments=[state,node,scalar,'truss.row_image_state_original('+self._value()+')',
          'truss.row_image_node_original('+self._node()+')','truss.row_image_scalar_original('+self._scalar()+')',replacement,source]
        return self.connection.run('SELECT * FROM truss.row_image_existing_string_candidate_original('+','.join(arguments)+')')[0]

    def test_candidate_preserves_ids_and_profiles_and_exact_new_source(self):
        from truss._row_image import decode_row_image
        from truss._row_event_attribution import attribute_row_event
        for text, expected_text in (("''", ''),("'snowman ☃ and quote '' preserved'", "snowman ☃ and quote ' preserved"),("'value'", 'value')):
            with self.subTest(text=text):
                token=json.dumps(expected_text,ensure_ascii=False).encode()
                row=self._candidate(text,"decode('"+token.hex()+"','hex')")
                before=tuple(decode_row_image(value) for value in row[:3])
                after=tuple(decode_row_image(value) for value in row[3:])
                self.assertEqual(row[0],row[3]);self.assertEqual(row[1],row[4])
                for index in range(13):
                    if index not in (3,12):
                        left,right=before[2].payload(index),after[2].payload(index)
                        self.assertEqual(None if left is None else bytes(left),None if right is None else bytes(right))
                self.assertEqual(bytes(after[2].payload(3)).decode('utf-8'),expected_text)
                self.assertEqual(bytes(after[2].payload(12)),token)
                event=attribute_row_event('UPDATE',before[2],after[2],before,after,6,8388608)
                self.assertEqual(event.old_owner,event.new_owner)
        unchanged=self._candidate("'value'","decode('2276616c756522','hex')")
        self.assertEqual(unchanged[:3],unchanged[3:])
        self.assertEqual(len(unchanged),6)  # OLD and NEW remain separate fields.

    def test_substituted_or_unsupported_inputs_refuse(self):
        from pg8000.exceptions import DatabaseError
        cases=[{'state':self._value(**{'12':"decode('0400','hex')"})},
          {'node':self._node(**{'1':'602'})}, {'scalar':self._scalar(**{'3':"'changed'"})},
          {'replacement':'NULL'}, {'source':'NULL'}, {'source':"decode('','hex')"},
          {'replacement':"repeat('x',1048577)"}, {'source':"decode(repeat('00',1048577),'hex')"}]
        for case in cases:
            with self.subTest(case=case):
                self.connection.run('SAVEPOINT candidate')
                with self.assertRaises(DatabaseError):self._candidate(**case)
                self.connection.run('ROLLBACK TO SAVEPOINT candidate');self.connection.run('RELEASE SAVEPOINT candidate')

    def test_native_text_domain_rejects_nul_and_non_utf8(self):
        from pg8000.exceptions import DatabaseError
        for expression in ("chr(0)","convert_from(decode('ff','hex'),'UTF8')"):
            self.connection.run('SAVEPOINT text_domain')
            with self.assertRaises(DatabaseError):self._candidate(expression)
            self.connection.run('ROLLBACK TO SAVEPOINT text_domain');self.connection.run('RELEASE SAVEPOINT text_domain')

    def test_actual_aggregate_bound_and_substituted_frame_lengths(self):
        from pg8000.exceptions import DatabaseError
        state,node,scalar=self._value(),self._node(),self._scalar()
        base=self.connection.run('SELECT 2*truss.row_image_state_length_original('+state+')+2*truss.row_image_node_length_original('+node+')+2*truss.row_image_scalar_length_original('+scalar+')')[0][0]
        # New text and source have the same lengths as the original string/token.
        # Each byte added to state is retained twice, making the total exactly 8 MiB.
        padding=(8388608-base)//2
        state=self._value(**{'12':"decode(repeat('04',"+str(padding+1)+"),'hex')"})
        args=[state,node,scalar,'truss.row_image_state_original('+state+')',
              'truss.row_image_node_original('+node+')','truss.row_image_scalar_original('+scalar+')',
              "'value'","decode('2276616c756522','hex')"]
        statement='SELECT * FROM truss.row_image_existing_string_candidate_original('
        result=self.connection.run(statement+','.join(args)+')')[0]
        self.assertEqual(sum(len(value) for value in result),8388608)
        for replacements, code in (({6:"'valuex'"},'54000'),({3:"decode('00','hex')",4:"decode('00','hex')"},'22023')):
            self.connection.run('SAVEPOINT aggregate')
            altered=args.copy()
            for index,value in replacements.items():altered[index]=value
            with self.assertRaises(DatabaseError) as caught:
                self.connection.run(statement+','.join(altered)+')')
            self.assertEqual(caught.exception.args[0]['C'],code)
            self.connection.run('ROLLBACK TO SAVEPOINT aggregate');self.connection.run('RELEASE SAVEPOINT aggregate')

    def test_old_and_new_string_token_correspondence_independently(self):
        from pg8000.exceptions import DatabaseError
        state,node=self._value(),self._node()
        bad=(b'"different"',b'123',b'null',b'{}',b'[]',b'"unterminated',b'\xff',b'"\\u0000"')
        for side in ('old','new'):
            for token in bad:
                scalar=self._scalar(**{'12':"decode('"+token.hex()+"','hex')"}) if side=='old' else self._scalar()
                new_source=token if side=='new' else b'"value"'
                args=[state,node,scalar,'truss.row_image_state_original('+state+')',
                    'truss.row_image_node_original('+node+')','truss.row_image_scalar_original('+scalar+')',
                    "'value'","decode('"+new_source.hex()+"','hex')"]
                self.connection.run('SAVEPOINT token_correspondence')
                with self.subTest(side=side,token=token),self.assertRaises(DatabaseError):
                    self.connection.run('SELECT * FROM truss.row_image_existing_string_candidate_original('+','.join(args)+')')
                self.connection.run('ROLLBACK TO SAVEPOINT token_correspondence')
                self.connection.run('RELEASE SAVEPOINT token_correspondence')

    def test_equivalent_escaped_originals_preserve_both_spellings(self):
        from truss._row_image import decode_row_image
        state,node=self._value(),self._node()
        old=b'  "v\\u0061lue"  ';new=b'\n"val\\u0075e"\t'
        scalar=self._scalar(**{'12':"decode('"+old.hex()+"','hex')"})
        args=[state,node,scalar,'truss.row_image_state_original('+state+')',
            'truss.row_image_node_original('+node+')','truss.row_image_scalar_original('+scalar+')',
            "'value'","decode('"+new.hex()+"','hex')"]
        row=self.connection.run('SELECT * FROM truss.row_image_existing_string_candidate_original('+','.join(args)+')')[0]
        self.assertEqual(bytes(decode_row_image(row[2]).payload(12)),old)
        self.assertEqual(bytes(decode_row_image(row[5]).payload(12)),new)
