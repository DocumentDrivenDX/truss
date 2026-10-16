from hashlib import sha256
import unittest
from truss._installation_archive import COLUMNS,compare_archive_rows

EXPECTED=(('bundle','original:bundle',b'original bundle'),('input','original:input',b'original input'))
def rows():return [(str(i), 'installation', role, identity, value, sha256(value).digest(),sha256(identity.encode()).digest()) for i,(role,identity,value) in enumerate(EXPECTED,1)]
def compare(values,**kw):return compare_archive_rows(COLUMNS,values,'installation',EXPECTED,kw.get('maximum_rows',10),kw.get('maximum_bytes',10000))
class ArchiveTests(unittest.TestCase):
 def test_complete_originals_retained_and_order_independent(self):
  original=rows();result=compare(list(reversed(original)));self.assertTrue(result.matches)
  self.assertIs(result.original_rows[0][4],original[1][4]);original.clear();self.assertEqual(len(result.original_rows),2)
 def test_missing_extra_duplicate_and_changed_are_mismatch(self):
  original=rows();self.assertFalse(compare(original[:1]).matches)
  duplicate=list(original[0]);duplicate[0]='3';self.assertFalse(compare([*original,duplicate]).matches)
  changed=list(original[0]);changed[4]=b'changed';changed[5]=sha256(changed[4]).digest();self.assertFalse(compare([changed,original[1]]).matches)
  extra=list(original[0]);extra[0]='3';extra[3]='extra';extra[6]=sha256(b'extra').digest();self.assertFalse(compare([*original,extra]).matches)
 def test_descriptor_bounds_ids_and_correspondence_refuse(self):
  for index,value in ((0,'0'),(0,'01'),(0,'9223372036854775808'),(1,'foreign'),(4,bytearray(b'x')),(5,b'x'*32),(6,b'x'*32)):
   original=rows();bad=list(original[0]);bad[index]=value
   with self.assertRaises(ValueError):compare([bad,original[1]])
  for kw in ({'maximum_rows':1},{'maximum_bytes':1},{'maximum_rows':True}):
   with self.assertRaises(ValueError):compare(rows(),**kw)
 def test_no_empty_absence_authority_or_duplicate_registration(self):
  self.assertFalse(compare([]).matches)
  with self.assertRaises(ValueError):compare_archive_rows(COLUMNS,rows(),'installation',EXPECTED+EXPECTED,10,10000)
