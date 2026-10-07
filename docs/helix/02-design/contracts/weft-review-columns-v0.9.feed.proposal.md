# Feed and lifecycle columns (0.9 proposal)

Companion to [full column index](weft-review-columns-v0.9.proposal.md).


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

## complete_feed_administration_receipt

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `storage_row_id` | `pg_catalog.int8` | no |
| `source_epoch` | `text` | no |
| `administrative_namespace` | `text` | no |
| `request_id` | `text` | no |
| `identity_bytes` | `bytea` | no |
| `identity_sha256` | `bytea` | yes |
| `canonical_input_bytes` | `bytea` | no |
| `input_profile_bytes` | `bytea` | no |
| `receipt_bytes` | `bytea` | no |
| `receipt_profile_bytes` | `bytea` | no |
| `actual_database_role` | `text` | no |
| `authorization_evidence_bytes` | `bytea` | no |
| `producing_xid` | `xid8` | no |
| `original_production_evidence_bytes` | `bytea` | no |

## complete_feed_seed_attempt

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `storage_row_id` | `pg_catalog.int8` | no |
| `attempt_identity_bytes` | `bytea` | no |
| `attempt_identity_sha256` | `bytea` | yes |
| `activation_profile_bytes` | `bytea` | no |
| `source_context_bytes` | `bytea` | no |
| `original_worker_bytes` | `bytea` | no |
| `state_kind` | `text` | no |
| `current_state_bytes` | `bytea` | no |
| `inclusive_replay_xmin` | `xid8` | no |
| `protection_evidence_bytes` | `bytea` | no |
| `invalidation_evidence_bytes` | `bytea` | yes |
| `classifier_retirement_evidence_bytes` | `bytea` | yes |

## complete_feed_seed_artifact

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `storage_row_id` | `pg_catalog.int8` | no |
| `attempt_row_id` | `pg_catalog.int8` | no |
| `artifact_role` | `text` | no |
| `artifact_ordinal` | `pg_catalog.int8` | no |
| `artifact_identity_bytes` | `bytea` | no |
| `artifact_identity_sha256` | `bytea` | yes |
| `artifact_profile_bytes` | `bytea` | no |
| `payload_bytes` | `bytea` | no |
| `payload_sha256` | `bytea` | yes |
| `production_custody_evidence_bytes` | `bytea` | no |

## key_lifecycle_history

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rev` | `pg_catalog.int4` | no |
| `seq` | `pg_catalog.int4` | no |
| `type_id` | `pg_catalog.int4` | no |
| `key_num` | `pg_catalog.int2` | no |
| `transition_kind` | `text` | no |
| `before_retired_rev` | `pg_catalog.int4` | yes |
| `after_retired_rev` | `pg_catalog.int4` | yes |
| `before_definition_bytes` | `bytea` | no |
| `after_definition_bytes` | `bytea` | no |
