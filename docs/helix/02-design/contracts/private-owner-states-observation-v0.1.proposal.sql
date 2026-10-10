-- Design-only complete original typed-owner row-home state enumeration.
-- Select ordinal 0 object or ordinal 1 edge, never both for one owner.
-- Statement-local $1 original positive graph owner ID; $2 signed discriminator.
-- No property/active-field filter or LIMIT; original complete visibility,
-- coherent cut and native scan/pre-materialization bounds are mandatory.
-- Numeric collection order does not select semantic property/member ordering.

SELECT h.state_id::pg_catalog.text AS state_id,
       h.owner_kind AS owner_kind,
       h.object_id::pg_catalog.text AS object_id,
       h.object_type_id::pg_catalog.text AS object_type_id,
       h.edge_id::pg_catalog.text AS edge_id,
       h.relationship_type_id::pg_catalog.text AS relationship_type_id,
       h.property_owner_type_id::pg_catalog.text AS property_owner_type_id,
       h.property_id::pg_catalog.text AS property_id,
       h.root_node_id::pg_catalog.text AS root_node_id,
       pg_catalog.encode(h.definition_bytes, 'hex') AS definition_bytes_hex,
       pg_catalog.encode(h.home_profile_bytes, 'hex') AS home_profile_bytes_hex,
       pg_catalog.encode(h.value_profile_bytes, 'hex') AS value_profile_bytes_hex,
       pg_catalog.encode(h.source_bytes, 'hex') AS state_source_bytes_hex
FROM truss.row_home_state AS h
WHERE h.owner_kind = 'object'::pg_catalog.text
  AND h.object_id = $1::pg_catalog.int8
  AND h.object_type_id = $2::pg_catalog.int4
ORDER BY h.property_owner_type_id, h.property_id, h.state_id;

SELECT h.state_id::pg_catalog.text AS state_id,
       h.owner_kind AS owner_kind,
       h.object_id::pg_catalog.text AS object_id,
       h.object_type_id::pg_catalog.text AS object_type_id,
       h.edge_id::pg_catalog.text AS edge_id,
       h.relationship_type_id::pg_catalog.text AS relationship_type_id,
       h.property_owner_type_id::pg_catalog.text AS property_owner_type_id,
       h.property_id::pg_catalog.text AS property_id,
       h.root_node_id::pg_catalog.text AS root_node_id,
       pg_catalog.encode(h.definition_bytes, 'hex') AS definition_bytes_hex,
       pg_catalog.encode(h.home_profile_bytes, 'hex') AS home_profile_bytes_hex,
       pg_catalog.encode(h.value_profile_bytes, 'hex') AS value_profile_bytes_hex,
       pg_catalog.encode(h.source_bytes, 'hex') AS state_source_bytes_hex
FROM truss.row_home_state AS h
WHERE h.owner_kind = 'edge'::pg_catalog.text
  AND h.edge_id = $1::pg_catalog.int8
  AND h.relationship_type_id = $2::pg_catalog.int4
ORDER BY h.property_owner_type_id, h.property_id, h.state_id;
