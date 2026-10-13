-- Render frozen row/catalog inputs without observing current data tables.
CREATE FUNCTION truss.render_scalar_object(current_object truss.object,selected_type truss.type_def,properties truss.prop_def[],has_row_home boolean,definition_pin text,captured_revision int,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE property truss.prop_def;cell jsonb;values_json jsonb:='[]';retained_json jsonb:='[]';result bytea;
BEGIN
 IF current_object.rev>captured_revision THEN
  RAISE EXCEPTION 'catalog changed during object observation' USING ERRCODE='55P03';END IF;
 IF octet_length(current_object.props::text)+coalesce(octet_length(current_object.retained::text),0)>maximum_bytes THEN
  RAISE EXCEPTION 'object output budget exceeded' USING ERRCODE='54000'; END IF;
 IF current_object.root_id IS NOT NULL OR current_object.ver<=0 OR current_object.rev<selected_type.since_rev OR current_object.rev>captured_revision OR selected_type.since_rev>captured_revision
 OR NOT isfinite(current_object.created_at) OR NOT isfinite(current_object.updated_at)
 OR current_object.created_at<'0001-01-01 00:00:00+00'::timestamptz OR current_object.created_at>='10000-01-01 00:00:00+00'::timestamptz
 OR current_object.updated_at<'0001-01-01 00:00:00+00'::timestamptz OR current_object.updated_at>='10000-01-01 00:00:00+00'::timestamptz
 OR has_row_home
 OR EXISTS(SELECT 1 FROM jsonb_object_keys(current_object.props) k WHERE NOT EXISTS(
   SELECT 1 FROM unnest(properties) p WHERE p.prop_id::text=k)) THEN
  RAISE EXCEPTION 'unsupported complete object representation' USING ERRCODE='0A000'; END IF;
 FOREACH property IN ARRAY properties LOOP
  IF truss.valid_property_definition(property) IS NOT TRUE OR property.since_rev>captured_revision THEN
   RAISE EXCEPTION 'unsupported property profile' USING ERRCODE='0A000'; END IF;
  IF NOT current_object.props ? property.prop_id::text THEN
   IF property.nullability='required' THEN RAISE EXCEPTION 'missing required property' USING ERRCODE='55000'; END IF;
   CONTINUE;
  END IF;
  cell:=current_object.props->property.prop_id::text;
  IF truss.valid_property_value(cell,property) IS NOT TRUE THEN RAISE EXCEPTION 'malformed exact logical value' USING ERRCODE='55000';END IF;
  cell:=truss.logical_flat_cell(cell);
  values_json:=values_json||jsonb_build_array(jsonb_build_array(property.name,cell));
 END LOOP;
 FOR cell IN SELECT jsonb_build_array(key,value) FROM jsonb_each(coalesce(current_object.retained,'{}'::jsonb)) ORDER BY key COLLATE "C" LOOP
  cell:=jsonb_build_array(cell->0,truss.logical_flat_cell(cell->1));
  retained_json:=retained_json||jsonb_build_array(cell);
 END LOOP;
 result:=convert_to(jsonb_build_object('profile','truss-python-scalar-object/0.4','releaseId',expected_release,
 'releaseSha256',expected_digest,'documentId',selected_type.document_id,'moduleId',selected_type.module,'recordId',selected_type.element,
 'id',current_object.id::text,'typeId',current_object.type_id::text,
 'definitionPin',definition_pin,'version',current_object.ver::text,
 'catalogRevision',captured_revision::text,'recordRevision',current_object.rev::text,
 'createdAt',to_char(current_object.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
 'updatedAt',to_char(current_object.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
 'values',values_json,'retained',retained_json)::text,'UTF8');
 IF octet_length(result)>maximum_bytes THEN RAISE EXCEPTION 'object output budget exceeded' USING ERRCODE='54000'; END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.render_scalar_object(truss.object,truss.type_def,truss.prop_def[],boolean,text,int,int,text,text) FROM PUBLIC;

-- Public identity read, scalar-string object profile; no mutation authority.
CREATE FUNCTION truss.get_object(selected_document text,selected_module text,selected_record text,selected_id bigint,maximum_bytes int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp SET row_security=off AS $$
DECLARE actor_oid oid; selected_type truss.type_def%ROWTYPE; current_object truss.object%ROWTYPE;
 property truss.prop_def%ROWTYPE; cell jsonb; values_json jsonb:='[]'; retained_json jsonb:='[]';
 properties truss.prop_def[];has_row_home boolean;definition_pin text;dependency record;frozen record;
 captured_revision int; result bytea; policy truss.module_access%ROWTYPE; installation truss.catalog_runtime_installation%ROWTYPE;
BEGIN
 actor_oid:=truss.runtime_person(false);
 IF selected_document IS NULL OR selected_module IS NULL OR selected_record IS NULL
 OR octet_length(selected_document) NOT BETWEEN 1 AND 4096 OR octet_length(selected_module) NOT BETWEEN 1 AND 4096
 OR octet_length(selected_record) NOT BETWEEN 1 AND 4096 OR selected_id IS NULL OR selected_id<=0
 OR maximum_bytes IS NULL OR maximum_bytes NOT BETWEEN 1 AND 16777216 THEN
  RAISE EXCEPTION 'bounded object selection required' USING ERRCODE='22023'; END IF;
 IF current_setting('transaction_read_only')='on' THEN
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1;
 ELSE
 SELECT rev INTO STRICT captured_revision FROM truss.schema_head WHERE id=1 FOR SHARE NOWAIT;
 END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF expected_release IS DISTINCT FROM installation.release_id OR expected_digest IS DISTINCT FROM installation.release_sha256
 OR installation.release_id<>'truss-catalog-runtime/0.53-candidate' THEN
  RAISE EXCEPTION 'selected installed object runtime required' USING ERRCODE='0A000'; END IF;
 IF captured_revision<1 THEN RAISE EXCEPTION 'accepted read catalog required' USING ERRCODE='0A000'; END IF;
 -- No object observation until exact document/module membership is established.
 IF current_setting('transaction_read_only')='on' THEN
 SELECT * INTO policy FROM truss.module_access WHERE document_id=selected_document AND module=selected_module;
 ELSE
 SELECT * INTO policy FROM truss.module_access WHERE document_id=selected_document AND module=selected_module FOR SHARE NOWAIT;
 END IF;
 IF NOT FOUND THEN RETURN NULL; END IF;
 IF NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
   SELECT actor_oid UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
   SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid
   WHERE r.rolname::text IN (policy.reader_role,policy.writer_role)) THEN RETURN NULL; END IF;
 SELECT * INTO selected_type FROM truss.type_def WHERE document_id=selected_document AND module=selected_module
   AND element=selected_record AND retired_rev IS NULL AND kind='record' AND NOT provisional AND since_rev<=captured_revision;
 IF NOT FOUND THEN RETURN NULL; END IF;
 -- Require every declaration owner before any object observation.
 IF NOT truss.runtime_object_values_readable(selected_type.type_id) THEN RETURN NULL;END IF;
 SELECT coalesce(array_agg(p ORDER BY p.prop_id),ARRAY[]::truss.prop_def[]) INTO properties FROM truss.prop_def p WHERE p.type_id=selected_type.type_id AND p.retired_rev IS NULL;
 SELECT d.definition_pin INTO STRICT definition_pin FROM truss.runtime_definition('type',selected_type.type_id) d;
 SELECT o AS object,EXISTS(SELECT 1 FROM truss.row_home_state r WHERE r.object_id=o.id AND r.object_type_id=o.type_id) AS row_home
 INTO frozen FROM truss.object o WHERE o.id=selected_id AND o.type_id=selected_type.type_id;
 IF NOT FOUND THEN RETURN NULL; END IF;
 current_object:=frozen.object;has_row_home:=frozen.row_home;
 result:=truss.render_scalar_object(current_object,selected_type,properties,has_row_home,definition_pin,captured_revision,maximum_bytes,installation.release_id,installation.release_sha256);
 actor_oid:=truss.runtime_person(false);
 IF current_setting('transaction_read_only')='on' THEN
  SELECT * INTO policy FROM truss.module_access WHERE document_id=selected_document AND module=selected_module;
  IF NOT FOUND THEN RETURN NULL; END IF;
 END IF;
 IF NOT EXISTS(WITH RECURSIVE memberships(role_oid) AS (
   SELECT actor_oid UNION SELECT m.roleid FROM pg_auth_members m JOIN memberships p ON m.member=p.role_oid)
   SELECT 1 FROM pg_roles r JOIN memberships m ON m.role_oid=r.oid
   WHERE r.rolname::text IN (policy.reader_role,policy.writer_role)) THEN RETURN NULL; END IF;
 IF NOT truss.runtime_object_values_readable(selected_type.type_id) THEN RETURN NULL;END IF;
 IF (SELECT rev FROM truss.schema_head WHERE id=1) IS DISTINCT FROM captured_revision THEN
  RAISE EXCEPTION 'catalog changed during object observation' USING ERRCODE='55P03';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.get_object(text,text,text,bigint,int,text,text) FROM PUBLIC;
