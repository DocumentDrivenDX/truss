import json,unittest
from hashlib import sha256
from unittest.mock import patch
from truss._installation_resources import ResourceEntry,decode_resource_index

class ResourceRegistrationPreflightTests(unittest.TestCase):
    def test_registered_count_and_bytes_refuse_before_index_parsing(self):
        raw=b'{"interface":"truss-python-resources/0.1.0","releaseId":"r","entries":[]}'
        a=ResourceEntry('a','a','initializer',2,'0'*64)
        b=ResourceEntry('b','b','archive',3,'1'*64)
        for entries,count,total in [((a,b),1,5),((a,b),2,4),((a,),1,1)]:
            with patch('json.loads') as parse:
                with self.subTest(entries=entries,count=count,total=total),self.assertRaises(ValueError):
                    decode_resource_index(raw,sha256(raw).hexdigest(),'r',entries,1000,count,total)
                parse.assert_not_called()
    def test_exact_combined_registration_limits_retain_full_membership(self):
        entries=(ResourceEntry('a','a','initializer',2,'0'*64),ResourceEntry('b','b','archive',3,'1'*64))
        raw=json.dumps({'interface':'truss-python-resources/0.1.0','releaseId':'r','entries':[{'id':e.id,'path':e.path,'role':e.role,'byteLength':e.byte_length,'sha256':e.sha256} for e in entries]}).encode()
        self.assertEqual(decode_resource_index(raw,sha256(raw).hexdigest(),'r',entries,len(raw),2,5),entries)
