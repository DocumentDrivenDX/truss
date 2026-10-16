DATE08_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.18.0', 'sha256': '5f8903ccb48244851fece0a7778eb07eb8a32950449e3ac6ca0d657441acb838'}
DECLARATIVE08_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.17.0', 'sha256': '76dafc79768be61a311e4161b936ccf176aba32b539af51794fe22d679725fc0'}
RECURSIVE08_PROFILE={'identity': 'truss-fresh-catalog-support', 'version': '0.16.0', 'sha256': 'f5c40d9539a4a6788f34b04c1dc41b7a094ff830117c1feaed1a41db4408b315'}
"""Same-preparation source references at defined Truss wrapper positions only."""
REFERENCE08_PROFILE={'identity':'truss-fresh-catalog-support','version':'0.14.0','sha256':'1d89c2cdaa468a0ca01f837624787ca678aa6b4dafed6417018e63c0ebcfca56'}
SOURCE_REFERENCE_FORMAT='truss-catalog-source-reference/0.1'


def compact_catalog_sources(prepared):
    return prepared.input()['supportProfile'] in (REFERENCE08_PROFILE,RECURSIVE08_PROFILE,DECLARATIVE08_PROFILE,DATE08_PROFILE)


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
