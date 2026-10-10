-- Design-only bounded selected-state batch; not captured/exported or native-qualified.
-- Each statement-local $1 is the same nonempty bounded original int8[] state set.
-- Full header membership, non-NULL unique positive IDs and same-cut/account required.

SELECT n.state_id::pg_catalog.text AS state_id,
       n.node_id::pg_catalog.text AS node_id,
       n.parent_node_id::pg_catalog.text AS parent_node_id,
       n.slot_kind AS slot_kind,
       n.sequence_ordinal::pg_catalog.text AS sequence_ordinal,
       n.map_key AS map_key,
       pg_catalog.encode(n.record_field_identity_bytes, 'hex') AS record_field_identity_hex,
       n.value_kind AS value_kind,
       pg_catalog.encode(n.definition_bytes, 'hex') AS definition_bytes_hex,
       pg_catalog.encode(n.source_bytes, 'hex') AS node_source_bytes_hex
FROM truss.row_home_node AS n
WHERE n.state_id = ANY($1::pg_catalog.int8[])
ORDER BY n.state_id, n.node_id;

SELECT s.state_id::pg_catalog.text AS state_id,
       s.node_id::pg_catalog.text AS node_id,
       s.scalar_kind AS scalar_kind,
       s.text_value AS text_value,
       s.boolean_value::pg_catalog.text AS boolean_value,
       s.numeric_value::pg_catalog.text AS native_numeric_text,
       s.numeric_token AS original_numeric_token,
       pg_catalog.encode(s.binary_value, 'hex') AS binary_value_hex,
       s.temporal_text AS temporal_text,
       s.temporal_instant::pg_catalog.text AS temporal_instant_text,
       pg_catalog.encode(s.opaque_bytes, 'hex') AS opaque_bytes_hex,
       pg_catalog.encode(s.codec_definition_bytes, 'hex') AS codec_bytes_hex,
       pg_catalog.encode(s.original_source_bytes, 'hex') AS source_bytes_hex,
       pg_catalog.current_setting('DateStyle') AS metadata_date_style,
       pg_catalog.current_setting('TimeZone') AS metadata_time_zone
FROM truss.row_home_scalar AS s
WHERE s.state_id = ANY($1::pg_catalog.int8[])
ORDER BY s.state_id, s.node_id;
