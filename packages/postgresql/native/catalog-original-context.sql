-- Private original native actor/context observation. Does not produce asserted
-- origin, installation epoch, profile authority or full originalExecution.
CREATE FUNCTION truss.runtime_collect_catalog_original_context(
 expected_writer text,expected_ordinal text,expected_generation text)
RETURNS TABLE(context_hex text,database_role text,login_role text,database_name text,backend_pid text)
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
 IF jsonb_typeof(context)<>'object' OR (SELECT count(*) FROM jsonb_object_keys(context))<>7
  OR NOT context ?& ARRAY['interfaceVersion','xid','ordinal','sessionUser','actingUser','database','backendPid']
  OR EXISTS(SELECT 1 FROM jsonb_each(context) e WHERE jsonb_typeof(e.value)<>'string')
  OR context->>'interfaceVersion' IS DISTINCT FROM 'truss-native-operation-context/0.1'
  OR context->>'xid' IS DISTINCT FROM expected_writer OR context->>'ordinal' IS DISTINCT FROM expected_ordinal
  OR context->>'sessionUser' IS DISTINCT FROM session_user::text
  OR context->>'actingUser' IS DISTINCT FROM current_user::text
  OR context->>'database' IS DISTINCT FROM current_database()
  OR context->>'backendPid' IS DISTINCT FROM pg_backend_pid()::text THEN
  RAISE EXCEPTION 'original native actor/context correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT encode(op.original_context_bytes,'hex'),context->>'actingUser',context->>'sessionUser',context->>'database',context->>'backendPid';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_original_context(text,text,text) FROM PUBLIC;
