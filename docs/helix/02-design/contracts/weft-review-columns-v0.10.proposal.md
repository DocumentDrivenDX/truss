# Selected review layout columns (0.10 proposal)

Companion to [CONTRACT-012](CONTRACT-012-weft-storage-handoff.md).
This is the selected 101-statement review composition, including explicit ADD COLUMN and column-type changes.
Baseline 0.2 remains a separate profile. Native installation and compiler binding adoption remain unqualified.
Nullability reports explicit NOT NULL/PRIMARY KEY effects only; CHECK expressions and protected guards may reject NULL independently.
The [source-effect inventory](weft-review-columns-v0.10.proposal.json) pins the complete native AST and original definition pointers.

| Table | Columns |
| --- | --- |
| `setting` | 2 |
| `module_access` | 4 |
| `schema_rev` | 3 |
| `schema_head` | 2 |
| `schema_doc` | 8 |
| `schema_change` | 6 |
| `type_def` | 19 |
| `prop_def` | 20 |
| `key_def` | 14 |
| `rel_def` | 25 |
| `rel_endpoint` | 3 |
| `object` | 10 |
| `edge` | 13 |
| `edge_limit` | 4 |
| `key_tombstone` | 7 |
| `record_source` | 5 |
| `feed_consumer` | 4 |
| `journal` | 13 |
| `row_home_operation` | 16 |
| `row_home_journal_stage` | 6 |
| `row_home_state` | 13 |
| `row_home_node` | 10 |
| `row_home_scalar` | 13 |
| `relationship_lineage` | 5 |
| `row_home_touch` | 12 |
| `row_home_capacity` | 7 |
| `key_bucket_guard` | 3 |
| `object_key_bucket` | 9 |
| `object_key_reservation_bucket` | 6 |
| `catalog_acceptance_report` | 2 |
| `installation_marker` | 11 |
| `installation_archive` | 7 |
| `feed_tx` | 12 |
| `feed_member` | 14 |
| `feed_prerequisite` | 10 |
| `feed_configuration_prerequisite` | 11 |
| `complete_feed_consumer` | 21 |
| `complete_feed_administration_receipt` | 14 |
| `complete_feed_seed_attempt` | 12 |
| `complete_feed_seed_artifact` | 10 |
| `key_lifecycle_history` | 9 |
| `installation_admission` | 12 |
| `key_migration_receipt` | 13 |

Complete-feed table column definitions are in the [feed chapter](weft-review-columns-v0.10.feed.proposal.md).

## setting

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `key` | `text` | no |
| `value` | `jsonb` | no |

## module_access

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `document_id` | `text` | no |
| `module` | `text` | no |
| `reader_role` | `text` | no |
| `writer_role` | `text` | no |

## schema_rev

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rev` | `pg_catalog.int4` | no |
| `accepted_at` | `timestamptz` | no |
| `origin` | `jsonb` | no |

## schema_head

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `id` | `pg_catalog.int4` | no |
| `rev` | `pg_catalog.int4` | no |

## schema_doc

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rev` | `pg_catalog.int4` | no |
| `ord` | `pg_catalog.int4` | no |
| `doc_id` | `text` | no |
| `doc_revision` | `text` | no |
| `umf_version` | `text` | no |
| `content_sha256` | `text` | no |
| `document` | `text` | no |
| `validation` | `jsonb` | no |

## schema_change

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rev` | `pg_catalog.int4` | no |
| `seq` | `pg_catalog.int4` | no |
| `kind` | `text` | no |
| `def_id` | `pg_catalog.int4` | no |
| `before` | `jsonb` | no |
| `after` | `jsonb` | no |

## type_def

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `document_id` | `text` | no |
| `type_id` | `pg_catalog.int4` | no |
| `module` | `text` | no |
| `element` | `text` | no |
| `kind` | `text` | no |
| `provisional` | `pg_catalog.bool` | no |
| `since_rev` | `pg_catalog.int4` | no |
| `doc_ord` | `pg_catalog.int4` | yes |
| `retired_rev` | `pg_catalog.int4` | yes |
| `lineage_profile` | `text` | no |
| `lineage_bytes` | `bytea` | no |
| `lineage_sha256` | `bytea` | yes |
| `definition_source_kind` | `text` | yes |
| `definition_rev` | `pg_catalog.int4` | yes |
| `definition_doc_ord` | `pg_catalog.int4` | yes |
| `definition_document_id` | `text` | yes |
| `binding_source_rev` | `pg_catalog.int4` | yes |
| `binding_source_pointer` | `text` | yes |
| `binding_source_bytes` | `bytea` | yes |

## prop_def

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `prop_id` | `pg_catalog.int4` | no |
| `type_id` | `pg_catalog.int4` | no |
| `element` | `text` | no |
| `name` | `text` | no |
| `scalar_type` | `text` | yes |
| `nullability` | `text` | no |
| `cardinality` | `text` | no |
| `facets` | `jsonb` | yes |
| `item` | `jsonb` | yes |
| `home` | `text` | no |
| `since_rev` | `pg_catalog.int4` | no |
| `doc_ord` | `pg_catalog.int4` | no |
| `retired_rev` | `pg_catalog.int4` | yes |
| `definition_source_kind` | `text` | yes |
| `definition_rev` | `pg_catalog.int4` | yes |
| `definition_doc_ord` | `pg_catalog.int4` | yes |
| `definition_document_id` | `text` | yes |
| `binding_source_rev` | `pg_catalog.int4` | yes |
| `binding_source_pointer` | `text` | yes |
| `binding_source_bytes` | `bytea` | yes |

## key_def

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `type_id` | `pg_catalog.int4` | no |
| `key_id` | `text` | no |
| `key_num` | `pg_catalog.int2` | no |
| `prop_ids` | `pg_catalog.int4[]` | no |
| `is_primary` | `pg_catalog.bool` | no |
| `since_rev` | `pg_catalog.int4` | no |
| `retired_rev` | `pg_catalog.int4` | yes |
| `definition_source_kind` | `text` | yes |
| `definition_rev` | `pg_catalog.int4` | yes |
| `definition_doc_ord` | `pg_catalog.int4` | yes |
| `definition_document_id` | `text` | yes |
| `binding_source_rev` | `pg_catalog.int4` | yes |
| `binding_source_pointer` | `text` | yes |
| `binding_source_bytes` | `bytea` | yes |

## rel_def

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `document_id` | `text` | no |
| `rel_type_id` | `pg_catalog.int4` | no |
| `module` | `text` | no |
| `rel_id` | `text` | no |
| `name` | `text` | no |
| `source_min` | `pg_catalog.int4` | no |
| `source_max` | `pg_catalog.int4` | yes |
| `target_min` | `pg_catalog.int4` | no |
| `target_max` | `pg_catalog.int4` | yes |
| `lifecycle` | `text` | no |
| `directed` | `pg_catalog.bool` | no |
| `target_key` | `text` | yes |
| `composition` | `pg_catalog.bool` | no |
| `assoc_type_id` | `pg_catalog.int4` | yes |
| `inverse` | `text` | yes |
| `since_rev` | `pg_catalog.int4` | no |
| `doc_ord` | `pg_catalog.int4` | no |
| `retired_rev` | `pg_catalog.int4` | yes |
| `definition_source_kind` | `text` | yes |
| `definition_rev` | `pg_catalog.int4` | yes |
| `definition_doc_ord` | `pg_catalog.int4` | yes |
| `definition_document_id` | `text` | yes |
| `binding_source_rev` | `pg_catalog.int4` | yes |
| `binding_source_pointer` | `text` | yes |
| `binding_source_bytes` | `bytea` | yes |

## rel_endpoint

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rel_type_id` | `pg_catalog.int4` | no |
| `source_type` | `pg_catalog.int4` | no |
| `target_type` | `pg_catalog.int4` | no |

## object

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `id` | `pg_catalog.int8` | no |
| `type_id` | `pg_catalog.int4` | no |
| `props` | `jsonb` | no |
| `retained` | `jsonb` | yes |
| `root_id` | `pg_catalog.int8` | yes |
| `root_type` | `pg_catalog.int4` | yes |
| `rev` | `pg_catalog.int4` | no |
| `ver` | `pg_catalog.int8` | no |
| `created_at` | `timestamptz` | no |
| `updated_at` | `timestamptz` | no |

## edge

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `id` | `pg_catalog.int8` | no |
| `rel_type_id` | `pg_catalog.int4` | no |
| `source_id` | `pg_catalog.int8` | no |
| `source_type` | `pg_catalog.int4` | no |
| `target_id` | `pg_catalog.int8` | no |
| `target_type` | `pg_catalog.int4` | no |
| `props` | `jsonb` | no |
| `order_key` | `text` | yes |
| `rev` | `pg_catalog.int4` | no |
| `ver` | `pg_catalog.int8` | no |
| `created_at` | `timestamptz` | no |
| `updated_at` | `timestamptz` | no |
| `retained` | `pg_catalog.jsonb` | yes |

## edge_limit

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rel_type_id` | `pg_catalog.int8` | no |
| `side` | `pg_catalog.bpchar (see original modifiers)` | no |
| `endpoint_id` | `pg_catalog.int8` | no |
| `edge_id` | `pg_catalog.int8` | no |

## key_tombstone

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `entity_kind` | `pg_catalog.bpchar (see original modifiers)` | no |
| `type_id` | `pg_catalog.int4` | no |
| `key_num` | `pg_catalog.int2` | no |
| `k` | `text` | no |
| `entity_id` | `pg_catalog.int8` | no |
| `ver` | `pg_catalog.int8` | no |
| `at` | `timestamptz` | no |

## record_source

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `entity_kind` | `pg_catalog.bpchar (see original modifiers)` | no |
| `entity_id` | `pg_catalog.int8` | no |
| `load_id` | `text` | no |
| `source` | `jsonb` | no |
| `imported_at` | `timestamptz` | no |

## feed_consumer

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `consumer` | `text` | no |
| `xid` | `xid8` | no |
| `seq` | `pg_catalog.int8` | no |
| `updated_at` | `timestamptz` | no |

## journal

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `seq` | `pg_catalog.int8` | no |
| `at` | `timestamptz` | no |
| `xid` | `xid8` | no |
| `entity_kind` | `pg_catalog.bpchar (see original modifiers)` | no |
| `entity_id` | `pg_catalog.int8` | no |
| `entity_type` | `pg_catalog.int4` | no |
| `ver` | `pg_catalog.int8` | no |
| `op` | `text` | no |
| `prop_id` | `pg_catalog.int4` | yes |
| `old_value` | `jsonb` | yes |
| `new_value` | `jsonb` | yes |
| `rev` | `pg_catalog.int4` | no |
| `origin` | `jsonb` | no |

## row_home_operation

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `original_writer_xid` | `xid8` | no |
| `operation_ordinal` | `pg_catalog.int8` | no |
| `operation_kind` | `text` | no |
| `phase` | `text` | no |
| `effect_generation` | `pg_catalog.int8` | no |
| `readiness_generation` | `pg_catalog.int8` | yes |
| `sealed_generation` | `pg_catalog.int8` | yes |
| `application_generation` | `pg_catalog.int8` | yes |
| `original_context_bytes` | `bytea` | no |
| `original_definition_bytes` | `bytea` | no |
| `original_input_bytes` | `bytea` | no |
| `original_prestate_bytes` | `bytea` | no |
| `admitted_candidate_bytes` | `bytea` | no |
| `effect_obligation_bytes` | `bytea` | no |
| `original_group_custody_bytes` | `bytea` | no |
| `application_result_bytes` | `bytea` | yes |

## row_home_journal_stage

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `original_writer_xid` | `pg_catalog.xid8` | no |
| `operation_ordinal` | `pg_catalog.int8` | no |
| `stage_name` | `pg_catalog.text` | no |
| `stage_ordinal` | `pg_catalog.int8` | no |
| `effect_generation` | `pg_catalog.int8` | no |
| `body_bytes` | `pg_catalog.bytea` | no |

## row_home_state

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `state_id` | `pg_catalog.int8` | no |
| `owner_kind` | `text` | no |
| `object_id` | `pg_catalog.int8` | yes |
| `object_type_id` | `pg_catalog.int4` | yes |
| `edge_id` | `pg_catalog.int8` | yes |
| `relationship_type_id` | `pg_catalog.int4` | yes |
| `property_owner_type_id` | `pg_catalog.int4` | no |
| `property_id` | `pg_catalog.int4` | no |
| `root_node_id` | `pg_catalog.int8` | no |
| `definition_bytes` | `bytea` | no |
| `home_profile_bytes` | `bytea` | no |
| `value_profile_bytes` | `bytea` | no |
| `source_bytes` | `bytea` | no |

## row_home_node

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `state_id` | `pg_catalog.int8` | no |
| `node_id` | `pg_catalog.int8` | no |
| `parent_node_id` | `pg_catalog.int8` | yes |
| `slot_kind` | `text` | no |
| `sequence_ordinal` | `pg_catalog.int8` | yes |
| `map_key` | `text` | yes |
| `record_field_identity_bytes` | `bytea` | yes |
| `value_kind` | `text` | no |
| `definition_bytes` | `bytea` | no |
| `source_bytes` | `bytea` | no |

## row_home_scalar

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `state_id` | `pg_catalog.int8` | no |
| `node_id` | `pg_catalog.int8` | no |
| `scalar_kind` | `text` | no |
| `text_value` | `text` | yes |
| `boolean_value` | `pg_catalog.bool` | yes |
| `numeric_value` | `pg_catalog.numeric` | yes |
| `numeric_token` | `text` | yes |
| `binary_value` | `bytea` | yes |
| `temporal_text` | `text` | yes |
| `temporal_instant` | `timestamptz` | yes |
| `opaque_bytes` | `bytea` | yes |
| `codec_definition_bytes` | `bytea` | no |
| `original_source_bytes` | `bytea` | no |

## relationship_lineage

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rel_type_id` | `pg_catalog.int4` | no |
| `lineage_category` | `text` | no |
| `identity_profile` | `text` | no |
| `original_identity_bytes` | `bytea` | no |
| `identity_sha256` | `bytea` | yes |

## row_home_touch

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `transaction_id` | `xid8` | no |
| `owner_kind` | `text` | no |
| `owner_id` | `pg_catalog.int8` | no |
| `owner_discriminator_id` | `pg_catalog.int4` | no |
| `property_owner_type_id` | `pg_catalog.int4` | no |
| `property_id` | `pg_catalog.int4` | no |
| `dirty_generation` | `pg_catalog.int8` | no |
| `sealed_generation` | `pg_catalog.int8` | yes |
| `original_layout_bytes` | `bytea` | no |
| `original_home_bytes` | `bytea` | no |
| `original_owner_property_bytes` | `bytea` | no |
| `original_operation_bytes` | `bytea` | no |

## row_home_capacity

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `singleton_id` | `pg_catalog.int2` | no |
| `retained_rows` | `pg_catalog.int8` | no |
| `retained_custody_bytes` | `pg_catalog.int8` | no |
| `reserved_rows` | `pg_catalog.int8` | no |
| `reserved_custody_bytes` | `pg_catalog.int8` | no |
| `original_layout_bytes` | `bytea` | no |
| `original_resource_profile_bytes` | `bytea` | no |

## key_bucket_guard

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `namespace_sha256` | `bytea` | no |
| `key_sha256` | `bytea` | no |
| `generation` | `pg_catalog.int8` | no |

## object_key_bucket

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `storage_row_id` | `pg_catalog.int8` | no |
| `type_id` | `pg_catalog.int4` | no |
| `key_num` | `pg_catalog.int2` | no |
| `object_id` | `pg_catalog.int8` | no |
| `namespace_bytes` | `bytea` | no |
| `key_bytes` | `bytea` | no |
| `original_context_bytes` | `bytea` | no |
| `namespace_sha256` | `bytea` | yes |
| `key_sha256` | `bytea` | yes |

## object_key_reservation_bucket

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `storage_row_id` | `pg_catalog.int8` | no |
| `namespace_bytes` | `bytea` | no |
| `key_bytes` | `bytea` | no |
| `original_reservation_bytes` | `bytea` | no |
| `namespace_sha256` | `bytea` | yes |
| `key_sha256` | `bytea` | yes |

## catalog_acceptance_report

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `rev` | `pg_catalog.int4` | no |
| `report_bytes` | `pg_catalog.bytea` | no |

## installation_marker

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `singleton_id` | `pg_catalog.int2` | no |
| `marker_interface_version` | `text` | no |
| `installation_id` | `text` | no |
| `layout_version` | `text` | no |
| `bundle_sha256` | `bytea` | no |
| `inventory_profile` | `text` | no |
| `inventory_sha256` | `bytea` | no |
| `database_identity` | `text` | no |
| `schema_name` | `text` | no |
| `installed_at` | `timestamptz` | no |
| `installed_at_text` | `text` | no |

## installation_archive

| Column | Declared native type | SQL NULL allowed by declaration |
| --- | --- | --- |
| `archive_row_id` | `pg_catalog.int8` | no |
| `installation_id` | `text` | no |
| `artifact_role` | `text` | no |
| `artifact_identity` | `text` | no |
| `artifact_bytes` | `bytea` | no |
| `artifact_sha256` | `bytea` | yes |
| `artifact_identity_sha256` | `bytea` | yes |
