-- CONTRACT-001 independent definition-source physical proposal, unadopted.
-- Source/constraint design only: not installed or executed against PostgreSQL.
-- Intended as a fresh empty-layout fragment after the baseline definition homes.
-- This is NOT populated conversion SQL or a complete replacement layout.
-- Requires exact selected source text/collation, revision and archive profiles.
-- Native source-kind branches do not authorize unsupported definition categories.
-- Legacy doc_ord/source FKs and their interpretation are reconciled separately
-- during complete layout adoption; do not advertise this fragment as that switch.
ALTER TABLE truss.schema_doc
  ALTER COLUMN doc_id TYPE text COLLATE pg_catalog."C";

ALTER TABLE truss.schema_doc
  ADD CONSTRAINT schema_doc_definition_source_tuple UNIQUE (rev, ord, doc_id);


ALTER TABLE truss.type_def
  ADD COLUMN definition_source_kind text COLLATE pg_catalog."C",
  ADD COLUMN definition_rev int,
  ADD COLUMN definition_doc_ord int,
  ADD COLUMN definition_document_id text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_rev int,
  ADD COLUMN binding_source_pointer text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_bytes bytea,
  ADD CONSTRAINT type_def_definition_document_fk
    FOREIGN KEY (definition_rev, definition_doc_ord, definition_document_id)
    REFERENCES truss.schema_doc (rev, ord, doc_id),
  ADD CONSTRAINT type_def_definition_binding_revision_fk
    FOREIGN KEY (binding_source_rev) REFERENCES truss.schema_rev (rev),
  ADD CONSTRAINT type_def_definition_source_complete CHECK (
    (provisional AND definition_source_kind IS NULL
      AND definition_rev IS NULL AND definition_doc_ord IS NULL
      AND definition_document_id IS NULL AND binding_source_rev IS NULL
      AND binding_source_pointer IS NULL AND binding_source_bytes IS NULL)
    OR (NOT provisional AND (definition_source_kind IS NOT NULL AND ((definition_source_kind = 'accepted_document'
        AND definition_rev IS NOT NULL AND definition_doc_ord IS NOT NULL
        AND definition_document_id IS NOT NULL
        AND binding_source_rev IS NULL AND binding_source_pointer IS NULL
        AND binding_source_bytes IS NULL) OR (definition_source_kind = 'accepted_binding'
        AND definition_rev IS NULL AND definition_doc_ord IS NULL
        AND definition_document_id IS NULL
        AND binding_source_rev IS NOT NULL AND binding_source_pointer IS NOT NULL
        AND binding_source_bytes IS NOT NULL
        AND octet_length(binding_source_bytes) > 0))))
  );


ALTER TABLE truss.prop_def
  ADD COLUMN definition_source_kind text COLLATE pg_catalog."C",
  ADD COLUMN definition_rev int,
  ADD COLUMN definition_doc_ord int,
  ADD COLUMN definition_document_id text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_rev int,
  ADD COLUMN binding_source_pointer text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_bytes bytea,
  ADD CONSTRAINT prop_def_definition_document_fk
    FOREIGN KEY (definition_rev, definition_doc_ord, definition_document_id)
    REFERENCES truss.schema_doc (rev, ord, doc_id),
  ADD CONSTRAINT prop_def_definition_binding_revision_fk
    FOREIGN KEY (binding_source_rev) REFERENCES truss.schema_rev (rev),
  ADD CONSTRAINT prop_def_definition_source_complete CHECK (
    definition_source_kind IS NOT NULL AND ((definition_source_kind = 'accepted_document'
        AND definition_rev IS NOT NULL AND definition_doc_ord IS NOT NULL
        AND definition_document_id IS NOT NULL
        AND binding_source_rev IS NULL AND binding_source_pointer IS NULL
        AND binding_source_bytes IS NULL) OR (definition_source_kind = 'accepted_binding'
        AND definition_rev IS NULL AND definition_doc_ord IS NULL
        AND definition_document_id IS NULL
        AND binding_source_rev IS NOT NULL AND binding_source_pointer IS NOT NULL
        AND binding_source_bytes IS NOT NULL
        AND octet_length(binding_source_bytes) > 0))
  );


ALTER TABLE truss.key_def
  ADD COLUMN definition_source_kind text COLLATE pg_catalog."C",
  ADD COLUMN definition_rev int,
  ADD COLUMN definition_doc_ord int,
  ADD COLUMN definition_document_id text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_rev int,
  ADD COLUMN binding_source_pointer text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_bytes bytea,
  ADD CONSTRAINT key_def_definition_document_fk
    FOREIGN KEY (definition_rev, definition_doc_ord, definition_document_id)
    REFERENCES truss.schema_doc (rev, ord, doc_id),
  ADD CONSTRAINT key_def_definition_binding_revision_fk
    FOREIGN KEY (binding_source_rev) REFERENCES truss.schema_rev (rev),
  ADD CONSTRAINT key_def_definition_source_complete CHECK (
    definition_source_kind IS NOT NULL AND ((definition_source_kind = 'accepted_document'
        AND definition_rev IS NOT NULL AND definition_doc_ord IS NOT NULL
        AND definition_document_id IS NOT NULL
        AND binding_source_rev IS NULL AND binding_source_pointer IS NULL
        AND binding_source_bytes IS NULL) OR (definition_source_kind = 'accepted_binding'
        AND definition_rev IS NULL AND definition_doc_ord IS NULL
        AND definition_document_id IS NULL
        AND binding_source_rev IS NOT NULL AND binding_source_pointer IS NOT NULL
        AND binding_source_bytes IS NOT NULL
        AND octet_length(binding_source_bytes) > 0))
  );


ALTER TABLE truss.rel_def
  ADD COLUMN definition_source_kind text COLLATE pg_catalog."C",
  ADD COLUMN definition_rev int,
  ADD COLUMN definition_doc_ord int,
  ADD COLUMN definition_document_id text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_rev int,
  ADD COLUMN binding_source_pointer text COLLATE pg_catalog."C",
  ADD COLUMN binding_source_bytes bytea,
  ADD CONSTRAINT rel_def_definition_document_fk
    FOREIGN KEY (definition_rev, definition_doc_ord, definition_document_id)
    REFERENCES truss.schema_doc (rev, ord, doc_id),
  ADD CONSTRAINT rel_def_definition_binding_revision_fk
    FOREIGN KEY (binding_source_rev) REFERENCES truss.schema_rev (rev),
  ADD CONSTRAINT rel_def_definition_source_complete CHECK (
    definition_source_kind IS NOT NULL AND ((definition_source_kind = 'accepted_document'
        AND definition_rev IS NOT NULL AND definition_doc_ord IS NOT NULL
        AND definition_document_id IS NOT NULL
        AND binding_source_rev IS NULL AND binding_source_pointer IS NULL
        AND binding_source_bytes IS NULL) OR (definition_source_kind = 'accepted_binding'
        AND definition_rev IS NULL AND definition_doc_ord IS NULL
        AND definition_document_id IS NULL
        AND binding_source_rev IS NOT NULL AND binding_source_pointer IS NOT NULL
        AND binding_source_bytes IS NOT NULL
        AND octet_length(binding_source_bytes) > 0))
  );
