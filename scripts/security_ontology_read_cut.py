# SPDX-License-Identifier: MIT OR Apache-2.0
"""Fixed lock-only issuer for an ordinary private graph executor.

Original owner/caller identities and routine/DDL lifetime are trusted custody.
No data exporter, arbitrary SQL or authority credential is issued.
"""
from pathlib import Path
from hashlib import sha256
from truss._security_catalog_subject_installation import _text_rows,verify_held_registered_role_catalog_cut_with_cursor
from truss._security_catalog_assessment import verify_held_accepted_catalog_source_cut

SOURCE=Path(__file__).with_name('security-ontology-read-cut.sql')
DIGEST='ef86642d6b38a398867962fe3fcbc12608667616b27c50eae69e6544b65c4e7d'


def verify_ontology_read_cut_issuer(cursor,owner_oid,caller_oid):
    if any(type(v) is not int or not 1<=v<=4294967295 for v in (owner_oid,caller_oid)) or owner_oid==caller_oid:raise ValueError('Original distinct graph cut issuer identities required')
    source=SOURCE.read_bytes()
    if sha256(source).hexdigest()!=DIGEST:raise ValueError('Original graph cut issuer source required')
    body=source.decode().split('AS $$',1)[1].split('$$;',1)[0]
    rows=_text_rows(cursor,"SELECT p.proowner::pg_catalog.text,l.lanname::pg_catalog.text,p.prokind::pg_catalog.text,p.pronargs::pg_catalog.text,p.proargtypes::pg_catalog.text,p.prorettype::pg_catalog.text,p.proretset::pg_catalog.text,p.proisstrict::pg_catalog.text,p.prosecdef::pg_catalog.text,p.provolatile::pg_catalog.text,p.proparallel::pg_catalog.text,p.proleakproof::pg_catalog.text,p.prosupport::pg_catalog.oid::pg_catalog.text,pg_catalog.to_jsonb(p.proconfig)::pg_catalog.text,p.prosrc,(p.prosqlbody IS NULL)::pg_catalog.text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace JOIN pg_catalog.pg_language l ON l.oid OPERATOR(pg_catalog.=) p.prolang WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND p.proname OPERATOR(pg_catalog.=) 'acquire_ontology_read_cut'",limit=1)
    if rows!=[(str(owner_oid),'plpgsql','f','0','','2278','false','false','true','v','u','false','0','["search_path=pg_catalog, pg_temp"]',body,'true')]:raise ValueError('Exact original graph cut issuer definition required')
    acl=_text_rows(cursor,"SELECT a.grantee::pg_catalog.text,a.grantor::pg_catalog.text,a.privilege_type::pg_catalog.text,a.is_grantable::pg_catalog.text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid OPERATOR(pg_catalog.=) 'truss.acquire_ontology_read_cut()'::pg_catalog.regprocedure ORDER BY a.grantee",limit=3)
    if acl!=sorted([(str(owner_oid),str(owner_oid),'EXECUTE','false'),(str(caller_oid),str(owner_oid),'EXECUTE','false')],key=lambda r:int(r[0])):raise ValueError('Exact private graph cut issuer ACL required')
    if _text_rows(cursor,'SELECT rolsuper::pg_catalog.text FROM pg_catalog.pg_roles WHERE oid OPERATOR(pg_catalog.=) %s::pg_catalog.oid',(owner_oid,),1)!=[('true',)]:raise ValueError('Original privileged graph cut issuer owner required')


def acquire_issued_ontology_read_cut(cursor,owner_oid,caller_oid):
    verify_ontology_read_cut_issuer(cursor,owner_oid,caller_oid)
    if _text_rows(cursor,'SELECT oid::pg_catalog.text FROM pg_catalog.pg_roles WHERE rolname OPERATOR(pg_catalog.=) CURRENT_USER',(),1)!=[(str(caller_oid),)]:raise ValueError('Original graph cut private executor required')
    cursor.execute('SELECT truss.acquire_ontology_read_cut()',prepare=False,binary=False)
    if cursor.description is None or len(cursor.description)!=1 or cursor.description[0].type_code!=2278 or cursor.fetchmany(2)!=[('',)]:raise ValueError('Exact graph cut VOID result required')
    verify_held_registered_role_catalog_cut_with_cursor(cursor)
    verify_held_accepted_catalog_source_cut(cursor)
    verify_held_ontology_fact_cut(cursor,include_subject=True)
    verify_ontology_read_cut_issuer(cursor,owner_oid,caller_oid)


def verify_held_ontology_fact_cut(cursor,*,include_subject=False):
    if type(include_subject) is not bool:raise ValueError('Exact ontology fact cut mode required')
    names=['object','edge']+(['catalog_subject_map'] if include_subject else [])
    rows=_text_rows(cursor,"SELECT c.relname::pg_catalog.text,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,c.relrowsecurity::pg_catalog.text,c.relforcerowsecurity::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid OPERATOR(pg_catalog.=) c.oid OR i.inhparent OPERATOR(pg_catalog.=) c.oid)::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_locks l WHERE l.pid OPERATOR(pg_catalog.=) pg_catalog.pg_backend_pid() AND l.locktype OPERATOR(pg_catalog.=) 'relation' AND l.database OPERATOR(pg_catalog.=) (SELECT oid FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database()) AND l.relation OPERATOR(pg_catalog.=) c.oid AND l.mode OPERATOR(pg_catalog.=) 'ShareLock' AND l.granted)::pg_catalog.text FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE n.nspname OPERATOR(pg_catalog.=) 'truss' AND c.relname OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.text[]) ORDER BY c.relname",(names,),len(names))
    if rows!=[(n,'r','p','false','false','false','true') for n in sorted(names)]:raise ValueError('Original held complete unfiltered ontology fact cut required')
