# SPDX-License-Identifier: MIT OR Apache-2.0
"""Basic wheel correspondence controls; no native runtime or installation."""
import hashlib
import importlib
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from zipfile import ZipFile
from typed_sdk_cohort import _installed_wheel,_extra_requirement,_one_weft_owner,_consumer_bindings,verify_cohort

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


class ConsumerCohortTests(unittest.TestCase):
    metadata=('Metadata-Version: 2.4\nName: umf-truss\nVersion: 0.0.52\n'
        'Requires-Dist: umf_access==0.1.0.dev8; extra == "typed-sdk"\n'
        'Requires-Dist: weft-sql==0.4.51; extra == "query"\n')
    def test_exact_extra_pin_and_normalized_distribution(self):
        self.assertEqual(_extra_requirement(self.metadata,'typed-sdk','umf-access'),'0.1.0.dev8')
        self.assertEqual(_extra_requirement(self.metadata,'query','weft-sql'),'0.4.51')
    def test_ambiguous_missing_or_nonexact_pin_refuses(self):
        bad=(self.metadata.replace('==0.1.0.dev8','>=0.1.0.dev8'),
            self.metadata.replace('extra == "typed-sdk"','extra == "other"'),
            self.metadata+'Requires-Dist: umf-access==0.1.0.dev8; extra == "typed-sdk"\n',
            self.metadata.replace('umf_access','other'))
        for metadata in bad:
            with self.subTest(metadata=metadata),self.assertRaises(ValueError):
                _extra_requirement(metadata,'typed-sdk','umf-access')
    def test_same_import_does_not_make_distribution_owners_interchangeable(self):
        for installed,selected,valid in ((['weft-sql'],'weft-sql',True),
                (['umf_weft'],'umf-weft',True),(['weft-sql','umf-weft'],'weft-sql',False),
                (['umf-weft'],'weft-sql',False),([], 'weft-sql',False),
                (['weft-sql','weft_sql'],'weft-sql',False)):
            values=[SimpleNamespace(metadata={'Name':name})for name in installed]
            with self.subTest(installed=installed),patch('typed_sdk_cohort.importlib.metadata.distributions',return_value=values):
                if valid:_one_weft_owner(selected)
                else:
                    with self.assertRaises(ValueError):_one_weft_owner(selected)
    def bindings(self,sdk='0.1.0.dev8',weft='0.4.51',weft_distribution='weft-sql'):
        args=SimpleNamespace(consumer_wheel=Path('original.whl'),consumer_wheel_sha256='a'*64)
        records={'sdk':{'distribution':'umf_access','version':sdk},
            'weft':{'distribution':weft_distribution,'version':weft}}
        original=SimpleNamespace(read_text=lambda _:self.metadata)
        with patch('typed_sdk_cohort._installed_wheel',return_value={'distribution':'umf-truss','version':'0.0.52'})as installed,patch('typed_sdk_cohort.importlib.metadata.distribution',return_value=original):
            result=_consumer_bindings(args,records)
            installed.assert_called_once_with(args.consumer_wheel,args.consumer_wheel_sha256,'truss','umf-truss')
            return result
    def test_actual_consumer_extra_requirements_bind_selected_wheels(self):
        result=self.bindings()
        self.assertEqual(result['selectedExtras']['sdk']['version'],'0.1.0.dev8')
        self.assertEqual(result['selectedExtras']['weft'],{'distribution':'weft-sql','version':'0.4.51'})
        for change in ({'sdk':'0.1.0.dev5'},{'weft':'0.4.56'},
                {'weft':'0.4.56','weft_distribution':'umf-weft'}):
            with self.subTest(change=change),self.assertRaises(ValueError):self.bindings(**change)
    def test_release_gate_cannot_omit_consumer_or_selected_wheels(self):
        args=SimpleNamespace(sdk_wheel=None,sdk_wheel_sha256=None,weft_wheel=None,
            weft_wheel_sha256=None,consumer_wheel=None,consumer_wheel_sha256=None,
            require_consumer=True)
        with self.assertRaises(ValueError):verify_cohort(args)
        args.require_consumer=False
        self.assertIsNone(verify_cohort(args))  # Historical opt-out grants no acceptance.
        args.consumer_wheel=Path('original.whl')
        with self.assertRaises(ValueError):verify_cohort(args)

if __name__=='__main__':unittest.main()
