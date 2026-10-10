CREATE FUNCTION truss.runtime_capture_row_images_snapshot_original(selected_state bigint, maximum_rows bigint, maximum_bytes bigint) RETURNS TABLE (image_kind text, original_image bytea) LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
 IF pg_catalog.current_setting('transaction_isolation') NOT IN ('repeatable read','serializable') THEN
  RAISE EXCEPTION 'original fixed transaction snapshot required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT c.image_kind,c.original_image
  FROM truss.runtime_capture_row_images_original(selected_state,maximum_rows,maximum_bytes) c;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_capture_row_images_snapshot_original(bigint, bigint, bigint) FROM public