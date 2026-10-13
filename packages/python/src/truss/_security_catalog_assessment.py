"""Private administrative accepted-source assessment; never an execution permit.

Uses original native expected-record/report consistency checks. The caller must
hold installation/head/profile barriers. Output/retained assessment bounds do
not establish total libpq/process allocation limits. This does not prove complete writer
closure, issuer authenticity, or same-transaction ABA absence.
"""
import json
from hashlib import sha256
from .catalog_runtime import _release
from .weft import _decode

MAX_BYTES=16777216

def capture_accepted_catalog(cursor,original_request):
    _,request=_decode(original_request,4_000_000,'mapping_input')
    manifest,digest,_=_release()
    cursor.execute('SELECT installation_id::text,release_id,release_sha256 FROM truss.runtime_current_installation()',prepare=False)
    installation=cursor.fetchmany(2)
    if len(installation)!=1 or installation[0][1:]!=(manifest['releaseId'],digest):
        raise ValueError('Original installed catalog release required')
    cursor.execute('SELECT rev FROM truss.schema_head WHERE id=1 FOR SHARE',prepare=False)
    heads=cursor.fetchmany(2)
    if len(heads)!=1 or type(heads[0][0]) is not int or heads[0][0]<1:
        raise ValueError('Positive accepted catalog revision required')
    revision=heads[0][0]
    cursor.execute('SELECT (SELECT max(revision) FROM truss.catalog_registration_request),(SELECT count(*) FROM truss.catalog_registration_request),(SELECT max(rev) FROM truss.schema_rev),(SELECT count(*) FROM truss.schema_rev)',prepare=False)
    if cursor.fetchmany(2)!=[(revision,revision,revision,revision+1)]:
        raise ValueError('Exact current accepted revision history required')
    cursor.execute('SELECT truss.catalog_check_records(truss.catalog_all_expected_records())',prepare=False)
    cursor.fetchmany(2)
    # Original stored receipts must still correspond to source and deterministic
    # native report construction; hashes alone do not supply owner execution.
    cursor.execute('SELECT coalesce(sum(octet_length(input_bytes)::bigint+octet_length(document_bytes)+octet_length(declaration_bytes)),0)<=%s FROM truss.catalog_registration_request',(MAX_BYTES,),prepare=False)
    budget=cursor.fetchmany(2)
    if budget!=[(True,)] or type(budget[0][0]) is not bool:raise ValueError('Stored receipt assessment budget exceeded')
    cursor.execute('''SELECT r.input_bytes,r.document_bytes,r.declaration_bytes,
      a.report_bytes,r.report_sha256,truss.catalog_make_report(r),r.installation_id::text,r.revision
      FROM truss.catalog_registration_request r JOIN truss.catalog_acceptance_report a ON a.rev=r.revision
      WHERE r.revision<=%s ORDER BY r.revision''',(revision,),prepare=False)
    receipts=cursor.fetchmany(65537)
    if not receipts or len(receipts)>65536:raise ValueError('Bounded complete registration receipts required')
    if len(receipts)!=revision or any(row[-1]!=i for i,row in enumerate(receipts,1)):raise ValueError('Complete accepted revision receipt history required')
    retained=0
    for input_bytes,docs,decls,report,report_hash,rebuilt,receipt_installation,receipt_revision in receipts:
        if receipt_installation!=installation[0][0]:raise ValueError('Original receipt installation required')
        if any(type(v) is not bytes for v in (input_bytes,docs,decls,report,report_hash,rebuilt)):
            raise ValueError('Original stock bytea catalog receipt required')
        retained+=sum(len(v) for v in (input_bytes,docs,decls,report,rebuilt))
        if retained>MAX_BYTES:raise ValueError('Catalog receipt assessment budget exceeded')
        if sha256(report).digest()!=report_hash or report!=rebuilt:raise ValueError('Original accepted report correspondence required')
        cursor.execute('SELECT truss.catalog_require_sources(%s,%s,%s)',(input_bytes,docs,decls),prepare=False);cursor.fetchmany(2)
    cursor.execute('''SELECT doc_id,doc_revision,umf_version,content_sha256,document FROM
      (SELECT DISTINCT ON (doc_id) * FROM truss.schema_doc WHERE rev<=%s ORDER BY doc_id,rev DESC,ord DESC) d
      ORDER BY doc_id''',(revision,),prepare=False)
    documents=cursor.fetchmany(257)
    if len(documents)>256:raise ValueError('Catalog source count exceeded')
    supplied={m['pin']['documentId']:m for m in request['modules']}
    if len(supplied)!=len(request['modules']) or set(supplied)!={d[0] for d in documents}:
        raise ValueError('Complete original accepted model source required')
    for doc_id,rev,version,digest_text,text in documents:
        m=supplied[doc_id]
        if m['pin']!={'documentId':doc_id,'revision':rev,'umfVersion':version,'sha256':digest_text} or m['documentJson']!=text or sha256(text.encode()).hexdigest()!=digest_text:
            raise ValueError('Exact accepted compiler source correspondence required')
    inventory={}
    for key,table,order in (('types','type_def','type_id'),('properties','prop_def','prop_id'),('keys','key_def','type_id,key_num'),('relationships','rel_def','rel_type_id'),('endpoints','rel_endpoint','rel_type_id,source_type,target_type')):
        # Fixed owner-controlled table/ordering constants, never request SQL.
        cursor.execute('SELECT to_jsonb(t)::text FROM truss.'+table+' t ORDER BY '+order,prepare=False)
        rows=cursor.fetchmany(65537)
        if len(rows)>65536 or any(len(row)!=1 or type(row[0]) is not str for row in rows):raise ValueError('Bounded native catalog inventory required')
        retained+=sum(len(row[0].encode()) for row in rows)
        if retained>MAX_BYTES:raise ValueError('Catalog inventory assessment budget exceeded')
        inventory[key]=[json.loads(row[0]) for row in rows]
    result=json.dumps({'version':'truss.accepted-catalog-assessment/0.1','scope':'accepted_source_and_native_definition_correspondence_only','installationId':installation[0][0],'releaseId':installation[0][1],'releaseSha256':installation[0][2],'revision':str(revision),'modelPins':[m['pin'] for m in request['modules']],'inventory':inventory,'securityReady':False},sort_keys=True,separators=(',',':')).encode()
    if len(result)>MAX_BYTES:raise ValueError('Catalog assessment output budget exceeded')
    return result
