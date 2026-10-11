-- Administrative rollback-only construction/write algorithm. Not installed
-- report authority and not called by the configured acceptance route.
-- Logical host strings remain tagged UTF8 throughout construction and encoding.
CREATE FUNCTION truss.runtime_catalog_report_native_tree(value jsonb, depth int DEFAULT 0)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE children jsonb:='[]'::jsonb; entry record; kind text;
BEGIN
 IF value IS NULL OR depth IS NULL OR depth<0 OR depth>128 THEN
  RAISE EXCEPTION 'bounded native report value required' USING ERRCODE='22023';
 END IF;
 kind:=jsonb_typeof(value);
 CASE kind
 WHEN 'null' THEN RETURN jsonb_build_object('kind','null');
 WHEN 'boolean' THEN RETURN jsonb_build_object('kind','boolean','value',value);
 WHEN 'string' THEN RETURN jsonb_build_object('kind','string','utf8Hex',encode(convert_to(value #>> '{}','UTF8'),'hex'));
 WHEN 'array' THEN
  IF jsonb_array_length(value)>4096 THEN RAISE EXCEPTION 'native report array capacity' USING ERRCODE='54000'; END IF;
  FOR entry IN SELECT x FROM jsonb_array_elements(value) x LOOP
   children:=children||jsonb_build_array(truss.runtime_catalog_report_native_tree(entry.x,depth+1));
  END LOOP;
  RETURN jsonb_build_object('kind','array','items',children);
 WHEN 'object' THEN
  IF (SELECT count(*) FROM jsonb_object_keys(value))>4096 THEN RAISE EXCEPTION 'native report object capacity' USING ERRCODE='54000'; END IF;
  FOR entry IN SELECT key,x FROM jsonb_each(value) e(key,x) LOOP
   children:=children||jsonb_build_array(jsonb_build_object('keyUtf8Hex',encode(convert_to(entry.key,'UTF8'),'hex'),
    'node',truss.runtime_catalog_report_native_tree(entry.x,depth+1)));
  END LOOP;
  RETURN jsonb_build_object('kind','object','members',children);
 ELSE RAISE EXCEPTION 'numeric-free native report value required' USING ERRCODE='22023';
 END CASE;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_catalog_report_native_tree(jsonb,int) FROM PUBLIC;

-- Decode original numeric-free JSON lexically into tagged UTF8. PostgreSQL text
-- never holds logical string/key NUL. Syntax, escapes and surrogate pairs are
-- checked before any report write; duplicate logical keys are rejected by codec.
CREATE FUNCTION truss.runtime_catalog_report_parse_value(original bytea, start_at int, depth int)
RETURNS TABLE(tree jsonb,next_at int,node_count int)
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE p int:=start_at; n int:=octet_length(original); b int; escape int; code int; low int;
 raw bytea:=decode('','hex'); children jsonb:='[]'::jsonb; child record; key_node jsonb;
 count_nodes int:=1; kind text; closing int; key_hex text;
BEGIN
 IF original IS NULL OR n NOT BETWEEN 1 AND 1048576 OR p<0 OR depth<0 OR depth>128 THEN
  RAISE EXCEPTION 'bounded original JSON source required' USING ERRCODE='22023'; END IF;
 WHILE p<n AND get_byte(original,p) IN (9,10,13,32) LOOP p:=p+1; END LOOP;
 IF p>=n THEN RAISE EXCEPTION 'original JSON value required' USING ERRCODE='22023'; END IF;
 b:=get_byte(original,p);p:=p+1;
 IF b=34 THEN
  WHILE p<n LOOP
   b:=get_byte(original,p);p:=p+1;
   IF b=34 THEN
    PERFORM truss.runtime_canonical_string_bytes(raw);
    RETURN QUERY SELECT jsonb_build_object('kind','string','utf8Hex',encode(raw,'hex')),p,count_nodes; RETURN;
   ELSIF b<32 THEN RAISE EXCEPTION 'unescaped JSON control required to refuse' USING ERRCODE='22023';
   ELSIF b=92 THEN
    IF p>=n THEN RAISE EXCEPTION 'complete JSON escape required' USING ERRCODE='22023'; END IF;
    escape:=get_byte(original,p);p:=p+1;
    IF escape IN (34,47,92) THEN raw:=raw||set_byte(decode('00','hex'),0,escape);
    ELSIF escape IN (98,102,110,114,116) THEN
     raw:=raw||set_byte(decode('00','hex'),0,CASE escape WHEN 98 THEN 8 WHEN 102 THEN 12 WHEN 110 THEN 10 WHEN 114 THEN 13 ELSE 9 END);
    ELSIF escape=117 THEN
     IF p+4>n OR convert_from(substr(original,p+1,4),'UTF8') !~ '^[0-9a-fA-F]{4}$' THEN
      RAISE EXCEPTION 'four JSON hex digits required' USING ERRCODE='22023'; END IF;
     code:=get_byte(decode(convert_from(substr(original,p+1,4),'UTF8'),'hex'),0)*256
       +get_byte(decode(convert_from(substr(original,p+1,4),'UTF8'),'hex'),1);p:=p+4;
     IF code BETWEEN 55296 AND 56319 THEN
      IF p+6>n OR substr(original,p+1,2)<>decode('5c75','hex')
       OR convert_from(substr(original,p+3,4),'UTF8') !~ '^[0-9a-fA-F]{4}$' THEN
       RAISE EXCEPTION 'original JSON surrogate pair required' USING ERRCODE='22023'; END IF;
      low:=get_byte(decode(convert_from(substr(original,p+3,4),'UTF8'),'hex'),0)*256
       +get_byte(decode(convert_from(substr(original,p+3,4),'UTF8'),'hex'),1);p:=p+6;
      IF low NOT BETWEEN 56320 AND 57343 THEN RAISE EXCEPTION 'original JSON low surrogate required' USING ERRCODE='22023'; END IF;
      code:=65536+(code-55296)*1024+low-56320;
     ELSIF code BETWEEN 56320 AND 57343 THEN RAISE EXCEPTION 'unpaired JSON low surrogate' USING ERRCODE='22023'; END IF;
     IF code=0 THEN raw:=raw||decode('00','hex'); ELSE raw:=raw||convert_to(chr(code),'UTF8'); END IF;
    ELSE RAISE EXCEPTION 'recognized JSON escape required' USING ERRCODE='22023'; END IF;
   ELSE raw:=raw||set_byte(decode('00','hex'),0,b);
   END IF;
  END LOOP;
  RAISE EXCEPTION 'closed JSON string required' USING ERRCODE='22023';
 ELSIF b IN (91,123) THEN
  kind:=CASE b WHEN 91 THEN 'array' ELSE 'object' END;closing:=CASE b WHEN 91 THEN 93 ELSE 125 END;
  WHILE p<n AND get_byte(original,p) IN (9,10,13,32) LOOP p:=p+1; END LOOP;
  IF p<n AND get_byte(original,p)=closing THEN
   RETURN QUERY SELECT jsonb_build_object('kind',kind,CASE kind WHEN 'array' THEN 'items' ELSE 'members' END,children),p+1,count_nodes;RETURN;
  END IF;
  LOOP
   IF jsonb_array_length(children)>=4096 THEN RAISE EXCEPTION 'original JSON container capacity' USING ERRCODE='54000'; END IF;
   IF kind='object' THEN
    SELECT * INTO STRICT child FROM truss.runtime_catalog_report_parse_value(original,p,depth+1);
    IF child.tree->>'kind'<>'string' THEN RAISE EXCEPTION 'JSON object key required' USING ERRCODE='22023'; END IF;
    key_hex:=child.tree->>'utf8Hex';p:=child.next_at;count_nodes:=count_nodes+child.node_count;
    WHILE p<n AND get_byte(original,p) IN (9,10,13,32) LOOP p:=p+1; END LOOP;
    IF p>=n OR get_byte(original,p)<>58 THEN RAISE EXCEPTION 'JSON member colon required' USING ERRCODE='22023'; END IF;p:=p+1;
   END IF;
   SELECT * INTO STRICT child FROM truss.runtime_catalog_report_parse_value(original,p,depth+1);
   p:=child.next_at;count_nodes:=count_nodes+child.node_count;
   IF count_nodes>32768 THEN RAISE EXCEPTION 'original JSON node capacity' USING ERRCODE='54000'; END IF;
   children:=children||jsonb_build_array(CASE kind WHEN 'array' THEN child.tree
     ELSE jsonb_build_object('keyUtf8Hex',key_hex,'node',child.tree) END);
   WHILE p<n AND get_byte(original,p) IN (9,10,13,32) LOOP p:=p+1; END LOOP;
   IF p>=n THEN RAISE EXCEPTION 'closed JSON container required' USING ERRCODE='22023'; END IF;
   b:=get_byte(original,p);p:=p+1;
   IF b=closing THEN EXIT; END IF;
   IF b<>44 THEN RAISE EXCEPTION 'JSON member separator required' USING ERRCODE='22023'; END IF;
  END LOOP;
  RETURN QUERY SELECT jsonb_build_object('kind',kind,CASE kind WHEN 'array' THEN 'items' ELSE 'members' END,children),p,count_nodes;RETURN;
 ELSIF substr(original,p,4)=convert_to('null','UTF8') THEN
  RETURN QUERY SELECT jsonb_build_object('kind','null'),p+3,count_nodes;RETURN;
 ELSIF substr(original,p,4)=convert_to('true','UTF8') THEN
  RETURN QUERY SELECT jsonb_build_object('kind','boolean','value',true),p+3,count_nodes;RETURN;
 ELSIF substr(original,p,5)=convert_to('false','UTF8') THEN
  RETURN QUERY SELECT jsonb_build_object('kind','boolean','value',false),p+4,count_nodes;RETURN;
 ELSE RAISE EXCEPTION 'numeric-free original JSON token required' USING ERRCODE='22023'; END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_catalog_report_parse_value(bytea,int,int) FROM PUBLIC;
CREATE FUNCTION truss.runtime_catalog_report_original_tree(original bytea) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE parsed record; p int;
BEGIN
 SELECT * INTO STRICT parsed FROM truss.runtime_catalog_report_parse_value(original,0,0);p:=parsed.next_at;
 WHILE p<octet_length(original) AND get_byte(original,p) IN (9,10,13,32) LOOP p:=p+1; END LOOP;
 IF p<>octet_length(original) THEN RAISE EXCEPTION 'one complete original JSON value required' USING ERRCODE='22023'; END IF;
 PERFORM truss.runtime_canonical_tree_bytes(parsed.tree);
 RETURN parsed.tree;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_catalog_report_original_tree(bytea) FROM PUBLIC;
CREATE FUNCTION truss.runtime_catalog_report_map_origin_tree(original jsonb, depth int DEFAULT 0) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result jsonb; children jsonb:='[]'::jsonb; child jsonb; mapped jsonb;
BEGIN
 IF original IS NULL OR depth IS NULL OR depth<0 OR depth>128 THEN RAISE EXCEPTION 'bounded tagged origin required' USING ERRCODE='22023'; END IF;
 CASE original->>'kind'
 WHEN 'null' THEN RETURN truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','null'));
 WHEN 'boolean' THEN RETURN truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','boolean','value',original->'value'));
 WHEN 'string' THEN
  result:=truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','string'));
  RETURN jsonb_set(result,'{members}',result->'members'||jsonb_build_array(jsonb_build_object('keyUtf8Hex','74657874','node',original)));
 WHEN 'array' THEN
  FOR child IN SELECT value FROM jsonb_array_elements(original->'items') LOOP
   children:=children||jsonb_build_array(truss.runtime_catalog_report_map_origin_tree(child,depth+1)); END LOOP;
  result:=truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','sequence'));
  RETURN jsonb_set(result,'{members}',result->'members'||jsonb_build_array(jsonb_build_object('keyUtf8Hex','6974656d73','node',jsonb_build_object('kind','array','items',children))));
 WHEN 'object' THEN
  FOR child IN SELECT value FROM jsonb_array_elements(original->'members') ORDER BY decode(value->>'keyUtf8Hex','hex') LOOP
   mapped:=jsonb_build_object('kind','object','members',jsonb_build_array(
    jsonb_build_object('keyUtf8Hex','6b6579','node',jsonb_build_object('kind','string','utf8Hex',child->>'keyUtf8Hex')),
    jsonb_build_object('keyUtf8Hex','76616c7565','node',truss.runtime_catalog_report_map_origin_tree(child->'node',depth+1))));
   children:=children||jsonb_build_array(mapped); END LOOP;
  result:=truss.runtime_catalog_report_native_tree(jsonb_build_object('kind','map'));
  RETURN jsonb_set(result,'{members}',result->'members'||jsonb_build_array(jsonb_build_object('keyUtf8Hex','656e7472696573','node',jsonb_build_object('kind','array','items',children))));
 ELSE RAISE EXCEPTION 'recognized tagged origin required' USING ERRCODE='22023'; END CASE;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_catalog_report_map_origin_tree(jsonb,int) FROM PUBLIC;

-- Selected Draft2020-12 structural vocabulary over tagged values. This is
-- private shape checking against exact archived schemas, not semantic admission.
CREATE FUNCTION truss.runtime_catalog_report_shape_matches(node jsonb, rule jsonb,
 registry jsonb, base_uri text, depth int DEFAULT 0) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE branch jsonb; child jsonb; member jsonb; key_name text; pointer text; uri text;
 resolved jsonb; matches int:=0; raw bytea; length_chars int; i int; kind text;
BEGIN
 IF depth IS NULL OR depth<0 OR node IS NULL OR rule IS NULL THEN RETURN false; END IF;
 IF depth>256 THEN RAISE EXCEPTION 'selected report schema evaluation depth capacity' USING ERRCODE='54000'; END IF;
 IF jsonb_typeof(rule)='boolean' THEN RETURN rule='true'::jsonb; END IF;
 IF jsonb_typeof(rule)<>'object' OR EXISTS(SELECT 1 FROM jsonb_object_keys(rule) k WHERE k<>ALL(ARRAY[
  '$schema','$id','$defs','$ref','title','description','type','properties','required','additionalProperties',
  'items','minItems','maxItems','minLength','maxLength','pattern','const','enum','oneOf','allOf','format'])) THEN
  RAISE EXCEPTION 'unsupported selected report shape vocabulary' USING ERRCODE='0A000'; END IF;
 IF rule ? '$ref' THEN
  uri:=split_part(rule->>'$ref','#',1); IF uri='' THEN uri:=base_uri; END IF;
  resolved:=registry->uri;pointer:=split_part(rule->>'$ref','#',2);
  IF pointer<>'' THEN
   IF left(pointer,1)<>'/' THEN RETURN false; END IF;
   FOREACH key_name IN ARRAY string_to_array(substr(pointer,2),'/') LOOP
    key_name:=replace(replace(key_name,'~1','/'),'~0','~');
    IF jsonb_typeof(resolved)='array' THEN
     IF key_name !~ '^(0|[1-9][0-9]*)$' OR length(key_name)>9 THEN RETURN false; END IF;
     resolved:=resolved->key_name::int;
    ELSE resolved:=resolved->key_name; END IF; END LOOP;
  END IF;
  IF NOT truss.runtime_catalog_report_shape_matches(node,resolved,registry,uri,depth+1) THEN RETURN false; END IF;
 END IF;
 IF rule ? 'oneOf' THEN
  FOR branch IN SELECT value FROM jsonb_array_elements(rule->'oneOf') LOOP
   IF truss.runtime_catalog_report_shape_matches(node,branch,registry,base_uri,depth+1) THEN matches:=matches+1; END IF; END LOOP;
  IF matches<>1 THEN RETURN false; END IF;
 END IF;
 IF rule ? 'allOf' THEN
  FOR branch IN SELECT value FROM jsonb_array_elements(rule->'allOf') LOOP
   IF NOT truss.runtime_catalog_report_shape_matches(node,branch,registry,base_uri,depth+1) THEN RETURN false; END IF; END LOOP;
 END IF;
 IF rule ? 'const' AND node IS DISTINCT FROM truss.runtime_catalog_report_native_tree(rule->'const') THEN RETURN false; END IF;
 IF rule ? 'enum' AND NOT EXISTS(SELECT 1 FROM jsonb_array_elements(rule->'enum') e
  WHERE node=truss.runtime_catalog_report_native_tree(e)) THEN RETURN false; END IF;
 kind:=node->>'kind';
 IF rule ? 'type' AND rule->>'type' IS DISTINCT FROM kind THEN RETURN false; END IF;
 IF kind='object' THEN
  FOR branch IN SELECT value FROM jsonb_array_elements(coalesce(rule->'required','[]'::jsonb)) LOOP
   IF NOT EXISTS(SELECT 1 FROM jsonb_array_elements(node->'members') m WHERE m->>'keyUtf8Hex'=encode(convert_to(branch #>> '{}','UTF8'),'hex')) THEN RETURN false; END IF;
  END LOOP;
  FOR member IN SELECT value FROM jsonb_array_elements(node->'members') LOOP
   raw:=decode(member->>'keyUtf8Hex','hex');
   -- Schema property names are textual. An unmatched logical NUL key is an
   -- additional property; it is never decoded into PostgreSQL text.
   IF position(decode('00','hex') IN raw)>0 THEN
    IF rule->'additionalProperties'='false'::jsonb THEN RETURN false; END IF;CONTINUE;
   END IF;
   key_name:=convert_from(raw,'UTF8');branch:=rule->'properties'->key_name;
   IF branch IS NOT NULL THEN
    IF NOT truss.runtime_catalog_report_shape_matches(member->'node',branch,registry,base_uri,depth+1) THEN RETURN false; END IF;
   ELSIF rule->'additionalProperties'='false'::jsonb THEN RETURN false;
   ELSIF jsonb_typeof(rule->'additionalProperties')='object' THEN
    IF NOT truss.runtime_catalog_report_shape_matches(member->'node',rule->'additionalProperties',registry,base_uri,depth+1) THEN RETURN false; END IF;
   END IF;
  END LOOP;
 ELSIF kind='array' THEN
  IF rule ? 'minItems' AND jsonb_array_length(node->'items')<(rule->>'minItems')::int THEN RETURN false; END IF;
  IF rule ? 'maxItems' AND jsonb_array_length(node->'items')>(rule->>'maxItems')::int THEN RETURN false; END IF;
  IF rule ? 'items' THEN
   FOR child IN SELECT value FROM jsonb_array_elements(node->'items') LOOP
    IF NOT truss.runtime_catalog_report_shape_matches(child,rule->'items',registry,base_uri,depth+1) THEN RETURN false; END IF; END LOOP;
  END IF;
 ELSIF kind='string' THEN
  raw:=decode(node->>'utf8Hex','hex');length_chars:=0;
  IF octet_length(raw)>0 THEN
   FOR i IN 0..octet_length(raw)-1 LOOP IF get_byte(raw,i)<128 OR get_byte(raw,i)>=192 THEN length_chars:=length_chars+1; END IF;END LOOP;
  END IF;
  IF rule ? 'minLength' AND length_chars<(rule->>'minLength')::int THEN RETURN false; END IF;
  IF rule ? 'maxLength' AND length_chars>(rule->>'maxLength')::int THEN RETURN false; END IF;
  IF rule ? 'pattern' THEN
   IF position(decode('00','hex') IN raw)>0 THEN RETURN false; END IF;
   IF convert_from(raw,'UTF8') !~ (rule->>'pattern') THEN RETURN false; END IF;
  END IF;
 END IF;
 RETURN true;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_catalog_report_shape_matches(jsonb,jsonb,jsonb,text,int) FROM PUBLIC;

CREATE FUNCTION truss.runtime_write_catalog_report_candidate(
 expected_writer text,expected_ordinal text,expected_generation text,
 registration_identity text,original_registration bytea,lifecycle_policy bytea,index_policy bytea)
RETURNS TABLE(writer_xid text,operation_ordinal text,effect_generation text,
 report_utf8_hex text,scope text,accepted_report_qualified boolean)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET bytea_output='hex' AS $$
DECLARE op truss.row_home_operation%ROWTYPE; current_op truss.row_home_operation%ROWTYPE;
 context jsonb; input jsonb; registration jsonb; source record; before_graph record; after_graph record;
 revision int; documents jsonb; counts jsonb; lifecycle jsonb; indexes jsonb;
 origin jsonb; execution jsonb; execution_tree jsonb; origin_envelope jsonb; journal_envelope jsonb; fields jsonb; tree jsonb; members jsonb; assertion_tree jsonb;
 assertion_digest text; assertions jsonb; member jsonb; pin_name text; pin jsonb;
 original_report bytea; returned_report bytea; recipe_bytes bytea; recipe jsonb; artifact bytea; selected_artifact_identity text; profile_rows jsonb; final_profile_rows jsonb; identities text[]; catalog_before jsonb; catalog_after jsonb; table_name text; table_rows jsonb; schema_registry jsonb:='{}'::jsonb; schema_name text; schema_value jsonb; report_tree jsonb; before_resources jsonb; after_resources jsonb; original_registration_id bigint; count_rows bigint;
BEGIN
 IF expected_writer IS NULL OR expected_ordinal IS NULL OR expected_generation IS NULL
  OR registration_identity IS NULL OR octet_length(registration_identity) NOT BETWEEN 1 AND 4096
  OR original_registration IS NULL OR octet_length(original_registration) NOT BETWEEN 1 AND 65536 THEN
  RAISE EXCEPTION 'bounded original candidate registration required' USING ERRCODE='22023'; END IF;
 PERFORM truss.runtime_require_catalog_observation(expected_writer,expected_ordinal,expected_generation);
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.operation_ordinal::text=expected_ordinal
   AND o.phase='admitted' AND o.operation_kind='catalog-acceptance' FOR UPDATE;
 context:=convert_from(op.original_context_bytes,'UTF8')::jsonb;
 IF context->>'interfaceVersion' IS DISTINCT FROM 'truss-native-operation-context/0.4' THEN
  RAISE EXCEPTION 'original configured candidate context required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT before_graph FROM truss.runtime_collect_configured_catalog_graph();
 -- This registration is explicitly candidate-only. It is NOT one of the four
 -- original production authority sources, even when all profile pins match.
 PERFORM truss.runtime_require_unique_source_json(convert_from(original_registration,'UTF8')::json);
 registration:=convert_from(original_registration,'UTF8')::jsonb;
 IF jsonb_typeof(registration) IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(registration))<>8
  OR NOT registration ?& ARRAY['interfaceVersion','scope','layoutProfile','reportProfile',
      'captureProfile','originMappingProfile','enforcementProfile','composition']
  OR registration->>'interfaceVersion' IS DISTINCT FROM 'truss-catalog-report-candidate-registration/0.1'
  OR registration->>'scope' IS DISTINCT FROM 'administrative_rollback_only_report_write' THEN
  RAISE EXCEPTION 'explicit administrative candidate registration required' USING ERRCODE='55000'; END IF;
 FOREACH pin_name IN ARRAY ARRAY['layoutProfile','reportProfile','captureProfile','originMappingProfile','enforcementProfile'] LOOP
  pin:=registration->pin_name;
  IF jsonb_typeof(pin) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(pin))<>3
   OR NOT pin ?& ARRAY['identity','version','sha256']
   OR EXISTS(SELECT 1 FROM jsonb_each(pin) e WHERE jsonb_typeof(e.value) IS DISTINCT FROM 'string' OR octet_length(e.value #>> '{}') NOT BETWEEN 1 AND 4096)
   OR pin->>'sha256' !~ '^[0-9a-f]{64}$' THEN
   RAISE EXCEPTION 'complete candidate profile pins required' USING ERRCODE='55000'; END IF;
 END LOOP;
 IF registration->'enforcementProfile' IS DISTINCT FROM jsonb_build_object(
  'identity','truss-catalog-enforcement-projection','version','0.1.0',
  'sha256','678e52ea00fa984b19162441a33b33ab3d822b58f8ae2c69195dc1d5d658c4b1') THEN
  RAISE EXCEPTION 'selected candidate enforcement projection required' USING ERRCODE='55000'; END IF;
 SELECT count(*) INTO count_rows FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND convert_to(a.artifact_identity,'UTF8')=convert_to(registration_identity,'UTF8');
 IF count_rows<>1 THEN RAISE EXCEPTION 'unique original candidate registration archive required' USING ERRCODE='55000'; END IF;
 SELECT a.archive_row_id INTO STRICT original_registration_id FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
   AND convert_to(a.artifact_identity,'UTF8')=convert_to(registration_identity,'UTF8')
   AND a.artifact_bytes=original_registration AND a.artifact_sha256=sha256(original_registration)
   AND a.artifact_identity_sha256=sha256(convert_to(registration_identity,'UTF8')) FOR SHARE NOWAIT;
 IF registration->'composition' IS DISTINCT FROM jsonb_build_object('identity','packages/python/src/truss/_profiles/catalog-report-composition-candidate.json','sha256','3f5f83a5b827451bdf29a018eca85b0bdac3811a37ec8efcbadafc1a79fd10fe') THEN
  RAISE EXCEPTION 'recognized full candidate composition recipe required' USING ERRCODE='55000'; END IF;
 identities:=ARRAY[registration_identity,'packages/python/src/truss/_profiles/catalog-report-composition-candidate.json'];
 IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
  AND a.artifact_role='input' AND a.artifact_identity='packages/python/src/truss/_profiles/catalog-report-composition-candidate.json')<>1 THEN
  RAISE EXCEPTION 'unique original candidate recipe archive required' USING ERRCODE='55000'; END IF;
 SELECT a.artifact_bytes INTO STRICT recipe_bytes FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity='packages/python/src/truss/_profiles/catalog-report-composition-candidate.json'
   AND a.artifact_sha256=sha256(a.artifact_bytes) AND a.artifact_sha256=decode('3f5f83a5b827451bdf29a018eca85b0bdac3811a37ec8efcbadafc1a79fd10fe','hex')
   AND a.artifact_identity_sha256=sha256(convert_to(a.artifact_identity,'UTF8')) FOR SHARE NOWAIT;
 recipe:=convert_from(recipe_bytes,'UTF8')::jsonb;
 FOREACH pin_name IN ARRAY ARRAY['reportProfile','captureProfile','originMappingProfile','enforcementProfile'] LOOP
  selected_artifact_identity:=recipe->'profileArtifacts'->pin_name->>'path';
  identities:=array_append(identities,selected_artifact_identity);
  IF (SELECT count(*) FROM truss.installation_archive a WHERE a.installation_id=context->>'installationId'
    AND a.artifact_role='input' AND convert_to(a.artifact_identity,'UTF8')=convert_to(selected_artifact_identity,'UTF8'))<>1 THEN
   RAISE EXCEPTION 'unique full candidate profile archive required' USING ERRCODE='55000'; END IF;
  SELECT a.artifact_bytes INTO STRICT artifact FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input'
    AND convert_to(a.artifact_identity,'UTF8')=convert_to(selected_artifact_identity,'UTF8')
    AND a.artifact_sha256=sha256(a.artifact_bytes)
    AND a.artifact_sha256=decode(recipe->'profileArtifacts'->pin_name->>'sha256','hex')
    AND a.artifact_identity_sha256=sha256(convert_to(selected_artifact_identity,'UTF8')) FOR SHARE NOWAIT;
  pin:=convert_from(artifact,'UTF8')::jsonb;
  IF registration->pin_name IS DISTINCT FROM jsonb_build_object('identity',pin->>'identity','version',pin->>'version',
     'sha256',encode(sha256(artifact),'hex'))
   OR (pin_name='captureProfile' AND encode(artifact,'hex') IS DISTINCT FROM context->>'assertedOriginCaptureProfileHex') THEN
   RAISE EXCEPTION 'original full candidate profile correspondence required' USING ERRCODE='55000'; END IF;
 END LOOP;
 before_resources:=truss.runtime_select_catalog_report_resources(expected_writer,expected_ordinal,expected_generation,
  (SELECT encode(c.admission_profile_bytes,'hex') FROM truss.operation_configuration c
   WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal));
 FOREACH schema_name IN ARRAY ARRAY['exact-value-v0.1.schema.json','history-record-v0.1.schema.json','history-event-v0.1.schema.json',
  'acceptance-input-v0.1.schema.json','acceptance-rejection-v0.1.schema.json','enforcement-report-v0.1.schema.json',
  'acceptance-report-v0.1.schema.json','history-retain-payload-v0.1.proposal.schema.json','history-event-v0.2.proposal.schema.json',
  'acceptance-report-v0.3.proposal.schema.json'] LOOP
  selected_artifact_identity:='packages/python/src/truss/_report_schemas/'||schema_name;
  SELECT convert_from(a.artifact_bytes,'UTF8')::jsonb INTO STRICT schema_value FROM truss.installation_archive a
   WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=selected_artifact_identity;
  IF schema_registry ? (schema_value->>'$id') THEN RAISE EXCEPTION 'unique selected report schema identity required' USING ERRCODE='55000'; END IF;
  schema_registry:=schema_registry||jsonb_build_object(schema_value->>'$id',schema_value);
  identities:=array_append(identities,selected_artifact_identity);
 END LOOP;
 SELECT jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id) INTO profile_rows FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=ANY(identities);
 catalog_before:='{}'::jsonb;
 FOREACH table_name IN ARRAY ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text COLLATE "C"),''[]''::jsonb) FROM truss.%I t',table_name) INTO table_rows;
  catalog_before:=jsonb_set(catalog_before,ARRAY[table_name],table_rows);
 END LOOP;
 IF octet_length(catalog_before::text)>4194304 THEN RAISE EXCEPTION 'candidate catalog comparison capacity' USING ERRCODE='54000'; END IF;
 PERFORM truss.runtime_require_catalog_input(op.original_input_bytes);
 input:=convert_from(op.original_input_bytes,'UTF8')::jsonb;
 IF registration->'layoutProfile' IS DISTINCT FROM input->'layoutProfile' THEN
  RAISE EXCEPTION 'original input layout candidate correspondence required' USING ERRCODE='55000'; END IF;
 IF (SELECT count(*) FROM truss.schema_rev WHERE rev>0)<>1
  OR NOT EXISTS(SELECT 1 FROM truss.schema_head WHERE id=1 AND rev=0)
  OR EXISTS(SELECT 1 FROM truss.catalog_acceptance_report) THEN
  RAISE EXCEPTION 'unpublished first revision candidate required' USING ERRCODE='55000'; END IF;
 SELECT rev INTO STRICT revision FROM truss.schema_rev WHERE rev>0;
 SELECT * INTO STRICT source FROM truss.runtime_collect_catalog_source_candidate(
  op.admitted_candidate_bytes,decode(convert_from(op.admitted_candidate_bytes,'UTF8')::jsonb->>'declarationsUtf8Hex','hex'));
 PERFORM * FROM truss.runtime_collect_new_catalog_inventory(revision);
 SELECT coalesce(jsonb_agg(to_jsonb(d) ORDER BY d.ord::int),'[]'::jsonb) INTO documents
  FROM truss.runtime_collect_report_documents(revision) d;
 SELECT to_jsonb(c) INTO STRICT counts FROM truss.runtime_collect_new_catalog_counts(revision) c;
 lifecycle:=truss.runtime_collect_fresh_catalog_lifecycle(expected_writer,expected_ordinal,expected_generation,revision,lifecycle_policy);
 indexes:=truss.runtime_collect_absent_binding_index_declarations(expected_writer,expected_ordinal,expected_generation,revision,index_policy);
 origin:=truss.runtime_catalog_report_original_tree(decode(context->>'assertedOriginUtf8Hex','hex'));
 execution:=jsonb_build_object('installationId',context->>'installationId','sourceEpoch',context->>'sourceEpoch',
  'origin',jsonb_build_object('databaseRole',context->>'actingUser'),
  'journalOrigin',jsonb_build_object('databaseRole',context->>'actingUser'),
  'originMappingProfile',registration->'originMappingProfile','captureProfile',registration->'captureProfile',
  'contextEvidence',jsonb_build_object('identity','truss.original-native-operation-context4/'||expected_writer||'/'||expected_ordinal,
   'bytesBase64',replace(encode(op.original_context_bytes,'base64'),chr(10),''),
   'sha256',encode(sha256(op.original_context_bytes),'hex')));
 execution_tree:=truss.runtime_catalog_report_native_tree(execution);
 origin_envelope:=truss.runtime_catalog_report_native_tree(jsonb_build_object('databaseRole',context->>'actingUser'));
 journal_envelope:=jsonb_set(origin_envelope,'{members}',origin_envelope->'members'||jsonb_build_array(jsonb_build_object(
  'keyUtf8Hex','6173736572746564','node',truss.runtime_catalog_report_map_origin_tree(origin))));
 origin_envelope:=jsonb_set(origin_envelope,'{members}',origin_envelope->'members'||jsonb_build_array(jsonb_build_object(
  'keyUtf8Hex','6173736572746564','node',origin)));
 SELECT jsonb_agg(CASE m->>'keyUtf8Hex' WHEN '6f726967696e' THEN jsonb_set(m,'{node}',origin_envelope)
  WHEN '6a6f75726e616c4f726967696e' THEN jsonb_set(m,'{node}',journal_envelope) ELSE m END)
  INTO members FROM jsonb_array_elements(execution_tree->'members') m;
 execution_tree:=jsonb_set(execution_tree,'{members}',members);
 fields:=jsonb_build_object('interfaceVersion','truss-acceptance-report/0.3.0-proposal',
  'reportProfile',registration->'reportProfile','rev',revision::text,
  'acceptedInput',input,'documents',documents,'counts',jsonb_build_object(
   'typesAdded',counts->'types_added','propertiesAdded',counts->'properties_added','keysAdded',counts->'keys_added',
   'relationshipsAdded',counts->'relationships_added','endpointsAdded',counts->'endpoints_added','elementsRetired',counts->'elements_retired'),
  'provisional','[]'::jsonb,'rebinds','[]'::jsonb,'pending_indexes',indexes->'declaredJobs',
  'lifecycleProfile',lifecycle->'lifecycleProfile','reactivations',lifecycle->'reactivations');
 tree:=truss.runtime_catalog_report_native_tree(fields); members:=tree->'members'||jsonb_build_array(jsonb_build_object('keyUtf8Hex','6f726967696e616c457865637574696f6e','node',execution_tree));
 FOR member IN SELECT value FROM jsonb_array_elements(source.host_sources->'members') LOOP
  IF member->>'keyUtf8Hex'=encode(convert_to('assertionEntries','UTF8'),'hex') THEN assertion_tree:=member->'node';
  ELSE members:=members||jsonb_build_array(member); END IF;
 END LOOP;
 IF assertion_tree IS NULL OR assertion_tree->>'kind' IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'original complete candidate assertion inventory required' USING ERRCODE='55000'; END IF;
 FOR member IN SELECT value FROM jsonb_array_elements(assertion_tree->'items') LOOP
  IF member->>'kind' IS DISTINCT FROM 'object' OR jsonb_typeof(member->'members') IS DISTINCT FROM 'array'
   OR jsonb_array_length(member->'members')<>6
   OR (SELECT count(*) FROM jsonb_array_elements(member->'members') m WHERE decode(m->>'keyUtf8Hex','hex')
    IN (convert_to('assertion','UTF8'),convert_to('source','UTF8'),convert_to('ruleName','UTF8'),convert_to('ruleNameOrigin','UTF8'),convert_to('enforcement','UTF8'),convert_to('reason','UTF8')))<>6
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(member->'members') m WHERE m->>'keyUtf8Hex'=encode(convert_to('enforcement','UTF8'),'hex')
    AND m->'node'=jsonb_build_object('kind','string','utf8Hex',encode(convert_to('none','UTF8'),'hex')))
   OR NOT EXISTS(SELECT 1 FROM jsonb_array_elements(member->'members') m WHERE m->>'keyUtf8Hex'=encode(convert_to('reason','UTF8'),'hex')
    AND m->'node'=jsonb_build_object('kind','string','utf8Hex',encode(convert_to('unqualified','UTF8'),'hex'))) THEN
   RAISE EXCEPTION 'selected six-field none unqualified assertion projection required' USING ERRCODE='55000'; END IF;
 END LOOP;
 assertion_digest:=encode(sha256(convert_to('truss-canonical/0.1.0'||chr(10)||'truss-catalog-assertion-inventory/0.1.0'||chr(10),'UTF8')
   ||truss.runtime_canonical_tree_bytes(assertion_tree)),'hex');
 assertions:=truss.runtime_catalog_report_native_tree(jsonb_build_object('interfaceVersion','truss-enforcement-report/0.1.0',
  'catalogRevision',revision::text,'reportProfile',registration->'enforcementProfile','layoutProfile',input->'layoutProfile',
  'scope',jsonb_build_object('kind','complete'),'assertionInventorySha256',assertion_digest));
 assertions:=jsonb_set(assertions,'{members}',assertions->'members'||jsonb_build_array(jsonb_build_object(
  'keyUtf8Hex',encode(convert_to('entries','UTF8'),'hex'),'node',assertion_tree)));
 members:=members||jsonb_build_array(jsonb_build_object('keyUtf8Hex',encode(convert_to('assertions','UTF8'),'hex'),'node',assertions));
 IF jsonb_array_length(members)<>19 THEN RAISE EXCEPTION 'complete nineteen-field candidate report required' USING ERRCODE='55000'; END IF;
 report_tree:=jsonb_build_object('kind','object','members',members);
 original_report:=truss.runtime_canonical_tree_bytes(report_tree);
 IF NOT truss.runtime_catalog_report_shape_matches(report_tree,schema_registry->'urn:truss:proposal:acceptance-report:0.3.0',
  schema_registry,'urn:truss:proposal:acceptance-report:0.3.0') THEN
  RAISE EXCEPTION 'complete selected candidate report shape required' USING ERRCODE='22023'; END IF;
 -- Only an administrative algorithm fixture calls this. No public assembly
 -- selection, accepted result, head transition or commit seal is issued here.
 INSERT INTO truss.catalog_acceptance_report(rev,report_bytes) VALUES(revision,original_report)
  RETURNING report_bytes INTO STRICT returned_report;
 IF returned_report IS DISTINCT FROM original_report OR NOT EXISTS(
  SELECT 1 FROM truss.catalog_acceptance_report r WHERE r.rev=revision AND r.report_bytes=original_report)
  OR (SELECT count(*) FROM truss.catalog_acceptance_report)<>1 THEN
  RAISE EXCEPTION 'original report insert and independent byte readback required' USING ERRCODE='55000'; END IF;
 SELECT jsonb_agg(to_jsonb(a) ORDER BY a.archive_row_id) INTO final_profile_rows FROM truss.installation_archive a
  WHERE a.installation_id=context->>'installationId' AND a.artifact_role='input' AND a.artifact_identity=ANY(identities);
 catalog_after:='{}'::jsonb;
 FOREACH table_name IN ARRAY ARRAY['schema_head','schema_rev','schema_doc','type_def','prop_def','key_def','rel_def','relationship_lineage','rel_endpoint'] LOOP
  EXECUTE format('SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY to_jsonb(t)::text COLLATE "C"),''[]''::jsonb) FROM truss.%I t',table_name) INTO table_rows;
  catalog_after:=jsonb_set(catalog_after,ARRAY[table_name],table_rows);
 END LOOP;
 after_resources:=truss.runtime_select_catalog_report_resources(expected_writer,expected_ordinal,(op.effect_generation+1)::text,
  (SELECT encode(c.admission_profile_bytes,'hex') FROM truss.operation_configuration c
   WHERE c.original_writer_xid=op.original_writer_xid AND c.operation_ordinal=op.operation_ordinal));
 IF after_resources IS DISTINCT FROM before_resources THEN
  RAISE EXCEPTION 'original complete report resource final cut required' USING ERRCODE='55000'; END IF;
 SELECT * INTO STRICT after_graph FROM truss.runtime_collect_configured_catalog_graph();
 SELECT o.* INTO STRICT current_op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=pg_current_xact_id_if_assigned() AND o.operation_ordinal=op.operation_ordinal;
 IF current_op.effect_generation<>op.effect_generation+1
  OR catalog_after IS DISTINCT FROM catalog_before OR final_profile_rows IS DISTINCT FROM profile_rows
  OR (to_jsonb(current_op)-'effect_generation') IS DISTINCT FROM (to_jsonb(op)-'effect_generation')
  OR (to_jsonb(after_graph)-'effect_generation') IS DISTINCT FROM (to_jsonb(before_graph)-'effect_generation')
  OR NOT EXISTS(SELECT 1 FROM truss.installation_archive a WHERE a.archive_row_id=original_registration_id
    AND a.artifact_bytes=original_registration AND a.artifact_sha256=sha256(original_registration)) THEN
  RAISE EXCEPTION 'original candidate report final source cut required' USING ERRCODE='55000'; END IF;
 RETURN QUERY SELECT op.original_writer_xid::text,op.operation_ordinal::text,current_op.effect_generation::text,
  encode(original_report,'hex'),'administrative_rollback_only_report_write'::text,false;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_write_catalog_report_candidate(text,text,text,text,bytea,bytea,bytea) FROM PUBLIC;
