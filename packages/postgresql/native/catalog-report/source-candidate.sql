-- Pre-effect retained source syntax; original producer meaning and installed
-- authority are separate requirements. Never accepts native-owned report fields.
CREATE FUNCTION truss.runtime_require_unique_source_json(original json) RETURNS void
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE pending json[]:=ARRAY[original]; depths int[]:=ARRAY[0];
 node json; member record; depth int; steps int:=1; children int;
BEGIN
 WHILE cardinality(pending)>0 LOOP
  node:=pending[cardinality(pending)];depth:=depths[cardinality(depths)];
  pending:=pending[1:cardinality(pending)-1];depths:=depths[1:cardinality(depths)-1];
  IF depth>128 THEN RAISE EXCEPTION 'source carrier depth capacity' USING ERRCODE='54000'; END IF;
  IF steps>32768 THEN RAISE EXCEPTION 'source carrier work capacity' USING ERRCODE='54000'; END IF;
  IF json_typeof(node)='object' THEN
   SELECT count(*) INTO children FROM json_each(node);
   IF children>4096 OR steps+children>32768 THEN
    RAISE EXCEPTION 'source carrier enqueue capacity' USING ERRCODE='54000'; END IF;
   steps:=steps+children;
   IF (SELECT count(*)<>count(DISTINCT key COLLATE "C") FROM json_each(node)) THEN
    RAISE EXCEPTION 'duplicate source carrier member' USING ERRCODE='22023';
   END IF;
   FOR member IN SELECT value FROM json_each(node) LOOP
    pending:=array_append(pending,member.value);depths:=array_append(depths,depth+1); END LOOP;
  ELSIF json_typeof(node)='array' THEN
   children:=json_array_length(node);
   IF children>4096 OR steps+children>32768 THEN
    RAISE EXCEPTION 'source carrier enqueue capacity' USING ERRCODE='54000'; END IF;
   steps:=steps+children;
   FOR member IN SELECT value FROM json_array_elements(node) LOOP
    pending:=array_append(pending,member.value);depths:=array_append(depths,depth+1); END LOOP;
  END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_unique_source_json(json) FROM PUBLIC;

CREATE FUNCTION truss.runtime_collect_catalog_source_candidate(candidate_bytes bytea,declarations_bytes bytea)
RETURNS TABLE(host_sources jsonb,original_report_evidence bytea,preparation_provenance jsonb)
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE raw json; envelope jsonb; tree jsonb; evidence bytea;
 fields text[]:=ARRAY['umf','diagnostics','documentInterpretations','losses','extensions',
  'transformRegistrations','assertionEntries']; encoded bytea;
BEGIN
 IF candidate_bytes IS NULL OR declarations_bytes IS NULL
  OR octet_length(candidate_bytes) NOT BETWEEN 1 AND 1048576
  OR octet_length(declarations_bytes) NOT BETWEEN 1 AND 1048576 THEN
  RAISE EXCEPTION 'bounded original source candidate required' USING ERRCODE='22023';
 END IF;
 raw:=convert_from(candidate_bytes,'UTF8')::json;
 PERFORM truss.runtime_require_unique_source_json(raw);
 envelope:=raw::jsonb;
 IF jsonb_typeof(envelope) IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(envelope))<>5
  OR NOT envelope ?& ARRAY['interfaceVersion','declarationsUtf8Hex','reportEvidenceUtf8Hex',
    'preparationProvenance','hostSources']
  OR envelope->>'interfaceVersion' IS DISTINCT FROM 'truss-catalog-source-candidate/0.1'
  OR jsonb_typeof(envelope->'declarationsUtf8Hex') IS DISTINCT FROM 'string'
  OR envelope->>'declarationsUtf8Hex' IS DISTINCT FROM encode(declarations_bytes,'hex')
  OR jsonb_typeof(envelope->'reportEvidenceUtf8Hex') IS DISTINCT FROM 'string'
  OR envelope->>'reportEvidenceUtf8Hex' !~ '^([0-9a-f]{2})+$'
  OR jsonb_typeof(envelope->'preparationProvenance') IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'closed original source candidate required' USING ERRCODE='22023';
 END IF;
 IF (SELECT count(*) FROM jsonb_object_keys(envelope->'preparationProvenance'))<>7
  OR NOT (envelope->'preparationProvenance') ?& ARRAY['owner_revision','owner_bundle_sha256',
    'acceptance_schema_sha256','release_manifest_sha256','runtime_version','scope','installation_profiles_verified']
  OR envelope->'preparationProvenance'->'installation_profiles_verified' IS DISTINCT FROM 'false'::jsonb
  OR envelope->'preparationProvenance'->>'scope' IS DISTINCT FROM 'original_umf_preparation_only'
  OR EXISTS(SELECT 1 FROM jsonb_each(envelope->'preparationProvenance') e
    WHERE e.key<>'installation_profiles_verified' AND (jsonb_typeof(e.value) IS DISTINCT FROM 'string' OR e.value #>> '{}'=''))
  OR EXISTS(SELECT 1 FROM unnest(ARRAY['owner_bundle_sha256','acceptance_schema_sha256','release_manifest_sha256']) k
    WHERE envelope->'preparationProvenance'->>k !~ '^[0-9a-f]{64}$') THEN
  RAISE EXCEPTION 'complete original preparation provenance required' USING ERRCODE='22023';
 END IF;
 tree:=envelope->'hostSources';
 IF tree->>'kind' IS DISTINCT FROM 'object' OR jsonb_typeof(tree->'members') IS DISTINCT FROM 'array'
  OR jsonb_array_length(tree->'members')<>7 THEN
  RAISE EXCEPTION 'complete source-only field inventory required' USING ERRCODE='22023';
 END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(tree->'members') m
  WHERE m->'node'->>'kind' IS DISTINCT FROM 'array'
   OR NOT EXISTS(SELECT 1 FROM unnest(fields) f
    WHERE m->>'keyUtf8Hex'=encode(convert_to(f,'UTF8'),'hex'))) THEN
  RAISE EXCEPTION 'native-owned or unknown source field' USING ERRCODE='22023';
 END IF;
 -- Codec validates all tagged metadata, scalar bytes and duplicate logical keys.
 encoded:=truss.runtime_canonical_tree_bytes(tree);
 evidence:=decode(envelope->>'reportEvidenceUtf8Hex','hex');
 -- Exact bytes are retained; no lossy jsonb interpretation of logical evidence.
 RETURN QUERY SELECT tree,evidence,envelope->'preparationProvenance';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_collect_catalog_source_candidate(bytea,bytea) FROM PUBLIC;
