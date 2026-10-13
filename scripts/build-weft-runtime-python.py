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

REVISION = 'cadc252d4308fbab81b81fa47cc2348c2924f7eb'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path, help='Local DocumentDrivenDX/weft clone containing the pinned commit')
    parser.add_argument('output', type=Path, help='New or empty build directory')
    parser.add_argument('--offline', action='store_true', help='Require already cached Cargo dependencies')
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
               '--locked', '--release', '--features', 'truss-postgresql-pg18',
               '--interpreter', sys.executable, '--out', str(output / 'wheels')]
    if args.offline:
        command.append('--offline')
    subprocess.run(command, cwd=output, check=True)
    wheels = list((output / 'wheels').glob('*.whl'))
    if len(wheels) != 1:
        raise RuntimeError('Expected one Weft Python wheel')
    print(f'Weft source: {REVISION}\nWheel: {wheels[0]}')


if __name__ == '__main__':
    main()
