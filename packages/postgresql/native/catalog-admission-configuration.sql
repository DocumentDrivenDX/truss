-- Original pre-effect bytes under live operation custody; profile meaning remains unadmitted.
CREATE FUNCTION truss.runtime_collect_catalog_admission_configuration(
 expected_writer_xid text,expected_operation_ordinal text,expected_effect_generation text,
 expected_configuration_profile_hex text)
RETURNS TABLE(context_hex text,configuration_generation text,key_reuse text,journal_mode text,
 configuration_hex text,selected_binding_hex text,installed_inventory_hex text,
 configuration_sha256 text,selected_binding_sha256 text,installed_inventory_sha256 text,
 configuration_profile_hex text,configuration_profile_sha256 text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original_context record; captured truss.operation_configuration%ROWTYPE;
BEGIN
 IF expected_configuration_profile_hex IS NULL
  OR octet_length(expected_configuration_profile_hex) NOT BETWEEN 2 AND 131072
  OR expected_configuration_profile_hex !~ '^([0-9a-f]{2})+$' THEN
  RAISE EXCEPTION 'bounded original configuration profile required' USING ERRCODE='22023';
 END IF;
 PERFORM truss.runtime_require_operation_configuration_current(
  expected_writer_xid,expected_operation_ordinal,expected_effect_generation);
 SELECT * INTO STRICT original_context FROM truss.runtime_collect_catalog_epoch_context(
  expected_writer_xid,expected_operation_ordinal,expected_effect_generation);
 SELECT c.* INTO STRICT captured FROM truss.operation_configuration c
  WHERE c.original_writer_xid=pg_current_xact_id_if_assigned()
   AND c.operation_ordinal::text=expected_operation_ordinal;
 IF encode(captured.admission_profile_bytes,'hex') IS DISTINCT FROM expected_configuration_profile_hex THEN
  RAISE EXCEPTION 'original configuration profile byte correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT original_context.context_hex,captured.configuration_generation::text,
  captured.key_reuse,captured.journal_mode,encode(captured.configuration_bytes,'hex'),
  encode(captured.selected_binding_bytes,'hex'),encode(captured.installed_inventory_bytes,'hex'),
  encode(captured.configuration_sha256,'hex'),encode(captured.selected_binding_sha256,'hex'),
  encode(captured.installed_inventory_sha256,'hex'),encode(captured.admission_profile_bytes,'hex'),
  encode(sha256(captured.admission_profile_bytes),'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_admission_configuration(text,text,text,text) FROM PUBLIC;
