# SPDX-License-Identifier: MIT OR Apache-2.0
"""Public original UMF preparation. No catalog acceptance or database effects.

The original JavaScript producer runs inside the packaged embedded V8 boundary.
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
from ._core10_catalog_release import MANIFEST_SHA256 as CORE10_MANIFEST_SHA256
from ._acceptance_json import decode_acceptance_json

MAX_INPUT=16777216
MAX_DOCUMENT=4194304
MAX_OUTPUT=67108864

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
        """Fresh source and the exact current UMF validation result."""
        evidence=json.loads(self.observation_bytes)
        if evidence.get('interfaceVersion')=='truss-registration-preparation/2.0':
            entry=next(d for d in evidence['documents'] if d['documentId']==self.document.document_id)
            if entry['contentSha256']!=sha256(self.document.content).hexdigest():raise ValueError('Original source digest required')
            result={'originalText':self.document.content.decode('utf8'),'source':self.source(),
                'sourceValidation':entry['validation']}
            if 'dddProfile' in entry:result.update(dddProfile=entry['dddProfile'],dddValidation=entry['dddValidation'])
            return result
        return evidence

    def source(self) -> dict[str,object]:
        """Fresh original schema; no retained duplicate source representation."""
        return json.loads(self.document.content)

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
    provenance: PreparationProvenance
    report_evidence_bytes: bytes

    @property
    def declarations_bytes(self) -> bytes:
        """Compatibility projection, derived on demand from the one original source."""
        return _json([_catalog_declarations(d.document.document_id,d.source()) for d in self.documents])

    @property
    def archive_documents_bytes(self) -> bytes:
        summary=json.loads(self.report_evidence_bytes)
        validations={d['documentId']:d for d in summary['documents']}
        def stored_validation(document_id):
            entry=validations[document_id]
            result={'storageFormat':'truss-catalog-source/2','sourceValidation':entry['validation'],'transition':None}
            if 'dddProfile' in entry:result.update(dddProfile=entry['dddProfile'],dddValidation=entry['dddValidation'])
            return result
        return _json([{'documentId':d.document.document_id,'revision':d.document.document_revision,
            'umfVersion':d.source()['umf'],'originalText':d.document.content.decode('utf8'),
            'validation':stored_validation(d.document.document_id)}
            for d in self.documents])

    def input(self) -> dict[str, object]:
        """Fresh AcceptanceInput dictionary; exact source remains in artifacts."""
        return json.loads(self.input_bytes)

# Producer provenance only: these private records grant no database authority.
_original_preparations = {}
def _snapshot(prepared):
    if (type(prepared) is not PreparedAcceptance
            or any(type(getattr(prepared,name)) is not bytes for name in
                   ('input_bytes','report_evidence_bytes'))
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
    return (prepared.input_bytes, prepared.report_evidence_bytes,
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
    def __init__(self,reason: str,*,diagnostics: tuple[bytes, ...]=(),
                 produced_bytes: int | None=None,limit_bytes: int | None=None) -> None:
        super().__init__('Truss preparation refused: '+reason)
        self.reason=reason
        self.diagnostics=diagnostics
        self.produced_bytes=produced_bytes
        self.limit_bytes=limit_bytes

def _reject(reason):raise PreparationRejected(reason)
def _text(value):
    if type(value) is not str or not 1<=len(value)<=4096 or '\0' in value:_reject('invalid_input')
    try:value.encode('utf8')
    except UnicodeError:_reject('invalid_input')

def _json(value):return json.dumps(value,ensure_ascii=True,separators=(',',':')).encode('utf8')

def _release_runtime():
    root=Path(__file__).parent/'_umf'
    try:
        manifest_bytes=(root/'runtime-manifest.json').read_bytes()
        from ._umf_runtime_release import MANIFEST_SHA256 as runtime_manifest_sha256
        if sha256(manifest_bytes).hexdigest()!=runtime_manifest_sha256:_reject('producer_unavailable')
        manifest=json.loads(manifest_bytes)
        for relative,digest in manifest['files'].items():
            if sha256((root/relative).read_bytes()).hexdigest()!=digest:_reject('producer_unavailable')
        return root,manifest
    except (OSError,KeyError,ValueError) as error:
        if isinstance(error,PreparationRejected):raise
        _reject('producer_unavailable')

def _release_core10():
    root=Path(__file__).parent/'_umf_core10'
    try:
        raw=(root/'manifest.json').read_bytes()
        if sha256(raw).hexdigest()!=CORE10_MANIFEST_SHA256:_reject('producer_unavailable')
        manifest=json.loads(raw)
        for relative,digest in manifest['files'].items():
            if sha256((root/relative).read_bytes()).hexdigest()!=digest:_reject('producer_unavailable')
        _release_runtime()
        return root,manifest
    except (OSError,KeyError,ValueError) as error:
        if isinstance(error,PreparationRejected):raise
        _reject('producer_unavailable')

def _release_for_prepared(prepared):
    _require_original_preparation(prepared)
    if prepared.provenance.release_manifest_sha256==CORE10_MANIFEST_SHA256:return _release_core10()
    _reject('producer_unavailable')

def _capture(command,*,input_bytes=b'',limit,timeout,cwd=None):
    """Bounded owner capture; retained subprocess support is private tooling."""
    if command[0]=='embedded-v8':
        from ._embedded import capture
        try:
            return capture(command[1],input_bytes=input_bytes,limit=limit,timeout=timeout)
        except ValueError as error:
            raise PreparationRejected('producer_unavailable') from error
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

def prepare_acceptance(documents: tuple[CatalogDocument, ...],configuration:bytes | None=None,*,bun_executable: str='bun') -> PreparedAcceptance:
    if configuration is None:
        from .catalog_preparation import prepare_catalog
        return prepare_catalog(documents,bun_executable=bun_executable)
    return _prepare_acceptance(documents,configuration,bun_executable=bun_executable)

def prepare_core10_acceptance(documents: tuple[CatalogDocument, ...],configuration:bytes | None=None,*,bun_executable: str='bun') -> PreparedAcceptance:
    """Current UMF 0.10.0 preparation entrypoint."""
    return prepare_acceptance(documents,configuration,bun_executable=bun_executable)

def _prepare_acceptance(documents: tuple[CatalogDocument, ...],configuration:bytes,*,bun_executable: str='bun') -> PreparedAcceptance:
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
        if type(document.content) is not bytes or not 1<=len(document.content)<=MAX_DOCUMENT:_reject('resource')
        total+=len(document.content)
        if total>MAX_INPUT:_reject('resource')
        try:
            source=json.loads(document.content.decode('utf8'))
            version=source.get('umf') if type(source) is dict else None
        except (ValueError,UnicodeError,RecursionError):_reject('invalid_document')
        if version is None:_reject('invalid_document')
        if version!='0.10.0':_reject('unsupported_profile')
        carriers.append({'documentId':document.document_id,'documentRevision':document.document_revision,
                         'artifact':{'identity':identity,'bytesBase64':base64.b64encode(document.content).decode('ascii'),
                                     'sha256':sha256(document.content).hexdigest()}})
    request=_json({'configurationHex':configuration.hex(),'documents':carriers})
    if len(request)>MAX_INPUT:_reject('resource')
    root,manifest=_release_core10()
    release_digest=CORE10_MANIFEST_SHA256
    try:
        completed=_capture(['embedded-v8',str(root/'preparation.mjs')],input_bytes=request,
                           limit=MAX_OUTPUT,timeout=10,cwd=root)
    except (OSError,subprocess.TimeoutExpired,TimeoutError,UnicodeError):_reject('runtime_unavailable')
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
        original=_json(result['input']);parsed=decode_acceptance_json(original)
        if parsed['documents']!=[{**carrier,'artifact':{k:v for k,v in carrier['artifact'].items() if k!='bytesBase64'},'umfProfile':result['provenance']['umfProfile'],'ingress':{'kind':'native'}} for carrier in carriers]:_reject('producer_unavailable')
        expected_configuration=decode_acceptance_json(configuration)
        actual_configuration={key:value for key,value in parsed.items() if key not in ('documents','interfaceVersion')}
        if actual_configuration!=expected_configuration or parsed['interfaceVersion']!='truss-acceptance-input/0.2.0':_reject('producer_unavailable')
        observed=result['documents']
        if len(observed)!=len(documents):_reject('producer_unavailable')
        for document,item in zip(documents,observed,strict=True):
            source=json.loads(document.content)
            ddd_known=source.get('vocabularies',{}).get('umf.ddd',{}).get('version')=='0.1.0'
            expected_item_keys={'documentId','revision','umfVersion','validation'}|({'dddProfile','dddValidation'} if ddd_known else set())
            if (set(item)!=expected_item_keys
                    or item['documentId']!=document.document_id or item['revision']!=document.document_revision
                    or item['umfVersion']!=source['umf']
                    or item['validation'].get('valid') is not True):_reject('producer_unavailable')
            if ddd_known:
                expected_ddd_profile={'identity':'umf-ddd-document-validation','version':manifest['owner']['revision'],
                    'sha256':manifest['owner']['bundleSha256']}
                ddd_validation=item['dddValidation']
                if (item['dddProfile']!=expected_ddd_profile or type(ddd_validation) is not dict
                        or ddd_validation.get('valid') is not True or type(ddd_validation.get('complete')) is not bool
                        or type(ddd_validation.get('diagnostics')) is not list):_reject('producer_unavailable')
        pin=result['provenance']['umfProfile']
        if (pin['identity'] != 'umf-core-document-validation'
                or pin['version'] != manifest['owner']['revision']
                or pin['sha256'] != manifest['owner']['bundleSha256']
                or result['provenance']['schemaSha256'] != manifest['files']['acceptance-input-v0.1.schema.json']):
            _reject('producer_unavailable')
        report_evidence=result['reportEvidence']
        expected_summary={'interfaceVersion':'truss-registration-preparation/2.0','documents':[
            {'documentId':document.document_id,'contentSha256':sha256(document.content).hexdigest(),
             'validation':item['validation'],**({'dddProfile':item['dddProfile'],'dddValidation':item['dddValidation']}
                 if 'dddProfile' in item else {})}
            for document,item in zip(documents,observed,strict=True)]}
        if report_evidence!=expected_summary:_reject('producer_unavailable')
        # Truss's executable catalog needs names; UMF itself deliberately does
        # not. Check only after original owner validation/correspondence, before
        # issuing a preparation that can reach native catalog acceptance.
        name_diagnostics=[]
        for document in documents:
            source=json.loads(document.content)
            for module_index,module in enumerate(source['modules']):
                for element_index,element in enumerate(module['elements']):
                    if element.get('kind') not in ('record','field'):
                        continue
                    if type(element.get('name')) is str and element['name']:
                        continue
                    name_diagnostics.append(_json({
                        'code':'TRUSS-NAME-MISSING','severity':'error',
                        'documentId':document.document_id,
                        'documentRevision':document.document_revision,
                        'moduleId':module['id'],'elementId':element['id'],
                        'kind':element['kind'],
                        'path':f'/modules/{module_index}/elements/{element_index}/name',
                        'message':f"Truss catalog registration requires a nonempty name for {element['kind']} {module['id']!r}/{element['id']!r}",
                    }))
        if name_diagnostics:
            raise PreparationRejected('invalid_document',diagnostics=tuple(name_diagnostics))
        summary_bytes=_json(report_evidence)
        evidence=tuple(DocumentInterpretation(document,summary_bytes) for document in documents)
        return _retain_original(PreparedAcceptance(original,evidence,
            PreparationProvenance(pin['version'],pin['sha256'],result['provenance']['schemaSha256'],release_digest,'mini-racer==0.14.1/V8 14.4.258.23'),summary_bytes))
    except (KeyError,ValueError,TypeError) as error:
        if isinstance(error,PreparationRejected):raise
        _reject('producer_unavailable')


def _catalog_declarations(document_id,source):
    """Truss storage references only; original UMF validation owns schema meaning."""
    index={(m['id'],e['id']):e for m in source['modules'] for e in m['elements']}
    records=[];relationships=[]
    for module in source['modules']:
        for element in module['elements']:
            if element['kind']!='record':continue
            fields=[]
            for ref in element.get('members',[]):
                field=index[(ref['module'],ref['element'])]
                if field['kind']!='field':raise ValueError('Original Field member required')
                fields.append({'fieldModule':ref['module'],'fieldId':ref['element'],'reference':ref,'declaration':field})
            records.append({'documentId':document_id,'moduleId':module['id'],'elementId':element['id'],
                'declaration':element,'membership':'declared' if 'members' in element else 'missing',
                'fields':fields,'keys':element.get('keys',[])})
        relationships.extend({'documentId':document_id,'moduleId':module['id'],'declaration':rel} for rel in module.get('relationships',[]))
    return {'records':records,'relationships':relationships,'scope':'original_declaration_correspondence_only'}
