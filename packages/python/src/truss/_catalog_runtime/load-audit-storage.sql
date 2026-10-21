-- Transactional import-load audit evidence. Rows are written by the native
-- batch processor in the same transaction as its chunk effects.
CREATE TABLE truss.runtime_import_audit_access (
 document_id text NOT NULL COLLATE pg_catalog."C",
 module text NOT NULL COLLATE pg_catalog."C",
 auditor_oid oid NOT NULL,
 granted_by oid NOT NULL,
 PRIMARY KEY(document_id,module),
 FOREIGN KEY(document_id,module) REFERENCES truss.module_access(document_id,module)
);
REVOKE ALL ON truss.runtime_import_audit_access FROM PUBLIC;

-- Query membership rows under this invocation's snapshot. pg_has_role can use
-- a role cache warmed by a nested SECURITY DEFINER call, so it is not used for
-- audit authority decisions.
CREATE FUNCTION truss.runtime_audit_role_member(selected_actor oid,selected_role oid) RETURNS boolean
LANGUAGE sql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 WITH RECURSIVE inherited(role_oid) AS (
  SELECT selected_actor UNION
  SELECT m.roleid FROM pg_catalog.pg_auth_members m JOIN inherited i ON m.member=i.role_oid
 ) SELECT EXISTS(SELECT 1 FROM inherited WHERE role_oid=selected_role);
$$;
REVOKE ALL ON FUNCTION truss.runtime_audit_role_member(oid,oid) FROM PUBLIC;

CREATE TABLE truss.runtime_import_load_chunk (
 invocation_id uuid NOT NULL,
 chunk_index int NOT NULL CHECK(chunk_index BETWEEN 0 AND 1023),
 total_chunks int NOT NULL CHECK(total_chunks BETWEEN 1 AND 1024),
 load_id text NOT NULL COLLATE pg_catalog."C",
 original_asserted_origin jsonb NOT NULL CHECK(jsonb_typeof(original_asserted_origin)='object'),
 asserted_origin_sha256 text NOT NULL COLLATE pg_catalog."C" CHECK(asserted_origin_sha256 ~ '^[0-9a-f]{64}$'),
 input_sha256 text NOT NULL COLLATE pg_catalog."C" CHECK(input_sha256 ~ '^[0-9a-f]{64}$'),
 input_count int NOT NULL CHECK(input_count BETWEEN 0 AND 1024),
 original_owners jsonb NOT NULL CHECK(jsonb_typeof(original_owners)='array'),
 owner_inventory_complete boolean NOT NULL,
 entries jsonb NOT NULL CHECK(jsonb_typeof(entries)='array'),
 native_actor oid NOT NULL,
 native_actor_name text NOT NULL COLLATE pg_catalog."C",
 audit_observed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 writer_xid xid8 NOT NULL,
 PRIMARY KEY(invocation_id,chunk_index),
 CHECK(chunk_index<total_chunks),
 CHECK(octet_length(load_id) BETWEEN 1 AND 4096),
 CHECK(octet_length(convert_to(original_owners::text,'UTF8'))<=1048576),
 CHECK(octet_length(convert_to(entries::text,'UTF8'))<=1048576),
 CHECK(octet_length(convert_to(original_asserted_origin::text,'UTF8'))<=1048576)
);
CREATE INDEX runtime_import_load_actor ON truss.runtime_import_load_chunk(invocation_id,native_actor);
CREATE INDEX runtime_import_load_observed ON truss.runtime_import_load_chunk(audit_observed_at DESC,invocation_id DESC,chunk_index DESC);
CREATE TRIGGER runtime_import_load_chunk_immutable BEFORE UPDATE OR DELETE OR TRUNCATE
 ON truss.runtime_import_load_chunk EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON truss.runtime_import_load_chunk FROM PUBLIC;

