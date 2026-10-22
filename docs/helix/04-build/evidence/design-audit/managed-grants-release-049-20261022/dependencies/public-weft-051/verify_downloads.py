"""Verify actual public Weft51 bytes, declared build provenance and Truss cohorts."""
from pathlib import Path
import hashlib, importlib.util, json, shutil, zipfile
from released_runtime_validation import parse_sha256sums, verify_asset_checksum

base = Path(__file__).resolve().parent
root = base / 'all'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
api = json.loads(Path(str(base) + '.api.json').read_bytes())
tag = json.loads(Path(str(base) + '.tag.json').read_bytes())
pins = json.loads((root / 'release-pins.json').read_bytes())
assert api['tagName'] == 'v0.4.51' and not api['isDraft'] and api['publishedAt']
assets = {a['name']: a for a in api['assets']}
assert len(assets) == 9 and all(a['state'] == 'uploaded' for a in assets.values())
assert {p.name for p in root.iterdir()} == set(assets)
for name, asset in assets.items():
    assert asset['digest'] == 'sha256:' + digest(root / name), name
sums = parse_sha256sums((root / 'SHA256SUMS').read_text())
assert set(sums) == {name for name in assets if name.endswith('.whl')}
for name in sums:
    verify_asset_checksum(root / name, sums, label='public Weft SHA256SUMS')
expected_tag = 'd4b0b98507ae15bd98180a2ea2030ea92ce11d96'
freeze = '557153731e9f5d0583193a1189a07c6ed485d3d3'
assert tag['object']['type'] == 'commit' and tag['object']['sha'] == expected_tag
assert pins['commit'] == expected_tag and pins['packagingCommit'] == freeze
assert pins['version'] == '0.4.51' and pins['distribution'] == 'weft-sql'
producer = Path('/Users/erik/Projects/truss/scripts/verify-weft-release-wheel.py')
spec = importlib.util.spec_from_file_location('verify_weft_wheel', producer)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
rows = []
for wheel in sorted(root.glob('*.whl')):
    report = next(x for x in pins['wheelPackaging'] if x['wheel'] == wheel.name)
    assert report['status'] == 'passed' and report['sourceCommit'] == freeze
    assert report['wheelSha256'] == sums[wheel.name]
    with zipfile.ZipFile(wheel) as archive:
        verifier._verify_record(archive, archive.infolist())
        native = [n for n in archive.namelist() if n.startswith('weft/weft') and n.endswith('.so')]
        assert len(native) == 1
        native_sha = hashlib.sha256(archive.read(native[0])).hexdigest()
        assert native_sha == report['nativeModuleSha256']
    row = {'wheel': wheel.name, 'wheelSha256': sums[wheel.name],
           'nativeModuleSha256': native_sha, 'recordVerified': True,
           'sourceFreezeDeclaredByPublicPackaging': freeze, 'localNativeExecution': False}
    if 'macosx' in wheel.name or 'x86_64' in wheel.name:
        row['TrussCohortVerification'] = verifier.verify_wheel(wheel, base / 'expected-cohorts.py')
    else:
        row.update(TrussAdmitted=False, scope='packaging-only; no local platform execution')
    rows.append(row)
qualification = json.loads((root / 'local-macos-qualification.json').read_bytes())
assert qualification['status'] == 'passed' and qualification['sourceFreezeCommit'] == freeze
assert qualification['wheel']['sha256'] == 'e60e552f02c670b43a43111b08d26d6b415aaa9b9de42f241c37ad1d9fdd2487'
selected = base / 'selected'
selected.mkdir(exist_ok=False)
for path in root.iterdir():
    if path.name == 'SHA256SUMS' or (path.suffix == '.whl' and ('macosx' in path.name or 'x86_64' in path.name)):
        shutil.copyfile(path, selected / path.name)
receipt = {'passedPublicIntegrity': True, 'releaseUrl': api['url'], 'publishedAt': api['publishedAt'],
           'tagCommit': expected_tag, 'compilerSourceFreeze': freeze,
           'scope': 'All nine assets verified against public GitHub SHA256 digests. Three wheel checksums, ZIP/RECORD and native bytes verified. Only Mac ARM64 and Linux x86_64 match Truss cohorts; Linux aarch64 is packaging-only. No native qualification executed by this producer.',
           'assetSha256': {p.name: digest(p) for p in root.iterdir()}, 'wheels': rows,
           'packagingRun': 39830424802, 'publisherRun': 39838369924,
           'producerSha256': digest(Path(__file__)), 'wheelVerifierSha256': digest(producer),
           'sourceProvenance': 'Public pins/packaging reports declare the freeze; owner strict-build handoff establishes build provenance. Public tag separately resolved.',
           'initialInspection': 'Earlier tool-only format assertion expected SUMS to cover all assets and refused; actual provider SUMS covers wheels only. Original failure remains in tool output; no raw file was retained. No qualification result was represented as passed.'}
(base / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'passed': True, 'assets': len(assets), 'wheelRecords': len(rows), 'compilerSourceFreeze': freeze}))
