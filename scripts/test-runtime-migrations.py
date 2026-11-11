#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Check that the installed package's fresh-install baseline installs and refuses older databases unchanged.

Runs the baseline unit and native test modules against the installed package; exits non-zero on failure.
"""
import argparse
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--installed-package',action='store_true')
args=parser.parse_args()
import truss
if args.installed_package and Path(truss.__file__).resolve().is_relative_to(ROOT/'packages/python/src'):
    raise SystemExit('Installed package required')
sys.path.insert(0,str(ROOT/'packages/python/tests'))
import test_current_baseline
import test_current_baseline_native
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromModule(module)
    for module in (test_current_baseline,test_current_baseline_native))
result=unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() and not result.skipped else 1)
