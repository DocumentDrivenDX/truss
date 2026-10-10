-- Design-only private original owner/property state lookup.
-- Ordinal 0 object, ordinal 1 edge; select one admitted route, not both.
-- Four statement-local original slots: graph owner ID, signed discriminator,
-- signed authored property-owner type and signed property identity.
-- Complete original visibility/cut/association and native bounds required.
-- LIMIT 2 diagnoses duplicate states, not complete owner visibility.

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
  AND h.property_owner_type_id = $3::pg_catalog.int4
  AND h.property_id = $4::pg_catalog.int4
LIMIT 2;

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
  AND h.property_owner_type_id = $3::pg_catalog.int4
  AND h.property_id = $4::pg_catalog.int4
LIMIT 2;
