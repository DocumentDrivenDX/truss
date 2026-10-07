-- Unadopted source proposal requiring baseline plus edge-retained-home-v0.1.proposal.sql.
-- Ordinal 0 object, ordinal 1 edge; exactly one admitted typed-owner route.
-- $1 positive original graph ID; $2 original signed type/relationship ID.
-- Selected coherent layout, private visibility/cut, temporal/JSONB codecs,
-- native pre-materialization bounds and original definition/owner evidence required.
-- LIMIT 2 diagnoses duplicate headers; it does not qualify record completeness.
-- JSONB text is native carrier observation, not original authored source bytes.
-- Both retained projections require independently selected exact value/presence semantics.
-- Reject baseline-only selection: its edge table has no retained column.
-- This variant is separate from the unchanged baseline metadata observation.

SELECT o.id::pg_catalog.text AS record_id,
       o.type_id::pg_catalog.text AS record_type_id,
       o.root_id::pg_catalog.text AS root_id,
       o.root_type::pg_catalog.text AS root_type_id,
       o.ver::pg_catalog.text AS record_version,
       o.rev::pg_catalog.text AS catalog_revision,
       o.created_at::pg_catalog.text AS created_at_text,
       o.updated_at::pg_catalog.text AS updated_at_text,
       o.props::pg_catalog.text AS properties_text,
       o.retained::pg_catalog.text AS retained_text,
       pg_catalog.current_setting('DateStyle') AS date_style,
       pg_catalog.current_setting('TimeZone') AS time_zone
FROM truss.object AS o
WHERE o.id = $1::pg_catalog.int8
  AND o.type_id = $2::pg_catalog.int4
LIMIT 2;

SELECT e.id::pg_catalog.text AS record_id,
       e.rel_type_id::pg_catalog.text AS record_type_id,
       e.source_id::pg_catalog.text AS source_id,
       e.source_type::pg_catalog.text AS source_type_id,
       e.target_id::pg_catalog.text AS target_id,
       e.target_type::pg_catalog.text AS target_type_id,
       e.order_key AS order_key,
       e.ver::pg_catalog.text AS record_version,
       e.rev::pg_catalog.text AS catalog_revision,
       e.created_at::pg_catalog.text AS created_at_text,
       e.updated_at::pg_catalog.text AS updated_at_text,
       e.props::pg_catalog.text AS properties_text,
       e.retained::pg_catalog.text AS retained_text,
       pg_catalog.current_setting('DateStyle') AS date_style,
       pg_catalog.current_setting('TimeZone') AS time_zone
FROM truss.edge AS e
WHERE e.id = $1::pg_catalog.int8
  AND e.rel_type_id = $2::pg_catalog.int4
LIMIT 2;
