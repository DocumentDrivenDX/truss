-- Administrative component fixture only. No protected producer or ready installation.
INSERT INTO truss.installation_marker VALUES
 (1,'truss-bootstrap-marker/0.1.0','guard-fixture','component-fixture',
  decode(repeat('00',32),'hex'),'component-fixture',decode(repeat('01',32),'hex'),
  'component-fixture','truss','2026-10-09T00:00:00Z','2026-10-09T00:00:00Z');
INSERT INTO truss.source_epoch_registry
 (installation_id,source_epoch,target_incarnation,transition_reason,profile_bytes,evidence_bytes)
 VALUES ('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation','initial',
  convert_to('fixture-profile','UTF8'),convert_to('fixture-evidence','UTF8'));
INSERT INTO truss.row_home_operation
 (original_writer_xid,operation_ordinal,operation_kind,phase,effect_generation,
  original_context_bytes,original_definition_bytes,original_input_bytes,
  original_prestate_bytes,admitted_candidate_bytes,effect_obligation_bytes,original_group_custody_bytes)
 VALUES (pg_current_xact_id(),0,'administrative-repair','admitted',0,
  convert_to('fixture-context','UTF8'),convert_to('fixture-definition','UTF8'),
  convert_to('fixture-input','UTF8'),convert_to('fixture-prestate','UTF8'),
  convert_to('fixture-candidate','UTF8'),convert_to('fixture-obligation','UTF8'),
  convert_to('fixture-custody','UTF8'));
INSERT INTO truss.operation_configuration
 (original_writer_xid,operation_ordinal,installation_id,source_epoch,target_incarnation,
  configuration_generation,key_reuse,journal_mode,original_context_sha256,
  admission_profile_bytes,configuration_bytes,selected_binding_bytes,installed_inventory_bytes)
 VALUES (pg_current_xact_id(),0,'guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',
  0,'forbid','engine',sha256(convert_to('fixture-context','UTF8')),
  convert_to('fixture-admission','UTF8'),convert_to('fixture-configuration','UTF8'),
  convert_to('fixture-binding','UTF8'),convert_to('fixture-inventory','UTF8'));
INSERT INTO truss.layout_migration_receipt
 (installation_id,original_source_epoch,original_target_incarnation,original_attempt_identity_bytes,
  receipt_profile_bytes,original_request_bytes,original_receipt_bytes)
 VALUES ('guard-fixture','guard-fixture-epoch','guard-fixture-incarnation',
  convert_to('fixture-attempt','UTF8'),convert_to('fixture-receipt-profile','UTF8'),
  convert_to('fixture-request','UTF8'),convert_to('fixture-receipt','UTF8'));
