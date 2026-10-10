from dataclasses import FrozenInstanceError
import struct
import unittest
from truss._row_image import decode_row_image
from truss._row_event_attribution import attribute_row_event
from test_row_image import samples


def originals():
    values=dict(samples())
    return tuple(decode_row_image(values['complete-stored-'+kind]) for kind in ('state','node','scalar'))


def change(image,index,raw):
    cell=image.cells[index]
    return decode_row_image(image.original[:cell.offset-4]+struct.pack('!i',len(raw))+raw+image.original[cell.offset+(cell.length or 0):])


def attribute(event,old,new,before,after,**options):
    args=dict(maximum_images=10,maximum_bytes=100000);args.update(options)
    return attribute_row_event(event,old,new,before,after,**args)


class RowEventAttributionTests(unittest.TestCase):
    def test_all_three_images_insert_delete_and_same_owner_update(self):
        images=originals()
        for image in images:
            for event,old,new,before,after in [('INSERT',None,image,(),images),('DELETE',image,None,images,()),('UPDATE',image,image,images,images)]:
                result=attribute(event,old,new,before,after)
                self.assertEqual(len(result.touch_owners),1)
                owner=result.touch_owners[0]
                self.assertEqual((owner.kind,owner.owner_id,owner.discriminator_id,owner.property_owner_type_id,owner.property_id),('object','100','1','1','101'))
                self.assertIs(result.old_image,old);self.assertIs(result.new_image,new)
                with self.assertRaises(FrozenInstanceError):owner.owner_id='other'

    def test_update_preserves_both_old_new_associations(self):
        old=originals();new=tuple(change(image,0,struct.pack('!q',502)) for image in old)
        new=(change(new[0],2,struct.pack('!q',200)),*new[1:])
        result=attribute('UPDATE',old[2],new[2],old,new)
        self.assertEqual([v.owner_id for v in result.touch_owners],['100','200'])
        self.assertEqual(result.old_owner.owner_id,'100');self.assertEqual(result.new_owner.owner_id,'200')

    def test_missing_duplicate_and_changed_originals_refuse(self):
        images=originals();state,node,scalar=images
        for before in ((node,scalar),(state,scalar),(state,node),(state,node,scalar,state)):
            with self.assertRaises(ValueError):attribute('DELETE',scalar,None,before,())
        replacement=change(scalar,3,b'changed-original')
        with self.assertRaises(ValueError):attribute('DELETE',scalar,None,(state,node,replacement),())
        conflicting_node=change(node,0,struct.pack('!q',502))
        with self.assertRaises(ValueError):attribute('DELETE',scalar,None,(*images,conflicting_node),())
        foreign=change(state,0,struct.pack('!q',502))
        with self.assertRaises(ValueError):attribute('DELETE',scalar,None,(foreign,node,scalar),())
        mixed=change(state,4,struct.pack('!q',100))
        with self.assertRaises(ValueError):attribute('DELETE',scalar,None,(mixed,node,scalar),())

    def test_event_availability_bounds_and_kind_refusals(self):
        images=originals();state,node,scalar=images
        for event,old,new in [('INSERT',state,state),('DELETE',None,state),('UPDATE',state,None),('UPDATE',state,node),('OTHER',state,None)]:
            with self.assertRaises(ValueError):attribute(event,old,new,images,images)
        for options in ({'maximum_images':2},{'maximum_bytes':1},{'maximum_bytes':True}):
            with self.assertRaises(ValueError):attribute('DELETE',scalar,None,images,(),**options)
        with self.assertRaises(ValueError):attribute('DELETE',scalar,None,list(images),())
        exact=sum(len(image.original) for image in images)
        self.assertEqual(attribute('DELETE',scalar,None,images,(),maximum_images=3,maximum_bytes=exact).old_owner.owner_id,'100')


if __name__=='__main__':unittest.main()
