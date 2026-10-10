-- Current versus pre-effect native bytes only; not complete installed authority.
CREATE FUNCTION truss.runtime_require_operation_configuration_current(
 expected_writer_xid text,expected_operation_ordinal text,expected_effect_generation text)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original_context record; context jsonb;
 captured truss.operation_configuration%ROWTYPE;
 current_configuration truss.installation_admission%ROWTYPE;
 sizes record;
BEGIN
 SELECT * INTO STRICT original_context FROM truss.runtime_collect_catalog_epoch_context(
  expected_writer_xid,expected_operation_ordinal,expected_effect_generation);
 context:=convert_from(decode(original_context.context_hex,'hex'),'UTF8')::jsonb;
 PERFORM 1 FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
 SELECT c.* INTO captured FROM truss.operation_configuration c
  WHERE c.original_writer_xid=pg_current_xact_id_if_assigned()
   AND c.operation_ordinal::text=expected_operation_ordinal;
 IF NOT FOUND THEN RAISE EXCEPTION 'original configuration capsule required' USING ERRCODE='55000'; END IF;
 SELECT octet_length(a.configuration_bytes)::bigint AS configuration,
  octet_length(a.selected_binding_bytes)::bigint AS binding,
  octet_length(a.installed_inventory_bytes)::bigint AS inventory
 INTO sizes FROM truss.installation_admission a WHERE a.head_id=1;
 IF NOT FOUND OR sizes.configuration<1 OR sizes.binding<1 OR sizes.inventory<1
  OR sizes.configuration+sizes.binding+sizes.inventory>16777216 THEN
  RAISE EXCEPTION 'bounded current configuration required' USING ERRCODE='55000';
 END IF;
 SELECT a.* INTO current_configuration FROM truss.installation_admission a WHERE a.head_id=1;
 IF NOT FOUND OR captured.installation_id IS DISTINCT FROM context->>'installationId'
  OR captured.source_epoch IS DISTINCT FROM context->>'sourceEpoch'
  OR captured.target_incarnation IS DISTINCT FROM context->>'targetIncarnation'
  OR captured.original_context_sha256 IS DISTINCT FROM sha256(decode(original_context.context_hex,'hex'))
  OR current_configuration.installation_id_utf8 IS DISTINCT FROM convert_to(captured.installation_id,'UTF8')
  OR current_configuration.source_epoch_utf8 IS DISTINCT FROM convert_to(captured.source_epoch,'UTF8')
  OR current_configuration.configuration_generation IS DISTINCT FROM captured.configuration_generation
  OR current_configuration.key_reuse IS DISTINCT FROM captured.key_reuse
  OR current_configuration.journal_mode IS DISTINCT FROM captured.journal_mode
  OR current_configuration.configuration_bytes IS DISTINCT FROM captured.configuration_bytes
  OR current_configuration.selected_binding_bytes IS DISTINCT FROM captured.selected_binding_bytes
  OR current_configuration.installed_inventory_bytes IS DISTINCT FROM captured.installed_inventory_bytes THEN
  RAISE EXCEPTION 'current configuration differs from original admission capsule' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_operation_configuration_current(text,text,text) FROM PUBLIC;
