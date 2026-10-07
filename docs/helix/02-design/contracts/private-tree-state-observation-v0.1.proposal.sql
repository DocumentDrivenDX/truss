-- Design-only private state-header lookup, not authority or an installer.
-- $1 original admitted positive state_id bigint. Read under complete original
-- owner/property visibility, selected native bounds and retained coherent cut.
-- Zero rows cannot independently classify property absence.
-- LIMIT 2 detects duplicate identity; a second row is integrity refusal.
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
WHERE h.state_id = $1::pg_catalog.int8
LIMIT 2;
