CREATE FUNCTION truss.key_bucket_integrity_metadata_v01(admitted_namespace_sha256 bytea, admitted_key_sha256 bytea) RETURNS TABLE (source_kind text, storage_row_id text, namespace_bytes_length text, key_bytes_length text, original_artifact_bytes_length text) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL unsafe SET search_path TO pg_catalog, pg_temp AS $$
BEGIN
  IF admitted_namespace_sha256 IS NULL OR admitted_key_sha256 IS NULL
     OR pg_catalog.octet_length(admitted_namespace_sha256) <> 32
     OR pg_catalog.octet_length(admitted_key_sha256) <> 32 THEN
    RAISE EXCEPTION 'invalid integrity route' USING ERRCODE = '22023';
  END IF;

  RETURN QUERY
  SELECT m.source_kind, m.row_id::text,
         m.namespace_length::text, m.key_length::text, m.artifact_length::text
  FROM (
    SELECT 'live'::text AS source_kind, b.storage_row_id AS row_id,
           pg_catalog.octet_length(b.namespace_bytes) AS namespace_length,
           pg_catalog.octet_length(b.key_bytes) AS key_length,
           pg_catalog.octet_length(b.original_context_bytes) AS artifact_length
    FROM truss.object_key_bucket AS b
    WHERE b.namespace_sha256 = admitted_namespace_sha256
      AND b.key_sha256 = admitted_key_sha256
    UNION ALL
    SELECT 'reservation'::text, b.storage_row_id,
           pg_catalog.octet_length(b.namespace_bytes),
           pg_catalog.octet_length(b.key_bytes),
           pg_catalog.octet_length(b.original_reservation_bytes)
    FROM truss.object_key_reservation_bucket AS b
    WHERE b.namespace_sha256 = admitted_namespace_sha256
      AND b.key_sha256 = admitted_key_sha256
  ) AS m
  ORDER BY m.row_id, m.source_kind COLLATE pg_catalog."C"
  LIMIT 10001;
END;
$$; REVOKE ALL ON FUNCTION truss.key_bucket_integrity_metadata_v01(bytea, bytea) FROM public