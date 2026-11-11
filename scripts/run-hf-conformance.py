#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run the independently asserted HF cases against the installed Truss package.

Fixtures create isolated temporary local PostgreSQL clusters over Unix sockets with
synthetic data; no application database connection is accepted. Exits non-zero if any
case fails, errors or is skipped.
"""
import argparse,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
sys.path.insert(0,str(ROOT/'packages/python/tests'))
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--installed-package',action='store_true',help='require truss to be imported from site-packages, not this checkout')
a=p.parse_args()
import truss
if a.installed_package and Path(truss.__file__).resolve().is_relative_to(ROOT/'packages/python/src'):
 raise SystemExit('Installed package required')
corpus=json.loads((ROOT/'packages/python/tests/fixtures/spec/hohfeld-followup-0.1.json').read_bytes())
import conftest
quarantined={k.replace('.py::','.').replace('::','.') for k in conftest.QUARANTINED_TESTS}|set(conftest.QUARANTINED_MODULES)
cases=[c for c in corpus['cases'] if c['test'] not in quarantined and c['test'].split('.')[0] not in conftest.QUARANTINED_MODULES]
print('quarantined cases skipped:',len(corpus['cases'])-len(cases),'(see packages/python/tests/conftest.py)')
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(case['test']) for case in cases)
result=unittest.TextTestRunner(verbosity=2).run(suite)
ok=result.wasSuccessful() and not result.skipped and result.testsRun==len(cases)
print(json.dumps({'tests':result.testsRun,'cases':len(cases),'skipped':len(result.skipped),'failures':len(result.failures),'errors':len(result.errors),'passed':ok}))
raise SystemExit(0 if ok else 1)
