# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic wheel correspondence controls; no native runtime or installation."""
import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile
from typed_sdk_cohort import _installed_wheel

class InstalledWheelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);package=self.root/'cohort_fixture';package.mkdir()
        (package/'__init__.py').write_text('VALUE=1\n')
        metadata=self.root/'cohort_fixture-1.0.dist-info';metadata.mkdir()
        (metadata/'METADATA').write_text('Metadata-Version: 2.1\nName: cohort-fixture\nVersion: 1.0\n')
        self.wheel=self.root/'fixture.whl'
        with ZipFile(self.wheel,'w')as archive:
            for file in (package/'__init__.py',metadata/'METADATA'):archive.write(file,str(file.relative_to(self.root)))
        self.digest=hashlib.sha256(self.wheel.read_bytes()).hexdigest()
        sys.path.insert(0,str(self.root));importlib.invalidate_caches()
        self.addCleanup(sys.path.remove,str(self.root));self.addCleanup(sys.modules.pop,'cohort_fixture',None)
    def check(self,digest=None):
        return _installed_wheel(self.wheel,self.digest if digest is None else digest,'cohort_fixture','cohort-fixture')
    def test_exact_then_modified_payload(self):
        self.assertEqual(self.check()['packageFiles'],1)
        (self.root/'cohort_fixture'/'__init__.py').write_text('VALUE=2\n')
        with self.assertRaisesRegex(ValueError,'payload differs'):self.check()
    def test_wrong_archive_pin(self):
        with self.assertRaisesRegex(ValueError,'digest differs'):self.check('0'*64)
    def test_shadow_import(self):
        module=importlib.import_module('cohort_fixture');module.__file__=str(self.root/'elsewhere'/'__init__.py')
        with self.assertRaisesRegex(ValueError,'Imported package differs'):self.check()

if __name__=='__main__':unittest.main()
