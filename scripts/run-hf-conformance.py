#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run independently asserted HF cases against an exact installed Truss cohort.

Fixtures create isolated temporary local PostgreSQL clusters and synthetic data.
The archive's test producers include explicit administrative fault controls;
passing them is not authorization for those controls on an application database.
"""
import argparse,hashlib,importlib.metadata,json,os,platform,sys,time,unittest
from importlib.resources import files
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--installed-package',action='store_true');a=p.parse_args()
corpus=ROOT/'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json';profile=json.loads(corpus.read_bytes())
sys.path.insert(0,str(ROOT/'packages/python/tests'))
import truss,weft
if a.installed_package and Path(truss.__file__).resolve().is_relative_to(ROOT/'packages/python/src'):raise ValueError('Installed package required')
if importlib.metadata.version('truss-toolkit')!=profile['toolkitVersion'] or weft.__version__!=profile['compilerVersion']:raise ValueError('Exact selected package/compiler cohort required')
actual=hashlib.sha256(files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()).hexdigest()
if actual!=profile['nativeManifestSha256']:raise ValueError('Exact selected native profile required')
for name,digest in profile['producers'].items():
 if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('Original producer changed: '+name)
observations=[]
class Result(unittest.TextTestResult):
 def startTest(self,test):super().startTest(test);self.started=time.monotonic();self.status='passed'
 def addFailure(self,test,error):self.status='failed';super().addFailure(test,error)
 def addError(self,test,error):self.status='error';super().addError(test,error)
 def addSkip(self,test,reason):self.status='skipped';super().addSkip(test,reason)
 def stopTest(self,test):observations.append({'id':test.id(),'status':self.status,'seconds':time.monotonic()-self.started});super().stopTest(test)
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(case['test']) for case in profile['cases'])
started=time.monotonic();result=unittest.TextTestRunner(verbosity=2,resultclass=Result).run(suite)
record={'sourceCommit':os.environ.get('GITHUB_SHA'),'workflowRunId':os.environ.get('GITHUB_RUN_ID'),'profile':profile['profile'],'corpusSha256':hashlib.sha256(corpus.read_bytes()).hexdigest(),'toolkit':importlib.metadata.version('truss-toolkit'),'compiler':weft.__version__,'loadedPackage':truss.__file__,'nativeManifestSha256':actual,'platform':platform.platform(),'python':sys.version,'seconds':time.monotonic()-started,'tests':result.testsRun,'skipped':len(result.skipped),'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful() and not result.skipped and result.testsRun==len(profile['cases']),'cases':observations,'limits':profile['limits']}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(record,indent=2)+'\n');raise SystemExit(not record['passed'])
