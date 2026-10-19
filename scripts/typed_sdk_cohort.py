# SPDX-License-Identifier: MIT OR Apache-2.0
"""Optional installed-wheel correspondence for the two native SDK runners."""
import hashlib
import importlib
import importlib.metadata
import json
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys
from zipfile import ZipFile


def add_cohort_arguments(parser):
    for package in ('sdk','weft'):
        parser.add_argument('--'+package+'-wheel',type=Path)
        parser.add_argument('--'+package+'-wheel-sha256')


def _installed_wheel(path,expected,package,distribution):
    if type(expected) is not str or re.fullmatch('[0-9a-f]{64}',expected) is None:
        raise ValueError('Exact lowercase wheel SHA256 required')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Selected wheel digest differs')
    installed=importlib.metadata.distribution(distribution)
    root=Path(installed.locate_file(package)).resolve()
    module=importlib.import_module(package)
    if Path(module.__file__).resolve().parent!=root:
        raise ValueError('Imported package differs from installed distribution')
    with ZipFile(BytesIO(raw)) as wheel:
        names=wheel.namelist()
        if len(names)!=len(set(names)):raise ValueError('Duplicate wheel member')
        payload={n:wheel.read(n) for n in names if n.startswith(package+'/') and not n.endswith('/')}
        metadata=[n for n in names if n.endswith('.dist-info/METADATA')]
        if not payload or len(metadata)!=1:raise ValueError('One original wheel distribution required')
        if installed.read_text('METADATA')!=wheel.read(metadata[0]).decode('utf8'):
            raise ValueError('Installed distribution metadata differs')
    actual={package+'/'+str(p.relative_to(root)).replace('\\','/'):p for p in root.rglob('*')
        if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
    if set(actual)!=set(payload):raise ValueError('Installed package file inventory differs')
    for name,body in payload.items():
        if actual[name].read_bytes()!=body:raise ValueError('Installed package payload differs: '+name)
    return {'distribution':installed.metadata['Name'],'version':installed.version,'wheel':str(path.resolve()),
        'wheelSha256':expected,'packageRoot':str(root),'importFile':str(Path(module.__file__).resolve()),
        'packageFiles':len(payload),'moduleVersion':getattr(module,'__version__',None)}


def verify_cohort(args):
    selected=(args.sdk_wheel,args.sdk_wheel_sha256,args.weft_wheel,args.weft_wheel_sha256)
    if all(value is None for value in selected):return None
    if any(value is None for value in selected):raise ValueError('Select both wheels and both SHA256 pins together')
    records={name:_installed_wheel(path,digest,package,distribution) for name,path,digest,package,distribution in (
        ('sdk',args.sdk_wheel,args.sdk_wheel_sha256,'umf_access','umf_access'),
        ('weft',args.weft_wheel,args.weft_wheel_sha256,'weft','weft-sql'))}
    # CLI subprocesses use this interpreter/environment too; reject a cwd or
    # PYTHONPATH shadow instead of installing packages or rewriting lookup paths.
    probe=subprocess.run([sys.executable,'-c',
        'import json,umf_access,weft; print(json.dumps([umf_access.__file__,weft.__file__]))'],
        text=True,capture_output=True,check=True)
    if [str(Path(p).resolve()) for p in json.loads(probe.stdout)]!=[records[k]['importFile'] for k in ('sdk','weft')]:
        raise ValueError('CLI interpreter imports a different package cohort')
    return {'python':sys.executable,'packages':records,'scope':'Exact installed SDK/Weft wheel correspondence; no native qualification'}
