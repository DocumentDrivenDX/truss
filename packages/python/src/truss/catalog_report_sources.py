"""Resolve a source reference within a catalog report's retained document."""
import base64
from dataclasses import dataclass
from decimal import Decimal, DecimalException, InvalidOperation, localcontext
from hashlib import sha256
import json


@dataclass(frozen=True, slots=True)
class CatalogSourceDocument:
    document_id: str
    document_revision: str
    artifact_identity: str
    content: bytes
    sha256: str


def resolve_catalog_report_source(report_bytes: bytes, source: dict[str, object]) -> CatalogSourceDocument:
    """Resolve a retained source reference without fetching a current document.

    Original bytes and digest are checked. Unknown content stays in those bytes;
    the assertion's sourcePointer remains the caller's occurrence location.
    """
    if type(report_bytes) is not bytes or not 1<=len(report_bytes)<=16777216:
        raise ValueError('Bounded catalog report bytes required')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate catalog report member')
            result[key]=value
        return result
    def number(token):
        if len(token)>512:raise ValueError('Catalog report number token limit exceeded')
        try:
            with localcontext() as context:
                context.traps[InvalidOperation]=True
                return Decimal(token)
        except DecimalException as error:
            raise ValueError('Catalog report number unavailable') from error
    def nonfinite(token):raise ValueError('Finite JSON catalog report required')
    try:
        report=json.loads(report_bytes.decode('utf8'),object_pairs_hook=pairs,parse_float=number,parse_constant=nonfinite)
    except (UnicodeError,RecursionError) as error:
        raise ValueError('Catalog report encoding required') from error
    if type(report) is dict and report.get('interfaceVersion')=='truss-catalog-registration-report/0.6':
        raise ValueError('Source-reference receipt: retrieve original bytes with accepted_document_in_transaction')
    if type(report) is not dict or report.get('interfaceVersion') not in ('truss-catalog-registration-report/0.2','truss-catalog-registration-report/0.3','truss-catalog-registration-report/0.4','truss-catalog-registration-report/0.5'):
        raise ValueError('Supported retained catalog report required')
    if (type(source) is not dict or set(source)!={'identity','sha256','reference'}
        or type(source['identity']) is not str or not 1<=len(source['identity'])<=4096
        or type(source['sha256']) is not str):
        raise ValueError('Closed catalog source artifact reference required')
    reference=source['reference']
    if type(reference) is not dict or set(reference)!={'interfaceVersion','documentId','contentSha256','documentRevision','basis'}:
        raise ValueError('Closed original document reference required')
    if (any(type(reference[k]) is not str or not 1<=len(reference[k])<=4096 for k in ('documentId','documentRevision','contentSha256'))
        or reference['interfaceVersion']!='truss-catalog-source-reference/0.1' or reference['basis']!='original'
        or any(type(value) is not str for value in reference.values())):
        raise ValueError('Original source reference format required')
    accepted=report.get('acceptedInput')
    documents=accepted.get('documents') if type(accepted) is dict else None
    if type(documents) is not list or not 1<=len(documents)<=512:
        raise ValueError('Retained accepted-input documents required')
    selected=[d for d in documents if type(d) is dict and d.get('documentId')==reference['documentId']]
    if len(selected)!=1:raise ValueError('One same-report source document required')
    document=selected[0];artifact=document.get('artifact')
    if (type(artifact) is not dict or document.get('documentRevision')!=reference['documentRevision']
        or artifact.get('identity')!=source['identity'] or artifact.get('sha256')!=source['sha256']
        or artifact.get('sha256')!=reference['contentSha256'] or type(artifact.get('bytesBase64')) is not str):
        raise ValueError('Same-report document identity/revision/digest required')
    try:content=base64.b64decode(artifact['bytesBase64'],validate=True)
    except ValueError as error:raise ValueError('Original source bytes required') from error
    if base64.b64encode(content).decode()!=artifact['bytesBase64'] or sha256(content).hexdigest()!=source['sha256']:
        raise ValueError('Exact source bytes and digest required')
    return CatalogSourceDocument(reference['documentId'],reference['documentRevision'],source['identity'],content,source['sha256'])
