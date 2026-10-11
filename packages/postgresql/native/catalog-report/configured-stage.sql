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
 response bytea; total_bytes bigint;
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
 -- Select and acquire the archive cut before any catalog business effect.
 SELECT * INTO STRICT before_release FROM truss.runtime_select_catalog_report_release(
  pg_current_xact_id()::text,issued_ordinal::text,'0',encode(configuration_profile,'hex'));
 SELECT * INTO STRICT staged FROM truss.runtime_stage_catalog_admitted(
  issued_ordinal,definition_bytes,input_bytes,candidate_bytes,obligation_bytes,group_bytes,
  documents_bytes,declarations_bytes,origin_bytes,original_prestate,original_context);
 result:=convert_from(decode(staged.provisional_result_hex,'hex'),'UTF8')::jsonb;
 SELECT * INTO STRICT after_release FROM truss.runtime_select_catalog_report_release(
  staged.writer_xid,staged.ordinal,result->>'effectGeneration',encode(configuration_profile,'hex'));
 IF to_jsonb(before_release) IS DISTINCT FROM to_jsonb(after_release) THEN
  RAISE EXCEPTION 'same original release source through catalog effects required' USING ERRCODE='55000';
 END IF;
 result:=jsonb_set(result,'{interfaceVersion}','"truss-native-provisional-catalog/0.3"'::jsonb);
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

-- Host-issued configured entry: the same original candidate/origin are captured
-- before dispatching the retained release producer. Still administrative only.
CREATE FUNCTION truss.runtime_stage_catalog_configured(
 issued_ordinal bigint,definition_bytes bytea,input_bytes bytea,candidate_bytes bytea,
 obligation_bytes bytea,group_bytes bytea,documents_bytes bytea,declarations_bytes bytea,
 origin_bytes bytea,capture_profile bytea,installation text,source_epoch text,
 incarnation text,configuration_profile bytea)
RETURNS TABLE(writer_xid text,ordinal text,context_hex text,provisional_result_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE prestate bytea; admitted record; item bytea; total bigint:=0;
BEGIN
 FOREACH item IN ARRAY ARRAY[definition_bytes,input_bytes,candidate_bytes,obligation_bytes,
  group_bytes,documents_bytes,declarations_bytes,origin_bytes,capture_profile,configuration_profile] LOOP
  IF item IS NULL OR octet_length(item) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original configured catalog artifacts required' USING ERRCODE='22023';
  END IF;
  total:=total+octet_length(item);
 END LOOP;
 IF total>4194304 OR octet_length(input_bytes)>16384
  OR octet_length(capture_profile)>65536 OR octet_length(configuration_profile)>65536 THEN
  RAISE EXCEPTION 'configured catalog aggregate capacity' USING ERRCODE='54000';
 END IF;
 IF jsonb_typeof(convert_from(origin_bytes,'UTF8')::jsonb) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original configured origin object required' USING ERRCODE='22023';
 END IF;
 PERFORM * FROM truss.runtime_collect_catalog_source_candidate(candidate_bytes,declarations_bytes);
 prestate:=decode(truss.runtime_capture_catalog_prestate(),'hex');
 SELECT * INTO STRICT admitted FROM truss.runtime_admit_operation_with_configuration_context(
  issued_ordinal,'catalog-acceptance',definition_bytes,input_bytes,prestate,candidate_bytes,
  obligation_bytes,group_bytes,origin_bytes,capture_profile,installation,source_epoch,
  incarnation,configuration_profile);
 RETURN QUERY SELECT * FROM truss.runtime_stage_catalog_with_release(issued_ordinal,
  definition_bytes,input_bytes,candidate_bytes,obligation_bytes,group_bytes,documents_bytes,
  declarations_bytes,origin_bytes,prestate,decode(admitted.context_hex,'hex'),configuration_profile);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_configured(bigint,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,bytea,text,text,text,bytea) FROM PUBLIC;
