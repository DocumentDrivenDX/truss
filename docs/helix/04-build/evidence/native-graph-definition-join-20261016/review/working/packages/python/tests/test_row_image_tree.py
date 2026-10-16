import struct
import unittest
from truss._row_image_capture import decode_row_image_capture,COLUMNS
from truss._row_image_tree import check_row_image_tree
from test_row_event_attribution import originals,change


def capture(images):return decode_row_image_capture(COLUMNS,[(i.kind,i.original) for i in images],'SELECT',str(len(images)),20,100000)

def sequence():
    state,node,scalar=originals();root=change(node,7,b'sequence')
    child=change(change(change(change(node,1,struct.pack('!q',801)),2,struct.pack('!q',601)),3,b'sequence'),4,struct.pack('!q',0))
    leaf=change(scalar,1,struct.pack('!q',801))
    return state,root,child,leaf

class RowImageTreeTests(unittest.TestCase):
    def test_scalar_null_and_empty_containers(self):
        state,node,scalar=originals();value=capture((state,node,scalar));self.assertIs(check_row_image_tree(value),value)
        for kind in (b'null',b'sequence',b'map',b'record',b'structured'):
            check_row_image_tree(capture((state,change(node,7,kind))))

    def test_contiguous_sequence_and_missing_payload(self):
        images=sequence();check_row_image_tree(capture(images))
        with self.assertRaisesRegex(ValueError,'row-image-tree:unavailable'):check_row_image_tree(capture(images[:-1]))
        with self.assertRaises(ValueError):check_row_image_tree(capture((images[0],images[1],change(images[2],4,struct.pack('!q',1)),images[3])))

    def test_orphan_cycle_and_extra_root(self):
        state,root,child,leaf=sequence()
        with self.assertRaises(ValueError):check_row_image_tree(capture((state,root,change(child,2,struct.pack('!q',999)),leaf)))
        a=change(change(child,2,struct.pack('!q',802)),7,b'sequence')
        b=change(change(a,1,struct.pack('!q',802)),2,struct.pack('!q',801))
        with self.assertRaises(ValueError):check_row_image_tree(capture((state,root,a,b)))
        with self.assertRaises(ValueError):check_row_image_tree(capture((state,root,change(root,1,struct.pack('!q',802)))))

    def test_wrong_parent_kind_and_container_payload(self):
        state,root,child,leaf=sequence()
        with self.assertRaises(ValueError):check_row_image_tree(capture((state,change(root,7,b'map'),child,leaf)))
        state,node,scalar=originals()
        with self.assertRaises(ValueError):check_row_image_tree(capture((state,change(node,7,b'null'),scalar)))

    def test_duplicate_child_slot_and_missing_state(self):
        state,root,child,leaf=sequence();second=change(child,1,struct.pack('!q',802));second_leaf=change(leaf,1,struct.pack('!q',802))
        with self.assertRaises(ValueError):check_row_image_tree(capture((state,root,child,leaf,second,second_leaf)))
        with self.assertRaises(ValueError):check_row_image_tree(capture((root,child,leaf)))
