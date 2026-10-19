# SPDX-License-Identifier: MIT OR Apache-2.0
"""Same-preparation source references for current UMF 0.10 catalogs."""
DATE10_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.20.0', 'sha256': '364335de9a0e6968106af189dcb11d5b4c86b2114361fcffd722c4154bf809cb'}
SOURCE_REFERENCE_FORMAT='truss-catalog-source-reference/0.1'


def compact_catalog_sources(prepared):
    return prepared.input()['supportProfile']==DATE10_PROFILE


def catalog_source_reference(prepared, document_id, basis='original'):
    if basis not in ('original','reversible_target'):
        raise ValueError('Explicit original source basis required')
    document=next((d for d in prepared.input()['documents'] if d['documentId']==document_id),None)
    if document is None:
        raise ValueError('Same-request source document required')
    return {'interfaceVersion':SOURCE_REFERENCE_FORMAT,'documentId':document_id,
            'contentSha256':document['artifact']['sha256'],'documentRevision':document['documentRevision'],'basis':basis}


def catalog_source_artifact(prepared, document_id):
    document=next(d for d in prepared.input()['documents'] if d['documentId']==document_id)
    artifact=document['artifact']
    if not compact_catalog_sources(prepared):return artifact
    return {'identity':artifact['identity'],'sha256':artifact['sha256'],
            'reference':catalog_source_reference(prepared,document_id)}


def resolve_catalog_observation(prepared, observed):
    original=observed['result']['observation']
    if not compact_catalog_sources(prepared):return original
    reference=catalog_source_reference(prepared,observed['documentId'],observed['basis'])
    if original.get('source')!=reference:
        raise ValueError('Exact same-request source reference required')
    document=next(d for d in prepared.documents if d.document.document_id==observed['documentId'])
    source=document.observation()['source' if observed['basis']=='original' else 'target']
    return {**original,'source':source}
