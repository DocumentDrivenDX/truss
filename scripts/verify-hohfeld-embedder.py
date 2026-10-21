#!/usr/bin/env python3
# SPDX-License-Identifier: MIT OR Apache-2.0
"""Run the frozen Hohfeld corpus with strengthened expectations for delivered APIs.

Use an installed Truss wheel, Python-only PATH, and the git-archive consumer
snapshot. This never changes the consumer source or its corpus. The one removed
0.0.41 limit must first demonstrably pass the original complete business case.
"""
import argparse
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import version
from importlib.resources import files
import json
from pathlib import Path
import platform
import shutil
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer',required=True,type=Path)
    parser.add_argument('--consumer-commit',required=True)
    parser.add_argument('--wheel',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    if shutil.which('bun') or shutil.which('node'):
        parser.error('Run deployment qualification with Bun and Node absent from PATH')
    sys.path[:0]=[str(args.consumer/'src'),str(args.consumer/'tests')]
    from hohfeld.conformance import run_corpus
    from truss_harness import Cluster,TrussHarness
    fixed='registry.register-checks-the-revision-it-was-planned-against'
    cluster=Cluster()
    try:
        original=run_corpus(lambda:TrussHarness(cluster),only=[fixed])
        if (len(original.results)!=1 or original.results[0].status!='failed'
            or not original.results[0].message.startswith('passes, so its limit (')):
            raise RuntimeError('The original complete registration case must pass before removing its stale limit: '+repr(original.results))
        prior_limit=asdict(TrussHarness.LIMITS[fixed])
        # Strengthen this one expectation from a documented refusal to all of the
        # original business-case assertions. Every other limit remains exact.
        del TrussHarness.LIMITS[fixed]
        report=run_corpus(lambda:TrussHarness(cluster))
    finally:
        cluster.close()
    payload={'consumerCommit':args.consumer_commit,'corpusVersion':report.corpus_version,
        'python':platform.python_version(),'platform':platform.system()+'-'+platform.machine(),
        'trussVersion':version('truss-toolkit'),'wheelSha256':sha256(args.wheel.read_bytes()).hexdigest(),
        'runtimeManifestSha256':sha256(files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()).hexdigest(),
        'externalJavaScriptRuntimeRequired':False,'strengthenedExpectations':{fixed:prior_limit},
        'originalLimitRemovalWitness':asdict(original.results[0]),'report':asdict(report)}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({'passed':report.passed,'counts':dict(Counter(r.status for r in report.results)),
        'skipped':len(report.skipped),'evidence':str(args.output)}))
    if not report.passed:
        print([(r.case,r.message) for r in report.failed])
        raise SystemExit(1)


if __name__=='__main__':main()
