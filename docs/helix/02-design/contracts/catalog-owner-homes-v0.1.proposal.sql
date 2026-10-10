-- Fresh-install replacement declarations for proposed catalog-owner/qualified-module-policy profiles.
-- NOT an ALTER migration, standalone installer, protected uniqueness guard or adopted binding.
-- Select in place of the three baseline CREATE TABLE statements, never append beside them.
-- Full lineage equality is protected/byte-exact; digest routing is deliberately nonunique.

CREATE TABLE truss.module_access (
  document_id text COLLATE pg_catalog."C" NOT NULL,
  module      text COLLATE pg_catalog."C" NOT NULL,
  reader_role text COLLATE pg_catalog."C" NOT NULL,
  writer_role text COLLATE pg_catalog."C" NOT NULL,
  CONSTRAINT module_access_qualified_pk PRIMARY KEY (document_id, module),
  CONSTRAINT module_access_roles_differ CHECK (reader_role <> writer_role)
);

CREATE TABLE truss.type_def (
  document_id text COLLATE pg_catalog."C" NOT NULL,
  type_id      int PRIMARY KEY,
  module       text COLLATE pg_catalog."C" NOT NULL,
  element      text COLLATE pg_catalog."C" NOT NULL,
  kind         text NOT NULL,
  provisional  boolean NOT NULL DEFAULT false,  -- named by a relationship but not yet defined
  since_rev    int NOT NULL REFERENCES truss.schema_rev (rev),
  doc_ord      int,                              -- defining document; NULL for a provisional type
  retired_rev  int REFERENCES truss.schema_rev (rev),
  lineage_profile text COLLATE pg_catalog."C" NOT NULL,
  lineage_bytes bytea NOT NULL,
  lineage_sha256 bytea GENERATED ALWAYS AS (pg_catalog.sha256(lineage_bytes)) STORED,
  CONSTRAINT type_def_lineage_profile_nonempty CHECK (octet_length(lineage_profile) > 0),
  CONSTRAINT type_def_lineage_bytes_nonempty CHECK (octet_length(lineage_bytes) > 0),
  FOREIGN KEY (since_rev, doc_ord) REFERENCES truss.schema_doc (rev, ord)
);

CREATE TABLE truss.rel_def (
  document_id text COLLATE pg_catalog."C" NOT NULL,
  rel_type_id   int PRIMARY KEY,
  module        text COLLATE pg_catalog."C" NOT NULL,
  rel_id        text COLLATE pg_catalog."C" NOT NULL,
  name          text NOT NULL,
  source_min    int NOT NULL,
  source_max    int,                           -- NULL means '*'
  target_min    int NOT NULL,
  target_max    int,
  lifecycle     text NOT NULL,
  directed      boolean NOT NULL,
  target_key    text,
  composition   boolean NOT NULL DEFAULT false,
  assoc_type_id int REFERENCES truss.type_def (type_id),  -- type whose properties an edge carries
  inverse       text,
  since_rev     int NOT NULL REFERENCES truss.schema_rev (rev),
  doc_ord       int NOT NULL,
  retired_rev   int REFERENCES truss.schema_rev (rev),
  FOREIGN KEY (since_rev, doc_ord) REFERENCES truss.schema_doc (rev, ord)
);

CREATE INDEX type_def_lineage_route ON truss.type_def (lineage_sha256, type_id);
-- No source-document FK manufactures declaring ownership; definition provenance is independent.
-- Property/key owners inherit type_def; edge disclosure includes declaring relationship and both endpoint owners.
-- Provisional types require an admitted declared owner; no invented source document.
-- Relationship total/unique full-byte identity uses the separate relationship_lineage adjunct.
-- PK grant-key native size/operator admission, role equality and policy/grant producers remain required.
-- All catalog/provisional/retired identities retain their allocated IDs; reactivation validates full original state.
