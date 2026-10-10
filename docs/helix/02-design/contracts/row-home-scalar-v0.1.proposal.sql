-- Unadopted fixed scalar payload candidate for CONTRACT-001 row-home nodes.
-- Not a bootstrap bundle; parent-kind/domain/token/profile guards remain required.
CREATE TABLE truss.row_home_scalar (
  state_id bigint NOT NULL,
  node_id bigint NOT NULL,
  scalar_kind text COLLATE pg_catalog."C" NOT NULL,
  text_value text COLLATE pg_catalog."C",
  boolean_value boolean,
  numeric_value numeric,
  numeric_token text COLLATE pg_catalog."C",
  binary_value bytea,
  temporal_text text COLLATE pg_catalog."C",
  temporal_instant timestamptz,
  opaque_bytes bytea,
  codec_definition_bytes bytea NOT NULL,
  original_source_bytes bytea NOT NULL,
  CONSTRAINT row_home_scalar_pk PRIMARY KEY (state_id, node_id),
  CONSTRAINT row_home_scalar_node_fk FOREIGN KEY (state_id, node_id)
    REFERENCES truss.row_home_node (state_id, node_id) ON DELETE CASCADE,
  CONSTRAINT row_home_scalar_carriers_nonempty CHECK (
    octet_length(codec_definition_bytes) > 0 AND octet_length(original_source_bytes) > 0),
  CONSTRAINT row_home_scalar_family CHECK (
    (scalar_kind = 'string' AND text_value IS NOT NULL
      AND boolean_value IS NULL AND numeric_value IS NULL AND numeric_token IS NULL
      AND binary_value IS NULL AND temporal_text IS NULL AND temporal_instant IS NULL
      AND opaque_bytes IS NULL)
    OR (scalar_kind = 'boolean' AND boolean_value IS NOT NULL
      AND text_value IS NULL AND numeric_value IS NULL AND numeric_token IS NULL
      AND binary_value IS NULL AND temporal_text IS NULL AND temporal_instant IS NULL
      AND opaque_bytes IS NULL)
    OR (scalar_kind IN ('integer', 'decimal') AND numeric_value IS NOT NULL
      AND numeric_token IS NOT NULL AND octet_length(numeric_token) > 0
      AND numeric_value::text COLLATE pg_catalog."C" NOT IN ('NaN', 'Infinity', '-Infinity')
      AND (scalar_kind = 'decimal' OR numeric_value = pg_catalog.trunc(numeric_value))
      AND text_value IS NULL AND boolean_value IS NULL AND binary_value IS NULL
      AND temporal_text IS NULL AND temporal_instant IS NULL AND opaque_bytes IS NULL)
    OR (scalar_kind = 'binary' AND binary_value IS NOT NULL
      AND text_value IS NULL AND boolean_value IS NULL AND numeric_value IS NULL
      AND numeric_token IS NULL AND temporal_text IS NULL AND temporal_instant IS NULL
      AND opaque_bytes IS NULL)
    OR (scalar_kind = 'timestamp' AND temporal_text IS NOT NULL
      AND text_value IS NULL AND boolean_value IS NULL AND numeric_value IS NULL
      AND numeric_token IS NULL AND binary_value IS NULL AND opaque_bytes IS NULL)
    OR (scalar_kind = 'opaque' AND opaque_bytes IS NOT NULL
      AND text_value IS NULL AND boolean_value IS NULL AND numeric_value IS NULL
      AND numeric_token IS NULL AND binary_value IS NULL
      AND temporal_text IS NULL AND temporal_instant IS NULL))
);
-- Temporal instant is optional: lexical retention does not qualify instant predicates.
-- Numeric token equality to numeric_value requires original source grammar/domain guard.
-- Native numeric range/facets and unsigned/signed semantics remain original codec rules.
-- One scalar row per scalar node; non-scalar nodes must have none (finalizer required).
-- No unrestricted B-tree on full text/binary/opaque or compound member identities.
-- Comparators/indices need selected domain/size/provenance qualification separately.
