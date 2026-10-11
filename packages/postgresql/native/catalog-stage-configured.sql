-- One original issued call: source preflight, epoch before head, configuration
-- admission and provisional effects. No report publication or installed authority.
CREATE FUNCTION truss.runtime_stage_catalog_configured(
 issued_ordinal bigint,definition_bytes bytea,input_bytes bytea,candidate_bytes bytea,
 obligation_bytes bytea,group_bytes bytea,documents_bytes bytea,declarations_bytes bytea,
 origin_bytes bytea,capture_profile_bytes bytea,expected_installation text,expected_epoch text,
 expected_incarnation text,configuration_profile_bytes bytea)
RETURNS TABLE(writer_xid text,ordinal text,context_hex text,provisional_result_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE item bytea; total_bytes bigint:=0; prestate bytea; admitted record;
BEGIN
 FOREACH item IN ARRAY ARRAY[definition_bytes,input_bytes,candidate_bytes,obligation_bytes,
   group_bytes,documents_bytes,declarations_bytes,origin_bytes,capture_profile_bytes,configuration_profile_bytes] LOOP
  IF item IS NULL OR octet_length(item) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original configured catalog artifacts required' USING ERRCODE='22023';
  END IF;
  total_bytes:=total_bytes+octet_length(item);
 END LOOP;
 IF total_bytes>4194304 OR octet_length(input_bytes)>16384
  OR octet_length(capture_profile_bytes)>65536 OR octet_length(configuration_profile_bytes)>65536 THEN
  RAISE EXCEPTION 'selected configured catalog artifact capacity' USING ERRCODE='54000';
 END IF;
 -- Custody validation requires the actual admitted root and occurs in the
 -- admitted core. Before admission this is syntax/duplicate preflight only.
 PERFORM truss.runtime_require_unique_source_json(convert_from(input_bytes,'UTF8')::json);
 IF json_typeof(convert_from(input_bytes,'UTF8')::json) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original catalog input object required' USING ERRCODE='22023';
 END IF;
 PERFORM * FROM truss.runtime_collect_catalog_source_candidate(candidate_bytes,declarations_bytes);
 PERFORM truss.runtime_require_unique_source_json(convert_from(origin_bytes,'UTF8')::json);
 IF json_typeof(convert_from(origin_bytes,'UTF8')::json) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'selected original origin object required' USING ERRCODE='22023';
 END IF;
 -- This lock precedes prestate capture's head exclusion. No second admission.
 PERFORM * FROM truss.runtime_lock_source_epoch(expected_installation,expected_epoch,expected_incarnation);
 prestate:=decode(truss.runtime_capture_catalog_prestate(),'hex');
 SELECT * INTO STRICT admitted FROM truss.runtime_admit_operation_with_configuration_context(
  issued_ordinal,'catalog-acceptance',definition_bytes,input_bytes,prestate,candidate_bytes,
  obligation_bytes,group_bytes,origin_bytes,capture_profile_bytes,
  expected_installation,expected_epoch,expected_incarnation,configuration_profile_bytes);
 IF octet_length(admitted.context_hex)>8192 THEN
  RAISE EXCEPTION 'selected original configured context response capacity' USING ERRCODE='54000';
 END IF;
 RETURN QUERY SELECT * FROM truss.runtime_stage_catalog_admitted(
  issued_ordinal,definition_bytes,input_bytes,candidate_bytes,obligation_bytes,group_bytes,
  documents_bytes,declarations_bytes,origin_bytes,prestate,decode(admitted.context_hex,'hex'));
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_catalog_configured(bigint,bytea,bytea,bytea,bytea,bytea,
 bytea,bytea,bytea,bytea,text,text,text,bytea) FROM PUBLIC;
