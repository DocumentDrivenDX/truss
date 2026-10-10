-- Private current-configuration observation under original operation custody.
-- It does not prove the configuration present when operation admission began.
-- No committed installation, policy, binding or inventory meaning is admitted.
CREATE FUNCTION truss.runtime_collect_catalog_original_configuration(
 expected_writer_xid text,expected_operation_ordinal text,expected_effect_generation text)
RETURNS TABLE(context_hex text,configuration_generation text,key_reuse text,journal_mode text,
 configuration_hex text,selected_binding_hex text,installed_inventory_hex text,
 configuration_sha256 text,selected_binding_sha256 text,installed_inventory_sha256 text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original_context record;
 context jsonb;
 sizes record;
 captured truss.installation_admission%ROWTYPE;
BEGIN
 -- The context collector independently checks original invoker, transaction,
 -- writer/ordinal/generation, actual epoch lock and registry correspondence.
 SELECT * INTO STRICT original_context
  FROM truss.runtime_collect_catalog_epoch_context(expected_writer_xid,
   expected_operation_ordinal,expected_effect_generation);
 context := convert_from(decode(original_context.context_hex,'hex'),'UTF8')::jsonb;
 -- Existing schema_head is the configuration lock home. Do not introduce a
 -- second installation_admission-row lock or claim this replaces full admission.
 PERFORM 1 FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
 IF NOT FOUND THEN
  RAISE EXCEPTION 'original configuration head unavailable' USING ERRCODE='55000';
 END IF;
 SELECT octet_length(a.configuration_bytes)::bigint AS configuration,
  octet_length(a.selected_binding_bytes)::bigint AS binding,
  octet_length(a.installed_inventory_bytes)::bigint AS inventory
 INTO sizes FROM truss.installation_admission a WHERE a.head_id=1;
 IF NOT FOUND OR sizes.configuration<1 OR sizes.binding<1 OR sizes.inventory<1
  OR sizes.configuration+sizes.binding+sizes.inventory>16777216 THEN
  RAISE EXCEPTION 'bounded original configuration artifacts unavailable' USING ERRCODE='55000';
 END IF;
 SELECT a.* INTO STRICT captured FROM truss.installation_admission a WHERE a.head_id=1;
 IF captured.installation_id_utf8 IS DISTINCT FROM convert_to(context->>'installationId','UTF8')
  OR captured.source_epoch_utf8 IS DISTINCT FROM convert_to(context->>'sourceEpoch','UTF8')
  OR captured.configuration_generation<0
  OR captured.key_reuse NOT IN ('forbid','allow') OR captured.journal_mode NOT IN ('engine','trigger')
  OR captured.configuration_sha256 IS DISTINCT FROM sha256(captured.configuration_bytes)
  OR captured.selected_binding_sha256 IS DISTINCT FROM sha256(captured.selected_binding_bytes)
  OR captured.installed_inventory_sha256 IS DISTINCT FROM sha256(captured.installed_inventory_bytes) THEN
  RAISE EXCEPTION 'original configuration/epoch byte correspondence required' USING ERRCODE='55000';
 END IF;
 RETURN QUERY SELECT original_context.context_hex,captured.configuration_generation::text,
  captured.key_reuse,captured.journal_mode,encode(captured.configuration_bytes,'hex'),
  encode(captured.selected_binding_bytes,'hex'),encode(captured.installed_inventory_bytes,'hex'),
  encode(captured.configuration_sha256,'hex'),encode(captured.selected_binding_sha256,'hex'),
  encode(captured.installed_inventory_sha256,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_original_configuration(text,text,text) FROM PUBLIC;
