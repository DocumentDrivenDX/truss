# SPDX-License-Identifier: MIT OR Apache-2.0
"""Load only an enrolled temporal owner binding; no ambient-version adoption."""
from hashlib import sha256
from importlib import metadata
from importlib.resources import files
from pathlib import Path

from ._owner_evidence_json import decode_owner_evidence_json

CHECKERS=('check_engine_temporal_read_shape_json','check_engine_temporal_page_shape_json',
          'check_engine_temporal_read_json','check_engine_temporal_page_json')


def compiler():
    try:
        raw=files('truss').joinpath('_temporal_owner/compiler.json').read_bytes()
        from .catalog_runtime import _release
        release,_,_=_release()
        if release['files'].get('../_temporal_owner/compiler.json')!=sha256(raw).hexdigest():return None
        manifest=decode_owner_evidence_json(raw)
        if (set(manifest)!={'distribution','version','sourceCommit','installedFiles','checkers'}
                or manifest['distribution']!='umf-weft' or tuple(manifest['checkers'])!=CHECKERS
                or type(manifest['sourceCommit']) is not str or len(manifest['sourceCommit'])!=40
                or any(c not in '0123456789abcdef' for c in manifest['sourceCommit'])
                or metadata.version(manifest['distribution'])!=manifest['version']):return None
        import weft as owner
        from weft import weft as native
        root=Path(owner.__file__).resolve().parent
        expected=manifest['installedFiles']
        if type(expected) is not dict or not expected:return None
        paths={}
        for name,digest in expected.items():
            if type(name) is not str or Path(name).is_absolute() or '..' in Path(name).parts:return None
            path=(root/name).resolve()
            if not path.is_relative_to(root) or sha256(path.read_bytes()).hexdigest()!=digest:return None
            paths[path]=digest
        if Path(owner.__file__).resolve() not in paths or Path(native.__file__).resolve() not in paths:return None
        for name in CHECKERS:
            operation=getattr(owner,name,None)
            if not callable(operation):return None
            module_name=getattr(operation,'__module__',None)
            if (module_name not in ('weft','weft.weft') or getattr(operation,'__name__',None)!=name
                    or getattr(native,name,None) is not operation):return None
        return owner
    except (ImportError,FileNotFoundError,ValueError,TypeError,KeyError,AttributeError,OSError):
        return None
