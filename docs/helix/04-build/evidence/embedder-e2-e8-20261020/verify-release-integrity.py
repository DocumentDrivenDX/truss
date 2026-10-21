#!/usr/bin/env python3
"""Independently verify already downloaded Truss 0.0.44 release artifacts.

No network, installation, extraction or GitHub mutation. Source comparison uses
the pinned candidate whose tree the delivery pipeline compares to the merge.
"""
import argparse
import ast
import base64
import csv
from email.parser import BytesParser
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile
import tomllib
import zipfile

VERSION = '0.0.44'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe(name):
    stripped = name.rstrip('/')
    return (chr(0) not in stripped and bool(stripped) and not stripped.startswith('/') and '\\' not in stripped
            and '\0' not in stripped and all(p not in ('', '.', '..') for p in stripped.split('/')))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(raw):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'Duplicate JSON member: ' + key)
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique)


def metadata(raw, project):
    message = BytesParser().parsebytes(raw)
    for key, value in (('Name', 'truss-toolkit'), ('Version', VERSION),
                       ('Requires-Python', project['requires-python']),
                       ('License-Expression', project['license'])):
        require(message.get_all(key) == [value], f'Exact metadata {key} required')
    require(set(message.get_all('License-File', [])) == set(project['license-files']),
            'Declared license files differ')
    def canonical_requirement(value):
        value = re.sub(r'\s+', '', value).replace("'", '"')
        match = re.match(r'([A-Za-z0-9_.-]+)(.*)', value)
        require(match is not None, 'Malformed dependency metadata')
        return re.sub(r'[-_.]+', '-', match[1]).lower() + match[2]
    expected = [canonical_requirement(v) for v in project.get('dependencies', [])]
    for extra, values in project.get('optional-dependencies', {}).items():
        expected.extend(canonical_requirement(v + '; extra == "' + extra + '"') for v in values)
    actual = [canonical_requirement(v) for v in message.get_all('Requires-Dist', [])]
    require(sorted(actual) == sorted(expected), 'Dependency metadata differs from qualified pyproject')
    require(set(message.get_all('Provides-Extra', [])) == set(project['optional-dependencies']),
            'Optional dependency names differ')


def wheel_members(path):
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        require(len(names) == len(set(names)), 'Duplicate wheel members')
        require(all(safe(n) for n in names) and all(safe(i.orig_filename) for i in infos), 'Unsafe wheel path')
        require(all(not stat.S_ISLNK(i.external_attr >> 16) for i in infos), 'Wheel symlink')
        require(all(not i.flag_bits & 1 for i in infos), 'Encrypted wheel member')
        require(all(stat.S_IFMT(i.external_attr >> 16) in (0,stat.S_IFREG,stat.S_IFDIR) for i in infos), 'Wheel special member')
        payload = {i.filename: archive.read(i) for i in infos if not i.is_dir()}
    record = f'truss_toolkit-{VERSION}.dist-info/RECORD'
    require([n for n in payload if n.endswith('.dist-info/RECORD')] == [record], 'Exact wheel RECORD required')
    rows = {}
    for row in csv.reader(io.StringIO(payload[record].decode('utf-8'), newline=''), strict=True):
        require(len(row) == 3, 'Malformed RECORD row')
        name, checksum, size = row
        require(safe(name) and name not in rows, 'Unsafe or duplicate RECORD row')
        rows[name] = checksum, size
    require(set(rows) == set(payload), 'RECORD does not cover exact complete wheel payload')
    for name, (checksum, size) in rows.items():
        if name == record:
            require((checksum, size) == ('', ''), 'RECORD self row must be unhashed')
            continue
        algorithm, separator, value = checksum.partition('=')
        require(separator and algorithm in ('sha256', 'sha384', 'sha512'), 'Invalid RECORD hash')
        observed = base64.urlsafe_b64encode(hashlib.new(algorithm, payload[name]).digest()).rstrip(b'=').decode()
        require(value == observed, 'RECORD hash mismatch: ' + name)
        require(bool(re.fullmatch(r'0|[1-9][0-9]*', size)) and int(size) == len(payload[name]),
                'RECORD size mismatch: ' + name)
    return payload


def tar_members(raw):
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        infos = archive.getmembers()
        names = [i.name for i in infos]
        require(len(names) == len(set(names)), 'Duplicate tar members')
        require(all(safe(n) for n in names), 'Unsafe tar path')
        require(all(i.isfile() or i.isdir() for i in infos), 'Tar link or special member')
        return {i.name: archive.extractfile(i).read() for i in infos if i.isfile()}


def literal_assignment(raw, name):
    values = [n.value for n in ast.parse(raw).body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    require(len(values) == 1, 'Unique source assignment required: ' + name)
    return ast.literal_eval(values[0])


def verify(args):
    root, output = args.repo, args.delivery_dir
    merge = args.expected_commit
    require(type(merge) is str and re.fullmatch('[0-9a-f]{40}', merge), 'Exact merge SHA required')
    def git(*parts):
        return subprocess.check_output(['git', *parts], cwd=root)
    require(bool(re.fullmatch('[0-9a-f]{40}', args.qualified_ref)), 'Full qualified source SHA required')
    qualified = git('rev-parse', args.qualified_ref + '^{commit}').decode().strip()
    require(qualified == args.qualified_ref == merge, 'Full exact tagged source commit required')
    reference = tar_members(git('archive', '--format=tar', qualified, 'packages/python'))
    def source(path):
        return reference['packages/python/' + path]
    project = tomllib.loads(source('pyproject.toml').decode())['project']
    require(project['version'] == VERSION and project['name'] == 'truss-toolkit', 'Qualified project identity differs')

    sums = {}
    for line in (output / 'SHA256SUMS').read_text().splitlines():
        require(bool(re.fullmatch(r'[0-9a-f]{64}  [^/\\]+', line)), 'Malformed checksum line')
        checksum, name = line.split('  ', 1)
        require(safe(name) and name not in sums, 'Unsafe or duplicate checksum member')
        require(digest((output / name).read_bytes()) == checksum, 'Asset checksum mismatch: ' + name)
        sums[name] = checksum
    require(set(sums)=={p.name for p in output.iterdir()}-{'SHA256SUMS'}, 'Exact checksum asset inventory required')
    wheel_name = f'truss_toolkit-{VERSION}-py3-none-any.whl'
    sdist_name = f'truss_toolkit-{VERSION}.tar.gz'
    require({wheel_name, sdist_name, 'release-pins.json'} <= set(sums), 'Missing checksummed release assets')
    require(sorted(p.name for p in output.glob('*.whl')) == [wheel_name], 'One exact wheel filename required')
    require(sorted(p.name for p in output.glob('*.tar.gz')) == [sdist_name], 'One exact sdist filename required')

    wheel = wheel_members(output / wheel_name)
    dist_prefix=f'truss_toolkit-{VERSION}.dist-info/'
    expected_dist={dist_prefix+n for n in ('METADATA','WHEEL','RECORD','entry_points.txt','top_level.txt')}
    expected_dist.update(dist_prefix+'licenses/'+n for n in project['license-files'])
    require({n for n in wheel if not n.startswith('truss/')}==expected_dist, 'Unexpected executable wheel payload')
    import configparser
    entries=configparser.ConfigParser();entries.read_string(wheel[dist_prefix+'entry_points.txt'].decode())
    require(entries.sections()==['console_scripts'] and dict(entries['console_scripts'])==project['scripts'], 'Wheel entry points differ from source')
    require(wheel[dist_prefix+'top_level.txt']==b'truss\n', 'Wheel top-level package differs')
    wheel_metadata=BytesParser().parsebytes(wheel[dist_prefix+'WHEEL'])
    require(wheel_metadata.get_all('Wheel-Version')==['1.0'] and wheel_metadata.get_all('Root-Is-Purelib')==['true'] and wheel_metadata.get_all('Tag')==['py3-none-any'], 'Wheel compatibility metadata differs')
    metadata(wheel[f'truss_toolkit-{VERSION}.dist-info/METADATA'], project)
    expected_runtime = {p.removeprefix('packages/python/src/truss/'): data for p, data in reference.items()
                        if p.startswith('packages/python/src/truss/')}
    umf_licenses = sorted(p for p in expected_runtime if p.startswith('_umf/licenses/'))
    require(set(umf_licenses) == {'_umf/licenses/' + p + '.txt' for p in
            ('ajv', 'fast-deep-equal', 'fast-uri', 'json-schema-traverse', 'require-from-string', 'yaml')},
            'Complete six-file UMF dependency license inventory required')
    observed_runtime = {p.removeprefix('truss/'): data for p, data in wheel.items() if p.startswith('truss/')}
    require(observed_runtime == expected_runtime, 'Wheel runtime inventory/bytes differ from qualified source')
    for name in project['license-files']:
        require(wheel[f'truss_toolkit-{VERSION}.dist-info/licenses/{name}'] == source(name), 'Wheel license source differs')

    sdist = tar_members((output / sdist_name).read_bytes())
    prefix = f'truss_toolkit-{VERSION}/'
    require(all(p.startswith(prefix) for p in sdist), 'Unexpected sdist root')
    sdist = {p.removeprefix(prefix): value for p, value in sdist.items()}
    runtime_sdist = {p.removeprefix('src/truss/'): data for p, data in sdist.items() if p.startswith('src/truss/')}
    require(runtime_sdist == expected_runtime, 'Sdist runtime inventory/bytes differ from qualified source')
    for name in ('pyproject.toml', 'README.md', *project['license-files']):
        require(sdist[name] == source(name), 'Sdist source differs: ' + name)
    generated={'PKG-INFO','setup.cfg',*('src/truss_toolkit.egg-info/'+n for n in ('PKG-INFO','SOURCES.txt','dependency_links.txt','entry_points.txt','requires.txt','top_level.txt'))}
    for name,data in sdist.items():
        source_name='packages/python/'+name
        if source_name in reference:require(data==reference[source_name], 'Sdist source differs: '+name)
        else:require(name in generated, 'Unreviewed sdist installation payload: '+name)
    require(sdist['setup.cfg']==b'[egg_info]\ntag_build = \ntag_date = 0\n\n', 'Unreviewed generated setup configuration')
    require(sdist['src/truss_toolkit.egg-info/entry_points.txt']==wheel[dist_prefix+'entry_points.txt'], 'Sdist entry points differ')
    require(sdist['src/truss_toolkit.egg-info/top_level.txt']==b'truss\n', 'Sdist top-level package differs')
    metadata(sdist['src/truss_toolkit.egg-info/PKG-INFO'], project)
    metadata(sdist['PKG-INFO'], project)

    pins = read_json((output / 'release-pins.json').read_bytes())
    manifest_bytes = expected_runtime['_catalog_runtime/manifest.json']
    manifest = json.loads(manifest_bytes)
    policy_bytes = expected_runtime['_profiles/fresh-catalog-support-current010.json']
    policy = json.loads(policy_bytes)
    abi_bytes = expected_runtime['_catalog_runtime/query-abi.json']
    abi = json.loads(abi_bytes)
    profiles = json.loads(expected_runtime['_catalog_runtime/group-profiles.json'])['profiles']
    capabilities = json.loads(expected_runtime['_catalog_runtime/capability-profiles.json'])['profiles']
    compiler_source = literal_assignment(git('show', qualified + ':scripts/build-weft-runtime-python.py'), 'REVISION')
    backend = literal_assignment(expected_runtime['_query_runtime.py'], 'BACKEND')
    expected_pins = {
        'tag': 'v' + VERSION, 'commit': merge, 'distribution': 'truss-toolkit', 'version': VERSION,
        'runtime': manifest['releaseId'], 'runtimeManifestSha256': digest(manifest_bytes), 'layout': manifest['layoutProfile'],
        'weftRelease': 'v0.4.48', 'weftBackend': backend['backendVersion'], 'pgserver': 'pgserver-pg18==18.6.1',
        'pgserverRelease': 'pg18.6-pgv0.8.6-r2', 'psycopg': '3.3.6', 'deploymentJavaScript': 'embedded-v8',
        'embeddedEngine': 'mini-racer==0.14.1', 'externalJavaScriptRuntimeRequired': False,
        'nativePlatforms': ['linux-x86_64'],
        'catalogRegistrationReportInterface': 'truss-catalog-registration-report/0.6',
        'catalogPreparationInterface': 'truss-registration-preparation/2.0',
        'catalogAcceptanceInputInterface': 'truss-acceptance-input/0.2.0', 'catalogViewInterface': 'truss-catalog-view/0.2.0',
        'mandatoryPreparationTranscript': False, 'supportedUmfVersions': ['0.10.0'], 'installationUpgradesSupported': False,
        'timestampComparisonProfile': 'umf-rfc3339-exact-instant/1.0.0', 'umfExactInstantCommit': 'cbb6fb87',
        'umf010CatalogSupport': {'identity': policy['identity'], 'version': policy['version'], 'sha256': digest(policy_bytes)},
        'umf010CatalogReportInterface': 'truss-catalog-registration-report/0.6',
        'catalogSourceReferenceFormat': 'truss-catalog-source-reference/0.1',
        'catalogRebindReportInterface': 'truss-catalog-registration-report/0.6', 'catalogRebindProfile': 'truss-native-catalog-rebind/0.4',
        'catalogRebindSupportedProfiles': ['truss-native-catalog-rebind/' + v for v in ('0.1', '0.2', '0.3', '0.4')],
        'catalogKeyBackfillReportInterface': 'truss-catalog-registration-report/0.6', 'catalogKeyBackfillProfile': 'truss-catalog-key-backfill/0.2',
        'catalogKeyBackfillSupportedProfiles': ['truss-catalog-key-backfill/0.1', 'truss-catalog-key-backfill/0.2'],
        'currentQueryProfile': 'truss-current-query-protection/0.1-candidate',
        'currentQueryResultAbi': 'weft.postgresql.current-values/0.2-candidate', 'currentQueryMode': 'explicitly-activated-read-only',
        'currentQueryPlatforms': ['linux-x86_64'], 'currentQueryWeftSource': compiler_source,
        'mutationProfile': next(p['pin'] for p in profiles if p['name'] == 'mutationProfile'),
        'valueProfile': next(p['pin'] for p in profiles if p['name'] == 'valueProfile'),
        'objectReadProfiles': ['truss-python-scalar-object/0.4', 'truss-python-logical-object/0.1'],
        'logicalQueryAbi': {'identity': abi['identity'], 'version': abi['version'], 'sha256': digest(abi_bytes)},
        'compiledQueryCapability': next(p['pin'] for p in capabilities if p['name'] == 'weft_execution'),
        'catalogRegistrationSourceFormat': 'truss-registration-summary/2.0', 'catalogPreparationSummaryInterface': 'truss-registration-preparation/2.0',
    }
    require(json.dumps(pins, sort_keys=True) == json.dumps(expected_pins, sort_keys=True),
            'Release-pins schema/values differ: ' + repr(sorted(k for k in set(pins) | set(expected_pins) if pins.get(k) != expected_pins.get(k))))
    require((output / 'logical-query-abi.json').read_bytes() == abi_bytes, 'Published query ABI differs')
    for name in ('catalog-registration-summary-v0.1.md', 'catalog-rebind-report-v0.2.md', 'catalog-rebind-report-v0.4.md',
                 'catalog-source-reference-v0.1.md', 'catalog-key-backfill-report-v0.1.md'):
        require(name in sums and (output / name).read_bytes() == git('show', qualified + ':docs/helix/02-design/contracts/' + name),
                'Published contract differs: ' + name)
    return {'status': 'verified', 'version': VERSION, 'publicationCommit': merge, 'qualifiedSourceRef': qualified,
            'sourceBinding': 'Exact tagged source; public remote tag target independently checked before verification',
            'wheelSha256': sums[wheel_name], 'sdistSha256': sums[sdist_name], 'runtimeFiles': len(expected_runtime),
            'wheelRecordMembers': len(wheel), 'checksumAssets': len(sums), 'releasePinsExact': True,
            'wheelMetadataExact': True, 'wheelRecordComplete': True, 'sdistSourceCorrespondence': True,
            'umfLicenseFiles': umf_licenses}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery-dir', type=Path, default=Path('/private/tmp/truss-v0044-delivery'))
    parser.add_argument('--repo', type=Path, default=Path('/Users/erik/Projects/truss'))
    parser.add_argument('--expected-commit',required=True)
    parser.add_argument('--qualified-ref', required=True, help='full SHA of the exact qualified candidate')
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args), indent=2))
    except Exception as error:
        print(json.dumps({'status': 'refused', 'reason': str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
