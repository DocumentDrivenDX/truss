#!/usr/bin/env python3
"""Post-publication verifier for the exact public Truss 0.0.49 release.

Requires a complete Truss asset directory and selected-wheel capsules for the
public PostgreSQL and Weft releases. It is intentionally fail-closed and must
not be run before v0.0.49 is published.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import time
import venv
import zipfile

SOURCE_ROOT = Path(os.environ.get('TRUSS_RELEASE_SOURCE_ROOT', '/Users/erik/Projects/truss')).resolve()
TRUSS_TAG = 'v0.0.49'
TRUSS_REPO = 'DocumentDrivenDX/truss'
RUNTIME_REPO = 'DocumentDrivenDX/pgserver'
WEFT_REPO = 'DocumentDrivenDX/weft'

parse_sha256sums = None
sha256_file = None
verify_asset_checksum = None


def load_validation_helpers(root: Path):
    """Load checksum helpers from the exact resolved source root."""
    scripts = (root / 'scripts').resolve(strict=True)
    path = (scripts / 'released_runtime_validation.py').resolve(strict=True)
    if path.parent != scripts or not path.is_file():
        raise ValueError('Source-root released-runtime helper must be a regular file in scripts/')
    spec = importlib.util.spec_from_file_location('_truss_released_runtime_validation_049', path)
    if spec is None or spec.loader is None:
        raise ValueError('Cannot load source-root released-runtime helper')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if Path(module.__file__).resolve() != path:
        raise ValueError('Released-runtime helper provenance differs from the selected source root')
    return module


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def run_logged(record, output: Path, name: str, command: list[str], *, cwd: Path | None = None,
               env: dict[str, str] | None = None, timeout: int = 600) -> subprocess.CompletedProcess:
    log = output / f'{name}.log'
    if log.exists():
        raise FileExistsError(log)
    started = time.time()
    try:
        result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
        raw = result.stdout + result.stderr
        returncode = result.returncode
        timed_out = False
    except subprocess.TimeoutExpired as error:
        raw = (error.stdout or b'') + (error.stderr or b'')
        returncode = None
        timed_out = True
    log.write_bytes(raw)
    record['steps'].append({'name': name, 'command': command, 'cwd': str(cwd or Path.cwd()),
        'returncode': returncode, 'timedOut': timed_out, 'log': log.name, 'logSha256': digest(log),
        'seconds': time.time() - started})
    save(record, output)
    if timed_out or returncode:
        raise RuntimeError(f'{name} failed with exit {returncode}; timeout={timed_out}; see {log}')
    return result


def save(record: dict, output: Path) -> None:
    path = output / 'qualification.json'
    path.write_bytes(json_bytes(record))


def exact_capsule(directory: Path, api_names: set[str], label: str) -> tuple[dict[str, str], dict]:
    if not directory.is_dir():
        raise ValueError(f'{label} asset capsule directory is missing: {directory}')
    members = list(directory.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in members):
        raise ValueError(f'{label} capsule must contain only top-level regular files')
    actual_names = {path.name for path in members}
    if actual_names != api_names:
        raise ValueError(f'{label} capsule/API asset inventory differs: missing={sorted(api_names-actual_names)}, extra={sorted(actual_names-api_names)}')
    sums_path = directory / 'SHA256SUMS'
    if 'SHA256SUMS' not in actual_names:
        raise ValueError(f'{label} capsule has no public SHA256SUMS')
    entries = parse_sha256sums(sums_path.read_text(), label=f'{label} SHA256SUMS')
    expected_names = api_names - {'SHA256SUMS'}
    if set(entries) != expected_names:
        raise ValueError(f'{label} SHA256SUMS is not a complete exact asset inventory: missing={sorted(expected_names-set(entries))}, extra={sorted(set(entries)-expected_names)}')
    for name in sorted(expected_names):
        verify_asset_checksum(directory / name, entries, label=f'{label} SHA256SUMS')
    payload_digests = {name: digest(directory / name) for name in sorted(expected_names)}
    return entries, {'assetNames': sorted(actual_names), 'payloadNames': sorted(expected_names),
        'payloadSha256': payload_digests,
        'sha256SumsSha256': digest(sums_path), 'manifestEntries': len(entries)}


def selected_capsule(directory: Path, api_names: set[str], selected_names: set[str], label: str,
                     *, api_digests: dict[str, str] | None = None,
                     checksum_required_names: set[str] | None = None) -> tuple[dict[str, str], dict]:
    """Verify a deliberately bounded public capsule containing selected assets only."""
    if 'SHA256SUMS' not in api_names or not selected_names <= api_names - {'SHA256SUMS'}:
        raise ValueError(f'{label} selected assets are not all in the public API inventory')
    expected_names = selected_names | {'SHA256SUMS'}
    if not directory.is_dir():
        raise ValueError(f'{label} asset capsule directory is missing: {directory}')
    members = list(directory.iterdir())
    if any(path.is_symlink() or not path.is_file() for path in members):
        raise ValueError(f'{label} capsule must contain only top-level regular files')
    actual_names = {path.name for path in members}
    if actual_names != expected_names:
        raise ValueError(f'{label} selected capsule inventory differs: missing={sorted(expected_names-actual_names)}, extra={sorted(actual_names-expected_names)}')
    sums_path = directory / 'SHA256SUMS'
    entries = parse_sha256sums(sums_path.read_text(), label=f'{label} SHA256SUMS')
    expected_manifest_names = api_names - {'SHA256SUMS'}
    if not set(entries) <= expected_manifest_names:
        raise ValueError(f'{label} SHA256SUMS contains assets absent from the public API inventory: {sorted(set(entries)-expected_manifest_names)}')
    required_checksums = selected_names if checksum_required_names is None else checksum_required_names
    if not required_checksums <= selected_names or not required_checksums <= set(entries):
        raise ValueError(f'{label} SHA256SUMS omits required selected assets: {sorted(required_checksums-set(entries))}')
    for name in sorted(selected_names):
        if name in entries:
            verify_asset_checksum(directory / name, entries, label=f'{label} SHA256SUMS')
        if api_digests and name in api_digests and api_digests[name] != digest(directory / name):
            raise ValueError(f'{label} public API digest differs for selected asset {name}')
    if api_digests and 'SHA256SUMS' in api_digests and api_digests['SHA256SUMS'] != digest(sums_path):
        raise ValueError(f'{label} public API digest differs for SHA256SUMS')
    selected_entries = {name: entries[name] for name in required_checksums}
    payload_digests = {name: digest(directory / name) for name in sorted(selected_names)}
    return selected_entries, {'assetNames': sorted(actual_names), 'payloadNames': sorted(selected_names),
        'payloadSha256': payload_digests, 'checksumPayloadNames': sorted(required_checksums),
        'sha256SumsSha256': digest(sums_path), 'manifestEntries': len(entries), 'selectedEntries': len(selected_names),
        'manifestAssetNames': sorted(entries),
        'publicApiAssetNames': sorted(api_names), 'selectionIsComplete': True}


def github_release(repo: str, tag: str, output: Path, key: str) -> dict:
    command = ['gh', 'release', 'view', tag, '--repo', repo, '--json',
        'tagName,isDraft,publishedAt,assets', '--jq',
        '{tagName:.tagName,isDraft:.isDraft,publishedAt:.publishedAt,assets:[.assets[].name],assetDigests:([.assets[]|select(.digest != null)|{name:.name,digest:.digest}])}']
    run = subprocess.run(command, capture_output=True, timeout=60)
    (output / f'{key}-github-release.log').write_bytes(run.stdout + run.stderr)
    if run.returncode:
        raise RuntimeError(f'Cannot read public GitHub release {repo}@{tag}')
    info = json.loads(run.stdout)
    if info.get('tagName') != tag or info.get('isDraft') is not False or not info.get('publishedAt'):
        raise ValueError(f'{repo}@{tag} is not a published public release')
    names = info.get('assets')
    if not isinstance(names, list) or not names or len(names) != len(set(names)):
        raise ValueError(f'{repo}@{tag} has no unique public asset inventory')
    api_digests = {}
    for item in info.get('assetDigests', []):
        if not isinstance(item, dict) or not isinstance(item.get('name'), str) or item['name'] not in names:
            raise ValueError(f'{repo}@{tag} has malformed per-asset digest metadata')
        value = item.get('digest')
        if not isinstance(value, str) or not re.fullmatch(r'sha256:[0-9a-f]{64}', value):
            raise ValueError(f'{repo}@{tag} has malformed SHA-256 asset digest metadata')
        if item['name'] in api_digests:
            raise ValueError(f'{repo}@{tag} has duplicate per-asset digest metadata')
        api_digests[item['name']] = value.split(':', 1)[1]
    info['assetDigests'] = api_digests
    return info


def remote_tag_commit(remote: str, tag: str) -> str:
    result = subprocess.check_output(['git', 'ls-remote', remote,
        f'refs/tags/{tag}', f'refs/tags/{tag}^{{}}'], text=True)
    rows = {line.split()[1]: line.split()[0] for line in result.splitlines() if line.strip()}
    peeled = rows.get(f'refs/tags/{tag}^{{}}') or rows.get(f'refs/tags/{tag}')
    if not peeled:
        raise ValueError(f'Public source tag {tag} is unavailable at {remote}')
    return peeled


def safe_extract_hf(archive_path: Path, destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [entry.filename for entry in infos]
        if len(names) != len(set(names)):
            raise ValueError('HF archive contains duplicate paths')
        if any(not name or name.startswith('/') or '\\' in name or
               any(part in ('', '.', '..') for part in name.split('/')) for name in names):
            raise ValueError('HF archive contains an unsafe path')
        if 'conformance-manifest.json' not in names or 'README.md' not in names:
            raise ValueError('HF archive manifest or README is missing')
        manifest = json.loads(archive.read('conformance-manifest.json'))
        file_map = manifest.get('files')
        if not isinstance(file_map, dict) or set(names) != set(file_map) | {'conformance-manifest.json', 'README.md'}:
            raise ValueError('HF archive member set does not equal its complete manifest')
        for name, expected in file_map.items():
            if digest_bytes(archive.read(name)) != expected:
                raise ValueError(f'HF archive source digest mismatch: {name}')
        for entry in infos:
            mode = entry.external_attr >> 16
            if mode and (mode & 0o170000) not in (0, 0o100000):
                raise ValueError(f'HF archive contains non-regular file: {entry.filename}')
            target = destination / entry.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(entry.filename))
    return {'manifest': manifest, 'archiveSha256': digest(archive_path), 'memberCount': len(names),
        'manifestSha256': digest(destination / 'conformance-manifest.json')}


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def wheel_prefix_inventory(wheel_path: Path, prefix: str) -> dict[str, str]:
    with zipfile.ZipFile(wheel_path) as archive:
        rows = {name[len(prefix):]: digest_bytes(archive.read(name)) for name in archive.namelist()
            if name.startswith(prefix) and not name.endswith('/')}
    if not rows:
        raise ValueError(f'Wheel has no {prefix} payload: {wheel_path.name}')
    return rows


def select_wheel(directory: Path, expected_prefix: str, entries: dict[str, str], label: str,
                 *, exact_sha256: str | None = None, require_compatible: bool = True) -> Path:
    from pip._vendor.packaging.tags import sys_tags
    from pip._vendor.packaging.utils import parse_wheel_filename
    supported = set(sys_tags())
    candidates = sorted(path for path in directory.glob('*.whl')
        if path.name.startswith(expected_prefix) and
        (exact_sha256 is None or digest(path) == exact_sha256) and
        (not require_compatible or bool(parse_wheel_filename(path.name)[3] & supported)))
    if not candidates:
        raise ValueError(f'No checksum-pinned {label} wheel in the complete public capsule')
    if exact_sha256 is None and len(candidates) != 1:
        raise ValueError(f'Expected one platform-compatible {label} wheel, found {len(candidates)}')
    if exact_sha256 is not None and len(candidates) != 1:
        raise ValueError(f'Expected one {label} wheel matching the release pin')
    wheel = candidates[0]
    verify_asset_checksum(wheel, entries, label=f'{label} SHA256SUMS')
    return wheel


def api_wheel_name(api_names: set[str], expected_prefix: str, label: str,
                   *, compatible: bool = True) -> str:
    from pip._vendor.packaging.tags import sys_tags
    from pip._vendor.packaging.utils import parse_wheel_filename
    supported = set(sys_tags())
    candidates = []
    for name in sorted(api_names):
        if not name.startswith(expected_prefix) or not name.endswith('.whl'):
            continue
        if compatible and not (parse_wheel_filename(name)[3] & supported):
            continue
        candidates.append(name)
    if len(candidates) != 1:
        raise ValueError(f'Expected one {label} asset for selected platform, found {candidates}')
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truss-capsule', required=True, type=Path)
    parser.add_argument('--runtime-capsule', required=True, type=Path)
    parser.add_argument('--weft-capsule', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--source-root', type=Path, default=SOURCE_ROOT)
    args = parser.parse_args()
    root = args.source_root.resolve()
    validation = load_validation_helpers(root)
    global parse_sha256sums, sha256_file, verify_asset_checksum
    parse_sha256sums = validation.parse_sha256sums
    sha256_file = validation.sha256_file
    verify_asset_checksum = validation.verify_asset_checksum
    output = args.output.resolve()
    if not output.is_relative_to(Path('/private/tmp/truss-managed-grants-049')):
        raise ValueError('Use a fresh private /private/tmp/truss-managed-grants-049 output directory')
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,51}', output.name):
        raise ValueError('Output directory name must also be a valid fresh public-checker run id')
    output.mkdir(parents=True, exist_ok=False)
    record = {'scope': 'Actual published v0.0.49 assets; complete Truss API inventory; selected Mac PostgreSQL and Mac/Linux Weft public assets with complete SHA256SUMS coverage; Linux release pins checked against the Linux wheel; Mac ARM64 local install and HF62; actual Lakebase acceptance is not run.',
        'startedAt': time.time(), 'passed': False, 'actualLakebaseAcceptance': 'not_run', 'steps': [], 'errors': []}
    save(record, output)
    try:
        if sys.version_info[:2] != (3, 11):
            raise ValueError('Run with Python 3.11 for the published release cohort')
        if platform.system() != 'Darwin' or platform.machine().lower() not in ('arm64', 'aarch64'):
            raise ValueError('Local public release proof must run on the current Mac ARM64 host')
        truss_release = github_release(TRUSS_REPO, TRUSS_TAG, output, 'truss')
        record['githubReleases'] = {'truss': truss_release}
        save(record, output)
        pins_path = args.truss_capsule / 'release-pins.json'
        pins = json.loads(pins_path.read_bytes())
        truss_entries, truss_inventory = exact_capsule(args.truss_capsule, set(truss_release['assets']), 'Truss')
        with (output / 'truss-release-inventory.json').open('xb') as stream:
            stream.write(json_bytes(truss_release))
        shutil.copyfile(args.truss_capsule / 'SHA256SUMS', output / 'truss-SHA256SUMS')
        shutil.copyfile(pins_path, output / 'release-pins.json')
        record['publicAssetCapsules'] = {'truss': truss_inventory,
            'trussAssetSha256': {name: digest(args.truss_capsule / name) for name in sorted(truss_entries)},
            'releasePinsSha256': digest(pins_path)}
        save(record, output)
        profile_path = root / 'packages/python/src/truss/_profiles/local-postgres-runtime.json'
        runtime_profile = json.loads(profile_path.read_bytes())
        runtime_tag = runtime_profile['releaseTag']
        runtime_release = github_release(RUNTIME_REPO, runtime_tag, output, 'runtime')
        record['githubReleases']['runtime'] = runtime_release
        save(record, output)
        (output / 'runtime-release-inventory.json').write_bytes(json_bytes(runtime_release))
        weft_tag = pins['weftRelease']
        weft_release = github_release(WEFT_REPO, weft_tag, output, 'weft')
        record['githubReleases']['weft'] = weft_release
        save(record, output)
        (output / 'weft-release-inventory.json').write_bytes(json_bytes(weft_release))

        truss_asset_names = set(truss_release['assets'])
        if 'release-pins.json' not in truss_asset_names:
            raise ValueError('Published Truss capsule does not include release-pins.json')
        expected_commit = pins['commit']
        if pins.get('tag') != TRUSS_TAG or pins.get('distribution') != 'truss-toolkit' or pins.get('version') != '0.0.49':
            raise ValueError('Published release-pins do not identify Truss 0.0.49')
        local_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
        local_tag = subprocess.check_output(['git', 'rev-parse', f'{TRUSS_TAG}^{{commit}}'], cwd=root, text=True).strip()
        remote_tag = remote_tag_commit('https://github.com/DocumentDrivenDX/truss.git', TRUSS_TAG)
        if not (local_head == local_tag == remote_tag == expected_commit):
            raise ValueError('Local source HEAD, local tag, public tag and release-pins commit differ')
        if subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True):
            raise ValueError('Source checkout must be clean before public asset verification')
        tracked_inputs = ['packages/python/pyproject.toml', 'packages/python/src/truss/_profiles/local-postgres-runtime.json',
            'packages/python/src/truss/_catalog_runtime/manifest.json', 'packages/python/src/truss/_migrations/manifest.json',
            'packages/python/src/truss/_current_query_originals.py', 'scripts/check-released-runtime.py',
            'scripts/released_runtime_validation.py', 'scripts/native_fixture.py', 'scripts/run-python-test-module.py',
            'scripts/check-native-worker-fixtures.py', 'scripts/run-hf-conformance.py',
            'scripts/verify-weft-release-wheel.py']
        source_basis = {name: digest(root / name) for name in tracked_inputs}
        project_version = __import__('tomllib').loads((root / 'packages/python/pyproject.toml').read_text())['project']['version']
        if project_version != pins['version']:
            raise ValueError('Pinned package version does not equal tagged source version')

        runtime_manifest = json.loads((root / 'packages/python/src/truss/_catalog_runtime/manifest.json').read_bytes())
        runtime_profile_source = json.loads(profile_path.read_bytes())
        if pins.get('runtime') != runtime_manifest['releaseId'] or pins.get('runtimeManifestSha256') != digest(root / 'packages/python/src/truss/_catalog_runtime/manifest.json'):
            raise ValueError('Public release pins differ from selected Truss runtime manifest')
        if pins.get('pgserver') != f"{runtime_profile_source['distribution']}=={runtime_profile_source['distributionVersion']}" or pins.get('pgserverRelease') != runtime_profile_source['releaseTag']:
            raise ValueError('Public pgserver pins differ from the selected runtime profile')
        if pins.get('nativePlatforms') != ['linux-x86_64']:
            raise ValueError('Unexpected native platform support declaration')
        if not pins.get('weftRelease', '').startswith('v') or not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', pins['weftRelease']):
            raise ValueError('Malformed public Weft release pin')
        truss_wheel = select_wheel(args.truss_capsule, 'truss_toolkit-0.0.49-', truss_entries, 'Truss')
        if not truss_wheel.name.endswith('-py3-none-any.whl'):
            raise ValueError('Unexpected public Truss wheel filename')
        if pins.get('hfConformanceArchive') not in truss_entries:
            raise ValueError('HF conformance archive is not in the pinned public Truss assets')
        hf_archive = args.truss_capsule / pins['hfConformanceArchive']
        hf_tree = output / 'hf-standalone'
        hf_inventory = safe_extract_hf(hf_archive, hf_tree)
        hf_manifest = hf_inventory['manifest']
        if hf_manifest.get('toolkitVersion') != pins['version'] or hf_manifest.get('nativeManifestSha256') != pins['runtimeManifestSha256']:
            raise ValueError('Published HF archive targets a different toolkit/runtime cohort')
        if pins.get('hfConformanceProfile') != hf_manifest.get('profile') or pins.get('hfConformanceCorpusSha256') != hf_manifest.get('files', {}).get('docs/helix/03-test/fixtures/hohfeld-followup-0.1.json'):
            raise ValueError('Published HF archive/profile/corpus pins differ')
        corpus = json.loads((hf_tree / 'docs/helix/03-test/fixtures/hohfeld-followup-0.1.json').read_bytes())
        corpus_cases = corpus['cases']
        if len(corpus_cases) != 62 or pins.get('hfConformanceTests') != 62:
            raise ValueError('Published standalone corpus is not the exact 62-case HF profile')

        cohorts = corpus.get('compilerCohorts')
        if not isinstance(cohorts, list):
            raise ValueError('Published HF corpus has no explicit compiler cohorts')
        mac_cohorts = [item for item in cohorts if item.get('platform') == 'macos-arm64']
        linux_cohorts = [item for item in cohorts if item.get('platform') == 'linux-x86_64']
        if len(mac_cohorts) != 1 or len(linux_cohorts) != 1:
            raise ValueError('Published HF corpus must pin one Mac ARM64 and one Linux x86_64 compiler cohort')
        mac_cohort, linux_cohort = mac_cohorts[0], linux_cohorts[0]
        for cohort in (mac_cohort, linux_cohort):
            if not all(re.fullmatch(r'[0-9a-f]{64}', cohort.get(key, '')) for key in ('wheelSha256', 'nativeModuleSha256')):
                raise ValueError('Malformed published compiler cohort hashes')

        runtime_api_names = set(runtime_release['assets'])
        runtime_wheel_name = api_wheel_name(runtime_api_names,
            f"{runtime_profile_source['distribution'].replace('-', '_')}-{runtime_profile_source['distributionVersion']}-",
            'Mac ARM64 PostgreSQL runtime')
        runtime_entries, runtime_inventory = selected_capsule(args.runtime_capsule, runtime_api_names,
            {runtime_wheel_name}, 'PostgreSQL runtime', api_digests=runtime_release['assetDigests'])
        shutil.copyfile(args.runtime_capsule / 'SHA256SUMS', output / 'runtime-SHA256SUMS')
        record['publicAssetCapsules']['runtime'] = runtime_inventory
        record['publicAssetCapsules']['runtimeAssetSha256'] = runtime_inventory['payloadSha256']
        save(record, output)
        runtime_wheel = select_wheel(args.runtime_capsule, runtime_wheel_name.rsplit('-', 3)[0] + '-',
            runtime_entries, 'Mac ARM64 PostgreSQL runtime')
        if runtime_wheel.name != runtime_wheel_name:
            raise ValueError('Selected PostgreSQL runtime wheel differs from public API selection')
        from pip._vendor.packaging.utils import parse_wheel_filename
        runtime_tags = parse_wheel_filename(runtime_wheel.name)[3]
        if not any(tag.interpreter == 'cp311' and tag.platform == 'macosx_14_0_arm64' for tag in runtime_tags):
            raise ValueError('Selected PostgreSQL runtime wheel is not the published CPython 3.11 macOS 14 ARM64 build')

        weft_api_names = set(weft_release['assets'])
        mac_wheel_name = api_wheel_name(weft_api_names, 'weft_sql-', 'Mac ARM64 Weft')
        linux_candidates = [name for name in weft_api_names if name.startswith('weft_sql-') and name.endswith('.whl')]
        linux_candidates = [name for name in linux_candidates if any(
            tag.platform.endswith('x86_64') and tag.platform.split('_', 1)[0] in ('linux', 'manylinux', 'musllinux')
            for tag in parse_wheel_filename(name)[3])]
        if len(linux_candidates) != 1:
            raise ValueError(f'Expected one public Linux x86_64 Weft wheel asset, found {sorted(linux_candidates)}')
        linux_wheel_name = linux_candidates[0]
        weft_packaging_names = {
            'release-pins.json',
            'packaging-aarch64-apple-darwin.json',
            'packaging-x86_64-unknown-linux-gnu.json',
        }
        if not weft_packaging_names <= weft_api_names:
            raise ValueError('Public Weft release is missing its selected wheel provenance assets')
        selected_weft_wheels = {mac_wheel_name, linux_wheel_name}
        selected_weft_names = selected_weft_wheels | weft_packaging_names
        weft_entries, weft_inventory = selected_capsule(args.weft_capsule, weft_api_names,
            selected_weft_names, 'Weft compiler', api_digests=weft_release['assetDigests'],
            checksum_required_names=selected_weft_wheels)
        shutil.copyfile(args.weft_capsule / 'SHA256SUMS', output / 'weft-SHA256SUMS')
        record['publicAssetCapsules'].update(weft=weft_inventory,
            weftAssetSha256=weft_inventory['payloadSha256'])
        save(record, output)
        mac_wheel = select_wheel(args.weft_capsule, mac_wheel_name.rsplit('-', 3)[0] + '-',
            weft_entries, 'Mac ARM64 Weft', exact_sha256=mac_cohort['wheelSha256'])
        linux_wheel = select_wheel(args.weft_capsule, linux_wheel_name.rsplit('-', 3)[0] + '-',
            weft_entries, 'Linux x86_64 Weft', exact_sha256=pins['weftWheelSha256'], require_compatible=False)
        if (mac_wheel.name != mac_wheel_name or linux_wheel.name != linux_wheel_name or
            linux_cohort['wheelSha256'] != pins['weftWheelSha256']):
            raise ValueError('Published Linux Weft wheel differs from release-pins/HF Linux cohort')
        from pip._vendor.packaging.tags import sys_tags
        if not (parse_wheel_filename(mac_wheel.name)[3] & set(sys_tags())):
            raise ValueError('Selected Mac Weft wheel is not compatible with the current Python 3.11 host')

        weft_release_pins = json.loads((args.weft_capsule / 'release-pins.json').read_bytes())
        if (weft_release_pins.get('tag') != weft_tag or
            weft_release_pins.get('commit') != weft_release_pins.get('workflowCommit') or
            weft_release_pins.get('distribution') != 'weft-sql' or
            weft_release_pins.get('version') != corpus['compilerVersion']):
            raise ValueError('Public Weft release-pins do not identify the selected release and distribution')
        weft_source_commit = remote_tag_commit('https://github.com/DocumentDrivenDX/weft.git', weft_tag)
        if weft_release_pins['commit'] != weft_source_commit:
            raise ValueError('Public Weft release tag commit differs from release-pins commit')
        source_freeze = weft_release_pins.get('packagingCommit')
        if (not isinstance(source_freeze, str) or not re.fullmatch(r'[0-9a-f]{40}', source_freeze) or
            source_freeze != mac_cohort['sourceRevision'] or linux_cohort['sourceRevision'] != source_freeze or
            pins.get('weftSourceRevision') != source_freeze):
            raise ValueError('Published Weft packaging source freeze differs from Truss and HF compiler cohorts')
        wheel_packaging = weft_release_pins.get('wheelPackaging')
        if not isinstance(wheel_packaging, list):
            raise ValueError('Public Weft release-pins omit wheel packaging provenance')
        packaging_by_wheel = {item.get('wheel'): item for item in wheel_packaging if isinstance(item, dict)}
        for label, wheel, cohort in (('macos-arm64', mac_wheel, mac_cohort), ('linux-x86_64', linux_wheel, linux_cohort)):
            item = packaging_by_wheel.get(wheel.name)
            if not item or (item.get('status') != 'passed' or item.get('version') != corpus['compilerVersion'] or
                item.get('wheelSha256') != cohort['wheelSha256'] or
                item.get('nativeModuleSha256') != cohort['nativeModuleSha256'] or
                item.get('sourceCommit') != source_freeze):
                raise ValueError(f'Public Weft release-pins do not bind the selected {label} wheel to its cohort')
        for filename, wheel, cohort in (
            ('packaging-aarch64-apple-darwin.json', mac_wheel, mac_cohort),
            ('packaging-x86_64-unknown-linux-gnu.json', linux_wheel, linux_cohort),
        ):
            report = json.loads((args.weft_capsule / filename).read_bytes())
            if (report.get('status') != 'passed' or report.get('version') != corpus['compilerVersion'] or
                report.get('wheel') != wheel.name or report.get('wheelSha256') != cohort['wheelSha256'] or
                report.get('nativeModuleSha256') != cohort['nativeModuleSha256'] or
                report.get('sourceCommit') != source_freeze):
                raise ValueError(f'Public Weft packaging receipt does not bind {filename} to the selected cohort')
        for filename in sorted(weft_packaging_names):
            shutil.copyfile(args.weft_capsule / filename, output / f'weft-{filename}')

        source_cohorts = root / 'packages/python/src/truss/_current_query_originals.py'
        verified_cohorts = {}
        for label, wheel, cohort in (('macos-arm64', mac_wheel, mac_cohort), ('linux-x86_64', linux_wheel, linux_cohort)):
            verification_run = run_logged(record, output, f'verify-weft-public-wheel-{label}', [sys.executable,
                str(root / 'scripts/verify-weft-release-wheel.py'), str(wheel), '--source', str(source_cohorts)], cwd=root)
            verification = json.loads(verification_run.stdout)
            if (verification.get('wheelSha256') != cohort['wheelSha256'] or
                verification.get('nativeModuleSha256') != cohort['nativeModuleSha256']):
                raise ValueError(f'Public Weft {label} wheel/module differs from its frozen cohort')
            verified_cohorts[label] = verification
        if (verified_cohorts['linux-x86_64']['wheelSha256'] != pins['weftWheelSha256'] or
            verified_cohorts['linux-x86_64']['nativeModuleSha256'] != pins['weftNativeModuleSha256']):
            raise ValueError('Published Linux Weft compiler differs from Linux release pins')
        if (pins.get('weftSourceRevision') != mac_cohort['sourceRevision'] or
            linux_cohort['sourceRevision'] != mac_cohort['sourceRevision']):
            raise ValueError('HF compiler source revision differs from the release-pins source freeze')

        runtime_api = runtime_profile_source['repository'] + '/releases/download/' + runtime_tag + '/' + runtime_wheel.name
        runtime_sha = verify_asset_checksum(runtime_wheel, runtime_entries, label='runtime SHA256SUMS')
        truss_sha = verify_asset_checksum(truss_wheel, truss_entries, label='Truss SHA256SUMS')
        mac_weft_sha = verify_asset_checksum(mac_wheel, weft_entries, label='Weft SHA256SUMS')
        linux_weft_sha = verify_asset_checksum(linux_wheel, weft_entries, label='Weft SHA256SUMS')
        venv_path = output / 'public-venv'
        venv.EnvBuilder(with_pip=True, clear=False).create(venv_path)
        python = venv_path / 'bin/python'
        pip_common = [str(python), '-m', 'pip', 'install', '--only-binary=:all:']
        run_logged(record, output, 'install-public-runtime-direct-url', pip_common + ['--no-deps', runtime_api + '#sha256=' + runtime_sha], cwd=root)
        run_logged(record, output, 'install-exact-public-macos-arm64-weft-wheel', pip_common + ['--no-deps', str(mac_wheel)], cwd=root)
        extras = '[local,native,experimental-pg8000,query]'
        run_logged(record, output, 'install-public-truss-wheel-and-pinned-dependencies', pip_common + [str(truss_wheel) + extras], cwd=root, timeout=1200)
        run_logged(record, output, 'pip-check', [str(python), '-m', 'pip', 'check'], cwd=root)

        checker_id = 'mg49-public-' + output.name
        evidence_dir = root / 'docs/helix/04-build/evidence/design-audit' / checker_id
        if evidence_dir.exists():
            raise FileExistsError(evidence_dir)
        env = {**os.environ, 'PYTHONPATH': os.pathsep.join([str(root / 'scripts'), str(root / 'packages/python/tests')]),
            'GITHUB_SHA': expected_commit}
        payload_check = r'''import hashlib,importlib,importlib.metadata,json,sys,zipfile
from pathlib import Path
rows={}
for wheel,pkgname in ((Path(sys.argv[1]),'pgserver'),(Path(sys.argv[2]),'truss'),(Path(sys.argv[3]),'weft')):
 module=importlib.import_module(pkgname);loaded=Path(module.__file__).resolve().parent
 prefix=pkgname+'/'
 with zipfile.ZipFile(wheel) as z:expected={n[len(prefix):]:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist() if n.startswith(prefix) and not n.endswith('/')}
 actual={p.relative_to(loaded).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in loaded.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc','.pyo')}
 if expected!=actual:raise SystemExit('whole installed payload differs: '+pkgname)
 rows[pkgname]={'path':str(loaded),'files':len(actual),'payloadSha256':hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
import weft,weft.weft as native
from truss._runtime_profile import RUNTIME_DISTRIBUTION,RUNTIME_VERSION
from truss._current_query_originals import _actual_consumer
compiler_sha=hashlib.sha256(Path(native.__file__).read_bytes()).hexdigest();cohort=_actual_consumer()
if cohort['weftModuleSha256']!=compiler_sha:raise SystemExit('installed compiler cohort mismatch')
rows['identities']={'trussVersion':importlib.metadata.version('truss-toolkit'),'runtimeDistribution':RUNTIME_DISTRIBUTION,'runtimeVersion':importlib.metadata.version(RUNTIME_DISTRIBUTION),'selectedRuntimeVersion':RUNTIME_VERSION,'weftVersion':importlib.metadata.version('weft-sql'),'weftModulePath':native.__file__,'weftModuleSha256':compiler_sha,'weftCohort':cohort}
print(json.dumps(rows,sort_keys=True))'''
        inventory_result = run_logged(record, output, 'verify-installed-whole-wheel-payloads', [str(python), '-c', payload_check,
            str(runtime_wheel), str(truss_wheel), str(mac_wheel)], cwd=root, env=env)
        installed_identity = json.loads(inventory_result.stdout)
        if any(installed_identity[name]['files'] < 1 for name in ('pgserver', 'truss', 'weft')):
            raise ValueError('Installed wheel payload inventory was empty')
        if installed_identity['identities']['trussVersion'] != pins['version'] or installed_identity['identities']['runtimeVersion'] != runtime_profile_source['distributionVersion']:
            raise ValueError('Installed runtime package versions differ from public pins')
        if installed_identity['identities']['weftVersion'] != corpus['compilerVersion']:
            raise ValueError('Installed Weft distribution version differs from the published compiler cohort')
        if (installed_identity['identities']['weftModuleSha256'] != mac_cohort['nativeModuleSha256'] or
            installed_identity['identities']['weftCohort'].get('weftWheelSha256') != mac_cohort['wheelSha256'] or
            installed_identity['identities']['weftCohort'].get('weftRevision') != mac_cohort['sourceRevision']):
            raise ValueError('Installed native Weft module differs from the published Mac ARM64 HF cohort')

        checker_cmd = [str(python), str(root / 'scripts/check-released-runtime.py'), str(runtime_wheel), str(truss_wheel),
            str(args.runtime_capsule / 'SHA256SUMS'), '--run-id', checker_id,
            '--truss-checksums', str(args.truss_capsule / 'SHA256SUMS')]
        run_logged(record, output, 'check-released-runtime-public', checker_cmd, cwd=root, env=env, timeout=1800)
        checker_receipt_path = evidence_dir / 'receipt.json'
        if not checker_receipt_path.is_file():
            raise ValueError('Public runtime checker did not write its receipt')
        checker_receipt = json.loads(checker_receipt_path.read_bytes())
        if not checker_receipt.get('passed') or checker_receipt.get('lakebaseQualified') is not False:
            raise ValueError('Public runtime checker did not pass or claimed Lakebase')
        shutil.copyfile(checker_receipt_path, output / 'released-runtime-receipt.json')

        hf_output = output / 'hf-qualification.json'
        hf_cmd = [str(python), str(hf_tree / 'scripts/run-hf-conformance.py'), '--installed-package', '--output', str(hf_output)]
        hf_test_root = hf_tree / 'packages/python/tests'
        if not hf_test_root.is_dir() or not (hf_tree / 'scripts/run-hf-conformance.py').is_file():
            raise ValueError('Standalone HF archive is missing its own runner or test modules')
        missing_hf_modules = sorted({case['test'].split('.', 1)[0] + '.py' for case in corpus_cases
            if not (hf_test_root / (case['test'].split('.', 1)[0] + '.py')).is_file()})
        if missing_hf_modules:
            raise ValueError(f'Standalone HF archive is missing selected test modules: {missing_hf_modules}')
        hf_env = {key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}
        hf_env['GITHUB_SHA'] = expected_commit
        record['hfImportIsolation'] = {'PYTHONPATH': hf_env.get('PYTHONPATH'), 'workingDirectory': str(hf_tree),
            'runner': str(hf_tree / 'scripts/run-hf-conformance.py'), 'testRoot': str(hf_test_root),
            'allSelectedModulesPresent': True}
        save(record, output)
        run_logged(record, output, 'hf62-public-archive', hf_cmd, cwd=hf_tree, env=hf_env, timeout=2400)
        hf_result = json.loads(hf_output.read_bytes())
        if not (hf_result.get('passed') and hf_result.get('tests') == 62 and hf_result.get('skipped') == 0 and hf_result.get('failures') == 0 and hf_result.get('errors') == 0):
            raise ValueError('Standalone public HF62 corpus did not pass exactly')
        if hf_result.get('sourceCommit') != expected_commit or hf_result.get('nativeManifestSha256') != pins['runtimeManifestSha256']:
            raise ValueError('HF62 receipt does not match public tag/runtime manifest')
        if (hf_result.get('compilerSourceRevision') != mac_cohort['sourceRevision'] or
            hf_result.get('compilerNativeModuleSha256') != mac_cohort['nativeModuleSha256']):
            raise ValueError('HF62 receipt compiler is not the exact published Mac ARM64 compiler cohort')
        unchanged = {name: digest(root / name) for name in tracked_inputs} == source_basis
        if not unchanged or subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip() != expected_commit:
            raise ValueError('Pinned source inputs changed during public release verification')
        capsule_digests = {}
        for label, directory, entries, inventory in (('truss', args.truss_capsule, truss_entries, truss_inventory),
                                           ('runtime', args.runtime_capsule, runtime_entries, runtime_inventory),
                                           ('weft', args.weft_capsule, weft_entries, weft_inventory)):
            selected_names = inventory['payloadNames']
            capsule_digests[label] = {name: digest(directory / name) for name in selected_names}
            if any(capsule_digests[label][name] != inventory['payloadSha256'][name] for name in selected_names):
                raise ValueError(f'{label} public asset capsule changed during verification')
        if subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--'], cwd=root).returncode != 0:
            raise ValueError('Tracked source files changed during public release verification')
        status = subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root, text=True)
        permitted_prefix = f'?? docs/helix/04-build/evidence/design-audit/{checker_id}/'
        if any(line and not line.startswith(permitted_prefix) for line in status.splitlines()):
            raise ValueError('Unexpected source checkout changes during public release verification')
        record.update({'publicAssets': {'truss': truss_inventory, 'runtime': runtime_inventory, 'weft': weft_inventory},
            'publicAssetSha256': capsule_digests,
            'assetChecksums': {'trussSha256': truss_sha, 'runtimeSha256': runtime_sha,
                'macWeftSha256': mac_weft_sha, 'linuxWeftSha256': linux_weft_sha},
            'releasePinsSha256': digest(pins_path), 'sourceCommit': expected_commit,
            'localPlatform': 'macos-arm64', 'publishedNativePlatforms': pins['nativePlatforms'],
            'runtimeWheel': runtime_wheel.name, 'trussWheel': truss_wheel.name,
            'macWeftWheel': mac_wheel.name, 'macWeftVerification': verified_cohorts['macos-arm64'],
            'linuxWeftWheel': linux_wheel.name, 'linuxWeftVerification': verified_cohorts['linux-x86_64'],
            'publicWeftTagCommit': weft_source_commit,
            'weftSourceFreezeRevision': source_freeze,
            'runtimeDirectUrl': runtime_api, 'installedPayload': installed_identity,
            'releasedRuntimeReceipt': str(checker_receipt_path), 'releasedRuntimeReceiptSha256': digest(checker_receipt_path),
            'hfArchive': pins['hfConformanceArchive'], 'hfArchiveSha256': hf_inventory['archiveSha256'],
            'hfReceipt': str(hf_output), 'hfReceiptSha256': digest(hf_output), 'hfTests': hf_result['tests'],
            'actualLakebaseAcceptance': 'not_run', 'sourceInputBasis': source_basis,
            'inputsUnchanged': unchanged, 'passed': True})
    except Exception as error:
        record['errors'].append(repr(error))
        record['passed'] = False
        record['completedAt'] = time.time()
        save(record, output)
        raise
    record['completedAt'] = time.time()
    save(record, output)
    print(json.dumps({'passed': True, 'output': str(output), 'actualLakebaseAcceptance': 'not_run'}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
