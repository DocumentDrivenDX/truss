-- Private physical-source candidate on an already admitted original operation.
-- Not registered ontology authority, installation, accepted lineage or publication.
CREATE FUNCTION truss.runtime_pending_association_reference(reference json)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF reference IS NULL OR json_typeof(reference)<>'object'
  OR (SELECT count(*) FROM json_object_keys(reference))<>3
  OR EXISTS(SELECT 1 FROM json_each(reference) e WHERE e.key NOT IN ('documentId','moduleId','elementId')
   OR json_typeof(e.value)<>'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096) THEN
  RAISE EXCEPTION 'qualified original association reference required' USING ERRCODE='22023';
 END IF;
 RETURN reference::jsonb;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_pending_association_reference(json) FROM PUBLIC;

CREATE FUNCTION truss.runtime_pending_association_type(revision int,reference jsonb)
RETURNS int LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result int;
BEGIN
 IF reference IS NULL OR jsonb_typeof(reference)<>'object'
  OR NOT reference ?& ARRAY['documentId','moduleId','elementId']
  OR (SELECT count(*) FROM jsonb_object_keys(reference))<>3
  OR EXISTS(SELECT 1 FROM jsonb_each(reference) e WHERE jsonb_typeof(e.value)<>'string'
   OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096) THEN
  RAISE EXCEPTION 'qualified original association reference required' USING ERRCODE='22023';
 END IF;
 SELECT t.type_id INTO STRICT result FROM truss.type_def t
  WHERE t.document_id COLLATE "C"=(reference->>'documentId') COLLATE "C"
   AND t.module COLLATE "C"=(reference->>'moduleId') COLLATE "C"
   AND t.element COLLATE "C"=(reference->>'elementId') COLLATE "C"
   AND t.kind='record' AND NOT t.provisional AND t.retired_rev IS NULL AND t.since_rev=revision;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_pending_association_type(int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_pending_association_fields(revision int,owner_id int,refs jsonb)
RETURNS int[] LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result int[]:=ARRAY[]::int[]; reference jsonb; property_id int; owner_document text;
BEGIN
 IF refs IS NULL OR jsonb_typeof(refs)<>'array' OR jsonb_array_length(refs) NOT BETWEEN 1 AND 256 THEN
  RAISE EXCEPTION 'bounded ordered association fields required' USING ERRCODE='22023';
 END IF;
 SELECT t.document_id INTO STRICT owner_document FROM truss.type_def t WHERE t.type_id=owner_id AND t.since_rev=revision;
 FOR reference IN SELECT value FROM jsonb_array_elements(refs) LOOP
  IF jsonb_typeof(reference)<>'object' OR NOT reference ?& ARRAY['documentId','moduleId','elementId']
   OR (SELECT count(*) FROM jsonb_object_keys(reference))<>3
   OR EXISTS(SELECT 1 FROM jsonb_each(reference) e WHERE jsonb_typeof(e.value)<>'string'
    OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096)
   OR reference->>'documentId' IS DISTINCT FROM owner_document THEN
   RAISE EXCEPTION 'owned original association field reference required' USING ERRCODE='22023';
  END IF;
  SELECT p.prop_id INTO STRICT property_id FROM truss.prop_def p WHERE p.type_id=owner_id
   AND p.declaration_module COLLATE "C"=(reference->>'moduleId') COLLATE "C"
   AND p.element COLLATE "C"=(reference->>'elementId') COLLATE "C"
   AND p.since_rev=revision AND p.retired_rev IS NULL
   AND p.scalar_type='string' AND p.nullability='required' AND p.cardinality='one';
  IF property_id=ANY(result) THEN RAISE EXCEPTION 'duplicate association field required refusal' USING ERRCODE='22023'; END IF;
  result:=array_append(result,property_id);
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_pending_association_fields(int,int,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.runtime_stage_pending_association_candidate(original_revision int)
RETURNS TABLE(mapping_pointer text,relationship_id text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE observed record; op truss.row_home_operation%ROWTYPE; binding jsonb; ontology json; entity_item json; association_item json; original_ref jsonb; seen_entity_refs jsonb[]:=ARRAY[]::jsonb[]; seen_association_refs jsonb[]:=ARRAY[]::jsonb[];
 ontology_bytes bytea; mapping jsonb; original_association json; endpoint json; role jsonb;
 original_entity json; owner truss.type_def%ROWTYPE; source_id int; target_id int;
 target_key_id text; role_owner int; fields int[]; target_fields int[]; endpoint_fields int[];
 own_key int[]; seen int[]:=ARRAY[]::int[]; assigned bigint; high_water bigint;
 index int:=0; ontology_start int:=1; pointer text; fragment bytea; fragments bytea[]:=ARRAY[]::bytea[];
 roles_seen text[]; role_name text; original_name text;
BEGIN
 -- Complete source/core checks occur once before any pending effect. They are
 -- intentionally not reused after a binding-derived row has been inserted.
 SELECT * INTO STRICT observed FROM truss.runtime_collect_original_catalog_binding(original_revision);
 SELECT array_agg(b.mapping_bytes ORDER BY b.mapping_index) INTO fragments
  FROM truss.runtime_extract_original_association_mapping_batch(decode(observed.binding_hex,'hex')) b;
 binding:=convert_from(decode(observed.binding_hex,'hex'),'UTF8')::jsonb;
 IF binding->>'profile' IS DISTINCT FROM 'truss-binary-association-candidate/0.2.0'
  OR NOT binding ?& ARRAY['profile','coreSha256','ontologySha256','modelRevision','ontologyRevision','mappings','ontologyArtifact']
  OR (SELECT count(*) FROM jsonb_object_keys(binding))<>7
  OR EXISTS(SELECT 1 FROM jsonb_each(binding) e WHERE e.key NOT IN ('mappings','ontologyArtifact') AND (jsonb_typeof(e.value)<>'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096))
  OR jsonb_typeof(binding->'mappings') IS DISTINCT FROM 'array'
  OR jsonb_array_length(binding->'mappings') NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'original binary association candidate profile required' USING ERRCODE='0A000';
 END IF;
 -- Every original slice was validated together before interpretation/writes.
 IF jsonb_typeof(binding->'ontologyArtifact') IS DISTINCT FROM 'object'
  OR NOT (binding->'ontologyArtifact') ?& ARRAY['identity','bytesBase64','sha256']
  OR (SELECT count(*) FROM jsonb_object_keys(binding->'ontologyArtifact'))<>3
  OR EXISTS(SELECT 1 FROM jsonb_each(binding->'ontologyArtifact') e WHERE jsonb_typeof(e.value)<>'string')
  OR jsonb_typeof(binding->'ontologyArtifact'->'identity') IS DISTINCT FROM 'string'
  OR octet_length(binding->'ontologyArtifact'->>'identity') NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'original ontology artifact required' USING ERRCODE='22023';
 END IF;
 ontology_bytes:=decode(binding->'ontologyArtifact'->>'bytesBase64','base64');
 IF ontology_bytes IS NULL OR octet_length(ontology_bytes) NOT BETWEEN 1 AND 1048576
  OR replace(encode(ontology_bytes,'base64'),chr(10),'') IS DISTINCT FROM binding->'ontologyArtifact'->>'bytesBase64'
  OR encode(sha256(ontology_bytes),'hex') IS DISTINCT FROM binding->'ontologyArtifact'->>'sha256'
  OR encode(sha256(ontology_bytes),'hex') IS DISTINCT FROM binding->>'ontologySha256' THEN
  RAISE EXCEPTION 'original ontology artifact correspondence required' USING ERRCODE='55000';
 END IF;
 WHILE ontology_start<=octet_length(ontology_bytes) LOOP
  EXIT WHEN chr(get_byte(ontology_bytes,ontology_start-1)) NOT IN (' ',chr(9),chr(10),chr(13));
  ontology_start:=ontology_start+1;
 END LOOP;
 IF ontology_start>octet_length(ontology_bytes) THEN RAISE EXCEPTION 'unique original ontology JSON required' USING ERRCODE='22023'; END IF;
 PERFORM truss.runtime_original_json_value_end(ontology_bytes,ontology_start);
 IF NOT (convert_from(ontology_bytes,'UTF8') IS JSON OBJECT) THEN
  RAISE EXCEPTION 'original ontology JSON object required' USING ERRCODE='22023';
 END IF;
 IF NOT (convert_from(ontology_bytes,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) THEN
  -- PostgreSQL16.15 also refuses escaped NUL values under WITH UNIQUE KEYS.
  -- Refuse this native parser subset; never call such valid source invalid or
  -- discard it. General admission must consume a registered original owner basis.
  RAISE EXCEPTION 'native ontology unique-key parser profile unavailable' USING ERRCODE='0A000';
 END IF;
 ontology:=convert_from(ontology_bytes,'UTF8')::json;
 IF json_typeof(ontology->'documentId') IS DISTINCT FROM 'string' OR json_typeof(ontology->'revision') IS DISTINCT FROM 'string'
  OR ontology->>'version' IS DISTINCT FROM '0.1.0'
  OR ontology->>'revision' IS DISTINCT FROM binding->>'ontologyRevision'
  OR json_typeof(ontology->'associations') IS DISTINCT FROM 'array'
  OR json_array_length(ontology->'associations') IS DISTINCT FROM jsonb_array_length(binding->'mappings')
  OR (ontology->'documents')::jsonb IS DISTINCT FROM jsonb_build_array(jsonb_build_object('documentId',ontology->>'documentId','revision',binding->>'modelRevision'))
  OR NOT EXISTS(SELECT 1 FROM truss.schema_doc d WHERE d.rev=original_revision AND d.doc_id=ontology->>'documentId'
   AND d.doc_revision=binding->>'modelRevision' AND d.content_sha256=binding->>'coreSha256') THEN
  RAISE EXCEPTION 'original ontology model correspondence required' USING ERRCODE='55000';
 END IF;
 IF json_typeof(ontology->'entities') IS DISTINCT FROM 'array' OR json_array_length(ontology->'entities') NOT BETWEEN 1 AND 4096 THEN
  RAISE EXCEPTION 'complete original entity inventory required' USING ERRCODE='55000';
 END IF;
 FOR entity_item IN SELECT value FROM json_array_elements(ontology->'entities') LOOP
  original_ref:=truss.runtime_pending_association_reference(entity_item->'type');
  IF original_ref=ANY(seen_entity_refs) THEN RAISE EXCEPTION 'duplicate original entity identity' USING ERRCODE='55000'; END IF;
  seen_entity_refs:=array_append(seen_entity_refs,original_ref);
 END LOOP;
 FOR association_item IN SELECT value FROM json_array_elements(ontology->'associations') LOOP
  original_ref:=truss.runtime_pending_association_reference(association_item->'type');
  IF original_ref=ANY(seen_association_refs) THEN RAISE EXCEPTION 'duplicate original association identity' USING ERRCODE='55000'; END IF;
  seen_association_refs:=array_append(seen_association_refs,original_ref);
 END LOOP;
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.phase='admitted' AND o.operation_kind='catalog-acceptance' FOR UPDATE;
 SELECT greatest(coalesce(max(r.rel_type_id)::bigint,0),0) INTO high_water FROM truss.rel_def r;
 IF high_water+jsonb_array_length(binding->'mappings')>2147483647 THEN
  RAISE EXCEPTION 'pending association identity capacity exhausted' USING ERRCODE='54000';
 END IF;
 index:=0;
 FOR mapping IN SELECT value FROM jsonb_array_elements(binding->'mappings') LOOP
  pointer:='/mappings/'||index::text;fragment:=fragments[index+1];index:=index+1;
  IF jsonb_typeof(mapping)<>'object' OR NOT mapping ?& ARRAY['association','instanceKeyId','sourceRole','targetRole','roles','storage']
   OR (SELECT count(*) FROM jsonb_object_keys(mapping))<>6
   OR jsonb_typeof(mapping->'roles') IS DISTINCT FROM 'array' OR jsonb_array_length(mapping->'roles')<>2
   OR mapping->'storage' IS DISTINCT FROM '{"sourceMin":"0","sourceMax":"*","targetMin":"0","targetMax":"*","directed":true,"lifecycle":"independent","composition":false,"inverse":null}'::jsonb
   OR jsonb_typeof(mapping->'instanceKeyId') IS DISTINCT FROM 'string' OR octet_length(mapping->>'instanceKeyId') NOT BETWEEN 1 AND 4096
   OR octet_length(mapping->>'sourceRole') NOT BETWEEN 1 AND 4096 OR octet_length(mapping->>'targetRole') NOT BETWEEN 1 AND 4096
   OR jsonb_typeof(mapping->'sourceRole') IS DISTINCT FROM 'string' OR jsonb_typeof(mapping->'targetRole') IS DISTINCT FROM 'string'
   OR mapping->>'sourceRole'=mapping->>'targetRole' THEN
   RAISE EXCEPTION 'original binary association mapping subset required' USING ERRCODE='0A000';
  END IF;
  IF mapping->'association'->>'documentId' IS DISTINCT FROM ontology->>'documentId' THEN
   RAISE EXCEPTION 'single original association model required' USING ERRCODE='55000';
  END IF;
  SELECT t.* INTO STRICT owner FROM truss.type_def t WHERE t.type_id=truss.runtime_pending_association_type(original_revision,mapping->'association');
  IF owner.type_id=ANY(seen) OR EXISTS(SELECT 1 FROM truss.rel_def r WHERE r.document_id=owner.document_id AND r.module=owner.module AND r.rel_id=owner.element) THEN
   RAISE EXCEPTION 'duplicate original association identity' USING ERRCODE='55000';
  END IF;
  seen:=array_append(seen,owner.type_id);
  SELECT a.value INTO STRICT original_association FROM json_array_elements(ontology->'associations') a WHERE truss.runtime_pending_association_reference(a.value->'type')=mapping->'association';
  IF json_typeof(original_association->'keyId') IS DISTINCT FROM 'string' OR original_association->>'keyId' IS DISTINCT FROM mapping->>'instanceKeyId'
   OR json_typeof(original_association->'endpoints') IS DISTINCT FROM 'array'
   OR json_array_length(original_association->'endpoints')<>2 THEN
   RAISE EXCEPTION 'original association declaration correspondence required' USING ERRCODE='55000';
  END IF;
  SELECT k.prop_ids INTO STRICT own_key FROM truss.key_def k WHERE k.type_id=owner.type_id AND k.key_id=mapping->>'instanceKeyId' AND k.retired_rev IS NULL AND k.since_rev=original_revision;
  source_id:=NULL;target_id:=NULL;target_key_id:=NULL;roles_seen:=ARRAY[]::text[];endpoint_fields:=ARRAY[]::int[];
  FOR role IN SELECT value FROM jsonb_array_elements(mapping->'roles') LOOP
   IF jsonb_typeof(role)<>'object' OR NOT role ?& ARRAY['role','associationFields','target','targetKeyId','targetFields']
    OR (SELECT count(*) FROM jsonb_object_keys(role))<>5 OR jsonb_typeof(role->'role') IS DISTINCT FROM 'string'
    OR jsonb_typeof(role->'targetKeyId') IS DISTINCT FROM 'string' OR octet_length(role->>'targetKeyId') NOT BETWEEN 1 AND 4096
    OR octet_length(role->>'role') NOT BETWEEN 1 AND 4096 OR role->>'role'=ANY(roles_seen) THEN
    RAISE EXCEPTION 'original association role coverage required' USING ERRCODE='55000';
   END IF;
   role_name:=role->>'role';roles_seen:=array_append(roles_seen,role_name);
   SELECT e.value INTO STRICT endpoint FROM json_array_elements(original_association->'endpoints') e WHERE json_typeof(e.value->'role')='string' AND octet_length(e.value->>'role') BETWEEN 1 AND 4096 AND e.value->>'role'=role_name;
   IF (endpoint->'fields')::jsonb IS DISTINCT FROM role->'associationFields' OR (endpoint->'target')::jsonb IS DISTINCT FROM role->'target' THEN
    RAISE EXCEPTION 'original association endpoint correspondence required' USING ERRCODE='55000';
   END IF;
   IF role->'target'->>'documentId' IS DISTINCT FROM ontology->>'documentId' THEN
    RAISE EXCEPTION 'single original association model required' USING ERRCODE='55000';
   END IF;
   role_owner:=truss.runtime_pending_association_type(original_revision,role->'target');
   SELECT e.value INTO STRICT original_entity FROM json_array_elements(ontology->'entities') e WHERE truss.runtime_pending_association_reference(e.value->'type')=role->'target';
   IF json_typeof(original_entity->'keyId') IS DISTINCT FROM 'string' OR original_entity->>'keyId' IS DISTINCT FROM role->>'targetKeyId' THEN
    RAISE EXCEPTION 'original association target key correspondence required' USING ERRCODE='55000';
   END IF;
   fields:=truss.runtime_pending_association_fields(original_revision,owner.type_id,role->'associationFields');
   target_fields:=truss.runtime_pending_association_fields(original_revision,role_owner,role->'targetFields');
   IF cardinality(fields)<>cardinality(target_fields) OR NOT EXISTS(SELECT 1 FROM truss.key_def k
    WHERE k.type_id=role_owner AND k.key_id=role->>'targetKeyId' AND k.since_rev=original_revision AND k.retired_rev IS NULL AND k.prop_ids=target_fields) THEN
    RAISE EXCEPTION 'original ordered endpoint key correspondence required' USING ERRCODE='55000';
   END IF;
   endpoint_fields:=endpoint_fields||fields;
   IF role_name=mapping->>'sourceRole' THEN source_id:=role_owner;
   ELSIF role_name=mapping->>'targetRole' THEN target_id:=role_owner;target_key_id:=role->>'targetKeyId';
   ELSE RAISE EXCEPTION 'original association orientation coverage required' USING ERRCODE='55000'; END IF;
  END LOOP;
  IF source_id IS NULL OR target_id IS NULL OR NOT own_key<@endpoint_fields THEN
   RAISE EXCEPTION 'lossless original association instance identity required' USING ERRCODE='0A000';
  END IF;
  SELECT e.value->>'name' INTO STRICT original_name FROM truss.schema_doc d
   CROSS JOIN LATERAL jsonb_array_elements(d.document::jsonb->'modules') m
   CROSS JOIN LATERAL jsonb_array_elements(m.value->'elements') e
   WHERE d.rev=original_revision AND d.doc_id=owner.document_id AND m.value->>'id'=owner.module AND e.value->>'id'=owner.element;
  assigned:=high_water+index;
  INSERT INTO truss.rel_def(document_id,rel_type_id,module,rel_id,name,source_min,source_max,target_min,target_max,lifecycle,directed,target_key,composition,assoc_type_id,inverse,since_rev,doc_ord,definition_source_kind,pending_writer_xid,pending_operation_ordinal,pending_binding_revision,pending_mapping_pointer,pending_mapping_bytes)
  VALUES(owner.document_id,assigned::int,owner.module,owner.element,original_name,0,NULL,0,NULL,'independent',true,target_key_id,false,owner.type_id,NULL,original_revision,owner.doc_ord,'operation_binding',op.original_writer_xid,op.operation_ordinal,original_revision,pointer,fragment);
  INSERT INTO truss.rel_endpoint(rel_type_id,source_type,target_type) VALUES(assigned::int,source_id,target_id);
  RETURN QUERY SELECT pointer,assigned::text;
 END LOOP;
EXCEPTION WHEN no_data_found OR too_many_rows THEN
 RAISE EXCEPTION 'unique original association dependency required' USING ERRCODE='55000';
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_pending_association_candidate(int) FROM PUBLIC;
