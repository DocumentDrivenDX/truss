"""Native caller -> private full graph executor -> buffered receiver spike.

Host authentication, original registration/source/routine custody and DDL
closure are premises. Observed native identity is not a caller-supplied Staff
name. This does not admit compiler results or issue an authority credential.
"""
from pathlib import Path
from hashlib import sha256
from uuid import uuid4
from truss.catalog_runtime import _pin_cursor
from truss.execution import Ok
from truss.psycopg_host import PsycopgHost,_HostPairReservation
from truss._security_catalog_subject_installation import (
    acquire_registered_role_catalog_cut_with_cursor,_text_rows)
from security_ontology_guarded_read import _prepare_ontology_resource_operation


def _verify_native_peer(cursor,identity,pid,challenge):
    """Original trusted server's live backend rendezvous, not OID equality.

    Fresh private challenge is installed on the reserved caller connection.
    Native server/host authentication and unmodified activity source are
    premises; no challenge or standalone credential is released to clients.
    """
    cursor.execute('SELECT pg_catalog.pg_stat_clear_snapshot()',prepare=False)
    cursor.fetchmany(2)
    rows=_text_rows(cursor,"SELECT a.datid::pg_catalog.text,a.usesysid::pg_catalog.text,a.pid::pg_catalog.text,a.application_name::pg_catalog.text FROM pg_catalog.pg_stat_activity a WHERE a.pid OPERATOR(pg_catalog.=) %s::pg_catalog.int4",(pid,),1)
    if rows!=[(identity[0],identity[1],pid,challenge)]:raise ValueError('Original live native ontology caller/executor correspondence required')


def _caller(cursor,observed):
    if observed[0][2:]!=('read_committed','read_write'):
        raise ValueError('Original fresh native ontology caller transaction required')
    _pin_cursor(cursor)
    rows=_text_rows(cursor,"SELECT (SELECT oid FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database())::pg_catalog.text,r.oid::pg_catalog.text,SESSION_USER::pg_catalog.text,CURRENT_USER::pg_catalog.text,r.rolcanlogin::pg_catalog.text,r.rolsuper::pg_catalog.text,r.rolcreatedb::pg_catalog.text,r.rolcreaterole::pg_catalog.text,r.rolreplication::pg_catalog.text,r.rolbypassrls::pg_catalog.text FROM pg_catalog.pg_roles r WHERE r.rolname OPERATOR(pg_catalog.=) SESSION_USER",limit=1)
    if len(rows)!=1 or rows[0][2]!=rows[0][3] or rows[0][4:]!=('true','false','false','false','false','false'):
        raise ValueError('Original ordinary native ontology caller required')
    return rows[0][:3]


def _registered_subject(cursor,identity,bindings):
    # The private executor already holds both shared role catalog locks and the
    # Subject map cut. Original registration comparisons are trusted custody.
    installation=_text_rows(cursor,"SELECT owner_oid::pg_catalog.text,(SELECT oid FROM pg_catalog.pg_database WHERE datname OPERATOR(pg_catalog.=) pg_catalog.current_database())::pg_catalog.text FROM truss.catalog_runtime_installation WHERE singleton",limit=1)
    if len(installation)!=1 or installation[0][1]!=identity[0]:raise ValueError('Original caller/executor database correspondence required')
    owner=installation[0][0]
    home=_text_rows(cursor,"SELECT c.relowner::pg_catalog.text,c.relkind::pg_catalog.text,c.relpersistence::pg_catalog.text,c.relrowsecurity::pg_catalog.text,c.relforcerowsecurity::pg_catalog.text,(EXISTS(SELECT 1 FROM pg_catalog.pg_inherits i WHERE i.inhrelid OPERATOR(pg_catalog.=) c.oid OR i.inhparent OPERATOR(pg_catalog.=) c.oid))::pg_catalog.text,(NOT EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE a.grantee OPERATOR(pg_catalog.<>) c.relowner OR a.grantor OPERATOR(pg_catalog.<>) c.relowner))::pg_catalog.text FROM pg_catalog.pg_class c WHERE c.oid OPERATOR(pg_catalog.=) 'truss.catalog_subject_map'::pg_catalog.regclass",limit=1)
    if home!=[(owner,'r','p','false','false','false','true')]:raise ValueError('Original private registered ontology Subject map required')
    mapped=_text_rows(cursor,'SELECT role_oid::pg_catalog.text,staff_key::pg_catalog.text FROM ONLY truss.catalog_subject_map ORDER BY role_oid',limit=256)
    if mapped!=[(str(oid),key) for oid,key in bindings]:raise ValueError('Original registered ontology Subject map changed')
    roles=_text_rows(cursor,"SELECT r.oid::pg_catalog.text,r.rolcanlogin::pg_catalog.text,r.rolsuper::pg_catalog.text,r.rolcreatedb::pg_catalog.text,r.rolcreaterole::pg_catalog.text,r.rolreplication::pg_catalog.text,r.rolbypassrls::pg_catalog.text,pg_catalog.pg_has_role(r.oid,%s::pg_catalog.oid,'MEMBER')::pg_catalog.text FROM pg_catalog.pg_roles r WHERE r.oid OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.oid[]) ORDER BY r.oid",(owner,[oid for oid,key in bindings]),256)
    if roles!=[(str(oid),'true','false','false','false','false','false','false') for oid,key in bindings]:raise ValueError('Original ordinary registered ontology roles required')
    raw_access=_text_rows(cursor,"SELECT r.oid::pg_catalog.text,pg_catalog.has_any_column_privilege(r.oid,'truss.object','SELECT')::pg_catalog.text,pg_catalog.has_any_column_privilege(r.oid,'truss.edge','SELECT')::pg_catalog.text,pg_catalog.has_any_column_privilege(r.oid,'truss.catalog_subject_map','SELECT')::pg_catalog.text FROM pg_catalog.pg_roles r WHERE r.oid OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.oid[]) ORDER BY r.oid",([oid for oid,key in bindings],),256)
    if raw_access!=[(str(oid),'false','false','false') for oid,key in bindings]:raise ValueError('Unmediated registered ontology raw reads refused')
    routes=_text_rows(cursor,"SELECT r.oid::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) p.pronamespace WHERE p.prosecdef AND n.nspname OPERATOR(pg_catalog.<>) 'pg_catalog' AND n.nspname OPERATOR(pg_catalog.<>) 'information_schema' AND pg_catalog.has_schema_privilege(r.oid,n.oid,'USAGE') AND pg_catalog.has_function_privilege(r.oid,p.oid,'EXECUTE'))::pg_catalog.text,EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid OPERATOR(pg_catalog.=) c.relnamespace WHERE (c.relkind OPERATOR(pg_catalog.=) 'v' OR c.relkind OPERATOR(pg_catalog.=) 'm') AND n.nspname OPERATOR(pg_catalog.<>) 'pg_catalog' AND n.nspname OPERATOR(pg_catalog.<>) 'information_schema' AND pg_catalog.has_schema_privilege(r.oid,n.oid,'USAGE') AND pg_catalog.has_any_column_privilege(r.oid,c.oid,'SELECT'))::pg_catalog.text FROM pg_catalog.pg_roles r WHERE r.oid OPERATOR(pg_catalog.=) ANY(%s::pg_catalog.oid[]) ORDER BY r.oid",([oid for oid,key in bindings],),256)
    if routes!=[(str(oid),'false','false') for oid,key in bindings]:raise ValueError('Unmediated registered ontology definer/view routes refused')
    subjects=[key for oid,key in bindings if str(oid)==identity[1]]
    if len(subjects)!=1:raise ValueError('Original native caller has no registered ontology Subject')
    return subjects[0]


def publish_native_ontology_resource_read(caller,caller_transaction,executor,executor_transaction,original_request,registered_bindings,publisher):
    """Selected original comparisons, not public query/credential admission.

    Caller and executor host custody are reserved through the final receiver.
    Executor locks survive in its caller-owned outer transaction; settlement
    must drain earlier operations before acknowledging changes.
    """
    if (type(caller) is not PsycopgHost or type(executor) is not PsycopgHost
            or type(original_request) is not bytes or not 1<=len(original_request)<=4000000
            or type(registered_bindings) is not tuple or not 1<=len(registered_bindings)<=256
            or any(type(b) is not tuple or len(b)!=2 or type(b[0]) is not int or not 1<=b[0]<=4294967295 or type(b[1]) is not str or not 1<=len(b[1].encode())<=4096 for b in registered_bindings)
            or tuple(sorted(registered_bindings))!=registered_bindings
            or len({b[0] for b in registered_bindings})!=len(registered_bindings) or not callable(publisher)):
        raise ValueError('Original bounded registered ontology read context required')
    request=bytes(original_request);bindings=tuple((oid,key) for oid,key in registered_bindings)
    source=Path(__file__);pin=sha256(source.read_bytes()).digest()
    def execute(cursor,observed):
        identity=_caller(cursor,observed)
        previous=_text_rows(cursor,"SELECT pg_catalog.current_setting('application_name')::pg_catalog.text",limit=1)
        if len(previous)!=1:raise ValueError('Original native caller application context required')
        challenge='truss_ontology_'+uuid4().hex
        if _text_rows(cursor,"SELECT pg_catalog.set_config('application_name',%s,true)::pg_catalog.text",(challenge,),1)!=[(challenge,)]:raise ValueError('Original native caller rendezvous required')
        def evaluate(private,private_observed):
            if private_observed[0][2:]!=('read_committed','read_write'):
                raise ValueError('Original fresh native ontology executor transaction required')
            _pin_cursor(private)
            acquire_registered_role_catalog_cut_with_cursor(private)
            _verify_native_peer(private,identity,observed[0][0],challenge)
            private.execute('LOCK TABLE ONLY truss.catalog_subject_map,truss.catalog_runtime_installation IN SHARE MODE NOWAIT',prepare=False)
            subject=_registered_subject(private,identity,bindings)
            raw=_prepare_ontology_resource_operation(request,subject)(private,private_observed)
            if _registered_subject(private,identity,bindings)!=subject:raise ValueError('Original native ontology Subject changed')
            _verify_native_peer(private,identity,observed[0][0],challenge)
            return raw
        result=executor._run_operation(executor_transaction,evaluate)
        if _text_rows(cursor,"SELECT pg_catalog.set_config('application_name',%s,true)::pg_catalog.text",(previous[0][0],),1)!=previous:raise ValueError('Original native caller application context restoration required')
        if not isinstance(result,Ok):raise ValueError('Original private native ontology execution refused')
        if _caller(cursor,caller._observe(cursor))!=identity:raise ValueError('Original native ontology caller changed')
        if sha256(source.read_bytes()).digest()!=pin:raise ValueError('Original native ontology Subject source changed')
        return result.value
    with _HostPairReservation(caller,executor):
        return caller._run_published_operation(caller_transaction,execute,publisher)
