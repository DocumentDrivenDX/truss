"""Selected original consumer authority variants through installed public APIs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

class OriginalConsumerReads(unittest.TestCase):
    def test_original_authority_queries(self):
        root=Path(__file__).resolve().parents[3]
        directory=Path(tempfile.mkdtemp(prefix='truss-original-consumer-',dir='/private/tmp'))
        result=subprocess.run([sys.executable,str(root/'packages/python/examples/run_consumer_reads.py'),
            str(root/'docs/helix/04-build/evidence/consumer-revision-2026-10-09/corpus.json'),str(directory),
            '--bun','/opt/homebrew/bin/bun'],check=False,capture_output=True,text=True,env=dict(os.environ))
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual([v['id'] for v in report['observations']],['read.missing-key-is-no-rows','read.columns-and-filters','read.relationship-filter-both-directions','read.key-lookup-whole-entity'])
        self.assertTrue(all(v['authority']=='passed' and v['replica']=='unavailable' for v in report['observations']))
        self.assertEqual(report['fixtureSync'],'committed original receipt included on authority')
        self.assertEqual(report['retainedExtensions'],4)
        shutil.rmtree(directory)
