-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Person status omits installation identifiers and native role names.
CREATE FUNCTION truss.person_runtime_status(expected_release text, expected_digest text,
 expected_layout jsonb) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor oid;installation truss.catalog_runtime_installation%ROWTYPE;revision int;catalog_state text;
 selected_document text;selected_module text;
BEGIN
 actor:=truss.runtime_person(false);
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation WHERE singleton;
 IF installation.release_id IS DISTINCT FROM expected_release
  OR installation.release_sha256 IS DISTINCT FROM expected_digest
  OR installation.layout_profile IS DISTINCT FROM expected_layout THEN
  RETURN convert_to('{"outcome":"status","installation":"incompatible","catalog":"unknown"}','UTF8');
 END IF;
 SELECT rev INTO STRICT revision FROM truss.schema_head WHERE id=1;
 IF revision=0 THEN catalog_state:='empty';
 ELSE
  SELECT m.document_id,m.module INTO selected_document,selected_module FROM truss.module_access m
   WHERE truss.runtime_can_read(m.document_id,m.module)
    OR truss.runtime_audit_role_member(actor,pg_catalog.to_regrole(m.writer_role))
    OR EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=m.document_id
     AND a.module=m.module AND truss.runtime_audit_role_member(actor,a.auditor_oid))
   ORDER BY m.document_id,m.module LIMIT 1;
  IF selected_document IS NULL OR selected_module IS NULL THEN
   RAISE EXCEPTION 'current enrolled module reader required' USING ERRCODE='42501';END IF;
  IF NOT (truss.runtime_can_read(selected_document,selected_module)
   OR EXISTS(SELECT 1 FROM truss.module_access m WHERE m.document_id=selected_document AND m.module=selected_module
    AND truss.runtime_audit_role_member(actor,pg_catalog.to_regrole(m.writer_role)))
   OR EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=selected_document
    AND a.module=selected_module AND truss.runtime_audit_role_member(actor,a.auditor_oid))) THEN
   RAISE EXCEPTION 'current enrolled module reader required' USING ERRCODE='42501';END IF;
  catalog_state:='accepted';
 END IF;
 IF truss.runtime_person(false) IS DISTINCT FROM actor THEN
  RAISE EXCEPTION 'current status person required' USING ERRCODE='42501';END IF;
 RETURN convert_to(jsonb_build_object('outcome','status','installation','compatible',
  'catalog',catalog_state)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.person_runtime_status(text,text,jsonb) FROM PUBLIC;

-- Direct installation administrators may recover role names separately from
-- the minimal person status response. No ordinary person route calls this.
CREATE FUNCTION truss.admin_install_recovery() RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor record;installation truss.catalog_runtime_installation%ROWTYPE;
 owner_name text;registrar_name text;has_owner boolean;
BEGIN
 SELECT oid,rolname::text,rolcanlogin,rolsuper,rolcreatedb,rolcreaterole,rolreplication,rolbypassrls,rolinherit,
  current_setting('role')='none' AS original_role INTO STRICT actor
 FROM pg_catalog.pg_roles WHERE rolname=session_user;
 IF actor.rolcanlogin IS NOT TRUE OR actor.original_role IS NOT TRUE
  OR NOT (actor.rolsuper OR actor.rolcreaterole) THEN
  RAISE EXCEPTION 'direct installation administrator required' USING ERRCODE='42501';END IF;
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation WHERE singleton;
 IF NOT actor.rolsuper THEN
  WITH RECURSIVE inherited(role_oid) AS (
   SELECT actor.oid UNION SELECT m.roleid FROM pg_catalog.pg_auth_members m
    JOIN inherited i ON m.member=i.role_oid WHERE m.inherit_option)
  SELECT EXISTS(SELECT 1 FROM inherited WHERE role_oid=installation.owner_oid) INTO has_owner;
  IF has_owner IS NOT TRUE THEN RAISE EXCEPTION 'installation owner administration required' USING ERRCODE='42501';END IF;
 END IF;
 SELECT rolname::text INTO owner_name FROM pg_catalog.pg_roles WHERE oid=installation.owner_oid
  AND NOT rolcanlogin AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
  AND NOT rolreplication AND NOT rolbypassrls AND NOT rolinherit;
 IF owner_name IS NULL THEN RAISE EXCEPTION 'installation owner profile is incompatible' USING ERRCODE='0A000';END IF;
 SELECT rolname::text INTO registrar_name FROM pg_catalog.pg_roles WHERE oid=installation.registrar_oid
  AND NOT rolcanlogin AND NOT rolsuper AND NOT rolcreatedb AND NOT rolcreaterole
  AND NOT rolreplication AND NOT rolbypassrls AND NOT rolinherit;
 IF registrar_name IS NULL THEN RAISE EXCEPTION 'installation registrar profile is incompatible' USING ERRCODE='0A000';END IF;
 IF installation.owner_oid=installation.registrar_oid OR owner_name IS NULL OR registrar_name IS NULL THEN
  RAISE EXCEPTION 'installation role profile is incompatible' USING ERRCODE='0A000';END IF;
 RETURN convert_to(jsonb_build_object('outcome','recovered','ownerRole',owner_name,
  'registrarRole',registrar_name)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.admin_install_recovery() FROM PUBLIC;
