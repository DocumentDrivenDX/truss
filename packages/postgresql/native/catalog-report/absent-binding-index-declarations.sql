-- Original release-owned index declaration policy; administrative report component.
-- No index dispatch/readiness, installation authority or complete report issuer.
CREATE FUNCTION truss.runtime_collect_absent_binding_index_declarations(
 expected_writer text,expected_ordinal text,expected_generation text,
 revision int,original_policy bytea)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; input jsonb; documents jsonb;
 policy_source bytea:=convert_to($policy${
  "identity": "truss-absent-binding-index-declarations",
  "version": "0.1.0",
  "scope": "immutable_index_job_declarations_only",
  "governingRules": [
    "ADR-002-D2",
    "ADR-002-D11",
    "ADR-002-D12",
    "CONTRACT-003-pending-index-declarations"
  ],
  "sourceComponent": {
    "identity": "truss-qualified-property-layout-source",
    "version": "0.15",
    "sha256": "cc725df53f0d74e13bb51fda29603f8cafe8c0cee237667778566f81b33f5011"
  },
  "selection": {
    "binding": "absent",
    "transforms": "empty",
    "ingress": "native",
    "storageHome": "json"
  },
  "indexDeclarationSources": [
    "explicit_acceptance_binding"
  ],
  "documentExtensionAndQueryJobDeclarations": "none_in_this_policy",
  "absentBindingDeclarations": "empty",
  "baselineEnforcementIndexes": "excluded_from_catalog_jobs",
  "statisticsDeclarations": "outside_this_field",
  "unknownExtensionSemantics": "retained_and_separately_unresolved",
  "installedProfileAuthority": false,
  "readinessAuthority": false
}
$policy$,'UTF8');
BEGIN
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(
  SELECT 1 FROM pg_roles r WHERE r.rolname=current_user AND r.rolsuper) THEN
  RAISE EXCEPTION 'administrative declaration observation only' USING ERRCODE='42501';
 END IF;
 IF original_policy IS DISTINCT FROM policy_source THEN
  RAISE EXCEPTION 'original selected declaration policy bytes required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned();
 PERFORM truss.runtime_require_catalog_input(op.original_input_bytes);
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 IF input->'binding' IS DISTINCT FROM '{"state":"absent"}'::jsonb
  OR input->'transforms' IS DISTINCT FROM '[]'::jsonb
  OR jsonb_typeof(input->'documents') IS DISTINCT FROM 'array'
  OR jsonb_array_length(input->'documents') NOT BETWEEN 1 AND 512
  OR EXISTS(SELECT 1 FROM jsonb_array_elements(input->'documents') d
    WHERE d->'ingress' IS DISTINCT FROM '{"kind":"native"}'::jsonb) THEN
  RAISE EXCEPTION 'unselected index declaration source requires its original producer' USING ERRCODE='0A000';
 END IF;
 -- This producer is bound to the existing new-catalog native component. Its
 -- inventory/document procedures establish current source correspondence; they
 -- do not turn caller profile pins into installed profile authority.
 PERFORM * FROM truss.runtime_collect_new_catalog_inventory(revision);
 SELECT jsonb_agg(to_jsonb(d) ORDER BY d.ord::int) INTO documents
  FROM truss.runtime_collect_report_documents(revision) d;
 IF EXISTS(SELECT 1 FROM truss.prop_def d WHERE d.since_rev=revision AND d.home<>'json') THEN
  RAISE EXCEPTION 'selected absent-binding JSON source required' USING ERRCODE='0A000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 RETURN jsonb_build_object('scope','original_absent_binding_index_declarations_only',
  'policyHex',encode(policy_source,'hex'),'policySha256',encode(sha256(policy_source),'hex'),
  'inputHex',encode(op.original_input_bytes,'hex'),'writerXid',expected_writer,
  'operationOrdinal',expected_ordinal,'effectGeneration',expected_generation,
  'revision',revision::text,'documents',documents,'declaredJobs','[]'::jsonb,
  'installedProfileQualified',false,'readinessQualified',false);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_absent_binding_index_declarations(text,text,text,int,bytea) FROM PUBLIC;
