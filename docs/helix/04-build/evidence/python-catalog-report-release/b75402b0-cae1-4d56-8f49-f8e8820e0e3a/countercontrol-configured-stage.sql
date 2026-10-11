-- One original configured staging call, retaining release and metadata source cuts.
-- Provisional administrative component; no authenticated PA or accepted authority.
CREATE FUNCTION truss.runtime_stage_catalog_with_release(
 issued_ordinal bigint,definition_bytes bytea,input_bytes bytea,
 candidate_bytes bytea,obligation_bytes bytea,group_bytes bytea,
 documents_bytes bytea,declarations_bytes bytea,origin_bytes bytea,
 original_prestate bytea,original_context bytea,configuration_profile bytea)
RETURNS TABLE(writer_xid text,ordinal text,context_hex text,provisional_result_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE before_release record; after_release record; staged record; result jsonb;
 response bytea; total_bytes bigint; before_resources jsonb; after_resources jsonb; final_graph record;
BEGIN
 IF original_context IS NULL OR octet_length(original_context) NOT BETWEEN 1 AND 1048576
  OR configuration_profile IS NULL OR octet_length(configuration_profile) NOT BETWEEN 1 AND 65536
  OR convert_from(original_context,'UTF8')::jsonb->>'interfaceVersion'
     IS DISTINCT FROM 'truss-native-operation-context/0.4' THEN
  RAISE EXCEPTION 'bounded original configured stage context required' USING ERRCODE='22023';
 END IF;
 SELECT sum(octet_length(a)) INTO total_bytes FROM unnest(ARRAY[definition_bytes,input_bytes,
  candidate_bytes,obligation_bytes,group_bytes,documents_bytes,declarations_bytes,origin_bytes,
  configuration_profile]) a;
 IF total_bytes>4194304 THEN
  RAISE EXCEPTION 'configured catalog artifact aggregate capacity exceeded' USING ERRCODE='54000';
 END IF;
 -- Deliberate paired omission: installed fence correspondence absent.
 -- Select and acquire the archive cut before any catalog business effect.
 SELECT * INTO STRICT before_release FROM truss.runtime_select_catalog_report_release(
  pg_current_xact_id()::text,issued_ordinal::text,'0',encode(configuration_profile,'hex'));
 before_resources:=truss.runtime_select_catalog_report_resources(
  pg_current_xact_id()::text,issued_ordinal::text,'0',encode(configuration_profile,'hex'));
 SELECT * INTO STRICT staged FROM truss.runtime_stage_catalog_admitted(
  issued_ordinal,definition_bytes,input_bytes,candidate_bytes,obligation_bytes,group_bytes,
  documents_bytes,declarations_bytes,origin_bytes,original_prestate,original_context);
 result:=convert_from(decode(staged.provisional_result_hex,'hex'),'UTF8')::jsonb;
 -- Deliberate paired omission: installed fence correspondence absent.
 SELECT * INTO STRICT after_release FROM truss.runtime_select_catalog_report_release(
  staged.writer_xid,staged.ordinal,result->>'effectGeneration',encode(configuration_profile,'hex'));
 IF to_jsonb(before_release) IS DISTINCT FROM to_jsonb(after_release) THEN
  RAISE EXCEPTION 'same original release source through catalog effects required' USING ERRCODE='55000';
 END IF;
 after_resources:=truss.runtime_select_catalog_report_resources(
  staged.writer_xid,staged.ordinal,result->>'effectGeneration',encode(configuration_profile,'hex'));
 IF after_resources IS DISTINCT FROM before_resources THEN
  RAISE EXCEPTION 'same original report resource inputs through catalog effects required' USING ERRCODE='55000';
 END IF;
 -- The extra release/resource collectors must not extend use beyond the core's checked
 -- cut. Recollect the complete metadata/graph and original operation afterward.
 SELECT * INTO STRICT final_graph FROM truss.runtime_collect_configured_catalog_graph();
 IF to_jsonb(final_graph) IS DISTINCT FROM result->'reportSources'->'end'
  OR NOT EXISTS(SELECT 1 FROM truss.row_home_operation o
   WHERE o.original_writer_xid=pg_current_xact_id_if_assigned()
    AND o.original_writer_xid::text=staged.writer_xid AND o.operation_ordinal=issued_ordinal
    AND o.operation_ordinal::text=staged.ordinal AND o.phase='admitted'
    AND o.effect_generation::text=result->>'effectGeneration'
    AND o.operation_kind='catalog-acceptance' AND o.original_context_bytes=original_context
    AND o.original_context_bytes=decode(staged.context_hex,'hex')
    AND o.original_definition_bytes=definition_bytes AND o.original_input_bytes=input_bytes
    AND o.original_prestate_bytes=original_prestate AND o.admitted_candidate_bytes=candidate_bytes
    AND o.effect_obligation_bytes=obligation_bytes AND o.original_group_custody_bytes=group_bytes) THEN
  RAISE EXCEPTION 'original configured release final cut required' USING ERRCODE='55000';
 END IF;
 result:=jsonb_set(result,'{reportSources,catalogResources}',before_resources);
 result:=jsonb_set(result,'{interfaceVersion}','"truss-native-provisional-catalog/0.4"'::jsonb);
 result:=jsonb_set(result,'{reportSources,catalogRelease}',jsonb_build_object(
  'interfaceVersion','truss-configured-catalog-release/0.1','writerXid',staged.writer_xid,
  'operationOrdinal',staged.ordinal,'initialEffectGeneration','0',
  'effectGeneration',result->>'effectGeneration',
  'configurationGeneration',after_release.configuration_generation,
  'policyHex',after_release.policy_hex,'policySha256',after_release.policy_sha256,
  'scope','original_configured_release_at_native_call_only'));
 response:=convert_to(result::text,'UTF8');
 IF octet_length(response)>131072 THEN
  RAISE EXCEPTION 'selected configured provisional response capacity exceeded' USING ERRCODE='54000';
 END IF;
 RETURN QUERY SELECT staged.writer_xid,staged.ordinal,staged.context_hex,encode(response,'hex');
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_with_release(bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC;
