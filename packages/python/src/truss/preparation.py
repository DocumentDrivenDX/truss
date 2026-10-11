"""Public original UMF preparation. No catalog acceptance or database effects.

The bundled original JavaScript producer requires the release-pinned Bun runtime.
Returned bytes are the existing Truss AcceptanceInput wire, ready for subsequent
catalog admission; caller-selected installation/policy profiles are not verified.
"""
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import base64
import json
import shutil
import subprocess
import selectors
import tempfile
import time
import weakref
from ._umf_release import MANIFEST_SHA256
from ._acceptance_json import decode_acceptance_json

MAX_INPUT=1048576
MAX_OUTPUT=16777216

@dataclass(frozen=True,slots=True)
class CatalogDocument:
    document_id: str
    document_revision: str
    content: bytes
    artifact_identity: str | None = None

@dataclass(frozen=True,slots=True)
class DocumentInterpretation:
    document: CatalogDocument
    observation_bytes: bytes

    def observation(self) -> dict[str, object]:
        """Fresh copy of the complete original owner observation/diagnostics."""
        return json.loads(self.observation_bytes)

@dataclass(frozen=True,slots=True)
class PreparationProvenance:
    owner_revision: str
    owner_bundle_sha256: str
    acceptance_schema_sha256: str
    release_manifest_sha256: str
    runtime_version: str
    scope: str = 'original_umf_preparation_only'
    installation_profiles_verified: bool = False

@dataclass(frozen=True,slots=True,weakref_slot=True)
class PreparedAcceptance:
    input_bytes: bytes
    documents: tuple[DocumentInterpretation,...]
    declarations_bytes: bytes
    archive_documents_bytes: bytes
    provenance: PreparationProvenance

    def input(self) -> dict[str, object]:
        """Fresh AcceptanceInput dictionary; exact source remains in artifacts."""
        return json.loads(self.input_bytes)

# Producer provenance only: these private records grant no database authority.
_original_preparations = {}
def _snapshot(prepared):
    if (type(prepared) is not PreparedAcceptance
            or any(type(getattr(prepared,name)) is not bytes for name in
                   ('input_bytes','declarations_bytes','archive_documents_bytes'))
            or type(prepared.documents) is not tuple
            or type(prepared.provenance) is not PreparationProvenance):
        raise ValueError('Exact original preparation carrier required')
    for item in prepared.documents:
        if (type(item) is not DocumentInterpretation or type(item.document) is not CatalogDocument
                or type(item.observation_bytes) is not bytes
                or type(item.document.content) is not bytes
                or type(item.document.document_id) is not str
                or type(item.document.document_revision) is not str
                or (item.document.artifact_identity is not None and type(item.document.artifact_identity) is not str)):
            raise ValueError('Exact original document carrier required')
    for name in PreparationProvenance.__dataclass_fields__:
        expected=bool if name=='installation_profiles_verified' else str
        if type(getattr(prepared.provenance,name)) is not expected:
            raise ValueError('Exact original provenance carrier required')
    return (prepared.input_bytes, prepared.declarations_bytes,
            prepared.archive_documents_bytes,
            tuple((d.document.document_id, d.document.document_revision,
                   d.document.content, d.document.artifact_identity, d.observation_bytes)
                  for d in prepared.documents),
            tuple(getattr(prepared.provenance, name)
                  for name in PreparationProvenance.__dataclass_fields__))

def _retain_original(prepared):
    key = id(prepared)
    _original_preparations[key] = (weakref.ref(prepared, lambda ref: _original_preparations.pop(key, None)),
                                   _snapshot(prepared))
    return prepared

def _require_original_preparation(prepared):
    entry = _original_preparations.get(id(prepared))
    if (type(prepared) is not PreparedAcceptance or entry is None
            or entry[0]() is not prepared or entry[1] != _snapshot(prepared)):
        raise ValueError('Original unchanged UMF preparation required')

class PreparationRejected(ValueError):
    def __init__(self,reason: str,*,diagnostics: tuple[bytes, ...]=()) -> None:
        super().__init__('Truss preparation refused: '+reason)
        self.reason=reason
        self.diagnostics=diagnostics

def _reject(reason):raise PreparationRejected(reason)
def _text(value):
    if type(value) is not str or not 1<=len(value)<=4096 or '\0' in value:_reject('invalid_input')
    try:value.encode('utf8')
    except UnicodeError:_reject('invalid_input')

def _json(value):return json.dumps(value,ensure_ascii=True,separators=(',',':')).encode('utf8')

def _release():
    root=Path(__file__).parent/'_umf'
    try:
        manifest_bytes=(root/'manifest.json').read_bytes()
        if sha256(manifest_bytes).hexdigest()!=MANIFEST_SHA256:_reject('producer_unavailable')
        manifest=json.loads(manifest_bytes)
        for relative,digest in manifest['files'].items():
            if sha256((root/relative).read_bytes()).hexdigest()!=digest:_reject('producer_unavailable')
        return root,manifest
    except (OSError,KeyError,ValueError) as error:
        if isinstance(error,PreparationRejected):raise
        _reject('producer_unavailable')

def _capture(command,*,input_bytes=b'',limit,timeout,cwd=None):
    """Bound combined pipe capture while draining both streams under one deadline."""
    deadline=time.monotonic()+timeout
    with tempfile.TemporaryFile() as source:
        source.write(input_bytes);source.seek(0)
        with subprocess.Popen(command,stdin=source,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=cwd) as process:
            output=bytearray();errors=bytearray();total=0
            try:
                with selectors.DefaultSelector() as poll:
                    poll.register(process.stdout,selectors.EVENT_READ,output)
                    poll.register(process.stderr,selectors.EVENT_READ,errors)
                    while poll.get_map():
                        remaining=deadline-time.monotonic()
                        if remaining<=0:raise subprocess.TimeoutExpired(command,timeout)
                        for key,_ in poll.select(remaining):
                            block=key.fileobj.read1(min(65536,limit-total+1))
                            if not block:poll.unregister(key.fileobj);continue
                            total+=len(block)
                            if total>limit:raise PreparationRejected('producer_unavailable')
                            key.data.extend(block)
                remaining=deadline-time.monotonic()
                if remaining<=0:raise subprocess.TimeoutExpired(command,timeout)
                code=process.wait(timeout=remaining)
                return subprocess.CompletedProcess(command,code,bytes(output),bytes(errors))
            finally:
                if process.poll() is None:
                    process.kill();process.wait()

def prepare_acceptance(documents: tuple[CatalogDocument, ...],configuration:bytes,*,bun_executable: str='bun') -> PreparedAcceptance:
    """Prepare original native JSON UMF documents under explicit acceptance choices.

    configuration is the numeric-free AcceptanceInput JSON object without its
    interfaceVersion/documents fields. It must include layoutProfile,
    acceptanceProfile, validatorProfile, supportProfile, binding, policy and
    transforms. These explicit choices are preserved, not endorsed as installed.
    No database is opened, and no accepted identity or report is produced.
    """
    if (type(documents) is not tuple or not 1<=len(documents)<=512
            or type(configuration) is not bytes or not 1<=len(configuration)<=MAX_INPUT
            or type(bun_executable) is not str or not bun_executable or len(bun_executable)>4096):
        _reject('invalid_input')
    carriers=[];seen=set();total=0
    for document in documents:
        if type(document) is not CatalogDocument:_reject('invalid_input')
        _text(document.document_id);_text(document.document_revision)
        identity=document.document_id if document.artifact_identity is None else document.artifact_identity
        _text(identity)
        if document.document_id in seen:_reject('invalid_input')
        seen.add(document.document_id)
        if type(document.content) is not bytes or not 1<=len(document.content)<=MAX_INPUT:_reject('resource')
        total+=len(document.content)
        if total>MAX_INPUT:_reject('resource')
        carriers.append({'documentId':document.document_id,'documentRevision':document.document_revision,
                         'artifact':{'identity':identity,'bytesBase64':base64.b64encode(document.content).decode('ascii'),
                                     'sha256':sha256(document.content).hexdigest()}})
    request=_json({'configurationHex':configuration.hex(),'documents':carriers})
    if len(request)>MAX_INPUT:_reject('resource')
    root,manifest=_release()
    executable=shutil.which(bun_executable)
    if executable is None:_reject('runtime_unavailable')
    try:
        runtime=_capture([executable,'--version'],limit=4096,timeout=5)
        if runtime.returncode or runtime.stdout.decode('ascii').strip()!=manifest['runtimeVersion']:_reject('runtime_unavailable')
        completed=_capture([executable,str(root/'packages/umf-bun/src/bridge.js')],input_bytes=request,
                           limit=MAX_OUTPUT,timeout=10,cwd=root)
    except (OSError,subprocess.TimeoutExpired,UnicodeError):_reject('runtime_unavailable')
    if completed.returncode or len(completed.stdout)>MAX_OUTPUT:_reject('producer_unavailable')
    try:result=json.loads(completed.stdout)
    except (ValueError,UnicodeError):_reject('producer_unavailable')
    if type(result) is not dict:_reject('producer_unavailable')
    if result.get('status')=='refused':
        reason=result.get('reason')
        if reason not in ('resource','invalid_input','invalid_document','unsupported_profile','producer_unavailable'):_reject('producer_unavailable')
        if type(result.get('diagnostics')) is not list:_reject('producer_unavailable')
        diagnostics=tuple(_json(d) for d in result['diagnostics'])
        raise PreparationRejected(reason,diagnostics=diagnostics)
    try:
        if result['status']!='prepared' or result['provenance']['scope']!='original_umf_preparation_only':_reject('producer_unavailable')
        original=bytes.fromhex(result['inputHex']);parsed=decode_acceptance_json(original)
        if parsed['documents']!=[{**carrier,'umfProfile':result['provenance']['umfProfile'],'ingress':{'kind':'native'}} for carrier in carriers]:_reject('producer_unavailable')
        expected_configuration=decode_acceptance_json(configuration)
        actual_configuration={key:value for key,value in parsed.items() if key not in ('documents','interfaceVersion')}
        if actual_configuration!=expected_configuration or parsed['interfaceVersion']!='truss-acceptance-input/0.1.0':_reject('producer_unavailable')
        observed=result['documents']
        if len(observed)!=len(documents):_reject('producer_unavailable')
        archives=result['archiveDocuments']
        if len(archives)!=len(documents):_reject('producer_unavailable')
        for document,item,archive in zip(documents,observed,archives,strict=True):
            if (item['documentId']!=document.document_id or item['revision']!=document.document_revision
                    or item['originalText']!=document.content.decode('utf8')
                    or item['interpretation']['originalText']!=document.content.decode('utf8')
                    or archive!={key:value for key,value in item.items() if key!='interpretation'}):
                _reject('producer_unavailable')
        evidence=tuple(DocumentInterpretation(document,_json(item['interpretation'])) for document,item in zip(documents,observed,strict=True))
        pin=result['provenance']['umfProfile']
        if (pin['identity'] != 'umf-record-interpretation'
                or pin['version'] != manifest['owner']['revision']
                or pin['sha256'] != manifest['owner']['bundleSha256']
                or result['provenance']['schemaSha256'] != manifest['files']['docs/helix/02-design/contracts/acceptance-input-v0.1.schema.json']):
            _reject('producer_unavailable')
        return _retain_original(PreparedAcceptance(original,evidence,_json(result['declarations']),_json(result['archiveDocuments']),
            PreparationProvenance(pin['version'],pin['sha256'],result['provenance']['schemaSha256'],MANIFEST_SHA256,manifest['runtimeVersion'])))
    except (KeyError,ValueError,TypeError) as error:
        if isinstance(error,PreparationRejected):raise
        _reject('producer_unavailable')
