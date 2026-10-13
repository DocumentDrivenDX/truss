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
        root=Path(__file__).resolve().parents[3]
        script=root/'packages/python/examples/run_corpus.py'
        case=root/'docs/helix/04-build/corpus/public-python/0.4/adopter-basic.json'
        directory=Path(tempfile.mkdtemp(prefix='truss-preview-case-',dir='/private/tmp'))
        # Preserve source state if execution or shutdown fails; never restart a failed run.
        result=subprocess.run([sys.executable,str(script),str(case),str(directory),'--bun','/opt/homebrew/bin/bun'],
            check=True,capture_output=True,text=True,env=dict(os.environ))
        report=json.loads(result.stdout)
        self.assertEqual(report['format'],'truss-public-python-preview/0.4')
        self.assertEqual(report['outcome'],'passed_preview')
        self.assertEqual(report['id'],'public-adopter-basic')
        self.assertEqual(len(report['observations']),sum(len(p['steps']) for p in json.loads(case.read_bytes())['phases']))
        shutil.rmtree(directory)
