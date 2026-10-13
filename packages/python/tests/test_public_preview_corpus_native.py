"""One installed-package execution of the portable JSON public preview case."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

class PublicPreviewCorpusTests(unittest.TestCase):
    def test_json_drives_public_preview(self):
        self.run_case('adopter-basic.json', 'public-adopter-basic')

    def test_exact_scalar_case(self):
        self.run_case('exact-scalars.json', 'public-exact-scalars')

    def run_case(self, filename, case_id):
        root=Path(__file__).resolve().parents[3]
        script=root/'packages/python/examples/run_corpus.py'
        case=root/'docs/helix/04-build/corpus/public-python/0.7'/filename
        directory=Path(tempfile.mkdtemp(prefix='truss-preview-case-',dir='/private/tmp'))
        # Preserve source state if execution or shutdown fails; never restart a failed run.
        result=subprocess.run([sys.executable,str(script),str(case),str(directory),'--bun','/opt/homebrew/bin/bun'],
            check=True,capture_output=True,text=True,env=dict(os.environ))
        report=json.loads(result.stdout)
        self.assertEqual(report['format'],'truss-public-python-preview/0.7')
        self.assertEqual(report['outcome'],'passed_preview')
        self.assertEqual(report['id'],case_id)
        self.assertEqual(len(report['observations']),sum(len(p['steps']) for p in json.loads(case.read_bytes())['phases']))
        shutil.rmtree(directory)
