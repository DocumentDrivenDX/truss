-- Additive timestamp projection for installed runtime 0.34.
-- Object timestamps belong to the verified current after-image, not journal.at.
CREATE FUNCTION truss.query_object_times(binding jsonb,selected_type int,selected_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE current_object truss.object%ROWTYPE;
BEGIN
 -- Establish original creation/current-version attribution and exact current image
 -- in this statement snapshot, including the caller's pending writes.
 PERFORM truss.query_object_attribution(binding,selected_type,selected_id);
 SELECT * INTO STRICT current_object FROM truss.object WHERE id=selected_id AND type_id=selected_type;
 IF NOT isfinite(current_object.created_at) OR NOT isfinite(current_object.updated_at)
  OR current_object.created_at<'0001-01-01 00:00:00+00'::timestamptz
  OR current_object.created_at>='10000-01-01 00:00:00+00'::timestamptz
  OR current_object.updated_at<'0001-01-01 00:00:00+00'::timestamptz
  OR current_object.updated_at>='10000-01-01 00:00:00+00'::timestamptz
 THEN RAISE EXCEPTION 'finite supported object timestamps required' USING ERRCODE='0A000';END IF;
 PERFORM truss.query_scope(binding);
 RETURN jsonb_build_object(
  '_created_at',to_char(current_object.created_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  '_updated_at',to_char(current_object.updated_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'));
END;
$$;
REVOKE ALL ON FUNCTION truss.query_object_times(jsonb,int,bigint) FROM PUBLIC;
