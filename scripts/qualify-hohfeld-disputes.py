#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Capture HF-01 probes. Test execution success does not close recorded defects."""
import argparse,hashlib,importlib.metadata,json,os,platform,sys,time,unittest
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--installed-package',action='store_true')
a=p.parse_args();root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'scripts'))
from publish_pypi_release import distribution_for_version
import tomllib
project=tomllib.loads((root/'packages/python/pyproject.toml').read_text())['project']
truss_distribution=distribution_for_version(project['version'])
sys.path.insert(0,str(root/'packages/python/tests'))
import truss
if a.installed_package:assert not Path(truss.__file__).resolve().is_relative_to(root/'packages/python/src')
a.output.parent.mkdir(parents=True,exist_ok=True)
os.environ['TRUSS_HF_OBSERVATIONS']=str(a.output.parent/'observations')
from test_hohfeld_disputes_native import HohfeldDisputesNativeTests
started=time.perf_counter();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HohfeldDisputesNativeTests))
files=sorted((a.output.parent/'observations').glob('*.json'));observations=[json.loads(f.read_text()) for f in files]
from importlib.resources import files as resources
record={'scope':'HF-01 public-artifact observation; probe execution is distinct from desired behavioral outcome','distribution':truss_distribution,'package':importlib.metadata.version(truss_distribution),'loadedPackage':truss.__file__,'platform':platform.platform(),'python':sys.version,'weft':importlib.metadata.version('weft-sql'),'nativeManifestSha256':hashlib.sha256(resources('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()).hexdigest(),'seconds':time.perf_counter()-started,'testsExecuted':result.testsRun,'probeFailures':len(result.failures),'probeErrors':len(result.errors),'skipped':len(result.skipped),'probeExecutionPassed':result.wasSuccessful(),'sourceCommit':os.environ.get('GITHUB_SHA'),'observations':[{'case':o['case'],'desiredOutcomeSatisfied':o['desiredOutcomeSatisfied'],'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f,o in zip(files,observations)],'producerSha256':{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in (Path(__file__),root/'packages/python/tests/test_hohfeld_disputes_native.py')}}
a.output.write_text(json.dumps(record,indent=2)+'\n');sys.exit(0 if result.wasSuccessful() and not result.skipped else 1)
