"""Build the committed Weft wheel used by the public Truss PG18 runtime."""
import argparse
import io
import os
import sysconfig
from importlib.metadata import version
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tarfile
import tempfile
import tomllib

REVISION = 'ff3695af5ece9d386b3dcbf266cf23d632997733'


def check_wheel(wheel: Path, expected_version: str):
    """Check the actual native import, without using an installed Weft package."""
    with tempfile.TemporaryDirectory(prefix='truss-weft-import-') as target:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '--no-index',
                        '--no-deps', '--target', target, str(wheel)], check=True)
        subprocess.run([sys.executable, '-I', '-c', """
import importlib.metadata
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import weft
import weft.weft as native
root = Path(sys.argv[1]).resolve()
for module in (weft, native):
    if not Path(module.__file__).resolve().is_relative_to(root):
        raise RuntimeError('Weft imported outside the temporary wheel installation')
if weft.__version__ != sys.argv[2] or importlib.metadata.version('weft-sql') != sys.argv[2]:
    raise RuntimeError('Unexpected Weft wheel version')
for name in ('compile_truss_runtime_json', 'compile_truss_runtime_page_json', 'prepare_application_lineage'):
    if not callable(getattr(weft, name, None)):
        raise RuntimeError('Missing public Weft API: ' + name)
for name in ('native_request_json', 'lower_postgresql_current_rows_candidate_json'):
    if not callable(getattr(getattr(native, 'CurrentQueryPreparation', None), name, None)):
        raise RuntimeError('Missing original Weft current-query API: ' + name)
""", target, expected_version], check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path, help='Local DocumentDrivenDX/weft clone containing the pinned commit')
    parser.add_argument('output', type=Path, help='New or empty build directory')
    parser.add_argument('--offline', action='store_true', help='Require already cached Cargo dependencies')
    parser.add_argument('--profile', choices=('release', 'dev'), default='release',
                        help='Explicit Cargo build profile; no automatic fallback')
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error('Build directory must be new or empty')
    archive = subprocess.check_output(['git', '-C', str(args.repository.resolve()), 'archive', REVISION])
    output.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tree:
        for member in tree.getmembers():
            if member.name.startswith('/') or '..' in PurePosixPath(member.name).parts or not (member.isfile() or member.isdir()):
                raise ValueError('Unsafe committed source archive member')
        tree.extractall(output)
    if version('maturin') != '1.9.6':
        raise RuntimeError('Install maturin==1.9.6 in the caller Python environment')
    maturin = Path(sysconfig.get_path('scripts')) / ('maturin.exe' if os.name == 'nt' else 'maturin')
    command = [str(maturin), 'build', '--manifest-path', 'crates/weft-python/Cargo.toml',
               '--locked', '--features', 'truss-postgresql-pg18,current-postgresql-scalar-candidate',
               '--interpreter', sys.executable, '--out', str(output / 'wheels')]
    if args.profile == 'release':
        command.append('--release')
    if args.offline:
        command.append('--offline')
    subprocess.run(command, cwd=output, check=True)
    wheels = list((output / 'wheels').glob('*.whl'))
    if len(wheels) != 1:
        raise RuntimeError('Expected one Weft Python wheel')
    expected_version = tomllib.loads((output / 'crates/weft-python/pyproject.toml').read_text())['project']['version']
    check_wheel(wheels[0], expected_version)
    print(f'Weft source: {REVISION}\nProfile: {args.profile}\nWheel: {wheels[0]}\nNative import and public API availability: passed')


if __name__ == '__main__':
    main()
