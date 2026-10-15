"""Private own-session Subject observation; never current-query permission.

The first component supports an accepted rootless Record with one required
String Key. A direct trusted installer enrolls native LOGIN OIDs. SCRAM/human
identity, full role/DDL lifetime and handoff to the private executor remain
separate native admission obligations.
"""
from dataclasses import dataclass, replace
from hashlib import sha256
import json
from psycopg import sql
from ._current_query_sources import capture_current_query_sources_with_cursor
from ._current_query_pipe import _envelope
from ._security_catalog_subject_installation import _text_rows
from ._installation_privileges import installation_administrator_with_cursor
from ._umf_key_tuples import KeyTupleRequest, encode_string_key_tuples
from .catalog_runtime import _pin_cursor
from .psycopg_host import PsycopgHost
from .execution import Error, ExecutionFailure


@dataclass(frozen=True, slots=True)
class CurrentQuerySubjectRegistration:
    installation_id: str
    source_receipt: str
    original_document: bytes
    identity: tuple[str,str,str]
    helper_source: str
    owner_oid: int
    bindings: tuple[tuple[int,str],...]
    status: str = 'pending_commit'


@dataclass(frozen=True, slots=True)
class CurrentQuerySubjectObservation:
    database_oid: str
    role_oid: str
    key: str
    object_id: str
    type_id: str
    object_version: str
    source_receipt: str
    installation_id: str
    original_key_receipt: bytes
    tuple_bytes: bytes


def _recipe(captured):
    source = _envelope(captured.initialize_bytes)['sources']
    ontology = source['ontology']
    subject = ontology['subject']
    if type(subject) is not dict or set(subject) != {'documentId','moduleId','elementId'}:
        raise ValueError('Original qualified Subject type required')
    entities = [e for e in ontology['entities'] if e['type'] == subject]
    if len(entities) != 1 or type(entities[0]['keyId']) is not str:
        raise ValueError('Original selected Subject Key required')
    key_id = entities[0]['keyId']
    assessment = json.loads(captured.accepted_assessment_bytes)
    inventory = assessment['inventory']
    types = [t for t in inventory['types'] if (t['document_id'],t['module'],t['element']) ==
             (subject['documentId'],subject['moduleId'],subject['elementId']) and t['retired_rev'] is None]
    if len(types) != 1 or types[0]['kind'] != 'record' or types[0]['provisional']:
        raise ValueError('Original accepted Subject Record required')
    type_id = types[0]['type_id']
    keys = [k for k in inventory['keys'] if k['type_id'] == type_id and k['key_id'] == key_id and k['retired_rev'] is None]
    if len(keys) != 1 or len(keys[0]['prop_ids']) != 1:
        raise ValueError('Single String Subject Key profile required')
    property_id = keys[0]['prop_ids'][0]
    properties = [p for p in inventory['properties'] if p['prop_id'] == property_id and p['type_id'] == type_id and p['retired_rev'] is None]
    if len(properties) != 1 or tuple(properties[0][k] for k in ('home','scalar_type','cardinality','nullability')) != ('json','string','one','required'):
        raise ValueError('Required singular String Subject Key profile required')
    modules = json.loads(captured.accepted_request_bytes)['modules']
    documents = [m for m in modules if m['pin']['documentId'] == subject['documentId']]
    if len(documents) != 1:
        raise ValueError('Original accepted Subject document required')
    document = documents[0]['documentJson'].encode('utf8')
    return type_id, property_id, document, (subject['moduleId'],subject['elementId'],key_id), subject, properties[0]


def _helper_source(cursor, captured, type_id, property_id, subject, field, key_id, document):
    marker = _text_rows(cursor,"SELECT pg_catalog.encode(inventory_sha256,'hex') FROM truss.installation_marker WHERE singleton_id=1",limit=1)
    if len(marker) != 1:
        raise ValueError('Original source inventory binding required')
    body = sql.SQL('''
BEGIN
 IF pg_catalog.current_setting('server_version_num') <> '180006'
 OR pg_catalog.current_setting('transaction_isolation') <> 'read committed'
 OR pg_catalog.current_setting('transaction_read_only') <> 'off'
 OR pg_catalog.current_setting('role') <> 'none' THEN
  RAISE EXCEPTION 'original ordinary RC/RW Subject session required' USING ERRCODE='55000'; END IF;
 LOCK TABLE ONLY truss.source_epoch_current,truss.source_epoch_registry IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.installation_marker IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_runtime_installation,truss.schema_head,truss.type_def,truss.prop_def,truss.key_def IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.catalog_subject_map IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT;
 PERFORM truss.runtime_person(false);
 RETURN QUERY SELECT
 (SELECT d.oid::text FROM pg_catalog.pg_database d WHERE d.datname=pg_catalog.current_database()),
 r.oid::text,m.staff_key,o.id::text,o.type_id::text,o.ver::text,{receipt},i.installation_id::text,
 {document_sha},{document_id},{module_id},{record_id},{key_id}
 FROM ONLY truss.catalog_subject_map m JOIN pg_catalog.pg_roles r ON r.oid=m.role_oid
 JOIN ONLY truss.catalog_runtime_installation i ON i.singleton
 JOIN ONLY truss.installation_marker a ON a.singleton_id=1 AND a.installation_id=i.installation_id::text
 JOIN ONLY truss.schema_head h ON h.id=1
 JOIN ONLY truss.type_def t ON t.type_id={type_id}
 JOIN ONLY truss.prop_def p ON p.type_id=t.type_id AND p.prop_id={property_id}
 JOIN ONLY truss.key_def k ON k.type_id=t.type_id AND k.prop_ids=ARRAY[{property_id}]
 JOIN ONLY truss.object o ON o.type_id=t.type_id AND o.root_id IS NULL
 WHERE r.rolname=SESSION_USER AND r.rolcanlogin AND NOT r.rolsuper
 AND NOT r.rolcreatedb AND NOT r.rolcreaterole AND NOT r.rolreplication AND NOT r.rolbypassrls
 AND NOT pg_catalog.pg_has_role(r.oid,i.owner_oid,'MEMBER')
 AND i.installation_id::text={installation} AND h.rev::text={revision}
 AND a.inventory_profile={source_profile}
 AND pg_catalog.encode(a.inventory_sha256,'hex')={inventory}
 AND t.document_id={document_id} AND t.module={module_id} AND t.element={record_id}
 AND t.kind='record' AND NOT t.provisional
 AND p.definition_document_id={field_document} AND p.declaration_module={field_module} AND p.element={field_id}
 AND k.key_id={key_id}
 AND t.retired_rev IS NULL AND p.retired_rev IS NULL AND k.retired_rev IS NULL
 AND p.home='json' AND p.scalar_type='string' AND p.cardinality='one' AND p.nullability='required'
 AND pg_catalog.jsonb_typeof(o.props->{property_text})='object'
 AND o.props->{property_text}->>'kind'='string'
 AND pg_catalog.jsonb_typeof(o.props->{property_text}->'text')='string'
 AND (o.props->{property_text}->>'text') COLLATE pg_catalog."C"=m.staff_key COLLATE pg_catalog."C";
END;
''').format(receipt=sql.Literal(captured.source_receipt),installation=sql.Literal(captured.installation_id),
            revision=sql.Literal(captured.accepted_revision),inventory=sql.Literal(captured.inventory_digest),source_profile=sql.Literal(captured.source_profile),
            type_id=sql.Literal(type_id),property_id=sql.Literal(property_id),property_text=sql.Literal(str(property_id)),
            document_id=sql.Literal(subject['documentId']),module_id=sql.Literal(subject['moduleId']),record_id=sql.Literal(subject['elementId']),
            field_document=sql.Literal(field['definition_document_id']),field_module=sql.Literal(field['declaration_module']),field_id=sql.Literal(field['element']),key_id=sql.Literal(key_id),document_sha=sql.Literal(sha256(document).hexdigest()))
    return body.as_string(cursor)


def _verify_helper(cursor, registration):
    rows = _text_rows(cursor,"SELECT p.prosrc,p.proowner::text,p.prosecdef::text,p.pronargs::text,l.lanname::text,pg_catalog.to_jsonb(p.proconfig)::text FROM pg_catalog.pg_proc p JOIN pg_catalog.pg_namespace n ON n.oid=p.pronamespace JOIN pg_catalog.pg_language l ON l.oid=p.prolang WHERE n.nspname='truss' AND p.proname='current_query_subject_current'",limit=1)
    if rows != [(registration.helper_source,str(registration.owner_oid),'true','0','plpgsql','["search_path=pg_catalog, pg_temp"]')]:
        raise ValueError('Original own-session Subject helper required')
    acl = _text_rows(cursor,"SELECT a.grantee::text,a.grantor::text,a.privilege_type::text,a.is_grantable::text FROM pg_catalog.pg_proc p CROSS JOIN LATERAL pg_catalog.aclexplode(coalesce(p.proacl,pg_catalog.acldefault('f',p.proowner))) a WHERE p.oid='truss.current_query_subject_current()'::pg_catalog.regprocedure ORDER BY a.grantee",limit=257)
    expected = sorted([(str(registration.owner_oid),str(registration.owner_oid),'EXECUTE','false'),
                       *[(str(oid),str(registration.owner_oid),'EXECUTE','false') for oid,_ in registration.bindings]], key=lambda row:int(row[0]))
    if acl != expected:
        raise ValueError('Original own-Subject helper ACL required')
    homes = _text_rows(cursor,"SELECT c.relowner::text,c.relkind::text,c.relrowsecurity::text,c.relforcerowsecurity::text,(NOT EXISTS(SELECT 1 FROM pg_catalog.aclexplode(coalesce(c.relacl,pg_catalog.acldefault('r',c.relowner))) a WHERE a.grantee<>c.relowner OR a.grantor<>c.relowner OR a.is_grantable))::text,(NOT EXISTS(SELECT 1 FROM pg_catalog.pg_attribute a WHERE a.attrelid=c.oid AND a.attacl IS NOT NULL))::text FROM pg_catalog.pg_class c WHERE c.oid='truss.catalog_subject_map'::pg_catalog.regclass",limit=1)
    if homes != [(str(registration.owner_oid),'r','false','false','true','true')]:
        raise ValueError('Private own-Subject mapping home required')


def register_current_query_subjects_in_transaction(host, transaction, *, bindings):
    if type(host) is not PsycopgHost:
        return Error(ExecutionFailure('execution_obligation','Original Subject installation host required'))
    if (type(bindings) is not tuple or not 1 <= len(bindings) <= 256
            or any(type(b) is not tuple or len(b) != 2 or any(type(v) is not str or not v or '\0' in v for v in b)
                   or len(b[0].encode()) > 63 or len(b[1].encode()) > 4096 for b in bindings)
            or len({b[0] for b in bindings}) != len(bindings)):
        return Error(ExecutionFailure('execution_obligation','Bounded native Subject enrollment required'))
    def install(cursor, observed):
        _pin_cursor(cursor)
        prior = _text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::text",limit=1)
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        captured = capture_current_query_sources_with_cursor(cursor)
        owner = _text_rows(cursor,'SELECT owner_oid::text FROM truss.catalog_runtime_installation WHERE singleton',limit=1)
        if len(owner) != 1:
            raise ValueError('Original Subject runtime owner required')
        actor = installation_administrator_with_cursor(cursor,int(owner[0][0]))
        if not actor[2]:
            raise ValueError('Direct trusted Subject installation administrator required')
        type_id, property_id, document, identity, subject, field = _recipe(captured)
        existing = _text_rows(cursor,"SELECT (pg_catalog.to_regclass('truss.catalog_subject_map') IS NULL)::text,(pg_catalog.to_regprocedure('truss.current_query_subject_current()') IS NULL)::text",limit=1)
        if existing != [('true','true')]:
            raise ValueError('Existing Subject registration requires explicit migration')
        cursor.execute('LOCK TABLE ONLY truss.object IN SHARE MODE NOWAIT',prepare=False)
        enrolled = []
        for role, key in bindings:
            roles = _text_rows(cursor,"SELECT oid::text,rolcanlogin::text,rolsuper::text,rolcreatedb::text,rolcreaterole::text,rolreplication::text,rolbypassrls::text,pg_catalog.pg_has_role(oid,%s::oid,'MEMBER')::text FROM pg_catalog.pg_roles WHERE rolname=%s",(int(owner[0][0]),role),1)
            if len(roles) != 1 or roles[0][1:] != ('true','false','false','false','false','false','false'):
                raise ValueError('Ordinary native Subject LOGIN required')
            found = _text_rows(cursor,"SELECT id::text FROM ONLY truss.object WHERE type_id=%s AND root_id IS NULL AND pg_catalog.jsonb_typeof(props->%s)='object' AND props->%s->>'kind'='string' AND pg_catalog.jsonb_typeof(props->%s->'text')='string' AND (props->%s->>'text') COLLATE pg_catalog.\"C\"=%s COLLATE pg_catalog.\"C\"",(type_id,str(property_id),str(property_id),str(property_id),str(property_id),key),1)
            if len(found) != 1:
                raise ValueError('Unique original stored Subject required')
            enrolled.append((int(roles[0][0]),key))
        body = _helper_source(cursor,captured,type_id,property_id,subject,field,identity[2],document)
        cursor.execute('CREATE TABLE truss.catalog_subject_map(role_oid pg_catalog.oid PRIMARY KEY,staff_key pg_catalog.text COLLATE pg_catalog."C" NOT NULL)',prepare=False)
        cursor.execute('REVOKE ALL ON TABLE truss.catalog_subject_map FROM PUBLIC',prepare=False)
        owner_name = _text_rows(cursor,'SELECT rolname::text FROM pg_catalog.pg_roles WHERE oid=%s::oid',(int(owner[0][0]),),1)[0][0]
        cursor.execute(sql.SQL('ALTER TABLE truss.catalog_subject_map OWNER TO {}').format(sql.Identifier(owner_name)),prepare=False)
        for oid,key in enrolled:
            cursor.execute('INSERT INTO truss.catalog_subject_map VALUES(%s,%s)',(oid,key),prepare=False)
        cursor.execute(sql.SQL('CREATE FUNCTION truss.current_query_subject_current() RETURNS TABLE(database_oid text,role_oid text,subject_key text,object_id text,type_id text,object_version text,source_receipt text,installation_id text,document_sha256 text,document_id text,module_id text,record_id text,key_id text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS {}').format(sql.Literal(body)),prepare=False)
        cursor.execute(sql.SQL('ALTER FUNCTION truss.current_query_subject_current() OWNER TO {}').format(sql.Identifier(owner_name)),prepare=False)
        cursor.execute('REVOKE ALL ON FUNCTION truss.current_query_subject_current() FROM PUBLIC',prepare=False)
        for role,_ in bindings:
            cursor.execute(sql.SQL('GRANT USAGE ON SCHEMA truss TO {}').format(sql.Identifier(role)),prepare=False)
            cursor.execute(sql.SQL('GRANT EXECUTE ON FUNCTION truss.current_query_subject_current() TO {}').format(sql.Identifier(role)),prepare=False)
        registration = CurrentQuerySubjectRegistration(captured.installation_id,captured.source_receipt,document,identity,body,int(owner[0][0]),tuple(sorted(enrolled)))
        _verify_helper(cursor,registration)
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
        if cursor.fetchmany(2) != prior:
            raise ValueError('Original Subject installation path restoration required')
        return registration
    return host._run_operation(transaction,install)


def observe_current_query_subject_in_transaction(host, transaction, registration, *, bun_executable='bun'):
    """Observe actual own-session key; detached output is not execution authority."""
    if type(host) is not PsycopgHost or type(registration) is not CurrentQuerySubjectRegistration:
        return Error(ExecutionFailure('execution_obligation','Original Subject observation inputs required'))
    registration = replace(registration)
    document, identity = registration.original_document, registration.identity
    if (type(document) is not bytes or not 1 <= len(document) <= 1048576
            or type(identity) is not tuple or len(identity) != 3
            or any(type(v) is not str or not v for v in identity)):
        return Error(ExecutionFailure('execution_obligation','Original Subject codec source required'))
    try:
        original = json.loads(document)
        document_id = original['id']
        if type(document_id) is not str or not document_id:
            raise ValueError('Original Subject document identity required')
    except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
        return Error(ExecutionFailure('execution_obligation','Original Subject codec document required'))
    codec_coordinates = (sha256(document).hexdigest(),document_id,*identity)
    def observe(cursor, observed):
        _pin_cursor(cursor)
        prior = _text_rows(cursor,"SELECT pg_catalog.current_setting('search_path')::pg_catalog.text",limit=1)
        if len(prior) != 1:
            raise ValueError('Original Subject observation search path required')
        cursor.execute("SELECT pg_catalog.set_config('search_path','pg_catalog, pg_temp',true)",prepare=False)
        def current():
            actor = _text_rows(cursor,"SELECT r.oid::text,(SESSION_USER=CURRENT_USER)::text,pg_catalog.current_setting('role')::text FROM pg_catalog.pg_roles r WHERE r.rolname=SESSION_USER",limit=1)
            if len(actor) != 1 or actor[0][1:] != ('true','none'):
                raise ValueError('Original native Subject session required')
            _verify_helper(cursor,registration)
            rows = _text_rows(cursor,'SELECT * FROM truss.current_query_subject_current()',limit=1)
            if len(rows) != 1 or rows[0][1] != actor[0][0] or rows[0][6:8] != (registration.source_receipt,registration.installation_id):
                raise ValueError('Original own-session Subject correspondence required')
            if rows[0][8:] != codec_coordinates:
                raise ValueError('Native-bound original Subject codec coordinates required')
            return rows[0]
        row = current()
        key = encode_string_key_tuples(document,(KeyTupleRequest(*identity,(row[2],)),),bun_executable=bun_executable)[0]
        if current() != row:
            raise ValueError('Original Subject changed during Key encoding')
        cursor.execute("SELECT pg_catalog.set_config('search_path',%s,true)",(prior[0][0],),prepare=False)
        if cursor.fetchmany(2) != prior:
            raise ValueError('Original Subject observation search path restoration required')
        return CurrentQuerySubjectObservation(*row[:8],key.original_receipt_bytes,key.tuple_bytes)
    return host._run_operation(transaction,observe)
