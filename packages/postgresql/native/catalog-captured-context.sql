-- Versioned context0.3 collector: captured bytes, not complete installed-profile authority.
-- Private original native actor/context observation. Does not produce asserted
-- origin, installation epoch, profile authority or full originalExecution.
CREATE FUNCTION truss.runtime_collect_catalog_captured_context(
 expected_writer text,expected_ordinal text,expected_generation text)
RETURNS TABLE(context_hex text,database_role text,login_role text,database_name text,backend_pid text,actor_role_oid text,login_role_oid text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; context jsonb;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
  THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker actor boundary required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase='admitted';
 context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 IF jsonb_typeof(context)<>'object' OR (SELECT count(*) FROM jsonb_object_keys(context))<>11
  OR NOT context ?& ARRAY['interfaceVersion','xid','ordinal','sessionUser','actingUser','database','backendPid','actorRoleOid','sessionRoleOid','assertedOriginUtf8Hex','assertedOriginCaptureProfileHex']
  OR EXISTS(SELECT 1 FROM jsonb_each(context) e WHERE jsonb_typeof(e.value)<>'string')
  OR context->>'interfaceVersion' IS DISTINCT FROM 'truss-native-operation-context/0.3'
  OR context->>'assertedOriginUtf8Hex' !~ '^([0-9a-f]{2})+$'
  OR octet_length(context->>'assertedOriginUtf8Hex') NOT BETWEEN 2 AND 262144
  OR context->>'assertedOriginCaptureProfileHex' !~ '^([0-9a-f]{2})+$'
  OR octet_length(context->>'assertedOriginCaptureProfileHex') NOT BETWEEN 2 AND 131072
  OR context->>'xid' IS DISTINCT FROM expected_writer OR context->>'ordinal' IS DISTINCT FROM expected_ordinal
  OR context->>'sessionUser' IS DISTINCT FROM session_user::text
  OR context->>'actingUser' IS DISTINCT FROM current_user::text
  OR context->>'actorRoleOid' IS DISTINCT FROM (SELECT r.oid::text FROM pg_catalog.pg_roles r WHERE r.rolname=current_user)
  OR context->>'sessionRoleOid' IS DISTINCT FROM (SELECT r.oid::text FROM pg_catalog.pg_roles r WHERE r.rolname=session_user)
  OR context->>'database' IS DISTINCT FROM current_database()
  OR context->>'backendPid' IS DISTINCT FROM pg_backend_pid()::text THEN
  RAISE EXCEPTION 'original native actor/context correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT encode(op.original_context_bytes,'hex'),context->>'actingUser',context->>'sessionUser',context->>'database',context->>'backendPid',context->>'actorRoleOid',context->>'sessionRoleOid';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_captured_context(text,text,text) FROM PUBLIC;
