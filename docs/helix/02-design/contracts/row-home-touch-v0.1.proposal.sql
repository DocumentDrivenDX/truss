-- Unadopted native dirty-generation custody home; not an installer or guard.
-- Native routines/triggers exclusively capture/update/seal these entries.
CREATE TABLE truss.row_home_touch (
  transaction_id xid8 NOT NULL DEFAULT pg_catalog.pg_current_xact_id(),
  owner_kind text COLLATE pg_catalog."C" NOT NULL,
  owner_id bigint NOT NULL,
  owner_discriminator_id int NOT NULL,
  property_owner_type_id int NOT NULL,
  property_id int NOT NULL,
  dirty_generation bigint NOT NULL,
  sealed_generation bigint,
  original_layout_bytes bytea NOT NULL,
  original_home_bytes bytea NOT NULL,
  original_owner_property_bytes bytea NOT NULL,
  original_operation_bytes bytea NOT NULL,
  CONSTRAINT row_home_touch_pk PRIMARY KEY
    (transaction_id, owner_kind, owner_id, owner_discriminator_id,
     property_owner_type_id, property_id),
  CONSTRAINT row_home_touch_kind CHECK (owner_kind IN ('object', 'edge')),
  CONSTRAINT row_home_touch_generations CHECK
    (dirty_generation > 0 AND (sealed_generation IS NULL
      OR (sealed_generation > 0 AND sealed_generation <= dirty_generation))),
  CONSTRAINT row_home_touch_originals CHECK
    (octet_length(original_layout_bytes) > 0 AND octet_length(original_home_bytes) > 0
      AND octet_length(original_owner_property_bytes) > 0
      AND octet_length(original_operation_bytes) > 0)
);
-- No graph/property FK: deleted/cascaded originals must retain attribution.
-- No public transaction-ID/default override, direct DML or seal authority.
-- PK does not prove original layout/home/association; changed originals refuse.
-- dirty_generation increment/overflow refusal and native seal/commit checks missing.
-- No native xid8/default/privilege/retention or ordinary-writer qualification.
