-- Private original fresh-catalog lifecycle; no accepted publication authority.
CREATE FUNCTION truss.runtime_require_catalog_lifecycle_observers()
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_proc p WHERE p.oid=to_regprocedure('truss.runtime_observe_catalog_generation()')
  AND NOT p.prosecdef AND p.provolatile='v' AND NOT p.proisstrict AND NOT p.proleakproof
  AND p.prorettype='pg_catalog.trigger'::regtype AND p.prolang=(SELECT l.oid FROM pg_language l WHERE l.lanname='plpgsql')
  AND p.proparallel='u' AND p.proconfig=ARRAY['search_path=pg_catalog, pg_temp']
  AND encode(sha256(convert_to(p.prosrc,'UTF8')),'hex')='50e70fa7cb99454c0104e5e9d14858ba0e8b664cecd3680281173fcdb3d1ca59')
  OR EXISTS(SELECT 1 FROM (VALUES ('schema_rev'),('schema_doc'),('type_def'),('prop_def'),('key_def'),('key_lifecycle_history'),('rel_def'),('rel_endpoint'),('relationship_lineage'),('schema_head'),('catalog_acceptance_report')) v(name)
   WHERE NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=to_regclass('truss.'||v.name)
    AND t.tgname='runtime_catalog_generation' AND t.tgfoid=to_regprocedure('truss.runtime_observe_catalog_generation()')
    AND t.tgtype=29 AND t.tgenabled='A' AND t.tgnargs=0 AND t.tgqual IS NULL AND NOT t.tgisinternal
    AND t.tgattr=''::int2vector AND t.tgconstraint=0 AND t.tgconstrrelid=0
    AND t.tgconstrindid=0 AND NOT t.tgdeferrable AND NOT t.tginitdeferred
    AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL AND t.tgparentid=0)) THEN
  RAISE EXCEPTION 'exact selected generation observer required' USING ERRCODE='55000';
 END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_catalog_lifecycle_observers() FROM PUBLIC;
CREATE FUNCTION truss.runtime_collect_fresh_catalog_lifecycle(
 expected_writer text,expected_ordinal text,expected_generation text,revision int,original_policy bytea)
RETURNS jsonb LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; prestate jsonb; name text; expected_events bigint;
 policy_source bytea:=convert_to($policy${
  "identity": "truss-fresh-catalog-lifecycle",
  "version": "0.1.0",
  "selection": "first_revision_new_identities_only",
  "sourceComponentVersion": "0.15",
  "targetReportInterfaceVersion": "truss-acceptance-report/0.3.0-proposal",
  "governingRules": [
    "ADR-004",
    "CONTRACT-003-reactivation-inventory"
  ],
  "requiredOriginalState": "head_zero_empty_prior_catalog_and_history",
  "eventPlan": "insert_only_complete_source_bijection",
  "reactivations": "empty_after_original_absence_and_event_verification",
  "installedProfileAuthority": false
}
$policy$,'UTF8');
BEGIN
 IF current_user IS DISTINCT FROM session_user OR NOT EXISTS(
  SELECT 1 FROM pg_roles r WHERE r.rolname=current_user AND r.rolsuper) THEN
  RAISE EXCEPTION 'administrative lifecycle observation only' USING ERRCODE='42501';
 END IF;
 IF original_policy IS DISTINCT FROM policy_source THEN
  RAISE EXCEPTION 'original fresh lifecycle policy required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 PERFORM truss.runtime_require_catalog_lifecycle_observers();
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned();
 prestate:=convert_from(op.original_prestate_bytes,'UTF8')::jsonb;
 IF prestate->>'interfaceVersion' IS DISTINCT FROM 'truss-native-catalog-prestate/0.1'
  OR prestate->'head'->>'rev' IS DISTINCT FROM '0' OR revision IS DISTINCT FROM 1 THEN
  RAISE EXCEPTION 'original fresh lifecycle prestate required' USING ERRCODE='0A000';
 END IF;
 IF jsonb_typeof(prestate->'revisions') IS DISTINCT FROM 'array'
  OR jsonb_array_length(prestate->'revisions')<>1
  OR prestate->'revisions'->0->>'rev' IS DISTINCT FROM '0' THEN
  RAISE EXCEPTION 'only original bootstrap revision permitted' USING ERRCODE='0A000';
 END IF;
 FOREACH name IN ARRAY ARRAY['documents','types','properties','keys','keyHistory',
 'relationships','relationshipLineage','endpoints','reports'] LOOP
  IF prestate->name IS DISTINCT FROM '[]'::jsonb THEN
   RAISE EXCEPTION 'complete empty original lifecycle inventory required' USING ERRCODE='0A000';
  END IF;
 END LOOP;
 -- Original inventory producer independently matches all source/identity families.
 PERFORM * FROM truss.runtime_collect_new_catalog_inventory(revision);
 PERFORM truss.runtime_verify_new_catalog_prestate(revision);
 IF convert_from(op.original_context_bytes,'UTF8')::jsonb->>'interfaceVersion'='truss-native-operation-context/0.4' THEN
  PERFORM * FROM truss.runtime_collect_configured_catalog_graph();
 ELSE
  PERFORM * FROM truss.runtime_collect_empty_catalog_graph();
 END IF;
 IF EXISTS(SELECT 1 FROM truss.schema_change) OR EXISTS(SELECT 1 FROM truss.key_lifecycle_history)
  OR EXISTS(SELECT 1 FROM truss.catalog_acceptance_report) THEN
  RAISE EXCEPTION 'unexpected lifecycle history or publication' USING ERRCODE='55000';
 END IF;
 SELECT (SELECT count(*) FROM truss.schema_rev WHERE rev=revision)+(SELECT count(*) FROM truss.schema_doc)
  +(SELECT count(*) FROM truss.type_def)+(SELECT count(*) FROM truss.prop_def)
  +(SELECT count(*) FROM truss.key_def)+(SELECT count(*) FROM truss.rel_def)
  +(SELECT count(*) FROM truss.relationship_lineage)+(SELECT count(*) FROM truss.rel_endpoint)
 INTO expected_events;
 IF op.effect_generation IS DISTINCT FROM expected_events THEN
  RAISE EXCEPTION 'original insert-only lifecycle event plan required' USING ERRCODE='55000';
 END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 RETURN jsonb_build_object('scope','original_fresh_catalog_lifecycle_only',
  'policyHex',encode(policy_source,'hex'),'inputHex',encode(op.original_input_bytes,'hex'),
  'writerXid',expected_writer,'operationOrdinal',expected_ordinal,'effectGeneration',expected_generation,
  'revision',revision::text,'expectedInsertEvents',expected_events::text,
  'lifecycleProfile',jsonb_build_object('identity','truss-fresh-catalog-lifecycle','version','0.1.0','sha256',encode(sha256(policy_source),'hex')),
  'reactivations','[]'::jsonb,'acceptedReportQualified',false);
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_fresh_catalog_lifecycle(text,text,text,int,bytea) FROM PUBLIC;
