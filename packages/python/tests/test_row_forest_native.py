# SPDX-License-Identifier: MIT OR Apache-2.0
"""Physical retained-forest parity; no complete native scope authority."""
import json
from test_row_touch_observer_native import RowTouchObserverNativeTests, ROOT
from test_row_image_tree import sequence, originals, change, capture
from truss._row_image_tree import check_row_image_tree
import struct

class RowForestNativeTests(RowTouchObserverNativeTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        c=cls.Connection(**cls.kwargs)
        try:c.run((ROOT/'packages/postgresql/native/row-image/forest.sql').read_text())
        finally:c.close()

    def forest(self,images):
        wire=json.dumps(dict(interfaceVersion='truss-native-row-image-scope/0.1',
            images=[dict(kind=i.kind,imageHex=i.original.hex()) for i in images])).encode()
        return self.connection.run('SELECT truss.row_image_forest_original(:wire)',wire=wire)

    def test_positive_host_native_parity(self):
        state,node,scalar=originals()
        for images in ((),(state,node,scalar),sequence(),(state,change(node,7,b'null'))):
            check_row_image_tree(capture(images));self.forest(images)

    def test_disconnected_cycle_and_other_invalid_forests(self):
        from pg8000.exceptions import DatabaseError
        state,root,child,leaf=sequence()
        a=change(change(child,2,struct.pack('!q',802)),7,b'sequence')
        b=change(change(a,1,struct.pack('!q',802)),2,struct.pack('!q',801))
        cases=[(state,root,a,b),(state,root,change(child,2,struct.pack('!q',999)),leaf),
            (state,root,change(child,4,struct.pack('!q',1)),leaf),(state,root,child),
            (state,root,change(root,1,struct.pack('!q',802)))]
        for images in cases:
            with self.assertRaises(ValueError):check_row_image_tree(capture(images))
            with self.assertRaises(DatabaseError) as caught:self.forest(images)
            self.assertEqual(caught.exception.args[0]['C'],'22023')

    def test_fk_admitted_cycle_and_exact_rollback(self):
        from truss._row_image import decode_row_image
        from pg8000.exceptions import DatabaseError
        c=self.connection;c.run('BEGIN')
        try:
            # Administrative fixture isolates physical validation from admission.
            for table in ('row_home_state','row_home_node','row_home_scalar'):
                c.run(f'DROP TRIGGER runtime_row_touch_observe ON truss.{table}')
            c.run("SET LOCAL session_replication_role='replica'")
            state=self.state()
            c.run('INSERT INTO truss.row_home_state SELECT (truss.row_touch_state_from_image_original(:image)).*',image=state)
            c.run("INSERT INTO truss.row_home_node VALUES(1,10,NULL,'root',NULL,NULL,NULL,'sequence',decode('01','hex'),decode('02','hex'))")
            c.run("SET LOCAL session_replication_role='origin'")
            def images():
                rows=c.run("SELECT 'state',truss.row_image_state_original(s) FROM truss.row_home_state s UNION ALL SELECT 'node',truss.row_image_node_original(n) FROM truss.row_home_node n")
                return tuple(decode_row_image(bytes(raw)) for kind,raw in rows)
            original=images();self.forest(original)
            c.run('SAVEPOINT cycle_fixture')
            c.run('SET CONSTRAINTS ALL DEFERRED')
            c.run("INSERT INTO truss.row_home_node VALUES(1,801,802,'sequence',0,NULL,NULL,'sequence',decode('01','hex'),decode('02','hex')),(1,802,801,'sequence',0,NULL,NULL,'sequence',decode('01','hex'),decode('02','hex'))")
            c.run('SET CONSTRAINTS ALL IMMEDIATE')
            malformed=images()
            self.assertEqual(len(malformed),4)
            with self.assertRaises(ValueError):check_row_image_tree(capture(malformed))
            c.run('SAVEPOINT native_refusal')
            with self.assertRaises(DatabaseError) as caught:self.forest(malformed)
            self.assertEqual(caught.exception.args[0]['C'],'22023')
            c.run('ROLLBACK TO SAVEPOINT native_refusal')
            c.run('ROLLBACK TO SAVEPOINT cycle_fixture')
            self.assertEqual(sorted(i.original for i in images()),sorted(i.original for i in original))
        finally:c.run('ROLLBACK')

    def test_deep_chain_and_exact_image_boundary(self):
        from truss._row_image_capture import decode_row_image_capture,COLUMNS
        from pg8000.exceptions import DatabaseError
        state,node,scalar=originals();root=change(node,7,b'sequence')
        images=[state,root]
        parent=601
        for identity in range(1000,2022):
            child=change(change(change(change(change(node,1,struct.pack('!q',identity)),2,struct.pack('!q',parent)),3,b'sequence'),4,struct.pack('!q',0)),7,b'sequence')
            images.append(child);parent=identity
        original=decode_row_image_capture(COLUMNS,[(i.kind,i.original) for i in images],'SELECT','1024',1024,1000000)
        check_row_image_tree(original);self.forest(images)
        images.append(change(images[-1],1,struct.pack('!q',3000)))
        with self.assertRaises(DatabaseError) as caught:self.forest(images)
        self.assertEqual(caught.exception.args[0]['C'],'0A000')

    def test_nested_map_record_and_multiple_states(self):
        state,node,scalar=originals()
        root=change(node,7,b'record')
        def child(identity,parent,slot,kind,ordinal=None,key=None,field=None):
            from truss._row_image import decode_row_image
            values=dict(state_id=501,node_id=identity,parent_node_id=parent,slot_kind=slot,
                value_kind=kind,sequence_ordinal=ordinal,map_key=key,
                record_field_identity_bytes=None if field is None else '\\x'+field.hex(),
                definition_bytes='\\x01',source_bytes='\\x02')
            return decode_row_image(self.image('node',values))
        mapping=child(801,601,'record','map',field=b'field\x00full')
        seq=child(802,801,'map','sequence',key='literal/\u0001')
        null=child(803,802,'sequence','null',ordinal=0)
        images=(state,root,mapping,seq,null)
        check_row_image_tree(capture(images));self.forest(images)
        second_state=change(change(state,0,struct.pack('!q',502)),8,struct.pack('!q',900))
        second_root=change(change(change(node,0,struct.pack('!q',502)),1,struct.pack('!q',900)),7,b'structured')
        combined=(*images,second_state,second_root)
        check_row_image_tree(capture(combined));self.forest(combined)
        from pg8000.exceptions import DatabaseError
        cases=[(*images,child(804,601,'record','null',field=b'field\x00full')),
               (*images,child(804,801,'map','null',key='literal/\u0001')),
               (*images,child(804,803,'map','null',key='wrong-parent')),
               (*images,change(seq,2,struct.pack('!q',900)),second_state,second_root)]
        for invalid in cases:
            with self.assertRaises(ValueError):check_row_image_tree(capture(invalid))
            with self.assertRaises(DatabaseError) as caught:self.forest(invalid)
            self.assertEqual(caught.exception.args[0]['C'],'22023')
