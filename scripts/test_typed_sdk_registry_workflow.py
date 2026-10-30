# SPDX-License-Identifier: MIT OR Apache-2.0
"""Exercise the actual registry gate bodies with inert metadata/module fixtures."""
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


def step_python(name):
    text=(Path(__file__).resolve().parents[1]/'.github/workflows/publish-pypi.yml').read_text()
    block=text.split('- name: '+name,1)[1].split("<<'PY'\n",1)[1]
    lines=[]
    for line in block.splitlines():
        if line.strip()=='PY':break
        lines.append(line[10:])
    return compile('\n'.join(lines),name,'exec')


class RegistryExtraTests(unittest.TestCase):
    digest='1a21c1ddd59f6b23e9f0b33228280564af0e96bb4d13699b89616d5143e4fd23'

    def test_selection_preserves_historical_query_gate(self):
        for version,expected in [('0.0.50','query'),('0.0.51','query'),
                ('0.0.52','query,typed-sdk'),('0.1.0','query,typed-sdk')]:
            with self.subTest(version=version),tempfile.TemporaryDirectory()as directory:
                output=Path(directory)/'env'
                with patch.dict(os.environ,VERSION=version,GITHUB_ENV=str(output)):
                    exec(step_python('Select the versioned public consumer extras'),{})
                self.assertEqual(output.read_text(),'TRUSS_CONSUMER_EXTRAS='+expected+'\n')

    def consumer(self,*,typed=True,sdk_version='0.1.0.dev8',sdk_digest=None,owners=('weft-sql',)):
        version='0.0.52' if typed else '0.0.51'
        requirements=['weft-sql==0.4.51; extra == "query"',
            'umf_access=='+sdk_version+'; extra == "typed-sdk"']
        modules={name:types.ModuleType(name)for name in ('truss','truss.access','weft','umf_access')}
        modules['weft'].__version__='0.4.51'
        modules['truss.access'].TrussTarget=type('TrussTarget',(),{'__module__':'truss.access'})
        versions={'umf-truss':version,'weft-sql':'0.4.51','umf_access':sdk_version}
        item={'metadata':{'name':'umf_access'},'download_info':{
            'url':'https://files.pythonhosted.org/original.whl',
            'archive_info':{'hashes':{'sha256':self.digest if sdk_digest is None else sdk_digest}}}}
        with tempfile.TemporaryDirectory()as directory,patch.dict(sys.modules,modules),patch.dict(
                os.environ,VERSION=version,RUNNER_TEMP=directory,TRUSS_DISTRIBUTION='umf-truss',
                TRUSS_CONSUMER_EXTRAS='query,typed-sdk' if typed else 'query'),patch(
                'importlib.metadata.requires',return_value=requirements),patch(
                'importlib.metadata.version',side_effect=lambda name:versions[name]),patch(
                'importlib.metadata.distributions',return_value=[types.SimpleNamespace(metadata={'Name':name})for name in owners]):
            (Path(directory)/'pip-install-report.json').write_text(json.dumps({'install':[item] if typed else []}))
            exec(step_python('Install the published Truss consumer extras from PyPI only'),{})
            return json.loads((Path(directory)/'consumer-receipt.json').read_text())

    def test_exact_sdk_artifact_and_separate_query_owner(self):
        self.assertEqual(self.consumer()['typed_sdk']['sha256'],self.digest)
        self.assertNotIn('typed_sdk',self.consumer(typed=False))

    def test_changed_artifact_or_unqualified_sdk_fails(self):
        for change in ({'sdk_digest':'0'*64},{'sdk_version':'0.1.0.dev9'},
                {'owners':('weft-sql','umf-weft')},{'owners':('weft__sql','umf-weft')}):
            with self.subTest(change=change),self.assertRaises(AssertionError):self.consumer(**change)


if __name__=='__main__':unittest.main()
