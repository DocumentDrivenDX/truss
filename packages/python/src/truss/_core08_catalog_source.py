"""Private current-owner source observations; original 0.7 preparation unchanged."""
from dataclasses import dataclass,field
from hashlib import sha256
from importlib.resources import files
import json
import shutil
import subprocess
from ._core08_catalog_release import MANIFEST_SHA256
from .preparation import _capture,PreparationRejected
from .weft import _decode,CompileRefusal

@dataclass(frozen=True,slots=True)
class Core08CatalogSource:
    original_document:bytes
    original_response:bytes
    producer_manifest_sha256:str
    native_ready:bool=field(default=False,init=False)

def prepare_core08_catalog_source(original_document:bytes,*,document_id:str,document_revision:str,bun_executable:str='bun')->Core08CatalogSource:
    """Retain all original owner observations before native ingress integration.

    This artifact is not PreparedAcceptance, an accepted report, catalog authority
    or a source/role/issuer/physical mapping qualification.
    """
    _decode(original_document,4_000_000,'core08_source')
    try:valid=all(type(v) is str and v and '\0' not in v and len(v.encode('utf8'))<=4096 for v in (document_id,document_revision,bun_executable))
    except UnicodeError:valid=False
    if not valid:raise CompileRefusal('core08_input','Original bounded producer input required')
    root=files('truss').joinpath('_umf_core08');raw=root.joinpath('manifest.json').read_bytes()
    if sha256(raw).hexdigest()!=MANIFEST_SHA256:raise CompileRefusal('core08_producer','Original producer manifest required')
    manifest=json.loads(raw)
    for path,digest in manifest['files'].items():
        if sha256(root.joinpath(path).read_bytes()).hexdigest()!=digest:raise CompileRefusal('core08_producer','Original producer asset required')
    executable=shutil.which(bun_executable)
    if executable is None:raise CompileRefusal('core08_runtime','Qualified Bun runtime required')
    try:runtime=_capture([executable,'--version'],limit=4096,timeout=5)
    except (OSError,subprocess.TimeoutExpired,PreparationRejected) as error:
        raise CompileRefusal('core08_runtime','Qualified runtime capture unavailable') from error
    try:runtime_version=runtime.stdout.decode('ascii').strip()
    except UnicodeError as error:raise CompileRefusal('core08_runtime','Qualified runtime version unavailable') from error
    if runtime.returncode or runtime_version!=manifest['runtimeVersion']:raise CompileRefusal('core08_runtime','Qualified Bun runtime required')
    request=json.dumps({'documentId':document_id,'documentRevision':document_revision,'documentJson':original_document.decode('utf8')},ensure_ascii=False,separators=(',',':')).encode('utf8')
    if len(request)>8_000_000:raise CompileRefusal('core08_input','Original producer transport capacity exceeded')
    try:response=_capture([executable,str(root.joinpath('receiver.mjs'))],input_bytes=request,limit=16_000_000,timeout=30)
    except (OSError,subprocess.TimeoutExpired,PreparationRejected) as error:
        raise CompileRefusal('core08_producer','Original bounded producer capture unavailable') from error
    if response.returncode:raise CompileRefusal('core08_producer','Original completed owner response required')
    _,value=_decode(response.stdout,16_000_000,'core08_response')
    if (type(value) is not dict or value.get('status')!='prepared' or value.get('nativeReady') is not False
            or set(value)!={'interfaceVersion','status','nativeReady','documentId','documentRevision','sourceSha256','originalDocumentJson','observations'}
            or value['interfaceVersion']!='truss-core08-catalog-source/0.1.0'
            or value['documentId']!=document_id or value['documentRevision']!=document_revision
            or value['sourceSha256']!=sha256(original_document).hexdigest()
            or value['originalDocumentJson'].encode('utf8')!=original_document
            or type(value['observations']) is not list):
        raise CompileRefusal('core08_source','Complete original owner observations unavailable')
    return Core08CatalogSource(original_document,response.stdout,MANIFEST_SHA256)
