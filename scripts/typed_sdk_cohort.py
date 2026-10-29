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
from email.parser import Parser
from zipfile import ZipFile


def add_cohort_arguments(parser):
    for package in ('sdk','weft'):
        parser.add_argument('--'+package+'-wheel',type=Path)
        parser.add_argument('--'+package+'-wheel-sha256')
    parser.add_argument('--weft-distribution',choices=('weft-sql','umf-weft'),default='weft-sql')
    parser.add_argument('--consumer-wheel',type=Path)
    parser.add_argument('--consumer-wheel-sha256')
    parser.add_argument('--require-consumer',action='store_true',
        help='Require the actual installed Truss wheel and its declared extra pins')


def _distribution_name(value):
    return re.sub(r'[-_.]+','-',value).lower()


def _extra_requirement(metadata,extra,distribution):
    """Admit the selected exact single dependency/extra, never infer it from imports."""
    matches=[]
    for value in Parser().parsestr(metadata).get_all('Requires-Dist',[]):
        name=re.match(r'\s*([A-Za-z0-9_.-]+)',value)
        if name is None or _distribution_name(name.group(1))!=distribution:continue
        pin=re.fullmatch(r'''\s*([A-Za-z0-9_.-]+)\s*==\s*([A-Za-z0-9_.+!-]+)\s*;\s*extra\s*==\s*(['"])([^'"]+)\3\s*''',value)
        if pin is None or pin.group(4)!=extra:
            raise ValueError('Original consumer requires one exact selected extra dependency')
        matches.append(pin.group(2))
    if len(matches)!=1:raise ValueError('Original consumer extra dependency is missing or ambiguous')
    return matches[0]


def _one_weft_owner(selected):
    # Both distributions install import `weft`. A matching last-writer payload
    # does not make two installed metadata owners an unambiguous cohort.
    owners=[_distribution_name(d.metadata.get('Name','')) for d in importlib.metadata.distributions()
        if _distribution_name(d.metadata.get('Name','')) in ('weft-sql','umf-weft')]
    if owners!=[selected]:raise ValueError('Select exactly one original Weft distribution owner')


def _consumer_bindings(args,records):
    consumer=_installed_wheel(args.consumer_wheel,args.consumer_wheel_sha256,'truss','umf-truss')
    metadata=importlib.metadata.distribution('umf-truss').read_text('METADATA')
    if metadata is None:raise ValueError('Original installed Truss metadata required')
    pins={
        'sdk':('umf-access',_extra_requirement(metadata,'typed-sdk','umf-access')),
        'weft':('weft-sql',_extra_requirement(metadata,'query','weft-sql')),
    }
    for name,(distribution,version) in pins.items():
        actual=records[name]
        if _distribution_name(actual['distribution'])!=distribution or actual['version']!=version:
            raise ValueError('Installed SDK/compiler differs from actual consumer extra requirement')
    consumer['selectedExtras']={name:{'distribution':dist,'version':version}
        for name,(dist,version)in pins.items()}
    return consumer


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
    consumer=(getattr(args,'consumer_wheel',None),getattr(args,'consumer_wheel_sha256',None))
    required=getattr(args,'require_consumer',False)
    if all(value is None for value in selected):
        if required or any(value is not None for value in consumer):
            raise ValueError('Consumer qualification requires both SDK/compiler wheels and hashes')
        return None
    if any(value is None for value in selected):raise ValueError('Select both wheels and both SHA256 pins together')
    if (consumer[0] is None)!=(consumer[1] is None) or required and consumer[0] is None:
        raise ValueError('Select the original consumer wheel and SHA256 together')
    compiler_distribution=getattr(args,'weft_distribution','weft-sql')
    if compiler_distribution not in ('weft-sql','umf-weft'):raise ValueError('Explicit Weft distribution required')
    _one_weft_owner(compiler_distribution)
    records={name:_installed_wheel(path,digest,package,distribution) for name,path,digest,package,distribution in (
        ('sdk',args.sdk_wheel,args.sdk_wheel_sha256,'umf_access','umf_access'),
        ('weft',args.weft_wheel,args.weft_wheel_sha256,'weft',compiler_distribution))}
    original_consumer=_consumer_bindings(args,records) if consumer[0] is not None else None
    # CLI subprocesses use this interpreter/environment too; reject a cwd or
    # PYTHONPATH shadow instead of installing packages or rewriting lookup paths.
    probe=subprocess.run([sys.executable,'-c',
        'import json,umf_access,weft; print(json.dumps([umf_access.__file__,weft.__file__]))'],
        text=True,capture_output=True,check=True)
    if [str(Path(p).resolve()) for p in json.loads(probe.stdout)]!=[records[k]['importFile'] for k in ('sdk','weft')]:
        raise ValueError('CLI interpreter imports a different package cohort')
    return {'python':sys.executable,'packages':records,'consumer':original_consumer,
        'scope':'Exact installed wheel/dependency correspondence only; no native qualification'}
