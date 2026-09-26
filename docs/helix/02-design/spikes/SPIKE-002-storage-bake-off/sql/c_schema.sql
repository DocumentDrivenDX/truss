-- SPIKE-002 option C: minimal generic catalog storage (throwaway). Fixed table set; nothing here is per type.
-- Per-type rows, indexes and optional CHECK constraints are emitted by loader/catalog.ts from the UMF model.
CREATE SCHEMA IF NOT EXISTS c;
-- Schema catalog: UMF documents verbatim per revision.
CREATE TABLE c.schema_rev (
  rev int PRIMARY KEY, umf_version text NOT NULL, content_sha256 text NOT NULL,
  document text NOT NULL, accepted_at timestamptz NOT NULL DEFAULT now());
-- Binding catalog (derived rows).
CREATE TABLE c.type_def (
  type_id int PRIMARY KEY, module text NOT NULL, element text NOT NULL, kind text NOT NULL, UNIQUE (module, element));
CREATE TABLE c.prop_def (
  prop_id int PRIMARY KEY, type_id int NOT NULL REFERENCES c.type_def, element text NOT NULL, name text NOT NULL,
  scalar_type text, nullability text NOT NULL, cardinality text NOT NULL, facets jsonb, item jsonb,
  home text NOT NULL DEFAULT 'json', since_rev int NOT NULL, UNIQUE (type_id, name), UNIQUE (element));
CREATE TABLE c.key_def (
  type_id int NOT NULL REFERENCES c.type_def, key_id text NOT NULL, prop_ids int[] NOT NULL, is_primary boolean NOT NULL,
  PRIMARY KEY (type_id, key_id));
CREATE TABLE c.rel_def (
  rel_type_id int PRIMARY KEY, module text NOT NULL, rel_id text NOT NULL, name text NOT NULL,
  source_min int NOT NULL, source_max int, target_min int NOT NULL, target_max int,   -- NULL max = '*'
  lifecycle text NOT NULL, directed boolean NOT NULL, target_key text, composition boolean NOT NULL DEFAULT false,
  since_rev int NOT NULL, inverse text, UNIQUE (module, rel_id));
-- Allowed endpoint types per relationship: adding a relationship is an INSERT, not DDL.
CREATE TABLE c.rel_endpoint (
  rel_type_id int NOT NULL REFERENCES c.rel_def, source_type int NOT NULL REFERENCES c.type_def,
  target_type int NOT NULL REFERENCES c.type_def, PRIMARY KEY (rel_type_id, source_type, target_type));
-- Instance graph: objects and edges share one id space.
CREATE SEQUENCE c.id_seq;
CREATE TABLE c.object (
  id bigint PRIMARY KEY DEFAULT nextval('c.id_seq'),
  type_id int NOT NULL REFERENCES c.type_def,
  props jsonb NOT NULL DEFAULT '{}' CONSTRAINT object_props_is_object CHECK (jsonb_typeof(props) = 'object'),
  retained jsonb,          -- data matching no definition
  rev int NOT NULL,
  UNIQUE (id, type_id));   -- target of the typed endpoint foreign keys below
CREATE TABLE c.edge (
  id bigint PRIMARY KEY DEFAULT nextval('c.id_seq'),
  rel_type_id int NOT NULL,
  source_id bigint NOT NULL, source_type int NOT NULL,
  target_id bigint NOT NULL, target_type int NOT NULL,
  ordinal int,
  CONSTRAINT edge_source_fk FOREIGN KEY (source_id, source_type) REFERENCES c.object (id, type_id),
  CONSTRAINT edge_target_fk FOREIGN KEY (target_id, target_type) REFERENCES c.object (id, type_id),
  CONSTRAINT edge_endpoint_types_fk FOREIGN KEY (rel_type_id, source_type, target_type) REFERENCES c.rel_endpoint);
-- Mutation journal: per-property history and provenance.
CREATE TABLE c.journal (
  seq bigserial PRIMARY KEY, xid xid8 NOT NULL DEFAULT pg_current_xact_id(), at timestamptz NOT NULL DEFAULT clock_timestamp(),
  object_id bigint NOT NULL, prop_id int, op text NOT NULL, old_value jsonb, new_value jsonb, rev int, origin text);
