#!/usr/bin/env python3
"""Replay selected owner controls; does not adopt or qualify a Truss runtime."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

REVISION = '953aa38c4be0748664d79633596be08cb47d2b41'
MEMBERS = ['src', 'spec', 'tests/core/javascript-numeric.test.ts', 'package.json',
           'native/tablespec/relationship-runtime/domain-base-types.json',
           'native/tablespec/sources/src/tablespec/schemas/umf.schema.json']


def main():
    if len(sys.argv) != 3:
        raise SystemExit('usage: replay-umf-numeric.py UMF_REPOSITORY NEW_RECEIPT_PATH')
    repo, destination = map(lambda value: Path(value).resolve(), sys.argv[1:])
    if destination.exists():
        raise SystemExit('refusing to replace an existing receipt')
    dependencies = repo / 'node_modules'
    if not dependencies.is_dir():
        raise SystemExit('cached dependencies unavailable; no automatic install')
    archive = subprocess.check_output(['git', 'archive', REVISION, *MEMBERS], cwd=repo)
    with tempfile.TemporaryDirectory(prefix='truss-umf-numeric-', dir='/private/tmp') as directory:
        root = Path(directory)
        sources = []
        with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
            for member in stream.getmembers():
                path = root / member.name
                if not path.resolve().is_relative_to(root):
                    raise SystemExit('archive path escapes source directory')
                if member.isdir():
                    path.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    data = stream.extractfile(member).read()
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                    sources.append({'path': member.name, 'sha256': hashlib.sha256(data).hexdigest()})
                else:
                    raise SystemExit('nonregular source archive member')
        (root / 'node_modules').symlink_to(dependencies, target_is_directory=True)
        command = ['bun', 'test', 'tests/core/javascript-numeric.test.ts']
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)
        output = result.stdout + result.stderr
        if result.returncode != 0 or '4 pass' not in output or '0 fail' not in output or '77 expect() calls' not in output:
            raise SystemExit(output)
        receipt = {
            'scope': 'Four owner numeric test groups on isolated committed source with cached dependencies; no browser/native/resource qualification or Truss adoption',
            'revision': REVISION, 'archiveSha256': hashlib.sha256(archive).hexdigest(),
            'archiveMembers': MEMBERS, 'sourceFiles': sources,
            'dependencyDirectory': str(dependencies), 'cleanDependencyResolution': False,
            'command': command, 'exitCode': result.returncode, 'output': output,
            'bunVersion': subprocess.check_output(['bun', '--version'], text=True).strip(),
            'producerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'runtimeAdopted': False, 'nativeQualified': False,
        }
        with destination.open('x') as stream:
            stream.write(json.dumps(receipt, indent=2) + '\n')
        print(json.dumps({'testGroups': 4, 'assertions': 77, 'runtimeAdopted': False}))


if __name__ == '__main__':
    main()
