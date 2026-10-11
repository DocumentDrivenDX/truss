-- Fresh-layout pending relationship-source adjunct; unadopted, not migration SQL.
-- Requires original source-home and operation/binding archive components.
-- Shape/FKs do not authenticate a source or register association semantics.
ALTER TABLE truss.rel_def
 ADD COLUMN pending_writer_xid xid8,
 ADD COLUMN pending_operation_ordinal bigint,
 ADD COLUMN pending_binding_revision int,
 ADD COLUMN pending_mapping_pointer text COLLATE pg_catalog."C",
 ADD COLUMN pending_mapping_bytes bytea,
 ADD CONSTRAINT rel_def_pending_operation_fk FOREIGN KEY (pending_writer_xid,pending_operation_ordinal)
  REFERENCES truss.row_home_operation (original_writer_xid,operation_ordinal),
 ADD CONSTRAINT rel_def_pending_binding_fk FOREIGN KEY (pending_binding_revision)
  REFERENCES truss.catalog_binding_archive (revision);
ALTER TABLE truss.rel_def DROP CONSTRAINT rel_def_definition_source_complete;
ALTER TABLE truss.rel_def ADD CONSTRAINT rel_def_definition_source_complete CHECK (
 (pending_writer_xid IS NULL AND pending_operation_ordinal IS NULL AND pending_binding_revision IS NULL AND pending_mapping_pointer IS NULL AND pending_mapping_bytes IS NULL
  AND (definition_source_kind IS NOT NULL AND ((definition_source_kind = 'accepted_document'
        AND definition_rev IS NOT NULL AND definition_doc_ord IS NOT NULL
        AND definition_document_id IS NOT NULL
        AND binding_source_rev IS NULL AND binding_source_pointer IS NULL
        AND binding_source_bytes IS NULL) OR (definition_source_kind = 'accepted_binding'
        AND definition_rev IS NULL AND definition_doc_ord IS NULL
        AND definition_document_id IS NULL
        AND binding_source_rev IS NOT NULL AND binding_source_pointer IS NOT NULL
        AND binding_source_bytes IS NOT NULL
        AND octet_length(binding_source_bytes) > 0))))
 OR (definition_source_kind IS NOT NULL AND definition_source_kind='operation_binding'
  AND pending_writer_xid IS NOT NULL AND pending_operation_ordinal IS NOT NULL AND pending_binding_revision IS NOT NULL AND pending_mapping_pointer IS NOT NULL AND pending_mapping_bytes IS NOT NULL
  AND definition_rev IS NULL AND definition_doc_ord IS NULL AND definition_document_id IS NULL
  AND binding_source_rev IS NULL AND binding_source_pointer IS NULL AND binding_source_bytes IS NULL
  AND assoc_type_id IS NOT NULL
  AND pending_binding_revision=since_rev AND pending_binding_revision>0
  AND pending_operation_ordinal>=0
  AND octet_length(pending_mapping_pointer) BETWEEN 1 AND 4096
  AND octet_length(pending_mapping_bytes) BETWEEN 1 AND 1048576)
);
