-- Independent reference manifest is rooted in retained original configuration.
-- Administrative candidate correspondence only, not protected installation authority.
CREATE FUNCTION truss.runtime_require_catalog_finalization_composition_candidate(w text,o text,g text)
RETURNS void LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET DateStyle='ISO, YMD'
SET IntervalStyle='iso_8601' SET extra_float_digits=3 SET bytea_output='hex'
SET standard_conforming_strings=on SET quote_all_identifiers=off AS $$
DECLARE configuration truss.operation_configuration%ROWTYPE; inventory jsonb; context jsonb;
 raw_manifest bytea; manifest jsonb; resource jsonb; artifact bytea; resource_length bigint;
 total_resource_bytes bigint:=0; expected_paths text[]; selected_paths text[];
 relation_oid oid; target_descriptor jsonb; expected_collector jsonb; actual_collector text;
 actual_routines jsonb; actual_schema jsonb; routine_json jsonb; declaration_bytes bigint:=0;
BEGIN
 PERFORM truss.runtime_require_catalog_observation(w,o,g);
 PERFORM truss.runtime_require_operation_configuration_current(w,o,g);
 LOCK TABLE truss.installation_archive IN SHARE MODE NOWAIT;
 PERFORM truss.runtime_require_selected_archive_write_fence();
 SELECT c.* INTO STRICT configuration FROM truss.operation_configuration c
  WHERE c.original_writer_xid=pg_current_xact_id_if_assigned() AND c.operation_ordinal::text=o;
 SELECT convert_from(t.original_context_bytes,'UTF8')::jsonb INTO STRICT context FROM truss.row_home_operation t
  WHERE t.original_writer_xid=configuration.original_writer_xid AND t.operation_ordinal=configuration.operation_ordinal;
 IF octet_length(configuration.installed_inventory_bytes)>8192 THEN
  RAISE EXCEPTION 'bounded original custody inventory required' USING ERRCODE='54000'; END IF;
 IF NOT(convert_from(configuration.installed_inventory_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
  RAISE EXCEPTION 'original unique custody inventory required' USING ERRCODE='55000'; END IF;
 inventory:=convert_from(configuration.installed_inventory_bytes,'UTF8')::jsonb;
 IF (SELECT count(*) FROM jsonb_object_keys(inventory))<>4
  OR NOT inventory ?& ARRAY['interfaceVersion','scope','referenceManifest','custodyDescriptorSha256']
  OR inventory->>'interfaceVersion' IS DISTINCT FROM 'truss-catalog-custody-installation-inventory/0.5-finalization-candidate'
  OR inventory->>'scope' IS DISTINCT FROM 'administrative_rollback_only_catalog_custody'
  OR jsonb_typeof(inventory->'referenceManifest') IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(inventory->'referenceManifest'))<>2
  OR NOT inventory->'referenceManifest' ?& ARRAY['identity','sha256']
  OR inventory->'referenceManifest'->>'identity' IS DISTINCT FROM 'truss.catalog-custody-finalization-independent-reference/0.1-candidate'
  OR jsonb_typeof(inventory->'referenceManifest'->'sha256') IS DISTINCT FROM 'string'
  OR inventory->'referenceManifest'->>'sha256' !~ '^[0-9a-f]{64}$'
  OR jsonb_typeof(inventory->'custodyDescriptorSha256') IS DISTINCT FROM 'string'
  OR inventory->>'custodyDescriptorSha256' !~ '^[0-9a-f]{64}$'
  OR current_setting('server_version_num') IS DISTINCT FROM '180006' THEN
  RAISE EXCEPTION 'closed original PostgreSQL18 custody inventory required' USING ERRCODE='55000'; END IF;
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
  AND a.artifact_role='input' AND a.artifact_identity=inventory->'referenceManifest'->>'identity')<>1 THEN
  RAISE EXCEPTION 'unique original independent reference required' USING ERRCODE='55000'; END IF;
 SELECT octet_length(a.artifact_bytes)::bigint INTO STRICT resource_length FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND a.artifact_identity=inventory->'referenceManifest'->>'identity';
 IF resource_length NOT BETWEEN 1 AND 4194304 THEN RAISE EXCEPTION 'reference manifest capacity' USING ERRCODE='54000'; END IF;
 total_resource_bytes:=resource_length;
 SELECT a.artifact_bytes INTO STRICT raw_manifest FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND a.artifact_identity=inventory->'referenceManifest'->>'identity'
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8'))
   AND a.artifact_sha256=sha256(a.artifact_bytes)
   AND a.artifact_sha256=decode(inventory->'referenceManifest'->>'sha256','hex') FOR SHARE NOWAIT;
 IF NOT(convert_from(raw_manifest,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
  RAISE EXCEPTION 'original unique independent reference required' USING ERRCODE='55000'; END IF;
 manifest:=convert_from(raw_manifest,'UTF8')::jsonb;
 IF (SELECT count(*) FROM jsonb_object_keys(manifest))<>7
  OR NOT manifest ?& ARRAY['interfaceVersion','scope','nativeVersion','sourceFiles','resources','routines','custodySchema']
  OR manifest->>'interfaceVersion' IS DISTINCT FROM 'truss-catalog-custody-finalization-independent-reference/0.1-candidate'
  OR manifest->>'scope' IS DISTINCT FROM 'administrative_rollback_only_catalog_custody'
  OR manifest->>'nativeVersion' IS DISTINCT FROM '180006'
  OR jsonb_typeof(manifest->'sourceFiles') IS DISTINCT FROM 'array'
  OR jsonb_array_length(manifest->'sourceFiles') NOT BETWEEN 1 AND 128
  OR jsonb_typeof(manifest->'resources') IS DISTINCT FROM 'array'
  OR jsonb_array_length(manifest->'resources')<>100
  OR jsonb_typeof(manifest->'routines') IS DISTINCT FROM 'array'
  OR jsonb_array_length(manifest->'routines') NOT BETWEEN 1 AND 1024
  OR jsonb_typeof(manifest->'custodySchema') IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'complete independently compiled reference required' USING ERRCODE='55000'; END IF;
 -- Original compiler source receipt is metadata, not a target-produced proof.
 FOR resource IN SELECT * FROM jsonb_array_elements(manifest->'sourceFiles') LOOP
  IF jsonb_typeof(resource) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(resource))<>2
   OR NOT resource ?& ARRAY['path','sha256'] OR jsonb_typeof(resource->'path') IS DISTINCT FROM 'string'
   OR octet_length(resource->>'path') NOT BETWEEN 1 AND 4096 OR jsonb_typeof(resource->'sha256') IS DISTINCT FROM 'string'
   OR resource->>'sha256' !~ '^[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'closed original compiler source pin required' USING ERRCODE='55000'; END IF;
 END LOOP;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(manifest->'sourceFiles') s GROUP BY s->>'path' HAVING count(*)<>1) THEN
  RAISE EXCEPTION 'unique original compiler sources required' USING ERRCODE='55000'; END IF;
 -- Fixed adjunct path closure is generated from the owner composition roster.
 expected_paths:=ARRAY['docs/helix/02-design/contracts/catalog-revision-custody-storage-v0.1.proposal.umf.json','docs/helix/02-design/models/truss-layout-core-structural-0.9.proposal.umf.json','docs/helix/04-build/evidence/catalog-revision-custody-storage.owner-export.sql','packages/postgresql/native/catalog-custody/configured-graph.sql','packages/postgresql/native/catalog-custody/configured-graph.umf.json','packages/postgresql/native/catalog-custody/fresh-lifecycle.sql','packages/postgresql/native/catalog-custody/fresh-lifecycle.umf.json','packages/postgresql/native/catalog-custody/stage-issued.sql','packages/postgresql/native/catalog-custody/stage-issued.umf.json','packages/postgresql/native/catalog-custody/configured-stage.sql','packages/postgresql/native/catalog-custody/configured-stage.umf.json','packages/postgresql/native/catalog-custody/report-write.sql','packages/postgresql/native/catalog-custody/report-write.umf.json','packages/postgresql/native/catalog-custody/branch-manifest.json','packages/python/src/truss/_profiles/catalog-report-custody-composition-candidate.json','packages/python/src/truss/_profiles/catalog-revision-custody-candidate.json','packages/python/src/truss/_profiles/catalog-revision-wide-report-composition-candidate.json','packages/postgresql/native/catalog-custody/capture.sql','packages/postgresql/native/catalog-custody/capture.umf.json','packages/postgresql/native/catalog-custody/composition-admission.sql','packages/postgresql/native/catalog-custody/composition-admission.umf.json','packages/postgresql/native/catalog-completion/configured-state-candidate.sql','packages/postgresql/native/catalog-completion/configured-state-candidate.umf.json','scripts/build-catalog-revision-custody-layout.ts','scripts/project-catalog-revision-custody-core.ts','scripts/build-catalog-custody-branch.ts','scripts/export-catalog-custody-capture.ts','packages/postgresql/native/catalog-custody/reference-collectors.sql','packages/postgresql/native/catalog-custody/reference-collectors.umf.json','scripts/build-catalog-custody-reference.py','packages/postgresql/native/catalog-custody/registration-composition-admission.sql','packages/postgresql/native/catalog-custody/registration-composition-admission.umf.json','packages/postgresql/native/catalog-custody/registration-capture.sql','packages/postgresql/native/catalog-custody/registration-capture.umf.json','packages/postgresql/native/catalog-custody/registrar.sql','packages/postgresql/native/catalog-custody/registrar.umf.json','packages/python/src/truss/_profiles/catalog-custody-registration-candidate.json','packages/python/src/truss/_profiles/catalog-revision-custody-registration-capture-candidate.json','packages/postgresql/native/catalog-custody/registration-statements/create.sql','packages/postgresql/native/catalog-custody/registration-statements/create.umf.json','packages/postgresql/native/catalog-custody/registration-statements/reserve.sql','packages/postgresql/native/catalog-custody/registration-statements/reserve.umf.json','packages/postgresql/native/catalog-custody/registration-statements/insert.sql','packages/postgresql/native/catalog-custody/registration-statements/insert.umf.json','packages/postgresql/native/catalog-custody/registration-statements/manifest.json','scripts/extract-catalog-custody-registration-statements.ts','scripts/export-catalog-custody-registration.ts','scripts/build-catalog-custody-registration-reference.py','packages/postgresql/native/catalog-report/prerequisite-registration-candidate.sql','packages/postgresql/native/catalog-custody/prerequisite-composition/composition-admission.sql','packages/postgresql/native/catalog-custody/prerequisite-composition/composition-admission.umf.json','packages/postgresql/native/catalog-custody/prerequisite-composition/registration-capture.sql','packages/postgresql/native/catalog-custody/prerequisite-composition/registration-capture.umf.json','packages/postgresql/native/catalog-custody/prerequisite-composition/registrar.sql','packages/postgresql/native/catalog-custody/prerequisite-composition/registrar.umf.json','packages/postgresql/native/catalog-custody/prerequisite-composition/prerequisites.sql','packages/postgresql/native/catalog-custody/prerequisite-composition/prerequisites.umf.json','packages/python/src/truss/_profiles/catalog-prerequisite-custody-capture-candidate.json','packages/python/src/truss/_profiles/catalog-prerequisite-custody-registration-candidate.json','packages/python/src/truss/_profiles/catalog-custody-prerequisite-registration-candidate.json','packages/postgresql/native/catalog-report/prerequisite-statements/catalog-reserve.sql','packages/postgresql/native/catalog-report/prerequisite-statements/catalog-reserve.umf.json','packages/postgresql/native/catalog-report/prerequisite-statements/configuration-reserve.sql','packages/postgresql/native/catalog-report/prerequisite-statements/configuration-reserve.umf.json','packages/postgresql/native/catalog-report/prerequisite-statements/catalog-insert.sql','packages/postgresql/native/catalog-report/prerequisite-statements/catalog-insert.umf.json','packages/postgresql/native/catalog-report/prerequisite-statements/configuration-insert.sql','packages/postgresql/native/catalog-report/prerequisite-statements/configuration-insert.umf.json','packages/postgresql/native/catalog-report/prerequisite-statements/manifest.json','scripts/export-catalog-custody-prerequisites.ts','scripts/build-catalog-custody-prerequisite-reference.py','packages/postgresql/native/catalog-finalization/finalization-composition-admission.owner-export.sql','packages/postgresql/native/catalog-finalization/finalizing-capture.owner-export.sql','packages/postgresql/native/catalog-finalization/finalizing-registrar.owner-export.sql','packages/postgresql/native/catalog-finalization/finalizing-prerequisites.owner-export.sql','packages/postgresql/native/catalog-finalization/readonly-custody-preflight.owner-export.sql','packages/postgresql/native/catalog-finalization/readonly-business-preflight.owner-export.sql','packages/postgresql/native/catalog-finalization/finalizing-completion-state.owner-export.sql','packages/postgresql/native/catalog-finalization/finalize-feed.owner-export.sql','packages/postgresql/native/catalog-finalization/finalizing-head.owner-export.sql','packages/postgresql/native/catalog-finalization/manifest-encoder.owner-export.sql','packages/postgresql/native/catalog-finalization/original-manifest.owner-export.sql','packages/postgresql/native/catalog-finalization/manifest-encoder.sql','packages/postgresql/native/catalog-finalization/manifest-encoder.umf.json','packages/postgresql/native/catalog-finalization/original-manifest.sql','packages/postgresql/native/catalog-finalization/original-manifest.umf.json','packages/postgresql/native/catalog-finalization/manifest-definition-v0.4.candidate.json','packages/postgresql/native/catalog-finalization/manifest-definition-v0.4.canonical','packages/postgresql/native/catalog-finalization/manifest-definition-v0.4.pin.json','packages/postgresql/native/catalog-finalization/statements/clear-parent.sql','packages/postgresql/native/catalog-finalization/statements/clear-parent.umf.json','packages/postgresql/native/catalog-finalization/statements/clear-member.sql','packages/postgresql/native/catalog-finalization/statements/clear-member.umf.json','packages/postgresql/native/catalog-finalization/statements/assign-ordinal.sql','packages/postgresql/native/catalog-finalization/statements/assign-ordinal.umf.json','packages/postgresql/native/catalog-finalization/statements/publish-manifest.sql','packages/postgresql/native/catalog-finalization/statements/publish-manifest.umf.json','packages/python/src/truss/_profiles/catalog-finalizing-custody-registration-candidate.json','packages/python/src/truss/_profiles/catalog-feed-finalization-candidate.json','packages/python/src/truss/_profiles/catalog-finalizing-custody-prerequisite-registration-candidate.json'];
 SELECT array_agg(path ORDER BY path COLLATE "C") INTO expected_paths FROM unnest(expected_paths) path;
 SELECT array_agg(r->>'path' ORDER BY r->>'path' COLLATE "C") INTO selected_paths FROM jsonb_array_elements(manifest->'resources') r;
 IF selected_paths IS DISTINCT FROM expected_paths THEN RAISE EXCEPTION 'complete original adjunct resource closure required' USING ERRCODE='55000'; END IF;
 FOR resource IN SELECT * FROM jsonb_array_elements(manifest->'resources') LOOP
  IF jsonb_typeof(resource) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(resource))<>2
   OR NOT resource ?& ARRAY['path','sha256'] OR jsonb_typeof(resource->'sha256') IS DISTINCT FROM 'string'
   OR resource->>'sha256' !~ '^[0-9a-f]{64}$'
   OR (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
    AND a.artifact_role='input' AND a.artifact_identity=resource->>'path')<>1 THEN
   RAISE EXCEPTION 'original unique adjunct resource required' USING ERRCODE='55000'; END IF;
  SELECT octet_length(a.artifact_bytes)::bigint INTO STRICT resource_length FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=resource->>'path';
  total_resource_bytes:=total_resource_bytes+resource_length;
  IF resource_length NOT BETWEEN 1 AND 4194304 OR total_resource_bytes>16777216 THEN
   RAISE EXCEPTION 'original adjunct resource retention capacity' USING ERRCODE='54000'; END IF;
  SELECT a.artifact_bytes INTO STRICT artifact FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=resource->>'path'
    AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8'))
    AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_sha256=decode(resource->>'sha256','hex') FOR SHARE NOWAIT;
 END LOOP;
 FOR routine_json IN SELECT * FROM jsonb_array_elements(manifest->'routines') LOOP
  IF jsonb_typeof(routine_json) IS DISTINCT FROM 'object' OR jsonb_typeof(routine_json->'definition') IS DISTINCT FROM 'string'
   OR octet_length(routine_json->>'definition') NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original routine declaration required' USING ERRCODE='54000'; END IF;
  declaration_bytes:=declaration_bytes+octet_length(routine_json->>'definition')::bigint;
  IF declaration_bytes>4194304 THEN RAISE EXCEPTION 'original routine aggregate capacity' USING ERRCODE='54000'; END IF;
 END LOOP;
 -- Check original collector definitions with native deparsing before invoking
 -- those collectors to compare the complete schema and transitive routine set.
 FOR resource IN SELECT value FROM jsonb_array_elements(jsonb_build_array(
  'runtime_collect_catalog_custody_declarations_candidate','runtime_collect_catalog_custody_schema_candidate')) LOOP
  SELECT r INTO STRICT expected_collector FROM jsonb_array_elements(manifest->'routines') r
   WHERE r->>'name'=resource #>> '{}' AND r->>'identityArguments'='';
  SELECT pg_get_functiondef(p.oid) INTO STRICT actual_collector FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
   WHERE n.nspname='truss' AND p.proname=resource #>> '{}' AND p.pronargs=0 AND p.prokind='f'
    AND NOT p.prosecdef AND p.provolatile='v' AND p.proparallel='u' AND NOT p.proleakproof;
  IF actual_collector IS DISTINCT FROM expected_collector->>'definition' THEN
   RAISE EXCEPTION 'original independent-reference collector required' USING ERRCODE='55000'; END IF;
 END LOOP;
 actual_routines:=truss.runtime_collect_catalog_custody_declarations_candidate();
 actual_schema:=truss.runtime_collect_catalog_custody_schema_candidate();
 IF actual_routines IS DISTINCT FROM manifest->'routines' OR actual_schema IS DISTINCT FROM manifest->'custodySchema' THEN
  RAISE EXCEPTION 'complete independent original routine and schema correspondence required' USING ERRCODE='55000'; END IF;
 target_descriptor:=truss.runtime_collect_catalog_custody_target_descriptor_candidate();
 IF encode(sha256(convert_to(target_descriptor::text,'UTF8')),'hex') IS DISTINCT FROM inventory->>'custodyDescriptorSha256' THEN
  RAISE EXCEPTION 'original admitted target descriptor required' USING ERRCODE='55000'; END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_require_catalog_finalization_composition_candidate(text,text,text) FROM PUBLIC;
