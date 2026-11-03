# SPDX-License-Identifier: MIT OR Apache-2.0
"""Selected packaging identities; absent qualified bytes always refuse admission."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[1]
COHORT = Path(__file__).with_name('truss-release-cohort.json')


def load_cohort(path=COHORT, *, require_qualified=False):
    cohort = json.loads(Path(path).read_text())
    expected = {
        'truss': ('umf-truss', '0.0.56'),
        'weft': ('umf-weft', '0.4.57'),
        'access': ('umf_access', '0.1.0.dev10'),
        'core': ('umf-core', '0.10.8'),
    }
    if cohort.get('schema') != 'truss-release-cohort/1':
        raise ValueError('Unknown release cohort schema')
    for key, (distribution, version) in expected.items():
        if cohort.get(key) != dict(distribution=distribution, version=version):
            raise ValueError('Selected package identity differs: ' + key)
    qualified = cohort.get('qualified')
    if require_qualified or qualified is not None:
        if not isinstance(qualified, dict):
            raise ValueError('Qualified artifact identities deferred: coherent source/bytes not frozen')
        for field, length in (('coreSourceRevision', 40), ('weftSourceRevision', 40),
                              ('nativeManifestSha256', 64)):
            value = qualified.get(field)
            if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{%d}' % length, value) or set(value) == {'0'}:
                raise ValueError('Exact qualified identity required: ' + field)
        rows = qualified.get('compilerCohorts')
        if not isinstance(rows, list) or not rows:
            raise ValueError('Actual qualified compiler cohorts required')
        for row in rows:
            if row.get('platform') != 'linux-x86_64' or row.get('sourceRevision') != qualified['weftSourceRevision']:
                raise ValueError('Qualified Linux compiler source required')
            filename = row.get('wheelFilename')
            if not isinstance(filename, str) or not re.fullmatch(r'umf_weft-0\.4\.57-[A-Za-z0-9_.+-]+\.whl', filename):
                raise ValueError('Exact qualified compiler wheel filename required')
            for field in ('wheelSha256', 'nativeModuleSha256'):
                value = row.get(field)
                if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value) or set(value) == {'0'}:
                    raise ValueError('Exact qualified compiler digest required: ' + field)
        for field in ('wheelSha256', 'nativeModuleSha256', 'platform', 'wheelFilename'):
            if len({row[field] for row in rows}) != len(rows):
                raise ValueError('Ambiguous qualified compiler cohort')
    return cohort


def check_project(root=ROOT):
    cohort = load_cohort()
    project = tomllib.loads((root / 'packages/python/pyproject.toml').read_text())['project']
    if (project['name'], project['version']) != (cohort['truss']['distribution'], cohort['truss']['version']):
        raise ValueError('Truss project identity differs')
    for extra, owner in (('query', 'weft'), ('typed-sdk', 'access')):
        selected = cohort[owner]
        if project['optional-dependencies'][extra] != [selected['distribution'] + '==' + selected['version']]:
            raise ValueError('Exact selected extra required: ' + extra)
    return cohort


def refuse_legacy_weft():
    try:
        importlib.metadata.distribution('weft-sql')
    except importlib.metadata.PackageNotFoundError:
        return
    raise ValueError('Legacy weft-sql conflicts with selected umf-weft import weft')


def verify_installed():
    cohort = load_cohort()
    refuse_legacy_weft()
    for owner in ('truss', 'weft', 'access', 'core'):
        row = cohort[owner]
        if importlib.metadata.version(row['distribution']) != row['version']:
            raise ValueError('Installed selected package version differs: ' + owner)
    import weft
    import umf_access
    for module, owner in ((weft, 'weft'), (umf_access, 'access')):
        distribution = importlib.metadata.distribution(cohort[owner]['distribution'])
        package = 'weft' if owner == 'weft' else 'umf_access'
        expected = Path(distribution.locate_file(package)).resolve()
        if not Path(module.__file__).resolve().is_relative_to(expected):
            raise ValueError('Selected package import origin differs: ' + owner)
    if weft.__version__ != cohort['weft']['version']:
        raise ValueError('Weft runtime version differs')
    return cohort


def hf_profile(root=ROOT, *, installed=False):
    """Overlay only producer identity; never rewrite the frozen HF assertions."""
    cohort = load_cohort(require_qualified=True)
    profile = json.loads((root / 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
    qualified = cohort['qualified']
    if installed:
        from importlib.resources import files
        native_bytes = files('truss').joinpath('_catalog_runtime/manifest.json').read_bytes()
    else:
        native_bytes = (root / 'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes()
    actual = hashlib.sha256(native_bytes).hexdigest()
    if actual != qualified['nativeManifestSha256']:
        raise ValueError('Qualified native manifest differs from actual source')
    # Any producer change requires separate owner review and a real new producer
    # receipt. This overlay never regenerates or silently accepts changed hashes.
    for name, digest in profile['producers'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('Original HF producer changed: ' + name)
    profile.update(toolkitVersion=cohort['truss']['version'],
                   compilerVersion=cohort['weft']['version'],
                   nativeManifestSha256=qualified['nativeManifestSha256'],
                   compilerCohorts=qualified['compilerCohorts'])
    return profile


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qualified', action='store_true')
    args = parser.parse_args()
    check_project()
    print(json.dumps(load_cohort(require_qualified=args.qualified), indent=2))
