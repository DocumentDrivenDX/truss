-- Catalog-only runtime. Business mutation/feed APIs are not granted by this release.
CREATE TABLE truss.catalog_runtime_installation (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),installation_id uuid NOT NULL UNIQUE,
 release_id text NOT NULL,release_sha256 text NOT NULL,layout_profile jsonb NOT NULL,preparation_configuration jsonb NOT NULL,
 owner_oid oid NOT NULL,registrar_oid oid NOT NULL,genesis_at timestamptz NOT NULL);
CREATE TABLE truss.catalog_registration_request (
 registration_id uuid PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 actor_oid oid NOT NULL,actor_name text NOT NULL,request_key text NOT NULL,
 writer_xid xid8 NOT NULL,accepted_at timestamptz NOT NULL,
 input_bytes bytea NOT NULL,document_bytes bytea NOT NULL,declaration_bytes bytea NOT NULL,
 source_bytes bytea NOT NULL,origin_bytes bytea NOT NULL,
 revision int NOT NULL UNIQUE REFERENCES truss.schema_rev(rev),report_sha256 bytea NOT NULL,
 UNIQUE(installation_id,actor_oid,request_key),CHECK(revision=1),
 CHECK(octet_length(request_key) BETWEEN 1 AND 1024),CHECK(octet_length(report_sha256)=32));

CREATE FUNCTION truss.runtime_person(require_registrar boolean) RETURNS oid
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE actor record; installation truss.catalog_runtime_installation%ROWTYPE;
 member_of_owner boolean; member_of_registrar boolean; member_of_server_capability boolean; unsafe_switchable boolean;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
  RAISE EXCEPTION 'catalog authorization requires READ COMMITTED' USING ERRCODE='0A000'; END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 SELECT oid,rolcanlogin,rolsuper,rolcreaterole,rolcreatedb,rolreplication,rolbypassrls INTO STRICT actor
 FROM pg_roles WHERE rolname=session_user;
 -- Read membership rows under the current snapshot instead of a role cache
 -- populated while executing a nested SECURITY DEFINER wrapper.
 WITH RECURSIVE memberships(role_oid) AS (
  SELECT actor.oid UNION
  SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid
 ) SELECT coalesce(bool_or(role_oid=installation.owner_oid),false),
          coalesce(bool_or(role_oid=installation.registrar_oid),false),
          coalesce(bool_or(role_oid IN (SELECT oid FROM pg_roles WHERE rolname IN
           ('pg_read_server_files','pg_write_server_files','pg_execute_server_program'))),false)
 INTO member_of_owner,member_of_registrar,member_of_server_capability FROM memberships;
 WITH RECURSIVE role_states(active_oid,privilege_oid) AS (
  SELECT actor.oid,actor.oid UNION
  SELECT CASE WHEN m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid)
              THEN m.roleid ELSE s.active_oid END,m.roleid
  FROM pg_auth_members m JOIN role_states s ON m.member=s.privilege_oid
  WHERE m.inherit_option OR m.admin_option OR (m.set_option AND s.active_oid=s.privilege_oid)
 ) SELECT EXISTS(SELECT 1 FROM (SELECT DISTINCT active_oid FROM role_states) s JOIN pg_roles r ON r.oid=s.active_oid
   WHERE r.rolsuper OR r.rolcreaterole OR r.rolcreatedb OR r.rolreplication OR r.rolbypassrls
    OR has_schema_privilege(r.oid,'truss','CREATE')
    OR EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'
      AND ((c.relkind IN ('r','p') AND (has_table_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
        OR has_any_column_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')))
       OR (c.relkind='S' AND has_sequence_privilege(r.oid,c.oid,'USAGE,SELECT,UPDATE'))))) INTO unsafe_switchable;
 IF current_setting('server_version_num')<>'180006' OR current_setting('role')<>'none' OR NOT actor.rolcanlogin OR actor.rolsuper
  OR actor.rolcreaterole OR actor.rolcreatedb OR actor.rolreplication OR actor.rolbypassrls
  OR actor.oid=installation.owner_oid OR member_of_owner OR member_of_server_capability OR unsafe_switchable
  OR NOT EXISTS(SELECT 1 FROM pg_namespace n JOIN pg_roles r ON r.oid=n.nspowner
   WHERE n.nspname='truss' AND r.oid=installation.owner_oid AND NOT r.rolcanlogin AND NOT r.rolsuper
    AND NOT r.rolcreaterole AND NOT r.rolcreatedb AND NOT r.rolreplication AND NOT r.rolbypassrls AND NOT r.rolinherit)
  OR has_schema_privilege(actor.oid,'truss','CREATE')
  OR EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'
    AND ((c.relkind IN ('r','p') AND (has_table_privilege(actor.oid,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
      OR has_any_column_privilege(actor.oid,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')))
     OR (c.relkind='S' AND has_sequence_privilege(actor.oid,c.oid,'USAGE,SELECT,UPDATE'))))
  OR (SELECT oid FROM pg_roles WHERE rolname=current_user) IS DISTINCT FROM installation.owner_oid
  OR require_registrar IS NULL OR (require_registrar AND NOT member_of_registrar) THEN
  RAISE EXCEPTION 'catalog registration authorization required' USING ERRCODE='42501'; END IF;
 RETURN actor.oid;
END;
$$;

CREATE FUNCTION truss.catalog_actor() RETURNS oid
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp
AS 'SELECT truss.runtime_person(true)';
REVOKE ALL ON FUNCTION truss.runtime_person(boolean) FROM PUBLIC;

CREATE FUNCTION truss.catalog_check_records(expected jsonb) RETURNS void
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE table_name text; planned jsonb; actual jsonb;
BEGIN
 FOREACH table_name IN ARRAY ARRAY['schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(r),''hex'') ORDER BY encode(record_send(r),''hex'') COLLATE "C"),''[]''::jsonb) FROM jsonb_populate_recordset(NULL::truss.%I,$1) r',table_name)
   INTO planned USING expected->table_name;
  EXECUTE format('SELECT coalesce(jsonb_agg(encode(record_send(r),''hex'') ORDER BY encode(record_send(r),''hex'') COLLATE "C"),''[]''::jsonb) FROM ONLY truss.%I r',table_name) INTO actual;
  IF planned IS DISTINCT FROM actual THEN
   RAISE EXCEPTION 'complete planned catalog records required' USING ERRCODE='55000'; END IF;
 END LOOP;
END;
$$;

CREATE FUNCTION truss.catalog_make_report(request truss.catalog_registration_request) RETURNS bytea
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET bytea_output='hex' AS $$
DECLARE report jsonb; source jsonb;
BEGIN
 source:=convert_from(request.source_bytes,'UTF8')::jsonb;
 report:=jsonb_build_object('interfaceVersion','truss-catalog-registration-report/0.1',
  'registrationId',request.registration_id::text,'installationId',request.installation_id::text,
  'revision',request.revision::text,'actor',request.actor_name,'actorOid',request.actor_oid::text,
  'writerXid',request.writer_xid::text,'requestKey',request.request_key,
  'acceptedAt',to_char(request.accepted_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'release',(SELECT jsonb_build_object('id',release_id,'sha256',release_sha256) FROM truss.catalog_runtime_installation),
  'acceptedInput',convert_from(request.input_bytes,'UTF8')::jsonb,'source',source,
  'assertedOrigin',convert_from(request.origin_bytes,'UTF8')::jsonb,
  'documents',(SELECT jsonb_agg(jsonb_build_object('documentId',d.doc_id,'revision',d.doc_revision,'sha256',d.content_sha256,'ordinal',d.ord::text) ORDER BY d.ord) FROM truss.schema_doc d WHERE d.rev=request.revision),
  'types',(SELECT coalesce(jsonb_agg(jsonb_build_object('documentId',t.document_id,'moduleId',t.module,'elementId',t.element,'typeId',t.type_id::text) ORDER BY t.type_id),'[]'::jsonb) FROM truss.type_def t),
  'properties',(SELECT coalesce(jsonb_agg(jsonb_build_object('typeId',p.type_id::text,'propertyId',p.prop_id::text,'moduleId',p.declaration_module,'elementId',p.element) ORDER BY p.prop_id),'[]'::jsonb) FROM truss.prop_def p),
  'relationships',(SELECT coalesce(jsonb_agg(jsonb_build_object('documentId',r.document_id,'moduleId',r.module,'relationshipId',r.rel_id,'typeId',r.rel_type_id::text) ORDER BY r.rel_type_id),'[]'::jsonb) FROM truss.rel_def r));
 RETURN convert_to(report::text,'UTF8');
END;
$$;

CREATE FUNCTION truss.catalog_validate_completion() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE request truss.catalog_registration_request%ROWTYPE; installation truss.catalog_runtime_installation%ROWTYPE;
 expected jsonb; origin bytea; original_report bytea;
BEGIN
 IF TG_TABLE_SCHEMA<>'truss' OR TG_TABLE_NAME<>'schema_head' OR NEW.id<>1 OR NEW.rev<>1 THEN
  RAISE EXCEPTION 'selected catalog completion required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 SELECT * INTO STRICT request FROM truss.catalog_registration_request WHERE revision=NEW.rev;
 IF request.actor_oid IS DISTINCT FROM truss.catalog_actor() THEN
  RAISE EXCEPTION 'current original registration authority required' USING ERRCODE='42501'; END IF;
 IF request.installation_id<>installation.installation_id OR NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev=request.revision) THEN
  RAISE EXCEPTION 'complete catalog publication required' USING ERRCODE='55000'; END IF;
 origin:=convert_to((convert_from(request.origin_bytes,'UTF8')::jsonb||jsonb_build_object('actor',request.actor_name,'db_role',request.actor_name))::text,'UTF8');
 expected:=truss.catalog_expected_records(request.declaration_bytes,request.document_bytes,origin,request.accepted_at,installation.genesis_at);
 PERFORM truss.catalog_check_records(expected);
 SELECT report_bytes INTO STRICT original_report FROM truss.catalog_acceptance_report WHERE rev=request.revision;
 IF sha256(original_report) IS DISTINCT FROM request.report_sha256 OR original_report IS DISTINCT FROM truss.catalog_make_report(request) THEN
  RAISE EXCEPTION 'complete original catalog report required' USING ERRCODE='55000'; END IF;
 RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER catalog_completion AFTER UPDATE ON truss.schema_head
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.catalog_validate_completion();
ALTER TABLE truss.schema_head ENABLE ALWAYS TRIGGER catalog_completion;

CREATE FUNCTION truss.catalog_immutable() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN RAISE EXCEPTION 'immutable catalog source or result' USING ERRCODE='55000'; END;
$$;
DO $$ DECLARE table_name text; BEGIN
 FOREACH table_name IN ARRAY ARRAY['schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint','catalog_acceptance_report','catalog_registration_request','catalog_runtime_installation'] LOOP
  EXECUTE format('CREATE TRIGGER catalog_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.%I FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable()',table_name);
  EXECUTE format('ALTER TABLE truss.%I ENABLE ALWAYS TRIGGER catalog_immutable',table_name);
 END LOOP;
END $$;

CREATE FUNCTION truss.catalog_require_sources(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea) RETURNS void
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE input jsonb; documents jsonb; declarations jsonb; doc jsonb; source jsonb; rec jsonb;
 source_record jsonb; field jsonb; source_field jsonb; rel jsonb; source_relation jsonb; ref jsonb;
 selected_doc jsonb; i int:=0; expected_records int; expected_fields int; expected_relations int;
BEGIN
 input:=convert_from(input_bytes,'UTF8')::jsonb;documents:=convert_from(documents_bytes,'UTF8')::jsonb;
 declarations:=convert_from(declarations_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(input) IS DISTINCT FROM 'object' OR (input-'interfaceVersion'-'documents') IS DISTINCT FROM (SELECT preparation_configuration FROM truss.catalog_runtime_installation)
  OR input->'layoutProfile' IS DISTINCT FROM (SELECT layout_profile FROM truss.catalog_runtime_installation)
  OR input->'binding' IS DISTINCT FROM '{"state":"absent"}'::jsonb OR input->'transforms' IS DISTINCT FROM '[]'::jsonb
  OR jsonb_typeof(documents) IS DISTINCT FROM 'array' OR jsonb_array_length(documents) NOT BETWEEN 1 AND 512
  OR jsonb_typeof(declarations) IS DISTINCT FROM 'array' OR jsonb_array_length(declarations)<>jsonb_array_length(documents)
  OR jsonb_typeof(input->'documents') IS DISTINCT FROM 'array' OR jsonb_array_length(input->'documents')<>jsonb_array_length(documents) THEN
  RAISE EXCEPTION 'selected original catalog inputs required' USING ERRCODE='22023'; END IF;
 FOR doc IN SELECT value FROM jsonb_array_elements(documents) LOOP
  selected_doc:=input->'documents'->i;source:=(doc->>'originalText')::jsonb;
  IF selected_doc->>'documentId' IS DISTINCT FROM doc->>'documentId'
   OR selected_doc->>'documentRevision' IS DISTINCT FROM doc->>'revision'
   OR selected_doc->'artifact'->>'sha256' IS DISTINCT FROM encode(sha256(convert_to(doc->>'originalText','UTF8')),'hex')
   OR decode(selected_doc->'artifact'->>'bytesBase64','base64') IS DISTINCT FROM convert_to(doc->>'originalText','UTF8')
   OR source->>'id' IS DISTINCT FROM doc->>'documentId' OR source->>'umf' IS DISTINCT FROM '0.7.0'
   OR doc->>'umfVersion' IS DISTINCT FROM source->>'umf'
   OR coalesce(source->'vocabularies','{}'::jsonb) IS DISTINCT FROM '{}'::jsonb OR coalesce(source->'extensions','{}'::jsonb) IS DISTINCT FROM '{}'::jsonb THEN
   RAISE EXCEPTION 'original document correspondence required' USING ERRCODE='22023'; END IF;
  SELECT count(*) FILTER(WHERE e.value->>'kind'='record'),count(*) FILTER(WHERE e.value->>'kind'='field')
   INTO expected_records,expected_fields FROM jsonb_array_elements(source->'modules') m CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e;
  SELECT count(*) INTO expected_relations FROM jsonb_array_elements(source->'modules') m CROSS JOIN LATERAL jsonb_array_elements(coalesce(m.value->'relationships','[]'::jsonb)) r;
  IF jsonb_typeof(declarations->i->'records') IS DISTINCT FROM 'array' OR jsonb_typeof(declarations->i->'relationships') IS DISTINCT FROM 'array'
   OR jsonb_array_length(declarations->i->'records')<>expected_records OR jsonb_array_length(declarations->i->'relationships')<>expected_relations
   OR (SELECT count(*) FROM jsonb_array_elements(declarations->i->'records') r CROSS JOIN LATERAL jsonb_array_elements(r.value->'fields') f)<>expected_fields THEN
   RAISE EXCEPTION 'complete original declaration set required' USING ERRCODE='22023'; END IF;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(declarations->i->'records') r
    GROUP BY r.value->>'documentId',r.value->>'moduleId',r.value->>'elementId' HAVING count(*)<>1)
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(declarations->i->'relationships') r
    GROUP BY r.value->>'documentId',r.value->>'moduleId',r.value->'declaration'->>'id' HAVING count(*)<>1) THEN
   RAISE EXCEPTION 'original declaration occurrence bijection required' USING ERRCODE='22023'; END IF;
  FOR rec IN SELECT value FROM jsonb_array_elements(declarations->i->'records') LOOP
   SELECT e.value INTO STRICT source_record FROM jsonb_array_elements(source->'modules') m CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
    WHERE m.value->>'id'=rec->>'moduleId' AND e.value->>'id'=rec->>'elementId' AND e.value->>'kind'='record';
   IF rec->>'documentId' IS DISTINCT FROM doc->>'documentId' OR rec->'declaration' IS DISTINCT FROM source_record
    OR rec->'keys' IS DISTINCT FROM coalesce(source_record->'keys','[]'::jsonb)
    OR jsonb_typeof(rec->'fields') IS DISTINCT FROM 'array' OR jsonb_typeof(source_record->'members') IS DISTINCT FROM 'array'
    OR jsonb_array_length(rec->'fields')<>jsonb_array_length(source_record->'members') THEN
    RAISE EXCEPTION 'original Record declaration required' USING ERRCODE='22023'; END IF;
   FOR field IN SELECT value FROM jsonb_array_elements(rec->'fields') LOOP
    SELECT e.value INTO STRICT source_field FROM jsonb_array_elements(source->'modules') m CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
     WHERE m.value->>'id'=field->>'fieldModule' AND e.value->>'id'=field->>'fieldId' AND e.value->>'kind'='field';
    IF field->'reference' IS DISTINCT FROM jsonb_build_object('module',field->>'fieldModule','element',field->>'fieldId')
     OR field->'declaration' IS DISTINCT FROM source_field OR source_field->>'scalarType' IS DISTINCT FROM 'string'
     OR source_field->>'cardinality' IS DISTINCT FROM 'one' OR source_field->>'nullability' NOT IN ('required','absent-allowed')
     OR EXISTS(SELECT 1 FROM jsonb_object_keys(source_field) k WHERE k NOT IN ('id','kind','name','scalarType','cardinality','nullability','extensions'))
     OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(source_record->'members') m WHERE m.value=field->'reference') THEN
     RAISE EXCEPTION 'selected original Field declaration required' USING ERRCODE='0A000'; END IF;
   END LOOP;
  END LOOP;
  IF EXISTS(SELECT 1 FROM jsonb_array_elements(declarations->i->'records') r CROSS JOIN LATERAL jsonb_array_elements(r.value->'fields') f
   GROUP BY f.value->>'fieldModule',f.value->>'fieldId' HAVING count(*)<>1) THEN
   RAISE EXCEPTION 'unique original Field ownership required' USING ERRCODE='22023'; END IF;
  FOR rel IN SELECT value FROM jsonb_array_elements(declarations->i->'relationships') LOOP
   SELECT r.value INTO STRICT source_relation FROM jsonb_array_elements(source->'modules') m CROSS JOIN LATERAL jsonb_array_elements(m.value->'relationships') r
    WHERE m.value->>'id'=rel->>'moduleId' AND r.value->>'id'=rel->'declaration'->>'id';
   IF rel->>'documentId' IS DISTINCT FROM doc->>'documentId' OR rel->'declaration' IS DISTINCT FROM source_relation
    OR (SELECT count(DISTINCT t.value->>'key') FROM jsonb_array_elements(source_relation->'target') t)<>1 THEN
    RAISE EXCEPTION 'selected original Relationship declaration required' USING ERRCODE='0A000'; END IF;
   FOR ref IN SELECT value FROM jsonb_array_elements(source_relation->'target') LOOP
    IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(source->'modules') m CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
     CROSS JOIN LATERAL jsonb_array_elements(e.value->'keys') k WHERE m.value->>'id'=ref->>'module' AND e.value->>'id'=ref->>'element'
     AND e.value->>'kind'='record' AND k.value->>'id'=ref->>'key') THEN
     RAISE EXCEPTION 'original target Key required' USING ERRCODE='22023'; END IF;
   END LOOP;
  END LOOP;
  i:=i+1;
 END LOOP;
END;
$$;

CREATE FUNCTION truss.catalog_accept(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea,
 source_bytes bytea,origin_bytes bytea,request_key text)
RETURNS TABLE(revision text,registration_id text,report_bytes bytea,replayed boolean)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output='hex' AS $$
DECLARE actor oid; installation truss.catalog_runtime_installation%ROWTYPE;
 request truss.catalog_registration_request%ROWTYPE; existing truss.catalog_registration_request%ROWTYPE;
 expected jsonb; origin bytea; original_report bytea; table_name text; columns text; rows jsonb; raw bytea; total bigint:=0;
BEGIN
 actor:=truss.catalog_actor();
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 IF installation.release_id<>'truss-catalog-runtime/0.6-candidate' OR request_key IS NULL OR octet_length(request_key) NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'selected catalog release and request key required' USING ERRCODE='22023'; END IF;
 FOREACH raw IN ARRAY ARRAY[input_bytes,documents_bytes,declarations_bytes,source_bytes,origin_bytes] LOOP
  IF raw IS NULL OR octet_length(raw) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'catalog input byte limit exceeded' USING ERRCODE='22023'; END IF;
  total:=total+octet_length(raw);
 END LOOP;
 IF total>4194304 OR jsonb_typeof(convert_from(origin_bytes,'UTF8')::jsonb) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'bounded catalog request required' USING ERRCODE='22023'; END IF;
 -- Bound concurrency without an automatic retry loop.
 PERFORM 1 FROM truss.schema_head WHERE id=1 FOR UPDATE NOWAIT;
 SELECT * INTO existing FROM truss.catalog_registration_request r WHERE r.installation_id=installation.installation_id AND r.actor_oid=actor AND r.request_key=catalog_accept.request_key;
 IF FOUND THEN
  IF existing.input_bytes IS DISTINCT FROM input_bytes OR existing.document_bytes IS DISTINCT FROM documents_bytes
   OR existing.declaration_bytes IS DISTINCT FROM declarations_bytes OR existing.source_bytes IS DISTINCT FROM source_bytes OR existing.origin_bytes IS DISTINCT FROM origin_bytes THEN
   RAISE EXCEPTION 'request key reused with different registration input' USING ERRCODE='23505'; END IF;
  PERFORM truss.catalog_actor();
  RETURN QUERY SELECT existing.revision::text,existing.registration_id::text,r.report_bytes,true FROM truss.catalog_acceptance_report r WHERE r.rev=existing.revision;
  IF NOT FOUND THEN RAISE EXCEPTION 'original registration report missing' USING ERRCODE='55000'; END IF;
  RETURN;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev=0) OR EXISTS(SELECT 1 FROM truss.type_def)
  OR EXISTS(SELECT 1 FROM truss.prop_def) OR EXISTS(SELECT 1 FROM truss.rel_def) OR EXISTS(SELECT 1 FROM truss.schema_doc) THEN
  RAISE EXCEPTION 'fresh catalog registration only in this release' USING ERRCODE='0A000'; END IF;
 PERFORM truss.catalog_require_sources(input_bytes,documents_bytes,declarations_bytes);
 origin:=convert_to((convert_from(origin_bytes,'UTF8')::jsonb||jsonb_build_object('actor',session_user::text,'db_role',session_user::text))::text,'UTF8');
 expected:=truss.catalog_expected_records(declarations_bytes,documents_bytes,origin,transaction_timestamp(),installation.genesis_at);
 FOREACH table_name IN ARRAY ARRAY['schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint'] LOOP
  rows:=expected->table_name;
  IF table_name='schema_rev' THEN rows:=jsonb_build_array(rows->1); END IF;
  SELECT string_agg(format('%I',a.attname),',' ORDER BY a.attnum) INTO columns FROM pg_attribute a
   WHERE a.attrelid=to_regclass('truss.'||table_name) AND a.attnum>0 AND NOT a.attisdropped AND a.attgenerated='';
  EXECUTE format('INSERT INTO truss.%I(%s) SELECT %s FROM jsonb_populate_recordset(NULL::truss.%I,$1)',table_name,columns,columns,table_name) USING rows;
 END LOOP;
 PERFORM truss.catalog_check_records(expected);
 request.registration_id:=gen_random_uuid();request.installation_id:=installation.installation_id;
 request.actor_oid:=actor;request.actor_name:=session_user::text;request.request_key:=request_key;
 request.writer_xid:=pg_current_xact_id();request.accepted_at:=transaction_timestamp();request.revision:=1;
 request.input_bytes:=input_bytes;request.document_bytes:=documents_bytes;request.declaration_bytes:=declarations_bytes;
 request.source_bytes:=source_bytes;request.origin_bytes:=origin_bytes;
 original_report:=truss.catalog_make_report(request);request.report_sha256:=sha256(original_report);
 INSERT INTO truss.catalog_acceptance_report VALUES(1,original_report);
 INSERT INTO truss.catalog_registration_request SELECT request.*;
 PERFORM truss.catalog_actor();
 UPDATE truss.schema_head SET rev=1 WHERE id=1 AND rev=0;
 IF NOT FOUND THEN RAISE EXCEPTION 'complete head transition required' USING ERRCODE='55000'; END IF;
 -- The deferred validator runs at commit; verify the same result before return.
 IF NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev=1) OR NOT EXISTS(SELECT 1 FROM truss.catalog_acceptance_report WHERE rev=1 AND catalog_acceptance_report.report_bytes=original_report) THEN
  RAISE EXCEPTION 'catalog publication incomplete' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT request.revision::text,request.registration_id::text,original_report,false;
END;
$$;

CREATE FUNCTION truss.catalog_report(selected_revision int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original bytea;
BEGIN
 PERFORM truss.catalog_actor();
 SELECT report_bytes INTO STRICT original FROM truss.catalog_acceptance_report WHERE rev=selected_revision;
 PERFORM truss.catalog_actor();
 RETURN original;
END;
$$;

CREATE FUNCTION truss.catalog_status() RETURNS TABLE(installation_id text,release_id text,release_sha256 text,layout_profile text,revision text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper) THEN PERFORM truss.catalog_actor(); END IF;
 RETURN QUERY SELECT i.installation_id::text,i.release_id,i.release_sha256,i.layout_profile::text,h.rev::text FROM truss.catalog_runtime_installation i CROSS JOIN truss.schema_head h WHERE h.id=1;
END;
$$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA truss FROM PUBLIC;
