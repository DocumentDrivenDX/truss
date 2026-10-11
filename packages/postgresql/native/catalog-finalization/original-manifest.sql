-- Deterministic original-fact constructor only. No table reads/writes or authority.
-- The eventual finalizer must obtain these inputs from admitted protected custody.
CREATE FUNCTION truss.runtime_original_catalog_manifest_candidate(
 original_input_bytes bytea, revision_text text, xid_text text, feed_context jsonb,
 manifest_definition bytea, payload_profile bytea, original_payload bytea,
 configuration_bytes bytea, configuration_profile bytea)
-- feed_tx.manifest_bytes stores tree_bytes; manifest_bytes is the full wire only.
RETURNS TABLE(tree_bytes bytea,manifest_bytes bytea,semantic_sha256 bytea)
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original_input jsonb; configuration jsonb; definition jsonb; profile jsonb; cfg_profile jsonb; document jsonb; artifact jsonb;
 seen jsonb:='{}'::jsonb; prerequisites jsonb:='[]'::jsonb; documents bytea[]:=ARRAY[]::bytea[];
 original bytea; raw bytea; association jsonb; configuration_artifact bytea;
 generation text; identity text; tree jsonb; cfg_tree jsonb; field text; chunks jsonb; pos int;
 total bigint:=0; document_count int:=0;
BEGIN
 IF original_input_bytes IS NULL OR octet_length(original_input_bytes) NOT BETWEEN 1 AND 1048576
  OR configuration_bytes IS NULL OR octet_length(configuration_bytes) NOT BETWEEN 1 AND 8388608 THEN
  RAISE EXCEPTION 'bounded original input/configuration required' USING ERRCODE='54000'; END IF;
 IF NOT (convert_from(original_input_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS)
  OR NOT (convert_from(configuration_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
  RAISE EXCEPTION 'duplicate-preserving original input/configuration admission required' USING ERRCODE='22023'; END IF;
 -- JSONB conversion explicitly refuses NUL rather than silently normalizing it.
 original_input:=convert_from(original_input_bytes,'UTF8')::jsonb;
 configuration:=convert_from(configuration_bytes,'UTF8')::jsonb;
 IF revision_text IS NULL OR revision_text !~ '^[1-9][0-9]*$' OR length(revision_text)>10
  OR revision_text::numeric>2147483647 OR xid_text IS NULL OR xid_text !~ '^[1-9][0-9]*$'
  OR length(xid_text)>20 OR xid_text::numeric>18446744073709551615 THEN
  RAISE EXCEPTION 'canonical native original coordinates required' USING ERRCODE='22023'; END IF;
 IF manifest_definition IS NULL OR octet_length(manifest_definition) NOT BETWEEN 1 AND 65536
  OR payload_profile IS NULL OR octet_length(payload_profile) NOT BETWEEN 1 AND 65536
  OR configuration_profile IS NULL OR octet_length(configuration_profile) NOT BETWEEN 1 AND 65536
  OR original_payload IS NULL OR octet_length(original_payload) NOT BETWEEN 1 AND 4194304 THEN
  RAISE EXCEPTION 'bounded complete original profile/payload required' USING ERRCODE='54000'; END IF;
 IF NOT (convert_from(payload_profile,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS)
  OR NOT (convert_from(configuration_profile,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
  RAISE EXCEPTION 'original profile unique keys required' USING ERRCODE='22023'; END IF;
 definition:=convert_from(manifest_definition,'UTF8')::jsonb;
 profile:=convert_from(payload_profile,'UTF8')::jsonb;cfg_profile:=convert_from(configuration_profile,'UTF8')::jsonb;
 IF EXISTS(SELECT 1 FROM jsonb_each(profile) WHERE key IN ('identity','version') AND (jsonb_typeof(value)<>'string' OR value #>> '{}'=''))
  OR NOT profile ?& ARRAY['identity','version']
  OR EXISTS(SELECT 1 FROM jsonb_each(cfg_profile) WHERE key IN ('identity','version') AND (jsonb_typeof(value)<>'string' OR value #>> '{}'=''))
  OR NOT cfg_profile ?& ARRAY['identity','version'] THEN
  RAISE EXCEPTION 'complete original profile identities required' USING ERRCODE='22023'; END IF;
 IF manifest_definition IS DISTINCT FROM truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(definition))
  OR definition->>'identity' IS DISTINCT FROM 'truss-administrative-single-catalog-manifest'
  OR definition->>'version' IS DISTINCT FROM '0.4.0-original-artifact-codec-candidate'
  OR encode(sha256(manifest_definition),'hex')<>'03264a3097e3632aecc69393a9ad96e036f35ef7c1044aa68a3ea575168813f5' THEN
  RAISE EXCEPTION 'exact selected original manifest definition required' USING ERRCODE='55000'; END IF;
 IF encode(sha256(payload_profile),'hex') IS DISTINCT FROM definition->'payloadDefinitionArtifact'->>'sha256' THEN
  RAISE EXCEPTION 'exact selected payload definition required' USING ERRCODE='55000'; END IF;
 IF jsonb_typeof(feed_context) IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(feed_context))<>3
  OR NOT feed_context ?& ARRAY['sourceEpoch','feedProfile','scopeIdentity']
  OR EXISTS(SELECT 1 FROM jsonb_each(feed_context) WHERE jsonb_typeof(value)<>'string' OR value #>> '{}'='') THEN
  RAISE EXCEPTION 'closed original feed context required' USING ERRCODE='22023'; END IF;
 IF feed_context->>'scopeIdentity' IS DISTINCT FROM definition->'feedContext'->>'scopeIdentity' THEN
  RAISE EXCEPTION 'exact selected manifest scope required' USING ERRCODE='55000'; END IF;
 IF jsonb_typeof(original_input->'documents') IS DISTINCT FROM 'array'
  OR jsonb_array_length(original_input->'documents') NOT BETWEEN 1 AND 512 THEN
  RAISE EXCEPTION 'complete bounded original documents required' USING ERRCODE='54000'; END IF;
 FOR document IN SELECT value FROM jsonb_array_elements(original_input->'documents') LOOP
  artifact:=document->'artifact';identity:=artifact->>'identity';
  IF jsonb_typeof(artifact) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(artifact))<>3
   OR NOT artifact ?& ARRAY['identity','bytesBase64','sha256'] OR identity IS NULL OR identity=''
   OR jsonb_typeof(artifact->'identity')<>'string' OR jsonb_typeof(artifact->'bytesBase64')<>'string'
   OR jsonb_typeof(artifact->'sha256')<>'string' THEN
   RAISE EXCEPTION 'closed original document artifact required' USING ERRCODE='22023'; END IF;
  original:=decode(artifact->>'bytesBase64','base64');total:=total+octet_length(original);
  IF octet_length(original)<1 OR total>1048576 THEN RAISE EXCEPTION 'original document aggregate capacity' USING ERRCODE='54000'; END IF;
  IF replace(encode(original,'base64'),chr(10),'') IS DISTINCT FROM artifact->>'bytesBase64'
   OR encode(sha256(original),'hex') IS DISTINCT FROM artifact->>'sha256' THEN
   RAISE EXCEPTION 'complete original artifact bytes/digest correspondence required' USING ERRCODE='55000'; END IF;
  IF jsonb_typeof(document->'umfProfile') IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'original UMF profile pin required' USING ERRCODE='22023'; END IF;
  IF (SELECT count(*) FROM jsonb_object_keys(document->'umfProfile'))<>3
   OR NOT (document->'umfProfile') ?& ARRAY['identity','version','sha256']
   OR EXISTS(SELECT 1 FROM jsonb_each(document->'umfProfile') WHERE jsonb_typeof(value)<>'string' OR value #>> '{}'='')
   OR document->'umfProfile'->>'sha256' !~ '^[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'closed exact original UMF profile pin required' USING ERRCODE='22023'; END IF;
  association:=jsonb_build_object('artifact',artifact,'profile',encode(truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(document->'umfProfile')),'hex'));
  IF seen ? identity THEN
   IF seen->identity IS DISTINCT FROM association THEN RAISE EXCEPTION 'conflicting original document identity' USING ERRCODE='55000'; END IF;
  ELSE seen:=seen||jsonb_build_object(identity,association); END IF;
 END LOOP;
 FOR identity,association IN SELECT key,value FROM jsonb_each(seen) ORDER BY convert_to(key,'UTF8') LOOP
  prerequisites:=prerequisites||jsonb_build_array(jsonb_build_object('revision',revision_text,'artifact',association->'artifact'));
  documents:=array_append(documents,decode(association->'artifact'->>'bytesBase64','base64'));
 END LOOP;
 IF NOT configuration ?& ARRAY['installationId','sourceEpoch','targetIncarnation','generation','keyReuse','journalMode','admissionProfileHex','configurationHex','bindingHex','inventoryHex']
  OR (SELECT count(*) FROM jsonb_object_keys(configuration))<>10
  OR EXISTS(SELECT 1 FROM jsonb_each(configuration) WHERE jsonb_typeof(value)<>'string' OR value #>> '{}'='') THEN
  RAISE EXCEPTION 'closed original configuration capsule required' USING ERRCODE='22023'; END IF;
 IF configuration->>'keyReuse' NOT IN ('forbid','allow') OR configuration->>'journalMode' NOT IN ('engine','trigger') THEN
  RAISE EXCEPTION 'selected mutation configuration enums required' USING ERRCODE='22023'; END IF;
 generation:=configuration->>'generation';
 IF generation IS NULL OR generation !~ '^(0|[1-9][0-9]*)$' OR length(generation)>19
  OR generation::numeric>9223372036854775807 OR configuration->>'sourceEpoch' IS DISTINCT FROM feed_context->>'sourceEpoch' THEN
  RAISE EXCEPTION 'original generation/epoch correspondence required' USING ERRCODE='22023'; END IF;
 cfg_tree:=jsonb_build_object('installation',configuration->'installationId','sourceEpoch',configuration->'sourceEpoch',
  'targetIncarnation',configuration->'targetIncarnation','generation',generation,
  'keyReuse',configuration->'keyReuse','journalMode',configuration->'journalMode');
 FOREACH field IN ARRAY ARRAY['admissionProfile','configuration','binding','inventory'] LOOP
  IF jsonb_typeof(configuration->(field||'Hex')) IS DISTINCT FROM 'string'
   OR configuration->>(field||'Hex') !~ '^([0-9a-f]{2})+$'
   OR length(configuration->>(field||'Hex'))>1572864 THEN RAISE EXCEPTION 'bounded original configuration bytes required' USING ERRCODE='54000'; END IF;
  raw:=decode(configuration->>(field||'Hex'),'hex');chunks:='[]'::jsonb;pos:=1;
  WHILE pos<=octet_length(raw) LOOP chunks:=chunks||jsonb_build_array(encode(substr(raw,pos,32768),'hex'));pos:=pos+32768; END LOOP;
  cfg_tree:=cfg_tree||jsonb_build_object(field||'HexChunks',chunks);
 END LOOP;
 configuration_artifact:=truss.runtime_canonical_tree_bytes(truss.runtime_catalog_report_native_tree(cfg_tree));
 identity:='truss.candidate.generation-configuration/0.1.0/'||encode(convert_to(configuration->>'sourceEpoch','UTF8'),'hex')||'/'||encode(convert_to(configuration->>'installationId','UTF8'),'hex')||'/'||generation;
 tree:=jsonb_build_object('interfaceVersion','truss-feed-transaction/0.2.0','context',feed_context,'xid',xid_text,
  'manifestProfile',jsonb_build_object('identity',definition->'identity','version',definition->'version','sha256',encode(sha256(manifest_definition),'hex')),
  'configurationPrerequisites',jsonb_build_array(jsonb_build_object('configuration',jsonb_build_object(
   'generation',generation,'keyReuse',configuration->'keyReuse','journalMode',configuration->'journalMode',
   'configurationProfile',jsonb_build_object('identity',cfg_profile->'identity','version',cfg_profile->'version','sha256',encode(sha256(configuration_profile),'hex')),
   'installedProducerInventorySha256',encode(sha256(decode(configuration->>'inventoryHex','hex')),'hex'),
   'sourceEpoch',configuration->'sourceEpoch','installationId',configuration->'installationId'),
   'artifact',jsonb_build_object('identity',identity,'bytesBase64',replace(encode(configuration_artifact,'base64'),chr(10),''),'sha256',encode(sha256(configuration_artifact),'hex')))),
  'members',jsonb_build_array(jsonb_build_object('ordinal','0','key',jsonb_build_object('kind','revision','revision',revision_text),
   'payloadProfile',jsonb_build_object('identity',profile->'identity','version',profile->'version','sha256',encode(sha256(payload_profile),'hex')),
   'payloadSha256',encode(sha256(original_payload),'hex'))),'prerequisites',prerequisites);
 tree_bytes:=truss.runtime_manifest_artifact_tree_bytes_candidate(truss.runtime_catalog_report_native_tree(tree),documents,configuration_artifact);
 semantic_sha256:=sha256(convert_to('truss-canonical/0.1.0'||chr(10)||'truss-feed-manifest/0.2.0'||chr(10),'UTF8')||tree_bytes);
 tree:=tree||jsonb_build_object('manifestSha256',encode(semantic_sha256,'hex'));
 manifest_bytes:=truss.runtime_manifest_artifact_tree_bytes_candidate(truss.runtime_catalog_report_native_tree(tree),documents,configuration_artifact);
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_original_catalog_manifest_candidate(bytea,text,text,jsonb,bytea,bytea,bytea,bytea,bytea) FROM PUBLIC;
