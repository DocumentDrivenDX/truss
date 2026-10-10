-- truss storage layout, version 0.1 (draft). Normative DDL for CONTRACT-001.
-- A fixed set of tables. Adding a type, property, key or relationship adds catalog rows only;
-- it never adds columns, tables, partitions or per-type indexes.
-- The schema name is a parameter of the deployment; `truss` is the default.

CREATE SCHEMA IF NOT EXISTS truss;
COMMENT ON SCHEMA truss IS 'truss-layout 0.2';

-- ---- Deployment settings ---------------------------------------------------------------
-- journal_mode: 'engine' (the engine writes the journal and maintains ver and updated_at)
-- or 'trigger' (database triggers do; the engine MUST NOT). See CONTRACT-002.
CREATE TABLE truss.setting (
  key   text PRIMARY KEY,
  value jsonb NOT NULL
);
INSERT INTO truss.setting VALUES ('journal_mode', '"engine"');
-- key_reuse: 'forbid' (a key value an object has held stays reserved, so an import skips it and a direct
-- create is refused) or 'allow' (a tombstone is still written but a create may reuse the value). See CONTRACT-004.
INSERT INTO truss.setting VALUES ('key_reuse', '"forbid"');

-- ---- Module access (optional; see module-isolation.sql and CONTRACT-005) ----------------------
-- Which database roles may read and write the types and relationships of a UMF module. Empty by default.
-- A role may appear in several rows, for example one reader role shared by two linked modules.
CREATE TABLE truss.module_access (
  module      text PRIMARY KEY,
  reader_role text NOT NULL,
  writer_role text NOT NULL,
  CONSTRAINT module_access_roles_differ CHECK (reader_role <> writer_role)
);

-- ---- Schema catalog: UMF documents verbatim and immutable per catalog revision --------
CREATE TABLE truss.schema_rev (
  rev          int PRIMARY KEY,
  accepted_at  timestamptz NOT NULL DEFAULT now(),
  report       jsonb NOT NULL,                -- acceptance and enforcement report (CONTRACT-003)
  origin       jsonb NOT NULL DEFAULT '{}'::jsonb,   -- who accepted it: actor, db_role, reason, x-* (CONTRACT-002, origin)
  CONSTRAINT schema_rev_origin_is_object CHECK (jsonb_typeof(origin) = 'object')
);
INSERT INTO truss.schema_rev VALUES (0, now(), '{}');   -- revision 0 is the empty catalog

-- The current revision, one row, updated in place by every acceptance (CONTRACT-001, Concurrency).
CREATE TABLE truss.schema_head (
  id   int PRIMARY KEY CHECK (id = 1),
  rev  int NOT NULL REFERENCES truss.schema_rev (rev)
);
INSERT INTO truss.schema_head VALUES (1, 0);

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
-- Prior definitions, kept when a revision changes a catalog row in place (CONTRACT-003).
CREATE TABLE truss.schema_change (
  rev     int  NOT NULL REFERENCES truss.schema_rev (rev),
  seq     int  NOT NULL,
  kind    text NOT NULL CHECK (kind IN ('type','prop','rel')),
  def_id  int  NOT NULL,
  before  jsonb NOT NULL,
  after   jsonb NOT NULL,
  PRIMARY KEY (rev, seq)
);

-- ---- Binding catalog: derived from the documents, rebuildable ---------------------------
CREATE TABLE truss.type_def (
  type_id      int PRIMARY KEY,
  module       text NOT NULL,
  element      text NOT NULL,
  kind         text NOT NULL,
  provisional  boolean NOT NULL DEFAULT false,  -- named by a relationship but not yet defined
  since_rev    int NOT NULL REFERENCES truss.schema_rev (rev),
  doc_ord      int,                              -- defining document; NULL for a provisional type
  retired_rev  int REFERENCES truss.schema_rev (rev),
  UNIQUE (module, element),
  FOREIGN KEY (since_rev, doc_ord) REFERENCES truss.schema_doc (rev, ord)
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
  doc_ord      int  NOT NULL,
  retired_rev  int REFERENCES truss.schema_rev (rev),
  UNIQUE (type_id, name),
  UNIQUE (type_id, element),
  FOREIGN KEY (since_rev, doc_ord) REFERENCES truss.schema_doc (rev, ord)
);
CREATE TABLE truss.key_def (
  type_id    int  NOT NULL REFERENCES truss.type_def (type_id),
  key_id     text NOT NULL,                     -- the stable UMF key identity
  key_num    smallint NOT NULL,                 -- compact number used in object_key; never reused
  prop_ids   int[] NOT NULL,                    -- components in order
  is_primary boolean NOT NULL,
  since_rev  int  NOT NULL REFERENCES truss.schema_rev (rev),
  retired_rev int REFERENCES truss.schema_rev (rev),   -- a retired key's rows are deleted; its number is not reused
  PRIMARY KEY (type_id, key_id),
  UNIQUE (type_id, key_num)
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
  doc_ord       int NOT NULL,
  retired_rev   int REFERENCES truss.schema_rev (rev),
  UNIQUE (module, rel_id),
  FOREIGN KEY (since_rev, doc_ord) REFERENCES truss.schema_doc (rev, ord)
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
  root_type   int,
  rev         int    NOT NULL REFERENCES truss.schema_rev (rev),  -- catalog revision of the last write
  ver         bigint NOT NULL DEFAULT 1,             -- record version; +1 per change
  created_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
  updated_at  timestamptz NOT NULL DEFAULT clock_timestamp(),
  CONSTRAINT object_pkey PRIMARY KEY (id, type_id),
  CONSTRAINT object_props_is_object CHECK (jsonb_typeof(props) = 'object'),
  CONSTRAINT object_retained_is_object CHECK (retained IS NULL OR jsonb_typeof(retained) = 'object'),
  CONSTRAINT object_root_both_or_neither CHECK ((root_id IS NULL) = (root_type IS NULL)),
  CONSTRAINT object_root_fk FOREIGN KEY (root_id, root_type) REFERENCES truss.object (id, type_id) ON DELETE RESTRICT
);
CREATE INDEX object_type_id ON truss.object (type_id, id);   -- keyset listing of one type

-- Business identity: one row per object per key, unique per (type, key, value).
-- `k` is the canonical key text (CONTRACT-001, Key identity).
CREATE TABLE truss.object_key (
  type_id    int      NOT NULL,
  key_num    smallint NOT NULL,
  k          text COLLATE "C" NOT NULL,
  object_id  bigint   NOT NULL,
  CONSTRAINT object_key_pkey PRIMARY KEY (type_id, key_num, k),
  CONSTRAINT object_key_one_per_object UNIQUE (object_id, type_id, key_num),
  CONSTRAINT object_key_def_fk FOREIGN KEY (type_id, key_num) REFERENCES truss.key_def (type_id, key_num),
  CONSTRAINT object_key_object_fk FOREIGN KEY (object_id, type_id)
    REFERENCES truss.object (id, type_id) ON DELETE CASCADE
);

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
-- Unique: one edge per relationship, source and target, whatever the relationship. Two kinds of link between
-- the same records are two relationships. The index still serves traversal by its (source_id, rel_type_id) prefix.
CREATE UNIQUE INDEX edge_out ON truss.edge (source_id, rel_type_id, target_id) INCLUDE (target_type);
CREATE INDEX edge_in  ON truss.edge (target_id, rel_type_id) INCLUDE (source_id, source_type);

-- Maximum multiplicity of one, enforced without a per-relationship index. A relationship that allows
-- one edge per source gets an 's' row for each edge, one that allows one per target gets a 't' row;
-- the primary key refuses a second. The engine or a host write function inserts the row with the edge.
CREATE TABLE truss.edge_limit (
  rel_type_id bigint NOT NULL,
  side        char(1) NOT NULL CHECK (side IN ('s', 't')),
  endpoint_id bigint NOT NULL,
  edge_id     bigint NOT NULL REFERENCES truss.edge (id) ON DELETE CASCADE,
  PRIMARY KEY (rel_type_id, side, endpoint_id)
);
CREATE INDEX edge_limit_edge ON truss.edge_limit (edge_id);

-- ---- Import identity and provenance -------------------------------------------------------
-- A key value an object has held, or the endpoints of an imported edge that was deleted, written in the
-- transaction that deletes or re-keys the record, never updated or removed. For an object, type_id is its
-- type and k its canonical key text (CONTRACT-001, Key identity); for an edge, type_id is its relationship,
-- key_num is 0, and k is the compact JSON array of the endpoint ids as decimal strings, source first.
CREATE TABLE truss.key_tombstone (
  entity_kind char(1) NOT NULL CHECK (entity_kind IN ('o', 'e')),
  type_id     int     NOT NULL,
  key_num     smallint NOT NULL,
  k           text COLLATE "C" NOT NULL,
  entity_id   bigint  NOT NULL,                      -- the object or edge that held it
  ver         bigint  NOT NULL,                      -- the version at which it stopped holding it
  at          timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (entity_kind, type_id, key_num, k),
  CONSTRAINT key_tombstone_edge_key CHECK (entity_kind = 'o' OR key_num = 0)
);

-- One row per imported record, written by the import that created it and never updated: the load, and the
-- source's own facts. source is a JSON object; the defined optional keys are author, at and system.
CREATE TABLE truss.record_source (
  entity_kind char(1) NOT NULL CHECK (entity_kind IN ('o', 'e')),
  entity_id   bigint  NOT NULL,
  load_id     text    NOT NULL,
  source      jsonb   NOT NULL DEFAULT '{}'::jsonb,
  imported_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  PRIMARY KEY (entity_kind, entity_id),
  CONSTRAINT record_source_is_object CHECK (jsonb_typeof(source) = 'object')
);
CREATE INDEX record_source_load ON truss.record_source (load_id);

-- ---- Change feed consumers ----------------------------------------------------------------
-- The position each registered consumer of the journal has reached (CONTRACT-006). A consumer reports its own
-- position; retention never drops a journal partition that holds rows past the lowest reported position.
CREATE TABLE truss.feed_consumer (
  consumer    text PRIMARY KEY,
  xid         xid8   NOT NULL,                       -- last journal row delivered, in (xid, seq) order
  seq         bigint NOT NULL,
  updated_at  timestamptz NOT NULL DEFAULT clock_timestamp()
);

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
  op           text NOT NULL CHECK (op IN ('create','update','delete','retain','rebind','transform')),
  prop_id      int,                                -- NULL for create and delete rows
  old_value    jsonb,
  new_value    jsonb,
  rev          int NOT NULL,                       -- catalog revision in force
  origin       jsonb NOT NULL DEFAULT '{}'::jsonb, -- who and what caused the change (CONTRACT-002)
  CONSTRAINT journal_pkey PRIMARY KEY (at, seq),
  CONSTRAINT journal_origin_is_object CHECK (jsonb_typeof(origin) = 'object')
) PARTITION BY RANGE (at);
-- No default partition: a deployment creates RANGE partitions ahead of time (CONTRACT-002).
CREATE INDEX journal_entity ON truss.journal (entity_kind, entity_id, ver);
CREATE INDEX journal_feed   ON truss.journal (xid, seq);
-- Finds the rows of an earlier group by the request id it carried (CONTRACT-004, apply_group). Partial, so it
-- holds an entry only for rows of a group that carried one; the other rows pay nothing for it.
CREATE INDEX journal_request ON truss.journal ((origin #>> '{request,id}')) WHERE origin ? 'request';
