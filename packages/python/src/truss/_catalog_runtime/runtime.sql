-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Catalog-only runtime. Business mutation/feed APIs are not granted by this release.
CREATE TABLE truss.catalog_runtime_installation (
 singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),installation_id uuid NOT NULL UNIQUE,
 release_id text NOT NULL,release_sha256 text NOT NULL,layout_profile jsonb NOT NULL,preparation_configuration jsonb NOT NULL,
 owner_oid oid NOT NULL,registrar_oid oid NOT NULL,genesis_at timestamptz NOT NULL);
CREATE TABLE truss.reader_catalog_validator_secret(secret bytea PRIMARY KEY CHECK(octet_length(secret)=32));
INSERT INTO truss.reader_catalog_validator_secret VALUES
 (sha256(convert_to(gen_random_uuid()::text||clock_timestamp()::text,'UTF8')));
CREATE TABLE truss.catalog_registration_request (
 registration_id uuid PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 actor_oid oid NOT NULL,actor_name text NOT NULL,request_key text NOT NULL,
 writer_xid xid8 NOT NULL,accepted_at timestamptz NOT NULL,
 input_bytes bytea NOT NULL,document_bytes bytea NOT NULL,declaration_bytes bytea NOT NULL,
 source_bytes bytea NOT NULL,origin_bytes bytea NOT NULL,
 expected_revision int,expected_documents bytea NOT NULL DEFAULT ''::bytea,
 revision int NOT NULL UNIQUE REFERENCES truss.schema_rev(rev),report_sha256 bytea NOT NULL,
 type_offset int NOT NULL CHECK(type_offset>=0),property_offset int NOT NULL CHECK(property_offset>=0),relationship_offset int NOT NULL CHECK(relationship_offset>=0),
 UNIQUE(installation_id,actor_oid,request_key),CHECK(revision>=1),
 CHECK(octet_length(request_key) BETWEEN 1 AND 1024),CHECK(octet_length(report_sha256)=32));
CREATE INDEX catalog_registration_request_writer ON truss.catalog_registration_request(writer_xid);
CREATE INDEX catalog_registration_request_input ON truss.catalog_registration_request(pg_catalog.sha256(input_bytes));
CREATE INDEX schema_doc_current ON truss.schema_doc(doc_id,rev DESC);

-- A new request for exactly the current accepted input observes the original
-- registration; it does not create another revision, report or source archive.
CREATE TABLE truss.catalog_unchanged_request (
 installation_id uuid NOT NULL REFERENCES truss.catalog_runtime_installation(installation_id),
 actor_oid oid NOT NULL,actor_name text NOT NULL,request_key text NOT NULL,
 registration_id uuid NOT NULL REFERENCES truss.catalog_registration_request(registration_id),
 origin_bytes bytea NOT NULL,expected_revision int,expected_documents bytea NOT NULL DEFAULT ''::bytea,
 PRIMARY KEY(installation_id,actor_oid,request_key),
 CHECK(octet_length(request_key) BETWEEN 1 AND 1024),
 CHECK(octet_length(origin_bytes) BETWEEN 1 AND 1048576));

CREATE FUNCTION truss.runtime_person(require_registrar boolean) RETURNS oid
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE actor record; installation truss.catalog_runtime_installation%ROWTYPE;
 member_of_owner boolean; member_of_registrar boolean; member_of_server_capability boolean; unsafe_switchable boolean;
BEGIN
 IF current_setting('transaction_isolation')<>'read committed' THEN
  RAISE EXCEPTION 'catalog authorization requires READ COMMITTED' USING ERRCODE='0A000'; END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF current_setting('truss.runtime_digest',true) IS DISTINCT FROM installation.release_sha256 THEN
  RAISE EXCEPTION 'latest runtime required; explicitly migrate the installation' USING ERRCODE='0A000'; END IF;
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
    OR CASE WHEN s.active_oid=actor.oid THEN false ELSE (has_schema_privilege(r.oid,'truss','CREATE')
    OR EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='truss'
      AND ((c.relkind IN ('r','p') AND (has_table_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
        OR has_any_column_privilege(r.oid,c.oid,'SELECT,INSERT,UPDATE,REFERENCES')))
       OR (c.relkind='S' AND has_sequence_privilege(r.oid,c.oid,'USAGE,SELECT,UPDATE'))))) END) INTO unsafe_switchable;
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
  RAISE EXCEPTION 'catalog registration authorization required' USING ERRCODE='P1403'; END IF;
 RETURN actor.oid;
END;
$$;

CREATE FUNCTION truss.catalog_actor() RETURNS oid
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp
AS 'SELECT truss.runtime_person(true)';
REVOKE ALL ON FUNCTION truss.runtime_person(boolean) FROM PUBLIC;

-- Read current native metadata directly; reconstruct an explicitly historical revision only.
CREATE FUNCTION truss.catalog_all_expected_records(selected_revision int DEFAULT NULL) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET bytea_output=hex AS $$
DECLARE expected jsonb:='{}';target_revision int;
BEGIN
 -- The no-argument call is the acceptance planner's working basis. Keep the
 -- live definitions and only their source archives, rather than copying the
 -- append-only archive and change log into every successive plan.
 IF selected_revision IS NULL THEN
  WITH head AS MATERIALIZED (SELECT rev FROM truss.schema_head WHERE id=1),
  source_coordinates AS MATERIALIZED (
   SELECT t.definition_rev rev,t.definition_doc_ord ord,t.definition_document_id doc_id FROM truss.type_def t
   UNION SELECT p.definition_rev,p.definition_doc_ord,p.definition_document_id FROM truss.prop_def p
   UNION SELECT k.definition_rev,k.definition_doc_ord,k.definition_document_id
    FROM truss.key_def k
   UNION SELECT r.definition_rev,r.definition_doc_ord,r.definition_document_id FROM truss.rel_def r),
  latest_documents AS MATERIALIZED (
   SELECT DISTINCT ON (d.doc_id) d.rev,d.ord,d.doc_id
   FROM truss.schema_doc d
   ORDER BY d.doc_id,d.rev DESC,d.ord DESC),
  needed_documents AS MATERIALIZED (
   SELECT rev,ord,doc_id FROM source_coordinates UNION SELECT rev,ord,doc_id FROM latest_documents),
  documents AS MATERIALIZED (
   SELECT d.rev,d.ord,d.doc_id,d.document::jsonb source
   FROM truss.schema_doc d JOIN needed_documents n USING(rev,ord,doc_id)),
  source_elements AS MATERIALIZED (
   SELECT d.rev,d.ord,d.doc_id,m.value->>'id' module_id,e.value->>'id' element_id,e.value element
   FROM documents d CROSS JOIN LATERAL jsonb_array_elements(d.source->'modules') m
   CROSS JOIN LATERAL jsonb_array_elements(coalesce(m.value->'elements','[]'::jsonb)) e)
  SELECT jsonb_build_object(
   'schema_rev',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb)
    FROM truss.schema_rev r CROSS JOIN head h WHERE r.rev=0 OR r.rev=h.rev),
   'schema_doc',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.rev,d.ord,d.doc_id),'[]'::jsonb)
    FROM truss.schema_doc d JOIN needed_documents n USING(rev,ord,doc_id)),
   'type_def',(SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.type_id),'[]'::jsonb) FROM truss.type_def t),
   'prop_def',(SELECT coalesce(jsonb_agg(to_jsonb(p)||jsonb_build_object('_originalField',e.element) ORDER BY p.prop_id),'[]'::jsonb)
    FROM truss.prop_def p JOIN source_elements e ON e.rev=p.definition_rev AND e.ord=p.definition_doc_ord
     AND e.doc_id=p.definition_document_id AND e.module_id=p.declaration_module AND e.element_id=p.element),
   'key_def',(SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.type_id,k.key_num),'[]'::jsonb) FROM truss.key_def k),
   'rel_def',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rel_type_id),'[]'::jsonb) FROM truss.rel_def r),
   'relationship_lineage',(SELECT coalesce(jsonb_agg(to_jsonb(l) ORDER BY l.rel_type_id),'[]'::jsonb) FROM truss.relationship_lineage l),
   'rel_endpoint',(SELECT coalesce(jsonb_agg(to_jsonb(e) ORDER BY e.rel_type_id,e.source_type,e.target_type),'[]'::jsonb) FROM truss.rel_endpoint e),
   'schema_change','[]'::jsonb) INTO expected;
  RETURN expected;
 END IF;
 SELECT greatest(0,least(selected_revision,(SELECT rev FROM truss.schema_head WHERE id=1)))
  INTO target_revision;
 WITH target AS MATERIALIZED (SELECT target_revision rev),
 future_changes AS MATERIALIZED (
  SELECT DISTINCT ON(c.kind,c.def_id) c.kind,c.def_id,c.before
  FROM truss.schema_change c CROSS JOIN target x WHERE c.rev>x.rev
  ORDER BY c.kind,c.def_id,c.rev,c.seq),
 type_images AS MATERIALIZED (
  SELECT CASE WHEN c.def_id IS NULL THEN to_jsonb(t) ELSE c.before END value
  FROM truss.type_def t CROSS JOIN target x
  LEFT JOIN future_changes c ON c.kind='type' AND c.def_id=t.type_id
  WHERE t.since_rev<=x.rev),
 property_images AS MATERIALIZED (
  SELECT CASE WHEN c.def_id IS NULL THEN to_jsonb(p) ELSE c.before END value
  FROM truss.prop_def p CROSS JOIN target x
  LEFT JOIN future_changes c ON c.kind='prop' AND c.def_id=p.prop_id
  WHERE p.since_rev<=x.rev),
 key_images AS MATERIALIZED (
  SELECT to_jsonb(k) value FROM truss.key_def k CROSS JOIN target x WHERE k.since_rev<=x.rev),
 relation_images AS MATERIALIZED (
  SELECT CASE WHEN c.def_id IS NULL THEN to_jsonb(r) ELSE c.before END value
  FROM truss.rel_def r CROSS JOIN target x
  LEFT JOIN future_changes c ON c.kind='rel' AND c.def_id=r.rel_type_id
  WHERE r.since_rev<=x.rev),
 needed_documents AS MATERIALIZED (
  SELECT (p.value->>'definition_rev')::int rev,(p.value->>'definition_doc_ord')::int ord,
   p.value->>'definition_document_id' doc_id FROM property_images p
  UNION
  SELECT (r.value->>'definition_rev')::int,(r.value->>'definition_doc_ord')::int,
   r.value->>'definition_document_id' FROM relation_images r),
 archives AS MATERIALIZED (
  SELECT d.rev,d.ord,d.doc_id,d.document::jsonb document FROM truss.schema_doc d
  JOIN needed_documents n USING(rev,ord,doc_id)),
 source_elements AS MATERIALIZED (
  SELECT d.rev,d.ord,d.doc_id,m.value->>'id' module_id,e.value->>'id' element_id,e.value element
  FROM archives d CROSS JOIN LATERAL jsonb_array_elements(d.document->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(coalesce(m.value->'elements','[]'::jsonb)) e),
 source_relationships AS MATERIALIZED (
  SELECT d.rev,d.ord,d.doc_id,m.value->>'id' module_id,r.value->>'id' relationship_id,r.value declaration
  FROM archives d CROSS JOIN LATERAL jsonb_array_elements(d.document->'modules') m
  CROSS JOIN LATERAL jsonb_array_elements(coalesce(m.value->'relationships','[]'::jsonb)) r),
 properties_asof AS MATERIALIZED (
  SELECT p.value||jsonb_build_object('_originalField',e.element) value
  FROM property_images p JOIN source_elements e
   ON e.rev=(p.value->>'definition_rev')::int AND e.ord=(p.value->>'definition_doc_ord')::int
   AND e.doc_id=p.value->>'definition_document_id' AND e.module_id=p.value->>'declaration_module'
   AND e.element_id=p.value->>'element'),
 relations_asof AS MATERIALIZED (
  SELECT r.value,s.declaration FROM relation_images r JOIN source_relationships s
   ON s.rev=(r.value->>'definition_rev')::int AND s.ord=(r.value->>'definition_doc_ord')::int
   AND s.doc_id=r.value->>'definition_document_id' AND s.module_id=r.value->>'module'
   AND s.relationship_id=r.value->>'rel_id'),
 endpoint_rows AS (
  SELECT DISTINCT (r.value->>'rel_type_id')::int rel_type_id,(source_type.value->>'type_id')::int source_type,
   (target_type.value->>'type_id')::int target_type
  FROM relations_asof r
  CROSS JOIN LATERAL jsonb_array_elements(r.declaration->'source') source_ref
  CROSS JOIN LATERAL jsonb_array_elements(r.declaration->'target') target_ref
  JOIN type_images source_type ON source_type.value->>'document_id'=r.value->>'document_id'
   AND source_type.value->>'module'=source_ref.value->>'module' AND source_type.value->>'element'=source_ref.value->>'element'
  JOIN type_images target_type ON target_type.value->>'document_id'=r.value->>'document_id'
   AND target_type.value->>'module'=target_ref.value->>'module' AND target_type.value->>'element'=target_ref.value->>'element'),
 lineage_rows AS (
  SELECT to_jsonb(l) value FROM truss.relationship_lineage l JOIN relations_asof r
   ON (r.value->>'rel_type_id')::int=l.rel_type_id)
 SELECT jsonb_build_object(
  'schema_rev',(SELECT coalesce(jsonb_agg(to_jsonb(r) ORDER BY r.rev),'[]'::jsonb)
   FROM truss.schema_rev r CROSS JOIN target x WHERE r.rev<=x.rev),
  'schema_doc',(SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.rev,d.ord),'[]'::jsonb)
   FROM truss.schema_doc d CROSS JOIN target x WHERE d.rev<=x.rev),
  'type_def',(SELECT coalesce(jsonb_agg(value ORDER BY (value->>'type_id')::int),'[]'::jsonb) FROM type_images),
  'prop_def',(SELECT coalesce(jsonb_agg(value ORDER BY (value->>'prop_id')::int),'[]'::jsonb) FROM properties_asof),
  'key_def',(SELECT coalesce(jsonb_agg(value ORDER BY (value->>'type_id')::int,(value->>'key_num')::int),'[]'::jsonb) FROM key_images),
  'rel_def',(SELECT coalesce(jsonb_agg(value ORDER BY (value->>'rel_type_id')::int),'[]'::jsonb) FROM relation_images),
  'relationship_lineage',(SELECT coalesce(jsonb_agg(value ORDER BY (value->>'rel_type_id')::int),'[]'::jsonb) FROM lineage_rows),
  'rel_endpoint',(SELECT coalesce(jsonb_agg(jsonb_build_object('rel_type_id',rel_type_id,'source_type',source_type,'target_type',target_type)
    ORDER BY rel_type_id,source_type,target_type),'[]'::jsonb) FROM endpoint_rows),
  'schema_change',(SELECT coalesce(jsonb_agg(to_jsonb(c) ORDER BY c.rev,c.seq),'[]'::jsonb)
   FROM truss.schema_change c CROSS JOIN target x WHERE c.rev<=x.rev)) INTO expected;
 RETURN expected;
END;
$$;

CREATE FUNCTION truss.catalog_make_report(request truss.catalog_registration_request,planned_basis jsonb DEFAULT NULL) RETURNS bytea
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET bytea_output='hex' AS $$
DECLARE report jsonb; source jsonb; basis jsonb;rebind_profile text;profile_count int;
BEGIN
  source:=convert_from(request.source_bytes,'UTF8')::jsonb;
  report:=jsonb_build_object('interfaceVersion','truss-catalog-registration-report/0.6',
   'registrationId',request.registration_id::text,'installationId',request.installation_id::text,
   'revision',request.revision::text,'actor',request.actor_name,'actorOid',request.actor_oid::text,
   'writerXid',request.writer_xid::text,'requestKey',request.request_key,
   'acceptedAt',to_char(request.accepted_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'release',source->'runtimeRelease','acceptedInput',convert_from(request.input_bytes,'UTF8')::jsonb,
   'source',source,'assertedOrigin',convert_from(request.origin_bytes,'UTF8')::jsonb,
   'effects',jsonb_build_object(
    'reboundObjects',(SELECT count(*) FROM truss.runtime_catalog_rebind_transition WHERE registration_id=request.registration_id),
    'keyBackfills',(SELECT count(*) FROM truss.runtime_catalog_key_backfill WHERE registration_id=request.registration_id)));
  -- Compact receipts keep effect payloads in their native history homes, but
  -- must still identify the original encoding used by those effects.
  IF EXISTS(SELECT 1 FROM truss.runtime_catalog_rebind_transition t WHERE t.registration_id=request.registration_id) THEN
   SELECT min(truss.catalog_rebind_profile(t.journal)),count(DISTINCT truss.catalog_rebind_profile(t.journal))
    INTO rebind_profile,profile_count FROM truss.runtime_catalog_rebind_transition t WHERE t.registration_id=request.registration_id;
   IF profile_count<>1 THEN RAISE EXCEPTION 'one original registration rebind profile required' USING ERRCODE='55000';END IF;
   report:=report||jsonb_build_object('rebindProfile',rebind_profile);
  END IF;
  IF EXISTS(SELECT 1 FROM truss.runtime_catalog_key_backfill t WHERE t.registration_id=request.registration_id) THEN
   basis:=coalesce(planned_basis,truss.catalog_all_expected_records(request.revision));
   report:=report||jsonb_build_object('keyBackfillProfile',CASE WHEN EXISTS(
    SELECT 1 FROM truss.runtime_catalog_key_backfill b CROSS JOIN LATERAL jsonb_array_elements(b.effects) e
    JOIN jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k ON k.type_id=b.type_id AND k.key_num=(e.value->>'keyNumber')::smallint
    JOIN jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p ON p.type_id=k.type_id AND p.prop_id=ANY(k.prop_ids)
    WHERE b.registration_id=request.registration_id AND p.since_rev=request.revision)
    THEN 'truss-catalog-key-backfill/0.2' ELSE 'truss-catalog-key-backfill/0.1' END);
  END IF;
  report:=report||jsonb_build_object('enforcement',truss.catalog_enforcement(request.revision));
  RETURN convert_to(report::text,'UTF8');
END;
$$;

CREATE FUNCTION truss.catalog_validate_completion() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE request truss.catalog_registration_request%ROWTYPE; installation truss.catalog_runtime_installation%ROWTYPE;
 expected jsonb; origin bytea; original_report bytea;
BEGIN
 IF TG_TABLE_SCHEMA<>'truss' OR TG_TABLE_NAME<>'schema_head' OR NEW.id<>1 OR NEW.rev<1 THEN
  RAISE EXCEPTION 'selected catalog completion required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 SELECT * INTO STRICT request FROM truss.catalog_registration_request WHERE revision=NEW.rev;
 IF request.actor_oid IS DISTINCT FROM truss.catalog_actor() THEN
  RAISE EXCEPTION 'current original registration authority required' USING ERRCODE='P1403'; END IF;
 IF request.installation_id<>installation.installation_id OR NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev>=request.revision) THEN
  RAISE EXCEPTION 'complete catalog publication required' USING ERRCODE='55000'; END IF;
 origin:=convert_to((convert_from(request.origin_bytes,'UTF8')::jsonb||jsonb_build_object('actor',request.actor_name,'db_role',request.actor_name))::text,'UTF8');
 SELECT report_bytes INTO STRICT original_report FROM truss.catalog_acceptance_report WHERE rev=request.revision;
 RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER catalog_completion AFTER UPDATE ON truss.schema_head
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.catalog_validate_completion();
ALTER TABLE truss.schema_head ENABLE ALWAYS TRIGGER catalog_completion;

CREATE FUNCTION truss.catalog_validate_unchanged() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original truss.catalog_registration_request%ROWTYPE; stored truss.catalog_unchanged_request%ROWTYPE;
 expected jsonb; original_origin bytea; report bytea; request_count bigint;
BEGIN
 IF TG_TABLE_SCHEMA<>'truss' OR TG_TABLE_NAME<>'catalog_unchanged_request'
  OR NEW.actor_oid IS DISTINCT FROM truss.catalog_actor() OR NEW.actor_name IS DISTINCT FROM session_user::text THEN
  RAISE EXCEPTION 'current unchanged request authority required' USING ERRCODE='P1403'; END IF;
 SELECT * INTO STRICT stored FROM truss.catalog_unchanged_request r
  WHERE r.installation_id=NEW.installation_id AND r.actor_oid=NEW.actor_oid AND r.request_key=NEW.request_key;
 IF stored IS DISTINCT FROM NEW THEN RAISE EXCEPTION 'original unchanged request required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT original FROM truss.catalog_registration_request r WHERE r.registration_id=NEW.registration_id;
 IF original.installation_id IS DISTINCT FROM NEW.installation_id
  OR NOT EXISTS(SELECT 1 FROM truss.runtime_current_installation() i WHERE i.installation_id=NEW.installation_id)
  OR NOT EXISTS(SELECT 1 FROM truss.schema_head h WHERE h.id=1 AND h.rev>=original.revision)
  OR jsonb_typeof(convert_from(NEW.origin_bytes,'UTF8')::jsonb) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original current registration required' USING ERRCODE='55000'; END IF;
 SELECT count(*) INTO request_count FROM (
  SELECT 1 FROM truss.catalog_registration_request r WHERE r.installation_id=NEW.installation_id AND r.actor_oid=NEW.actor_oid AND r.request_key=NEW.request_key
  UNION ALL SELECT 1 FROM truss.catalog_unchanged_request r WHERE r.installation_id=NEW.installation_id AND r.actor_oid=NEW.actor_oid AND r.request_key=NEW.request_key) requests;
 IF request_count<>1 THEN RAISE EXCEPTION 'unambiguous catalog request required' USING ERRCODE='55000'; END IF;
 original_origin:=convert_to((convert_from(original.origin_bytes,'UTF8')::jsonb||jsonb_build_object('actor',original.actor_name,'db_role',original.actor_name))::text,'UTF8');
 SELECT report_bytes INTO STRICT report FROM truss.catalog_acceptance_report WHERE rev=original.revision;
 RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER catalog_unchanged_completion AFTER INSERT ON truss.catalog_unchanged_request
DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.catalog_validate_unchanged();
ALTER TABLE truss.catalog_unchanged_request ENABLE ALWAYS TRIGGER catalog_unchanged_completion;

CREATE FUNCTION truss.catalog_immutable() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN RAISE EXCEPTION 'immutable catalog source or result' USING ERRCODE='55000'; END;
$$;
DO $$ DECLARE table_name text; BEGIN
 FOREACH table_name IN ARRAY ARRAY['schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint','schema_change','catalog_acceptance_report','catalog_registration_request','catalog_unchanged_request','catalog_runtime_installation'] LOOP
  EXECUTE format('CREATE TRIGGER catalog_immutable BEFORE %s ON truss.%I FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable()',CASE WHEN table_name IN ('type_def','prop_def','rel_def') THEN 'DELETE OR TRUNCATE' ELSE 'UPDATE OR DELETE OR TRUNCATE' END,table_name);
  EXECUTE format('ALTER TABLE truss.%I ENABLE ALWAYS TRIGGER catalog_immutable',table_name);
 END LOOP;
END $$;

CREATE FUNCTION truss.catalog_require_sources(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea) RETURNS void
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE input jsonb;documents jsonb;declarations jsonb;
BEGIN
 input:=convert_from(input_bytes,'UTF8')::jsonb;documents:=convert_from(documents_bytes,'UTF8')::jsonb;
 declarations:=convert_from(declarations_bytes,'UTF8')::jsonb;
 IF input->>'interfaceVersion' IS DISTINCT FROM 'truss-acceptance-input/0.2.0' OR jsonb_typeof(input) IS DISTINCT FROM 'object' OR (input-'interfaceVersion'-'documents') IS DISTINCT FROM (SELECT preparation_configuration FROM truss.runtime_current_installation())
  OR input->'layoutProfile' IS DISTINCT FROM (SELECT layout_profile FROM truss.runtime_current_installation())
  OR input->'binding' IS DISTINCT FROM '{"state":"absent"}'::jsonb OR input->'transforms' IS DISTINCT FROM '[]'::jsonb
  OR jsonb_typeof(documents) IS DISTINCT FROM 'array' OR jsonb_array_length(documents) NOT BETWEEN 1 AND 512
  OR jsonb_typeof(declarations) IS DISTINCT FROM 'array' OR jsonb_array_length(declarations)<>jsonb_array_length(documents)
  OR jsonb_typeof(input->'documents') IS DISTINCT FROM 'array' OR jsonb_array_length(input->'documents')<>jsonb_array_length(documents) THEN
  RAISE EXCEPTION 'selected original catalog inputs required' USING ERRCODE='22023'; END IF;
 -- Current trusted preparation validates and compiles the source once.
 -- Do not replay its field/key/member correspondence inside PostgreSQL.
END;
$$;

-- The selected DDD extension evolution is an append-only optional or empty-Record required Field
-- whose exact core Field and Record member are added together. Unknown payload
-- content stays in source custody; no other DDD change is inferred compatible.
CREATE FUNCTION truss.catalog_ddd_optional_evolution_supported(documents_bytes bytea) RETURNS boolean
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE candidate jsonb;candidate_source jsonb;original jsonb;old_module jsonb;new_module jsonb;old_record jsonb;new_record jsonb;
 old_ddd jsonb;new_ddd jsonb;old_fields jsonb;new_fields jsonb;appended_member jsonb;added_name text;
 field_module text;field_id text;field_element jsonb;core_scalar text;ddd_scalar text;old_count int;member_index int;
BEGIN
 FOR candidate IN SELECT value FROM jsonb_array_elements(convert_from(documents_bytes,'UTF8')::jsonb) LOOP
  SELECT document::jsonb INTO original FROM truss.schema_doc
   WHERE doc_id=candidate->>'documentId' ORDER BY rev DESC LIMIT 1;
  IF NOT FOUND OR original IS NULL THEN CONTINUE;END IF;
  candidate_source:=(candidate->>'originalText')::jsonb;
  IF original->'vocabularies'->'umf.ddd' IS DISTINCT FROM candidate_source->'vocabularies'->'umf.ddd'
    OR original->'extensions'->'umf.ddd' IS DISTINCT FROM candidate_source->'extensions'->'umf.ddd' THEN RETURN false;END IF;
  FOR old_module IN SELECT value FROM jsonb_array_elements(coalesce(original->'modules','[]'::jsonb)) LOOP
   SELECT value INTO new_module FROM jsonb_array_elements(coalesce(candidate_source->'modules','[]'::jsonb)) WHERE value->>'id'=old_module->>'id';
   IF NOT FOUND THEN
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(coalesce(old_module->'elements','[]'::jsonb)) e
      WHERE e.value->>'kind'='record' AND e.value->'extensions' ? 'umf.ddd') THEN RETURN false;END IF;
    CONTINUE;
   END IF;
   IF old_module->'extensions'->'umf.ddd' IS DISTINCT FROM new_module->'extensions'->'umf.ddd' THEN RETURN false;END IF;
   FOR old_record IN SELECT value FROM jsonb_array_elements(coalesce(old_module->'elements','[]'::jsonb))
    WHERE value->>'kind'='record' LOOP
    SELECT value INTO new_record FROM jsonb_array_elements(coalesce(new_module->'elements','[]'::jsonb))
     WHERE value->>'id'=old_record->>'id' AND value->>'kind'='record';
    old_ddd:=old_record->'extensions'->'umf.ddd';
    IF NOT FOUND THEN IF old_ddd IS NOT NULL THEN RETURN false;END IF;CONTINUE;END IF;
    new_ddd:=new_record->'extensions'->'umf.ddd';
    IF old_ddd IS NOT DISTINCT FROM new_ddd THEN
     IF old_ddd IS NOT NULL AND (original->'vocabularies'->'umf.ddd'->>'version' IS DISTINCT FROM candidate_source->'vocabularies'->'umf.ddd'->>'version'
       OR original->'vocabularies'->'umf.ddd'->>'version' IS DISTINCT FROM '0.1.0') THEN RETURN false;END IF;
     IF old_ddd ? 'fields' AND old_record->'members' IS DISTINCT FROM new_record->'members' THEN RETURN false;END IF;
     CONTINUE;
    END IF;
    old_fields:=old_ddd->'fields';new_fields:=new_ddd->'fields';
    IF original->>'umf' IS DISTINCT FROM '0.10.0'
      OR candidate_source->>'umf' IS DISTINCT FROM '0.10.0'
      OR original->'vocabularies'->'umf.ddd'->>'version' IS DISTINCT FROM '0.1.0'
      OR candidate_source->'vocabularies'->'umf.ddd'->>'version' IS DISTINCT FROM '0.1.0'
      OR jsonb_typeof(old_fields) IS DISTINCT FROM 'object' OR jsonb_typeof(new_fields) IS DISTINCT FROM 'object' THEN
      RETURN false;
    END IF;
    IF (new_record-ARRAY['members','extensions']) IS DISTINCT FROM (old_record-ARRAY['members','extensions'])
      OR ((new_record->'extensions')-'umf.ddd'::text) IS DISTINCT FROM ((old_record->'extensions')-'umf.ddd'::text)
      OR (new_ddd-'fields'::text) IS DISTINCT FROM (old_ddd-'fields'::text)
      OR (SELECT count(*) FROM jsonb_object_keys(new_fields))<>(SELECT count(*) FROM jsonb_object_keys(old_fields))+1
      OR jsonb_array_length(coalesce(new_record->'members','[]'::jsonb))<>jsonb_array_length(coalesce(old_record->'members','[]'::jsonb))+1
      OR EXISTS(SELECT 1 FROM jsonb_object_keys(old_fields) AS k(key) WHERE new_fields->(k.key) IS DISTINCT FROM old_fields->(k.key)) THEN
      RETURN false;
    END IF;
    old_count:=jsonb_array_length(old_record->'members');
    IF old_count>0 THEN
     FOR member_index IN 0..old_count-1 LOOP
      IF old_record->'members'->member_index IS DISTINCT FROM new_record->'members'->member_index THEN RETURN false;END IF;
     END LOOP;
    END IF;
    appended_member:=new_record->'members'->old_count;
    IF jsonb_typeof(appended_member) IS DISTINCT FROM 'object'
      OR (SELECT count(*) FROM jsonb_object_keys(appended_member))<>2
      OR jsonb_typeof(appended_member->'module') IS DISTINCT FROM 'string'
      OR jsonb_typeof(appended_member->'element') IS DISTINCT FROM 'string' THEN RETURN false;END IF;
    added_name:=NULL;
    SELECT k.key INTO added_name FROM jsonb_object_keys(new_fields) AS k(key) WHERE NOT (old_fields ? k.key);
    IF added_name IS NULL OR old_fields ? added_name THEN RETURN false;END IF;
    field_module:=appended_member->>'module';field_id:=appended_member->>'element';
    SELECT element.value INTO field_element
     FROM jsonb_array_elements(coalesce(candidate_source->'modules','[]'::jsonb)) module(value)
     CROSS JOIN LATERAL jsonb_array_elements(coalesce(module.value->'elements','[]'::jsonb)) element(value)
     WHERE module.value->>'id'=field_module AND element.value->>'id'=field_id;
    IF NOT FOUND OR field_element->>'kind' IS DISTINCT FROM 'field'
      OR field_element->>'name' IS DISTINCT FROM added_name
      OR field_element->>'nullability' NOT IN ('absent-allowed','required')
      OR field_element->>'cardinality' IS DISTINCT FROM 'one' THEN RETURN false;END IF;
    core_scalar:=field_element->>'scalarType';
    ddd_scalar:=CASE core_scalar WHEN 'string' THEN 'string' WHEN 'boolean' THEN 'boolean'
      WHEN 'integer' THEN 'integer' WHEN 'decimal' THEN 'decimal' WHEN 'timestamp' THEN 'date-time' WHEN 'binary' THEN 'bytes' END;
    IF ddd_scalar IS NULL OR jsonb_typeof(new_fields->added_name) IS DISTINCT FROM 'object'
      OR (SELECT count(*) FROM jsonb_object_keys(new_fields->added_name)) NOT BETWEEN 2 AND 3
      OR ((new_fields->added_name)-ARRAY['type','cardinality','description']) IS DISTINCT FROM '{}'::jsonb
      OR jsonb_typeof(new_fields->added_name->'cardinality') IS DISTINCT FROM 'string'
      OR new_fields->added_name->>'cardinality' IS DISTINCT FROM (CASE field_element->>'nullability' WHEN 'required' THEN 'one' ELSE 'optional' END)
      OR jsonb_typeof(new_fields->added_name->'type') IS DISTINCT FROM 'object'
      OR (SELECT count(*) FROM jsonb_object_keys(new_fields->added_name->'type'))<>2
      OR new_fields->added_name->'type'->>'kind' IS DISTINCT FROM 'scalar'
      OR new_fields->added_name->'type'->>'name' IS DISTINCT FROM ddd_scalar
      OR new_fields->added_name ? 'description' AND jsonb_typeof(new_fields->added_name->'description') IS DISTINCT FROM 'string' THEN
      RETURN false;
    END IF;
   END LOOP;
  END LOOP;
 END LOOP;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_ddd_optional_evolution_supported(bytea) FROM PUBLIC;

CREATE FUNCTION truss.catalog_accept_with_keys(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea,
 source_bytes bytea,origin_bytes bytea,request_key text,key_receipts bytea,preview_mode boolean,
 expected_revision int,expected_documents bytea)
RETURNS TABLE(revision text,registration_id text,report_bytes bytea,replayed boolean,unchanged boolean,actor_name text,violations_bytes bytea)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output='hex' AS $$
DECLARE actor oid; installation truss.catalog_runtime_installation%ROWTYPE;
 request truss.catalog_registration_request%ROWTYPE; existing truss.catalog_registration_request%ROWTYPE;
 alias_request truss.catalog_unchanged_request%ROWTYPE;
 expected jsonb; prior_expected jsonb; origin bytea; original_report bytea; table_name text; columns text; assignments text;identity_column text;conflict_columns text; rows jsonb; raw bytea; total bigint:=0; request_count bigint;
 expected_docs jsonb; expected_doc jsonb;
 prior_revision int;new_revision int;type_start int;property_start int;relationship_start int;component_index int:=0;component_limit int;compact boolean;violations bytea;key_candidates jsonb;verified_keys jsonb;
BEGIN
 IF preview_mode IS NULL THEN RAISE EXCEPTION 'explicit catalog mode required' USING ERRCODE='22023';END IF;
 compact:=(convert_from(input_bytes,'UTF8')::jsonb)->>'interfaceVersion'='truss-acceptance-input/0.2.0';
 IF compact AND declarations_bytes<>''::bytea THEN RAISE EXCEPTION 'source-only catalog request required' USING ERRCODE='22023';END IF;
 actor:=truss.catalog_actor();
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id<>'truss-catalog-runtime/0.74-candidate' OR request_key IS NULL OR octet_length(request_key) NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'selected catalog release and request key required' USING ERRCODE='22023'; END IF;
 FOREACH raw IN ARRAY ARRAY[input_bytes,documents_bytes,declarations_bytes,source_bytes,origin_bytes] LOOP
  component_index:=component_index+1;
  component_limit:=CASE WHEN component_index=5 THEN 1048576 WHEN component_index=4 THEN 4194304 ELSE 16777216 END;
  IF raw IS NULL OR NOT (compact AND component_index=3 AND octet_length(raw)=0) AND octet_length(raw) NOT BETWEEN 1 AND component_limit THEN
   RAISE EXCEPTION 'catalog input byte limit exceeded' USING ERRCODE='22023'; END IF;
  total:=total+octet_length(raw);
 END LOOP;
 IF total>16777216 OR jsonb_typeof(convert_from(origin_bytes,'UTF8')::jsonb) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'bounded catalog request required' USING ERRCODE='22023'; END IF;
 IF expected_revision IS NOT NULL AND expected_revision NOT BETWEEN -1 AND 2147483647
  OR expected_documents IS NULL OR octet_length(expected_documents) NOT BETWEEN 2 AND 1048576 THEN
  RAISE EXCEPTION 'bounded catalog source expectations required' USING ERRCODE='22023';END IF;
 -- The private host's immutable semantic-parameter lane excludes SQL NULL.
 -- Normalize its -1 sentinel immediately so custody and replay remain byte-for-byte
 -- identical to historical no-CAS requests.
 IF expected_revision=-1 THEN expected_revision:=NULL;END IF;
 expected_docs:=convert_from(expected_documents,'UTF8')::jsonb;
 IF jsonb_typeof(expected_docs) IS DISTINCT FROM 'array' OR jsonb_array_length(expected_docs)>512 THEN
  RAISE EXCEPTION 'catalog source expectations required' USING ERRCODE='22023';END IF;
 IF jsonb_array_length(expected_docs)>0 THEN
  IF jsonb_array_length(expected_docs)<>jsonb_array_length(convert_from(documents_bytes,'UTF8')::jsonb)
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(expected_docs) e
    WHERE jsonb_typeof(e.value) IS DISTINCT FROM 'object'
     OR (SELECT count(*) FROM jsonb_object_keys(e.value))<>2
     OR jsonb_typeof(e.value->'documentId') IS DISTINCT FROM 'string'
     OR octet_length(e.value->>'documentId') NOT BETWEEN 1 AND 4096
     OR jsonb_typeof(e.value->'sourceCatalogRevision') IS DISTINCT FROM 'number'
     OR (e.value->>'sourceCatalogRevision') !~ '^(0|[1-9][0-9]*)$'
     OR (e.value->>'sourceCatalogRevision')::numeric>2147483647)
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(expected_docs) e GROUP BY e.value->>'documentId' HAVING count(*)<>1)
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(convert_from(documents_bytes,'UTF8')::jsonb) d GROUP BY d.value->>'documentId' HAVING count(*)<>1)
   OR EXISTS(SELECT 1 FROM jsonb_array_elements(convert_from(documents_bytes,'UTF8')::jsonb) d
    WHERE NOT EXISTS(SELECT 1 FROM jsonb_array_elements(expected_docs) e WHERE e.value->>'documentId'=d.value->>'documentId')) THEN
   RAISE EXCEPTION 'exact submitted document expectation set required' USING ERRCODE='22023';END IF;
 END IF;
 IF compact THEN declarations_bytes:=truss.runtime_owned_catalog_declarations(documents_bytes);END IF;
 -- Bound concurrency without an automatic retry loop.
 SELECT rev INTO STRICT prior_revision FROM truss.schema_head WHERE id=1 FOR UPDATE NOWAIT;
 prior_expected:=truss.catalog_all_expected_records();
 SELECT count(*) INTO request_count FROM (
  SELECT 1 FROM truss.catalog_registration_request r WHERE r.installation_id=installation.installation_id AND r.actor_oid=actor AND r.request_key=catalog_accept_with_keys.request_key
  UNION ALL SELECT 1 FROM truss.catalog_unchanged_request r WHERE r.installation_id=installation.installation_id AND r.actor_oid=actor AND r.request_key=catalog_accept_with_keys.request_key) requests;
 IF request_count>1 THEN RAISE EXCEPTION 'unambiguous catalog request required' USING ERRCODE='55000'; END IF;
 SELECT * INTO existing FROM truss.catalog_registration_request r WHERE r.installation_id=installation.installation_id AND r.actor_oid=actor AND r.request_key=catalog_accept_with_keys.request_key;
 IF FOUND THEN
  IF existing.input_bytes IS DISTINCT FROM input_bytes OR existing.expected_revision IS DISTINCT FROM expected_revision OR existing.expected_documents IS DISTINCT FROM expected_documents OR (CASE WHEN octet_length(existing.document_bytes)=0 THEN
    convert_from(truss.runtime_owned_request_documents(existing),'UTF8')::jsonb IS DISTINCT FROM convert_from(documents_bytes,'UTF8')::jsonb
   ELSE existing.document_bytes IS DISTINCT FROM documents_bytes OR existing.declaration_bytes IS DISTINCT FROM declarations_bytes END) OR existing.origin_bytes IS DISTINCT FROM origin_bytes THEN
   RAISE EXCEPTION 'request key reused with different registration input' USING ERRCODE='P1001'; END IF;
  PERFORM truss.catalog_actor();
  PERFORM truss.catalog_rebind_report_reader(existing.registration_id);
  RETURN QUERY SELECT existing.revision::text,existing.registration_id::text,r.report_bytes,true,false,existing.actor_name,NULL::bytea FROM truss.catalog_acceptance_report r WHERE r.rev=existing.revision;
  IF NOT FOUND THEN RAISE EXCEPTION 'original registration report missing' USING ERRCODE='55000'; END IF;
  PERFORM truss.catalog_actor();
  PERFORM truss.catalog_rebind_report_reader(existing.registration_id);
  RETURN;
 END IF;
 SELECT * INTO alias_request FROM truss.catalog_unchanged_request r
  WHERE r.installation_id=installation.installation_id AND r.actor_oid=actor AND r.request_key=catalog_accept_with_keys.request_key;
 IF FOUND THEN
  SELECT * INTO STRICT existing FROM truss.catalog_registration_request r WHERE r.registration_id=alias_request.registration_id;
  IF existing.input_bytes IS DISTINCT FROM input_bytes OR (CASE WHEN octet_length(existing.document_bytes)=0 THEN
    convert_from(truss.runtime_owned_request_documents(existing),'UTF8')::jsonb IS DISTINCT FROM convert_from(documents_bytes,'UTF8')::jsonb
   ELSE existing.document_bytes IS DISTINCT FROM documents_bytes OR existing.declaration_bytes IS DISTINCT FROM declarations_bytes END)
   OR alias_request.origin_bytes IS DISTINCT FROM origin_bytes OR alias_request.expected_revision IS DISTINCT FROM expected_revision
   OR alias_request.expected_documents IS DISTINCT FROM expected_documents THEN
   RAISE EXCEPTION 'request key reused with different registration input' USING ERRCODE='P1001'; END IF;
  PERFORM truss.catalog_actor();
  PERFORM truss.catalog_rebind_report_reader(existing.registration_id);
  RETURN QUERY SELECT existing.revision::text,existing.registration_id::text,r.report_bytes,true,true,alias_request.actor_name,NULL::bytea
   FROM truss.catalog_acceptance_report r WHERE r.rev=existing.revision;
  IF NOT FOUND THEN RAISE EXCEPTION 'original registration report missing' USING ERRCODE='55000'; END IF;
  PERFORM truss.catalog_actor();
  PERFORM truss.catalog_rebind_report_reader(existing.registration_id);
  RETURN;
 END IF;
 -- Source and optional global CAS checks happen only after exact authorized
 -- replay resolution, under the same schema-head serialization lock.
 IF expected_revision IS NOT NULL AND prior_revision IS DISTINCT FROM expected_revision THEN
  RAISE EXCEPTION 'expected catalog revision changed' USING ERRCODE='P1011';END IF;
 IF jsonb_array_length(expected_docs)>0 THEN
  FOR expected_doc IN SELECT value FROM jsonb_array_elements(expected_docs) LOOP
   IF coalesce((SELECT max(rev) FROM truss.schema_doc WHERE doc_id=expected_doc->>'documentId'),0)
     IS DISTINCT FROM (expected_doc->>'sourceCatalogRevision')::int THEN
    RAISE EXCEPTION 'expected document source revision changed' USING ERRCODE='P1011';END IF;
  END LOOP;
 END IF;
 -- Ordinary registration keeps one validation summary per original document.
 -- Semantic source/declaration checks and atomic publication remain native.
 IF (convert_from(source_bytes,'UTF8')::jsonb)->>'sourceFormat' ='truss-registration-summary/2.0' THEN
  DECLARE
   summary jsonb:=convert_from(source_bytes,'UTF8')::jsonb;
   original_input jsonb:=convert_from(input_bytes,'UTF8')::jsonb;
   original_docs jsonb:=convert_from(documents_bytes,'UTF8')::jsonb;
   doc jsonb; validation jsonb; selected_doc jsonb; ddd_profile jsonb; ddd_validation jsonb; ddd_known boolean; doc_index int:=0;
  BEGIN
   IF (SELECT count(*) FROM jsonb_object_keys(summary))<>3
    OR jsonb_typeof(summary->'umf') IS DISTINCT FROM 'array'
    OR jsonb_typeof(summary->'documentValidations') IS DISTINCT FROM 'array'
    OR jsonb_array_length(summary->'documentValidations')<>jsonb_array_length(original_docs)
    OR original_input->'binding' IS DISTINCT FROM '{"state":"absent"}'::jsonb
    OR original_input->'transforms' IS DISTINCT FROM '[]'::jsonb THEN
    RAISE EXCEPTION 'original native registration summary required' USING ERRCODE='22023';END IF;
   FOR doc IN SELECT value FROM jsonb_array_elements(original_docs) LOOP
    validation:=summary->'documentValidations'->doc_index;
    selected_doc:=original_input->'documents'->doc_index;
    ddd_known:=((doc->>'originalText')::jsonb->'vocabularies'->'umf.ddd'->>'version')='0.1.0';
    ddd_profile:=validation->'dddProfile';ddd_validation:=validation->'dddValidation';
    IF (SELECT count(*) FROM jsonb_object_keys(validation))<>
      (CASE WHEN ddd_known THEN 5 ELSE 3 END)
      OR validation->>'documentId' IS DISTINCT FROM doc->>'documentId'
      OR validation->>'contentSha256' IS DISTINCT FROM selected_doc->'artifact'->>'sha256'
      OR selected_doc->'ingress' IS DISTINCT FROM '{"kind":"native"}'::jsonb
      OR validation->'validation' IS DISTINCT FROM doc->'validation'->'sourceValidation'
      OR validation->'validation'->'valid' IS DISTINCT FROM 'true'::jsonb
      OR jsonb_typeof(validation->'validation'->'complete') IS DISTINCT FROM 'boolean'
      OR jsonb_typeof(validation->'validation'->'diagnostics') IS DISTINCT FROM 'array'
      OR ddd_known AND (ddd_profile IS DISTINCT FROM jsonb_build_object('identity','umf-ddd-document-validation',
       'version',original_input->'validatorProfile'->>'version','sha256',original_input->'validatorProfile'->>'sha256')
       OR ddd_profile IS DISTINCT FROM doc->'validation'->'dddProfile'
       OR ddd_validation IS DISTINCT FROM doc->'validation'->'dddValidation'
       OR ddd_validation->'valid' IS DISTINCT FROM 'true'::jsonb
       OR jsonb_typeof(ddd_validation->'complete') IS DISTINCT FROM 'boolean'
       OR jsonb_typeof(ddd_validation->'diagnostics') IS DISTINCT FROM 'array')
      OR NOT ddd_known AND (validation ? 'dddProfile' OR validation ? 'dddValidation'
       OR doc->'validation' ? 'dddProfile' OR doc->'validation' ? 'dddValidation') THEN
      RAISE EXCEPTION 'original document validation summary required' USING ERRCODE='22023';END IF;
    doc_index:=doc_index+1;
   END LOOP;
  END;
 ELSE
  RAISE EXCEPTION 'Current registration summary required' USING ERRCODE='22023';
 END IF;

 SELECT r.* INTO existing FROM truss.catalog_registration_request r
  WHERE pg_catalog.sha256(r.input_bytes)=pg_catalog.sha256(catalog_accept_with_keys.input_bytes)
  AND r.input_bytes=catalog_accept_with_keys.input_bytes AND CASE WHEN octet_length(r.document_bytes)=0 THEN
   convert_from(truss.runtime_owned_request_documents(r),'UTF8')::jsonb=convert_from(catalog_accept_with_keys.documents_bytes,'UTF8')::jsonb
  ELSE r.document_bytes=catalog_accept_with_keys.documents_bytes AND r.declaration_bytes=catalog_accept_with_keys.declarations_bytes END
  AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(convert_from(catalog_accept_with_keys.documents_bytes,'UTF8')::jsonb) d
   WHERE NOT EXISTS(SELECT 1 FROM truss.schema_doc current_doc WHERE current_doc.doc_id=d.value->>'documentId'
    AND current_doc.rev=(SELECT max(latest.rev) FROM truss.schema_doc latest WHERE latest.doc_id=current_doc.doc_id)
    AND current_doc.document=d.value->>'originalText' AND current_doc.doc_revision=d.value->>'revision'));
 IF FOUND THEN
  PERFORM truss.catalog_require_sources(input_bytes,documents_bytes,declarations_bytes);
  IF NOT preview_mode THEN
  INSERT INTO truss.catalog_unchanged_request(installation_id,actor_oid,actor_name,request_key,registration_id,origin_bytes,expected_revision,expected_documents)
   VALUES(installation.installation_id,actor,session_user::text,request_key,existing.registration_id,origin_bytes,expected_revision,expected_documents);
  IF NOT FOUND THEN RAISE EXCEPTION 'unchanged request not stored' USING ERRCODE='55000';END IF;
  END IF;
  alias_request.actor_name:=session_user::text;
  PERFORM truss.catalog_actor();
  PERFORM truss.catalog_rebind_report_reader(existing.registration_id);
  RETURN QUERY SELECT existing.revision::text,existing.registration_id::text,r.report_bytes,false,true,alias_request.actor_name,NULL::bytea
   FROM truss.catalog_acceptance_report r WHERE r.rev=existing.revision;
  IF NOT FOUND THEN RAISE EXCEPTION 'original registration report missing' USING ERRCODE='55000'; END IF;
  PERFORM truss.catalog_actor();
  PERFORM truss.catalog_rebind_report_reader(existing.registration_id);
  RETURN;
 END IF;
 PERFORM truss.catalog_require_sources(input_bytes,documents_bytes,declarations_bytes);
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(convert_from(documents_bytes,'UTF8')::jsonb) d
  JOIN truss.schema_doc s ON s.doc_id=d.value->>'documentId') THEN
  IF NOT truss.catalog_ddd_optional_evolution_supported(documents_bytes) THEN
   RAISE EXCEPTION 'known DDD source evolution is outside selected additive-member compatibility' USING ERRCODE='0A000';END IF;
  violations:=truss.catalog_scalar_violations_with_sources(declarations_bytes,documents_bytes);
  IF violations IS NOT NULL THEN
   PERFORM truss.catalog_actor();
   RETURN QUERY SELECT prior_revision::text,NULL::text,NULL::bytea,false,false,session_user::text,violations;
   RETURN;
  END IF;
 END IF;
 IF prior_revision<> (SELECT coalesce(max(r.revision),0) FROM truss.catalog_registration_request r) THEN
  RAISE EXCEPTION 'complete current catalog head required' USING ERRCODE='55000';END IF;
 IF prior_revision=2147483647 THEN RAISE EXCEPTION 'catalog revision exhausted' USING ERRCODE='54000';END IF;
 new_revision:=prior_revision+1;
 SELECT coalesce(max(type_id),0) INTO type_start FROM truss.type_def;
 SELECT coalesce(max(prop_id),0) INTO property_start FROM truss.prop_def;
 SELECT coalesce(max(rel_type_id),0) INTO relationship_start FROM truss.rel_def;
 IF type_start>2147418111 OR property_start>2147418111 OR relationship_start>2147418111 THEN
  RAISE EXCEPTION 'catalog identity range exhausted' USING ERRCODE='54000';END IF;
 origin:=convert_to((convert_from(origin_bytes,'UTF8')::jsonb||jsonb_build_object('actor',session_user::text,'db_role',session_user::text))::text,'UTF8');
 expected:=truss.catalog_revision_plan(prior_expected,truss.catalog_expected_records(declarations_bytes,documents_bytes,origin,transaction_timestamp(),installation.genesis_at,new_revision,0,0,0));
 -- Input and public-view wire budgets apply to their actual carriers. Source
 -- archives and immutable history are not another request or a rendered view.
 IF jsonb_array_length(expected->'type_def')+jsonb_array_length(expected->'prop_def')+jsonb_array_length(expected->'key_def')+jsonb_array_length(expected->'rel_def')>65536
  THEN RAISE EXCEPTION 'complete catalog resource limit' USING ERRCODE='54000';END IF;
 violations:=truss.catalog_rebind_violations(expected,new_revision,declarations_bytes);
 IF violations IS NOT NULL THEN
  PERFORM truss.catalog_actor();
  RETURN QUERY SELECT prior_revision::text,NULL::text,NULL::bytea,false,false,session_user::text,violations;RETURN;
 END IF;
 key_candidates:=truss.catalog_key_backfill_candidates(expected,new_revision);
 IF preview_mode THEN
  RETURN QUERY SELECT prior_revision::text,NULL::text,
   convert_to(jsonb_build_object('interfaceVersion','truss-catalog-key-candidates/0.1','candidates',key_candidates)::text,'UTF8'),
   false,false,session_user::text,NULL::bytea;RETURN;
 END IF;
 verified_keys:=truss.catalog_key_backfill_verify(expected,new_revision,coalesce(key_receipts,convert_to('[]','UTF8')));
 violations:=truss.catalog_key_backfill_violations(verified_keys);
 IF violations IS NOT NULL THEN
  PERFORM truss.catalog_actor();
  RETURN QUERY SELECT prior_revision::text,NULL::text,NULL::bytea,false,false,session_user::text,violations;RETURN;
 END IF;
 FOREACH table_name IN ARRAY ARRAY['schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint','schema_change'] LOOP
  rows:=expected->table_name;
  SELECT string_agg(format('%I',a.attname),',' ORDER BY a.attnum),string_agg(format('%I=EXCLUDED.%I',a.attname,a.attname),',' ORDER BY a.attnum) INTO columns,assignments FROM pg_attribute a
   WHERE a.attrelid=to_regclass('truss.'||table_name) AND a.attnum>0 AND NOT a.attisdropped AND a.attgenerated='';
  IF table_name='schema_change' THEN
   -- The planner supplies only this new revision's changes.
   INSERT INTO truss.schema_change SELECT p.* FROM truss.catalog_planned_changes(rows) p;
  ELSIF table_name IN ('type_def','prop_def','rel_def') THEN
   identity_column:=CASE table_name WHEN 'type_def' THEN 'type_id' WHEN 'prop_def' THEN 'prop_id' ELSE 'rel_type_id' END;
   EXECUTE format('INSERT INTO truss.%I AS stored(%s) SELECT %s FROM jsonb_populate_recordset(NULL::truss.%I,$1) ON CONFLICT(%I) DO UPDATE SET %s WHERE stored IS DISTINCT FROM EXCLUDED',table_name,columns,columns,table_name,identity_column,assignments) USING rows;
  ELSE
   conflict_columns:=CASE table_name WHEN 'schema_rev' THEN 'rev' WHEN 'schema_doc' THEN 'rev,ord'
    WHEN 'key_def' THEN 'type_id,key_id' WHEN 'relationship_lineage' THEN 'rel_type_id'
    WHEN 'rel_endpoint' THEN 'rel_type_id,source_type,target_type' END;
   EXECUTE format('INSERT INTO truss.%I(%s) SELECT %s FROM jsonb_populate_recordset(NULL::truss.%I,$1) ON CONFLICT(%s) DO NOTHING',table_name,columns,columns,table_name,conflict_columns) USING rows;
  END IF;
 END LOOP;
 request.registration_id:=gen_random_uuid();request.installation_id:=installation.installation_id;
 request.actor_oid:=actor;request.actor_name:=session_user::text;request.request_key:=request_key;
 request.writer_xid:=pg_current_xact_id();request.accepted_at:=transaction_timestamp();request.revision:=new_revision;
 request.expected_revision:=expected_revision;request.expected_documents:=expected_documents;
 request.type_offset:=type_start;request.property_offset:=property_start;request.relationship_offset:=relationship_start;
 request.input_bytes:=input_bytes;request.document_bytes:=CASE WHEN compact THEN ''::bytea ELSE documents_bytes END;
 request.declaration_bytes:=CASE WHEN compact THEN ''::bytea ELSE declarations_bytes END;
 IF compact THEN
  request.source_bytes:=convert_to(jsonb_build_object('sourceFormat','truss-registration-summary/2.0',
   'umf',(convert_from(source_bytes,'UTF8')::jsonb)->'umf',
   'runtimeRelease',jsonb_build_object('id',installation.release_id,'sha256',installation.release_sha256),
   'validationLocation','schema_doc.validation',
   'documentValidations',(SELECT jsonb_agg(jsonb_build_object('documentId',v.value->>'documentId',
    'contentSha256',v.value->>'contentSha256','valid',v.value->'validation'->'valid','complete',v.value->'validation'->'complete') ORDER BY v.ordinality)
    FROM jsonb_array_elements((convert_from(source_bytes,'UTF8')::jsonb)->'documentValidations') WITH ORDINALITY v))::text,'UTF8');
 ELSE request.source_bytes:=source_bytes;END IF;
 request.origin_bytes:=origin_bytes;
 PERFORM truss.catalog_rebind_objects(request,expected);
 PERFORM truss.catalog_key_backfill_apply(request,verified_keys);
 PERFORM truss.catalog_rebind_report_reader(request.registration_id,expected);
 original_report:=truss.catalog_make_report(request,expected);request.report_sha256:=sha256(original_report);
 IF octet_length(original_report)>16777216 THEN RAISE EXCEPTION 'bounded original registration report required' USING ERRCODE='54000';END IF;
 INSERT INTO truss.catalog_acceptance_report VALUES(new_revision,original_report);
 INSERT INTO truss.catalog_registration_request SELECT request.*;
 PERFORM truss.catalog_actor();
 UPDATE truss.schema_head SET rev=new_revision WHERE id=1 AND rev=prior_revision;
 IF NOT FOUND THEN RAISE EXCEPTION 'complete head transition required' USING ERRCODE='55000'; END IF;
 -- Property and key rebinds do not change the graph. Only changed bounded
 -- relationships need a census; a removed max-one bound also needs marker cleanup.
 IF EXISTS(SELECT 1 FROM truss.rel_def r LEFT JOIN truss.schema_change c
   ON c.rev=new_revision AND c.kind='rel' AND c.def_id=r.rel_type_id
   WHERE (r.since_rev=new_revision OR c.def_id IS NOT NULL)
    AND (r.source_min>0 OR r.target_min>0 OR r.source_max IS NOT NULL OR r.target_max IS NOT NULL
     OR (c.before->>'source_max')::int=1 OR (c.before->>'target_max')::int=1)) THEN
  PERFORM truss.runtime_graph_validate(true);
 END IF;
 PERFORM truss.catalog_rebind_report_reader(request.registration_id);
 RETURN QUERY SELECT request.revision::text,request.registration_id::text,original_report,false,false,request.actor_name,NULL::bytea;
END;
$$;

-- Preserve the original no-CAS native entrypoint and all existing call sites.
CREATE FUNCTION truss.catalog_accept_with_keys(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea,
 source_bytes bytea,origin_bytes bytea,request_key text,key_receipts bytea,preview_mode boolean)
RETURNS TABLE(revision text,registration_id text,report_bytes bytea,replayed boolean,unchanged boolean,actor_name text,violations_bytes bytea)
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
 SELECT * FROM truss.catalog_accept_with_keys(input_bytes,documents_bytes,declarations_bytes,source_bytes,origin_bytes,
  request_key,key_receipts,preview_mode,NULL,convert_to('[]','UTF8'));
$$;
REVOKE ALL ON FUNCTION truss.catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean) FROM PUBLIC;
REVOKE ALL ON FUNCTION truss.catalog_accept_with_keys(bytea,bytea,bytea,bytea,bytea,text,bytea,boolean,int,bytea) FROM PUBLIC;
CREATE FUNCTION truss.catalog_accept(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea,source_bytes bytea,origin_bytes bytea,request_key text)
RETURNS TABLE(revision text,registration_id text,report_bytes bytea,replayed boolean,unchanged boolean,actor_name text,violations_bytes bytea)
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
 SELECT * FROM truss.catalog_accept_with_keys(input_bytes,documents_bytes,declarations_bytes,source_bytes,origin_bytes,request_key,NULL,false);
$$;
CREATE FUNCTION truss.catalog_accept_preview(input_bytes bytea,documents_bytes bytea,declarations_bytes bytea,source_bytes bytea,origin_bytes bytea,request_key text)
RETURNS TABLE(revision text,registration_id text,report_bytes bytea,replayed boolean,unchanged boolean,actor_name text,violations_bytes bytea)
LANGUAGE sql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
 SELECT * FROM truss.catalog_accept_with_keys(input_bytes,documents_bytes,declarations_bytes,source_bytes,origin_bytes,request_key,NULL,true);
$$;
REVOKE ALL ON FUNCTION truss.catalog_accept_preview(bytea,bytea,bytea,bytea,bytea,text) FROM PUBLIC;

CREATE FUNCTION truss.catalog_report(selected_revision int) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original bytea;
BEGIN
 PERFORM truss.catalog_actor();
 PERFORM truss.catalog_rebind_report_reader((SELECT registration_id FROM truss.catalog_registration_request WHERE revision=selected_revision));
 SELECT report_bytes INTO STRICT original FROM truss.catalog_acceptance_report WHERE rev=selected_revision;
 PERFORM truss.catalog_actor();
 PERFORM truss.catalog_rebind_report_reader((SELECT registration_id FROM truss.catalog_registration_request WHERE revision=selected_revision));
 RETURN original;
END;
$$;

CREATE FUNCTION truss.catalog_status() RETURNS TABLE(installation_id text,release_id text,release_sha256 text,layout_profile text,revision text)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF NOT EXISTS(WITH RECURSIVE person AS (
  SELECT oid,rolsuper,rolcreaterole FROM pg_roles WHERE rolname=session_user), inherited(role_oid) AS (
  SELECT oid FROM person UNION SELECT m.roleid FROM pg_auth_members m JOIN inherited p ON m.member=p.role_oid WHERE m.inherit_option)
  SELECT 1 FROM person p CROSS JOIN truss.catalog_runtime_installation i
   WHERE current_setting('role')='none' AND (p.rolsuper OR p.rolcreaterole AND EXISTS(SELECT 1 FROM inherited WHERE role_oid=i.owner_oid)))
 THEN PERFORM truss.catalog_actor(); END IF;
 RETURN QUERY SELECT i.installation_id::text,i.release_id,i.release_sha256,i.layout_profile::text,h.rev::text FROM truss.runtime_current_installation() i CROSS JOIN truss.schema_head h WHERE h.id=1;
END;
$$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA truss FROM PUBLIC;
