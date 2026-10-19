# SPDX-License-Identifier: MIT OR Apache-2.0
"""Closed-function guard inventory; arbitrary callbacks keep their own guard."""
import re
import unittest
from importlib.resources import files
from truss.psycopg_host import _MANAGED_FUNCTIONS, _MANAGED_TABLE_FUNCTIONS

class ManagedFunctionInventoryTests(unittest.TestCase):
    def test_selected_functions_have_volatile_installed_source(self):
        root=files('truss').joinpath('_catalog_runtime')
        sources='\n'.join(p.read_text() for p in root.iterdir() if p.name.endswith('.sql'))
        for name in sorted(_MANAGED_FUNCTIONS | _MANAGED_TABLE_FUNCTIONS.keys()):
            with self.subTest(function=name):
                selected=re.search(r'CREATE(?: OR REPLACE)? FUNCTION truss\.'+re.escape(name)+r'\(.*?\bAS \$\$',sources,re.S)
                self.assertIsNotNone(selected)
                self.assertRegex(selected[0],r'\bVOLATILE\b')

if __name__=='__main__':unittest.main()
