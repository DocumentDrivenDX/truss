# Complete-feed columns (0.6 proposal)

Companion to [full column index](weft-review-columns-v0.6.proposal.md).


## feed_tx

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `source_epoch` | `pg_catalog.text` | no |
| `feed_profile` | `pg_catalog.text` | no |
| `original_writer_xid` | `pg_catalog.xid8` | no |
| `registration_counter` | `pg_catalog.int8` | no |
| `prerequisite_registration_counter` | `pg_catalog.int8` | no |
| `configuration_registration_counter` | `pg_catalog.int8` | no |
| `membership_generation` | `pg_catalog.int8` | no |
| `finalized_generation` | `pg_catalog.int8` | yes |
| `original_context_bytes` | `pg_catalog.bytea` | no |
| `manifest_profile_bytes` | `pg_catalog.bytea` | no |
| `manifest_bytes` | `pg_catalog.bytea` | yes |
| `manifest_sha256` | `pg_catalog.bytea` | yes |

## feed_member

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `source_epoch` | `pg_catalog.text` | no |
| `feed_profile` | `pg_catalog.text` | no |
| `original_writer_xid` | `pg_catalog.xid8` | no |
| `registration_address` | `pg_catalog.int8` | no |
| `fact_kind` | `pg_catalog.text` | no |
| `original_fact_key_bytes` | `pg_catalog.bytea` | no |
| `original_fact_key_profile_bytes` | `pg_catalog.bytea` | no |
| `original_payload_bytes` | `pg_catalog.bytea` | no |
| `original_payload_profile_bytes` | `pg_catalog.bytea` | no |
| `original_payload_sha256` | `pg_catalog.bytea` | no |
| `original_owner_context_bytes` | `pg_catalog.bytea` | no |
| `original_write_at` | `pg_catalog.timestamptz` | no |
| `original_fact_clock_bytes` | `pg_catalog.bytea` | no |
| `delivery_ordinal` | `pg_catalog.int8` | yes |

## feed_prerequisite

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `source_epoch` | `pg_catalog.text` | no |
| `feed_profile` | `pg_catalog.text` | no |
| `original_writer_xid` | `pg_catalog.xid8` | no |
| `prerequisite_address` | `pg_catalog.int8` | no |
| `original_revision` | `pg_catalog.int8` | no |
| `original_artifact_identity_bytes` | `pg_catalog.bytea` | no |
| `original_definition_bytes` | `pg_catalog.bytea` | no |
| `original_definition_profile_bytes` | `pg_catalog.bytea` | no |
| `original_definition_sha256` | `pg_catalog.bytea` | no |
| `original_owner_context_bytes` | `pg_catalog.bytea` | no |

## feed_configuration_prerequisite

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `source_epoch` | `pg_catalog.text` | no |
| `feed_profile` | `pg_catalog.text` | no |
| `original_writer_xid` | `pg_catalog.xid8` | no |
| `configuration_address` | `pg_catalog.int8` | no |
| `original_installation_identity_bytes` | `pg_catalog.bytea` | no |
| `original_configuration_generation` | `pg_catalog.int8` | no |
| `original_configuration_profile_bytes` | `pg_catalog.bytea` | no |
| `original_configuration_bytes` | `pg_catalog.bytea` | no |
| `original_producer_inventory_bytes` | `pg_catalog.bytea` | no |
| `original_configuration_sha256` | `pg_catalog.bytea` | no |
| `original_owner_context_bytes` | `pg_catalog.bytea` | no |

## complete_feed_consumer

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `storage_row_id` | `pg_catalog.int8` | no |
| `source_epoch` | `text` | no |
| `feed_profile` | `text` | no |
| `scope_identity` | `text` | no |
| `consumer_id` | `text` | no |
| `registration_id` | `text` | no |
| `worker_generation` | `pg_catalog.int8` | no |
| `state_kind` | `text` | no |
| `consumer_identity_bytes` | `bytea` | no |
| `consumer_identity_sha256` | `bytea` | yes |
| `original_registration_bytes` | `bytea` | no |
| `current_state_bytes` | `bytea` | no |
| `current_state_sha256` | `bytea` | yes |
| `applied_boundary_bytes` | `bytea` | yes |
| `applied_boundary_profile_bytes` | `bytea` | yes |
| `inclusive_protection_xid` | `xid8` | no |
| `protection_evidence_bytes` | `bytea` | no |
| `procedure_profile_bytes` | `bytea` | no |
| `downstream_profile_bytes` | `bytea` | no |
| `registered_at` | `timestamptz` | no |
| `acknowledged_at` | `timestamptz` | yes |
