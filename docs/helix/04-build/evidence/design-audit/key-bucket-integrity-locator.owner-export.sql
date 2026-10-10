CREATE FUNCTION truss.key_bucket_integrity_locator_v01(admitted_namespace_sha256 bytea, admitted_key_sha256 bytea, admitted_storage_row_id bigint, admitted_source_kind text) RETURNS TABLE (source_kind text, storage_row_id text, object_id text, type_id text, key_num text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL unsafe SET search_path TO pg_catalog, pg_temp AS $$
DECLARE
  native_row record;
BEGIN
  IF admitted_namespace_sha256 IS NULL OR admitted_key_sha256 IS NULL
     OR pg_catalog.octet_length(admitted_namespace_sha256) <> 32
     OR pg_catalog.octet_length(admitted_key_sha256) <> 32
     OR admitted_storage_row_id IS NULL OR admitted_storage_row_id <= 0
     OR admitted_source_kind IS NULL OR admitted_source_kind NOT IN ('live', 'reservation') THEN
    RAISE EXCEPTION 'invalid integrity locator' USING ERRCODE = '22023';
  END IF;
  SELECT v.kind, v.row_id, v.object_id, v.type_id, v.key_num
  INTO STRICT native_row
  FROM (
    SELECT 'live'::text AS kind, b.storage_row_id AS row_id,
           b.object_id::text AS object_id, b.type_id::text AS type_id,
           b.key_num::text AS key_num
    FROM truss.object_key_bucket AS b
    WHERE admitted_source_kind = 'live' AND b.storage_row_id = admitted_storage_row_id
      AND b.namespace_sha256 = admitted_namespace_sha256 AND b.key_sha256 = admitted_key_sha256
    UNION ALL
    SELECT 'reservation'::text, b.storage_row_id, NULL::text, NULL::text, NULL::text
    FROM truss.object_key_reservation_bucket AS b
    WHERE admitted_source_kind = 'reservation' AND b.storage_row_id = admitted_storage_row_id
      AND b.namespace_sha256 = admitted_namespace_sha256 AND b.key_sha256 = admitted_key_sha256
  ) AS v;
  RETURN QUERY SELECT native_row.kind, native_row.row_id::text,
                      native_row.object_id, native_row.type_id, native_row.key_num;
END;
$$; REVOKE ALL ON FUNCTION truss.key_bucket_integrity_locator_v01(bytea, bytea, bigint, text) FROM public