-- CONTRACT-001/005 internal lossless extraction candidate; unapplied/unqualified.
-- Fixed 64 KiB output chunk; NOT a server allocation/detoast/work bound.
-- Host assigns exact SELECT-only observer owner and internal EXECUTE whitelist.
-- Outer procedure owns full metadata, original guards, reconstruction and ledger.
CREATE FUNCTION truss.key_bucket_integrity_chunk_v01(
  admitted_namespace_sha256 bytea, admitted_key_sha256 bytea,
  admitted_storage_row_id bigint, admitted_source_kind text,
  admitted_carrier text, admitted_offset bigint, admitted_total_length bigint
)
RETURNS TABLE (total_length text, byte_offset text, original_chunk bytea)
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
DECLARE
  actual_length bigint;
  selected_chunk bytea;
BEGIN
  IF admitted_namespace_sha256 IS NULL OR admitted_key_sha256 IS NULL
     OR pg_catalog.octet_length(admitted_namespace_sha256) <> 32
     OR pg_catalog.octet_length(admitted_key_sha256) <> 32
     OR admitted_storage_row_id IS NULL OR admitted_storage_row_id <= 0
     OR admitted_source_kind IS NULL OR admitted_source_kind NOT IN ('live', 'reservation')
     OR admitted_carrier IS NULL OR admitted_carrier NOT IN ('namespace', 'key', 'original')
     OR admitted_total_length IS NULL OR admitted_total_length < 1
     OR admitted_total_length > 2147483647
     OR admitted_offset IS NULL OR admitted_offset < 0
     OR admitted_offset >= admitted_total_length THEN
    RAISE EXCEPTION 'invalid integrity extraction' USING ERRCODE = '22023';
  END IF;

  SELECT pg_catalog.octet_length(v.original_bytes)::bigint,
         pg_catalog.substring(v.original_bytes, admitted_offset::integer + 1, 65536)
  INTO STRICT actual_length, selected_chunk
  FROM (
    SELECT CASE admitted_carrier WHEN 'namespace' THEN b.namespace_bytes
             WHEN 'key' THEN b.key_bytes ELSE b.original_context_bytes END AS original_bytes
    FROM truss.object_key_bucket AS b
    WHERE admitted_source_kind = 'live' AND b.storage_row_id = admitted_storage_row_id
      AND b.namespace_sha256 = admitted_namespace_sha256 AND b.key_sha256 = admitted_key_sha256
    UNION ALL
    SELECT CASE admitted_carrier WHEN 'namespace' THEN b.namespace_bytes
             WHEN 'key' THEN b.key_bytes ELSE b.original_reservation_bytes END
    FROM truss.object_key_reservation_bucket AS b
    WHERE admitted_source_kind = 'reservation' AND b.storage_row_id = admitted_storage_row_id
      AND b.namespace_sha256 = admitted_namespace_sha256 AND b.key_sha256 = admitted_key_sha256
  ) AS v;
  IF actual_length <> admitted_total_length
     OR pg_catalog.octet_length(selected_chunk) <>
        LEAST(65536::bigint, admitted_total_length - admitted_offset) THEN
    RAISE EXCEPTION 'integrity extraction mismatch' USING ERRCODE = '55000';
  END IF;
  RETURN QUERY SELECT actual_length::text, admitted_offset::text, selected_chunk;
END;
$body$;
REVOKE ALL ON FUNCTION truss.key_bucket_integrity_chunk_v01(bytea, bytea, bigint, text, text, bigint, bigint) FROM PUBLIC;
-- Missing/multiple original native rows fail STRICT; raw native errors stay private.
-- No GRANT/owner assignment/public facade or native invocation in this draft.
