# SPDX-License-Identifier: MIT OR Apache-2.0
"""One basic test executes the exact documented public adopter program."""
import importlib.util
from pathlib import Path
import tempfile
import shutil
import unittest

class AdopterWorkflowTests(unittest.TestCase):
    def test_documented_public_workflow(self):
        example=Path(__file__).resolve().parents[1]/'examples/adopter_workflow.py'
        spec=importlib.util.spec_from_file_location('adopter_workflow',example)
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        directory=Path(tempfile.mkdtemp(prefix='truss-adopter-',dir='/private/tmp'))
        # A raised/unconfirmed runtime shutdown preserves its database for recovery.
        result=module.run_workflow(directory,bun_executable='/opt/homebrew/bin/bun')
        shutil.rmtree(directory)
        self.assertEqual({key:value for key,value in result.items() if key!='feed_transactions'},
            {'catalog':'accepted','mutation':'committed','replay':'committed','receipt':'included',
             'query':'relationship','dry_run':'rolled_back','import':'created','ack':'committed'})
        self.assertGreater(result['feed_transactions'],0)
