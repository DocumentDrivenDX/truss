-- truss storage layout, version 0.1 (draft). Normative DDL for CONTRACT-001.
-- A fixed set of tables: adding a type, property or relationship adds catalog rows
-- (plus the declared partition and indexes), never columns or table rewrites.
-- The schema name is a parameter of the deployment; `truss` is the default.
-- Source tags are in CONTRACT-001: each element is accepted (ADR-002), derived
-- from SPIKE-002, or proposed by this contract.

CREATE SCHEMA IF NOT EXISTS truss;
COMMENT ON SCHEMA truss IS 'truss-layout 0.1';

-- ---- Schema catalog: UMF documents verbatim and immutable per catalog revision --------
CREATE TABLE truss.schema_rev (
  rev          int PRIMARY KEY,
  accepted_at  timestamptz NOT NULL DEFAULT now(),
  report       jsonb NOT NULL                 -- acceptance and enforcement report (CONTRACT-003)
);
CREATE TABLE truss.schema_doc (
  rev              int  NOT NULL REFERENCES truss.schema_rev (rev),
  ord              int  NOT NULL,             -- order of import within the revision
  doc_id           text NOT NULL,             -- UMF document identity
  doc_revision     text NOT NULL,             -- owner-issued revision token
  umf_version      text NOT NULL,             -- exact UMF core version
  content_sha256   text NOT NULL,
  document         text NOT NULL,             -- the bytes as received
  validation       jsonb NOT NULL,
  PRIMARY KEY (rev, ord),
  UNIQUE (rev, doc_id)
);

-- ---- Binding catalog: derived from the documents, rebuildable ---------------------------
CREATE TABLE truss.type_def (
  type_id      int PRIMARY KEY,
  module       text NOT NULL,
  element      text NOT NULL,
  kind         text NOT NULL,
  provisional  boolean NOT NULL DEFAULT false,  -- named by a relationship but not yet defined
  since_rev    int NOT NULL REFERENCES truss.schema_rev (rev),
  retired_rev  int REFERENCES truss.schema_rev (rev),
  UNIQUE (module, element)
);
CREATE TABLE truss.prop_def (
  prop_id      int PRIMARY KEY,
  type_id      int  NOT NULL REFERENCES truss.type_def (type_id),
  element      text NOT NULL,
  name         text NOT NULL,
  scalar_type  text,
  nullability  text NOT NULL,
  cardinality  text NOT NULL,
  facets       jsonb,
  item         jsonb,
  home         text NOT NULL DEFAULT 'json' CHECK (home IN ('json','row')),
  since_rev    int  NOT NULL REFERENCES truss.schema_rev (rev),
  retired_rev  int REFERENCES truss.schema_rev (rev),
  UNIQUE (type_id, name),
  UNIQUE (element)
);
CREATE TABLE truss.key_def (
  type_id    int  NOT NULL REFERENCES truss.type_def (type_id),
  key_id     text NOT NULL,
  prop_ids   int[] NOT NULL,
  is_primary boolean NOT NULL,
  PRIMARY KEY (type_id, key_id)
);
CREATE TABLE truss.rel_def (
  rel_type_id   int PRIMARY KEY,
  module        text NOT NULL,
  rel_id        text NOT NULL,
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
  retired_rev   int REFERENCES truss.schema_rev (rev),
  UNIQUE (module, rel_id)
);
CREATE TABLE truss.rel_endpoint (
  rel_type_id int NOT NULL REFERENCES truss.rel_def (rel_type_id),
  source_type int NOT NULL REFERENCES truss.type_def (type_id),
  target_type int NOT NULL REFERENCES truss.type_def (type_id),
  PRIMARY KEY (rel_type_id, source_type, target_type)
);

-- ---- Instance graph: objects and edges share one id space --------------------------------
CREATE SEQUENCE truss.id_seq;

CREATE TABLE truss.object (
  id          bigint NOT NULL DEFAULT nextval('truss.id_seq'),
  type_id     int    NOT NULL REFERENCES truss.type_def (type_id),
  props       jsonb  NOT NULL DEFAULT '{}'::jsonb,   -- keyed by prop_id rendered as text
  retained    jsonb,                                 -- data that matched no definition
  root_id     bigint,                                -- aggregate root of a composed object
  rev         int    NOT NULL REFERENCES truss.schema_rev (rev),  -- catalog revision of the last write
  ver         bigint NOT NULL DEFAULT 1,             -- record version; +1 per change
  created_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
  updated_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT object_pkey PRIMARY KEY (id, type_id),
  CONSTRAINT object_props_is_object CHECK (jsonb_typeof(props) = 'object'),
  CONSTRAINT object_retained_is_object CHECK (retained IS NULL OR jsonb_typeof(retained) = 'object')
) PARTITION BY LIST (type_id);
CREATE TABLE truss.object_default PARTITION OF truss.object DEFAULT;

CREATE TABLE truss.edge (
  id          bigint PRIMARY KEY DEFAULT nextval('truss.id_seq'),
  rel_type_id int    NOT NULL,
  source_id   bigint NOT NULL,
  source_type int    NOT NULL,
  target_id   bigint NOT NULL,
  target_type int    NOT NULL,
  props       jsonb  NOT NULL DEFAULT '{}'::jsonb,   -- relationship attributes, keyed by prop_id as text
  order_key   text COLLATE "C",                      -- fractional, lexicographically sortable
  rev         int    NOT NULL REFERENCES truss.schema_rev (rev),
  ver         bigint NOT NULL DEFAULT 1,
  created_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
  updated_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT edge_props_is_object CHECK (jsonb_typeof(props) = 'object'),
  CONSTRAINT edge_source_fk FOREIGN KEY (source_id, source_type)
    REFERENCES truss.object (id, type_id) ON DELETE RESTRICT,
  CONSTRAINT edge_target_fk FOREIGN KEY (target_id, target_type)
    REFERENCES truss.object (id, type_id) ON DELETE RESTRICT,
  CONSTRAINT edge_endpoint_types_fk FOREIGN KEY (rel_type_id, source_type, target_type)
    REFERENCES truss.rel_endpoint (rel_type_id, source_type, target_type)
);
CREATE INDEX edge_out ON truss.edge (source_id, rel_type_id) INCLUDE (target_id, target_type);
CREATE INDEX edge_in  ON truss.edge (target_id, rel_type_id) INCLUDE (source_id, source_type);

-- ---- History -----------------------------------------------------------------------------
CREATE SEQUENCE truss.journal_seq;
CREATE TABLE truss.journal (
  seq          bigint NOT NULL DEFAULT nextval('truss.journal_seq'),
  at           timestamptz NOT NULL DEFAULT clock_timestamp(),
  xid          xid8 NOT NULL DEFAULT pg_current_xact_id(),
  entity_kind  char(1) NOT NULL CHECK (entity_kind IN ('o','e')),   -- object or edge
  entity_id    bigint NOT NULL,
  entity_type  int NOT NULL,                       -- type_id for an object, rel_type_id for an edge
  ver          bigint NOT NULL,                    -- record version after the change
  op           text NOT NULL CHECK (op IN ('create','update','delete','retain','rebind')),
  prop_id      int,                                -- NULL for create and delete rows
  old_value    jsonb,
  new_value    jsonb,
  rev          int NOT NULL,                       -- catalog revision in force
  origin       jsonb NOT NULL DEFAULT '{}'::jsonb, -- who and what caused the change (CONTRACT-002)
  CONSTRAINT journal_pkey PRIMARY KEY (at, seq),
  CONSTRAINT journal_origin_is_object CHECK (jsonb_typeof(origin) = 'object')
) PARTITION BY RANGE (at);
CREATE TABLE truss.journal_default PARTITION OF truss.journal DEFAULT;
CREATE INDEX journal_entity ON truss.journal (entity_kind, entity_id, ver);
