-- Integrated native event/custody implementation, PostgreSQL16 component.
-- PA01–04 supplies protected original context/subject/profile admission.
-- No public grant, installed readiness, row seal or commit-barrier replacement.
CREATE FUNCTION truss.row_touch_integer_original(value bytea) RETURNS bigint
LANGUAGE plpgsql IMMUTABLE STRICT SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE result numeric:=0; i int; size int:=octet_length(value);
BEGIN
 IF size NOT IN (4,8) THEN RAISE EXCEPTION 'native integer width required' USING ERRCODE='22023';END IF;
 FOR i IN 0..size-1 LOOP result:=result*256+get_byte(value,i);END LOOP;
 IF get_byte(value,0)>=128 THEN result:=result-power(256::numeric,size);END IF;
 RETURN result::bigint;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_integer_original(bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_image_cells_original(kind text,image bytea) RETURNS bytea[]
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE prefix bytea; oids int[]; required boolean[]; cells bytea[]:=ARRAY[]::bytea[];
 pos int; i int; actual_oid bigint; length int; value bytea;
BEGIN
 IF image IS NULL OR octet_length(image) NOT BETWEEN 1 AND 8388608 THEN
  RAISE EXCEPTION 'bounded original native image required' USING ERRCODE='22023';END IF;
 prefix:=convert_to('truss.row-image.'||kind||'/0.1','UTF8')||decode('00','hex');
 CASE kind
 WHEN 'state' THEN oids:=ARRAY[20,25,20,23,20,23,23,23,20,17,17,17,17];required:=ARRAY[true,true,false,false,false,false,true,true,true,true,true,true,true];
 WHEN 'node' THEN oids:=ARRAY[20,20,20,25,20,25,17,25,17,17];required:=ARRAY[true,true,false,true,false,false,false,true,true,true];
 WHEN 'scalar' THEN oids:=ARRAY[20,20,25,25,16,1700,25,17,25,1184,17,17,17];required:=ARRAY[true,true,true,false,false,false,false,false,false,false,false,true,true];
 ELSE RAISE EXCEPTION 'original image family required' USING ERRCODE='22023';
 END CASE;
 pos:=octet_length(prefix)+1;
 IF substring(image FROM 1 FOR pos-1) IS DISTINCT FROM prefix OR octet_length(image)<pos+3
  OR truss.row_touch_integer_original(substring(image FROM pos FOR 4))<>array_length(oids,1) THEN
  RAISE EXCEPTION 'complete original native image domain required' USING ERRCODE='22023';END IF;
 pos:=pos+4;
 FOR i IN 1..array_length(oids,1) LOOP
  IF octet_length(image)<pos+7 THEN RAISE EXCEPTION 'complete native cell header required' USING ERRCODE='22023';END IF;
  actual_oid:=truss.row_touch_integer_original(substring(image FROM pos FOR 4));
  length:=truss.row_touch_integer_original(substring(image FROM pos+4 FOR 4));pos:=pos+8;
  IF actual_oid<>oids[i] OR length< -1 OR (length= -1 AND required[i]) THEN
   RAISE EXCEPTION 'original native cell type/null profile required' USING ERRCODE='22023';END IF;
  IF length= -1 THEN cells:=array_append(cells,NULL);CONTINUE;END IF;
  IF length>octet_length(image)-pos+1 OR (oids[i] IN (20,1184) AND length<>8)
   OR (oids[i]=23 AND length<>4) OR (oids[i]=16 AND length<>1) THEN
   RAISE EXCEPTION 'original native cell width required' USING ERRCODE='22023';END IF;
  value:=substring(image FROM pos FOR length);pos:=pos+length;
  IF oids[i]=16 AND get_byte(value,0) NOT IN (0,1) THEN RAISE EXCEPTION 'native boolean required' USING ERRCODE='22023';END IF;
  IF oids[i]=25 THEN PERFORM convert_from(value,'UTF8');END IF;
  cells:=array_append(cells,value);
 END LOOP;
 IF pos<>octet_length(image)+1 THEN RAISE EXCEPTION 'native trailing image bytes refused' USING ERRCODE='22023';END IF;
 RETURN cells;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_image_cells_original(text,bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_json_original(original bytea) RETURNS jsonb
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE text_value text;
BEGIN
 IF original IS NULL OR octet_length(original) NOT BETWEEN 1 AND 8388608 THEN
  RAISE EXCEPTION 'bounded original custody JSON required' USING ERRCODE='22023';END IF;
 text_value:=convert_from(original,'UTF8');
 IF NOT (text_value IS JSON OBJECT WITH UNIQUE KEYS) THEN
  RAISE EXCEPTION 'complete original unique-member custody JSON required' USING ERRCODE='22023';END IF;
 RETURN text_value::jsonb;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_json_original(bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_artifact_original(value jsonb) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE original bytea;
BEGIN
 IF jsonb_typeof(value) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(value))<>3
  OR NOT value ?& ARRAY['identity','bytesBase64','sha256'] OR EXISTS(SELECT 1 FROM jsonb_each(value) e WHERE jsonb_typeof(e.value)<>'string')
  OR octet_length(value->>'identity') NOT BETWEEN 1 AND 65536
  OR value->>'sha256' !~ '^[0-9a-f]{64}$'
  OR octet_length(value->>'bytesBase64') NOT BETWEEN 1 AND 11184812
  OR value->>'bytesBase64' !~ '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$' THEN
  RAISE EXCEPTION 'complete original artifact required' USING ERRCODE='22023';END IF;
 original:=decode(value->>'bytesBase64','base64');
 IF octet_length(original) NOT BETWEEN 1 AND 8388608
  OR encode(sha256(original),'hex') IS DISTINCT FROM value->>'sha256' THEN
  RAISE EXCEPTION 'original artifact byte correspondence required' USING ERRCODE='22023';END IF;
 RETURN original;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_artifact_original(jsonb) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_scope_original(original bytea) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE scope jsonb; item jsonb; cells bytea[]; seen text[]:=ARRAY[]::text[];
 key text; kind text; image bytea; state_id bigint; node_id bigint;
 node_states jsonb:='{}'::jsonb;
BEGIN
 scope:=truss.row_touch_json_original(original);
 IF (SELECT count(*) FROM jsonb_object_keys(scope))<>2 OR NOT scope ?& ARRAY['interfaceVersion','images']
  OR scope->>'interfaceVersion' IS DISTINCT FROM 'truss-native-row-image-scope/0.1'
  OR jsonb_typeof(scope->'images') IS DISTINCT FROM 'array' OR jsonb_array_length(scope->'images')>1024 THEN
  RAISE EXCEPTION 'original selected native image scope required' USING ERRCODE='0A000';END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(scope->'images') LOOP
  IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(item))<>2
   OR NOT item ?& ARRAY['kind','imageHex'] OR jsonb_typeof(item->'kind')<>'string'
   OR jsonb_typeof(item->'imageHex')<>'string' OR item->>'imageHex' !~ '^([0-9a-f]{2})+$'
   OR octet_length(item->>'imageHex')>16777216 THEN RAISE EXCEPTION 'original scope member required' USING ERRCODE='22023';END IF;
  kind:=item->>'kind';image:=decode(item->>'imageHex','hex');cells:=truss.row_touch_image_cells_original(kind,image);
  state_id:=truss.row_touch_integer_original(cells[1]);
  IF state_id<=0 THEN RAISE EXCEPTION 'positive original state required' USING ERRCODE='22023';END IF;
  node_id:=NULL;IF kind<>'state' THEN node_id:=truss.row_touch_integer_original(cells[2]);IF node_id<=0 THEN RAISE EXCEPTION 'positive original node required' USING ERRCODE='22023';END IF;END IF;
  IF kind='node' THEN
   IF node_states ? node_id::text AND node_states->>node_id::text IS DISTINCT FROM state_id::text THEN
    RAISE EXCEPTION 'original node identity belongs to one state' USING ERRCODE='22023';END IF;
   node_states:=node_states||jsonb_build_object(node_id::text,state_id::text);
  END IF;
  key:=kind||'/'||state_id::text||'/'||coalesce(node_id::text,'');
  IF key=ANY(seen) THEN RAISE EXCEPTION 'duplicate original scope member' USING ERRCODE='22023';END IF;
  seen:=array_append(seen,key);
 END LOOP;
 -- Parent correspondence is checked for every member, including disconnected ones.
 FOR item IN SELECT value FROM jsonb_array_elements(scope->'images') LOOP
  kind:=item->>'kind';cells:=truss.row_touch_image_cells_original(kind,decode(item->>'imageHex','hex'));
  state_id:=truss.row_touch_integer_original(cells[1]);
  IF kind<>'state' AND NOT ('state/'||state_id::text||'/'=ANY(seen)) THEN RAISE EXCEPTION 'complete retained state required' USING ERRCODE='22023';END IF;
  IF kind='scalar' AND NOT ('node/'||state_id::text||'/'||truss.row_touch_integer_original(cells[2])::text=ANY(seen)) THEN RAISE EXCEPTION 'complete retained node required' USING ERRCODE='22023';END IF;
 END LOOP;
 RETURN scope;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_scope_original(bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_state_from_image_original(image bytea) RETURNS truss.row_home_state
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE c bytea[]; result truss.row_home_state%ROWTYPE;
BEGIN
 c:=truss.row_touch_image_cells_original('state',image);
 result.state_id:=truss.row_touch_integer_original(c[1]);result.owner_kind:=convert_from(c[2],'UTF8');
 result.object_id:=truss.row_touch_integer_original(c[3]);result.object_type_id:=truss.row_touch_integer_original(c[4]);
 result.edge_id:=truss.row_touch_integer_original(c[5]);result.relationship_type_id:=truss.row_touch_integer_original(c[6]);
 result.property_owner_type_id:=truss.row_touch_integer_original(c[7]);result.property_id:=truss.row_touch_integer_original(c[8]);
 result.root_node_id:=truss.row_touch_integer_original(c[9]);result.definition_bytes:=c[10];result.home_profile_bytes:=c[11];
 result.value_profile_bytes:=c[12];result.source_bytes:=c[13];
 IF truss.row_image_state_original(result) IS DISTINCT FROM image THEN RAISE EXCEPTION 'retained complete state parity required' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_state_from_image_original(bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_node_from_image_original(image bytea) RETURNS truss.row_home_node
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE c bytea[]; result truss.row_home_node%ROWTYPE;
BEGIN
 c:=truss.row_touch_image_cells_original('node',image);
 result.state_id:=truss.row_touch_integer_original(c[1]);result.node_id:=truss.row_touch_integer_original(c[2]);result.parent_node_id:=truss.row_touch_integer_original(c[3]);
 result.slot_kind:=convert_from(c[4],'UTF8');result.sequence_ordinal:=truss.row_touch_integer_original(c[5]);result.map_key:=convert_from(c[6],'UTF8');
 result.record_field_identity_bytes:=c[7];result.value_kind:=convert_from(c[8],'UTF8');result.definition_bytes:=c[9];result.source_bytes:=c[10];
 IF truss.row_image_node_original(result) IS DISTINCT FROM image THEN RAISE EXCEPTION 'retained complete node parity required' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_node_from_image_original(bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_frame_original(original bytea,generation bigint) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb; item jsonb; scope jsonb; selected jsonb; seen text[]:=ARRAY[]::text[]; counter text;
BEGIN
 plan:=truss.row_touch_json_original(original);
 IF (SELECT count(*) FROM jsonb_object_keys(plan))<>2 OR NOT plan ?& ARRAY['interfaceVersion','frames']
  OR plan->>'interfaceVersion' IS DISTINCT FROM 'truss-native-row-image-frames/0.1'
  OR jsonb_typeof(plan->'frames') IS DISTINCT FROM 'array' OR jsonb_array_length(plan->'frames') NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'original native event frames required' USING ERRCODE='0A000';END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(plan->'frames') LOOP
  IF jsonb_typeof(item) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(item))<>3
   OR NOT item ?& ARRAY['effectGeneration','scope','event'] OR jsonb_typeof(item->'effectGeneration') IS DISTINCT FROM 'string'
   OR item->>'effectGeneration' !~ '^(0|[1-9][0-9]{0,18})$'
   OR (item->>'effectGeneration')::numeric>9223372036854775807 THEN
   RAISE EXCEPTION 'original event frame generation required' USING ERRCODE='22023';END IF;
  counter:=item->>'effectGeneration';
  IF counter=ANY(seen) THEN RAISE EXCEPTION 'duplicate event frame generation' USING ERRCODE='22023';END IF;
  seen:=array_append(seen,counter);
  IF jsonb_typeof(item->'event') IS DISTINCT FROM 'object'
   OR (SELECT count(*) FROM jsonb_object_keys(item->'event'))<>4
   OR NOT item->'event' ?& ARRAY['kind','opcode','oldImageHex','newImageHex']
   OR jsonb_typeof(item->'event'->'kind') IS DISTINCT FROM 'string'
   OR item->'event'->>'kind' NOT IN ('state','node','scalar')
   OR jsonb_typeof(item->'event'->'opcode') IS DISTINCT FROM 'string'
   OR item->'event'->>'opcode' NOT IN ('INSERT','UPDATE','DELETE') THEN
   RAISE EXCEPTION 'complete original event descriptor required' USING ERRCODE='22023';END IF;
  IF item->'event'->>'opcode'='INSERT' AND item->'event'->'oldImageHex'<>'null'::jsonb
   OR item->'event'->>'opcode'='DELETE' AND item->'event'->'newImageHex'<>'null'::jsonb THEN
   RAISE EXCEPTION 'original event absence required' USING ERRCODE='22023';END IF;
  IF item->'event'->>'opcode'<>'INSERT' THEN
   IF jsonb_typeof(item->'event'->'oldImageHex') IS DISTINCT FROM 'string' OR item->'event'->>'oldImageHex' !~ '^([0-9a-f]{2})+$' THEN
    RAISE EXCEPTION 'original OLD image descriptor required' USING ERRCODE='22023';END IF;
   PERFORM truss.row_touch_image_cells_original(item->'event'->>'kind',decode(item->'event'->>'oldImageHex','hex'));
  END IF;
  IF item->'event'->>'opcode'<>'DELETE' THEN
   IF jsonb_typeof(item->'event'->'newImageHex') IS DISTINCT FROM 'string' OR item->'event'->>'newImageHex' !~ '^([0-9a-f]{2})+$' THEN
    RAISE EXCEPTION 'original NEW image descriptor required' USING ERRCODE='22023';END IF;
   PERFORM truss.row_touch_image_cells_original(item->'event'->>'kind',decode(item->'event'->>'newImageHex','hex'));
  END IF;
  scope:=truss.row_touch_scope_original(truss.row_touch_artifact_original(item->'scope'))||jsonb_build_object('_event',item->'event');
  IF counter=generation::text THEN selected:=scope;END IF;
 END LOOP;
 IF selected IS NULL THEN RAISE EXCEPTION 'original actual event generation not planned' USING ERRCODE='55000';END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_frame_original(bytea,bigint) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_scope_image_original(scope jsonb,kind text,state_id bigint,node_id bigint) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE item jsonb; image bytea; c bytea[]; result bytea;
BEGIN
 FOR item IN SELECT value FROM jsonb_array_elements(scope->'images') LOOP
  IF item->>'kind'<>kind THEN CONTINUE;END IF;
  image:=decode(item->>'imageHex','hex');c:=truss.row_touch_image_cells_original(kind,image);
  IF truss.row_touch_integer_original(c[1])=state_id AND (kind='state' OR truss.row_touch_integer_original(c[2])=node_id) THEN
   IF result IS NOT NULL THEN RAISE EXCEPTION 'ambiguous retained image' USING ERRCODE='55000';END IF;
   result:=image;
  END IF;
 END LOOP;
 IF result IS NULL THEN RAISE EXCEPTION 'complete original event member required' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_scope_image_original(jsonb,text,bigint,bigint) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_registry_original(op truss.row_home_operation) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE context jsonb; group_value jsonb; execution jsonb; name text; address jsonb; expected_address text;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none' THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker observation boundary required' USING ERRCODE='55000';END IF;
 context:=truss.row_touch_json_original(op.original_context_bytes);
 IF (SELECT count(*) FROM jsonb_object_keys(context))<>17
  OR NOT context ?& ARRAY['interfaceVersion','profile','installationIdentity','originalWriterXid','operationOrdinal','addressDomain','authority','durability',
   'originalInstallation','originalLayout','originalResourceProfile','originalOperationDefinition','originalExecutionContext','originalActingRoleContext','originalCatalogAuthorityCut','originalOwnerUnion','originalGroupAdmission']
  OR context->>'interfaceVersion' IS DISTINCT FROM 'truss-row-operation-context/0.1.0'
  OR context->>'addressDomain' IS DISTINCT FROM 'truss-row-operation-address/0.1.0'
  OR context->>'authority' IS DISTINCT FROM 'actual-protected-native-registry-correspondence'
  OR context->>'durability' IS DISTINCT FROM 'transaction-local-until-original-commit-observation'
  OR context->>'originalWriterXid' IS DISTINCT FROM op.original_writer_xid::text
  OR context->>'operationOrdinal' IS DISTINCT FROM op.operation_ordinal::text
  OR EXISTS(SELECT 1 FROM jsonb_each(context) e WHERE e.key IN ('interfaceVersion','installationIdentity','originalWriterXid','operationOrdinal','addressDomain','authority','durability') AND jsonb_typeof(e.value)<>'string')
  OR jsonb_typeof(context->'installationIdentity') IS DISTINCT FROM 'string'
  OR octet_length(context->>'installationIdentity') NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'original row-operation context required; native capture contexts are distinct' USING ERRCODE='55000';END IF;
 IF jsonb_typeof(context->'profile') IS DISTINCT FROM 'object'
  OR (SELECT count(*) FROM jsonb_object_keys(context->'profile'))<>3
  OR NOT context->'profile' ?& ARRAY['identity','version','sha256']
  OR EXISTS(SELECT 1 FROM jsonb_each(context->'profile') e WHERE jsonb_typeof(e.value)<>'string')
  OR octet_length(context->'profile'->>'identity') NOT BETWEEN 1 AND 65536
  OR octet_length(context->'profile'->>'version') NOT BETWEEN 1 AND 1024
  OR context->'profile'->>'sha256' !~ '^[0-9a-f]{64}$' THEN
  RAISE EXCEPTION 'original row-operation profile carrier required' USING ERRCODE='22023';END IF;
 FOREACH name IN ARRAY ARRAY['originalInstallation','originalLayout','originalResourceProfile','originalOperationDefinition','originalExecutionContext','originalActingRoleContext','originalCatalogAuthorityCut','originalOwnerUnion','originalGroupAdmission'] LOOP
  PERFORM truss.row_touch_artifact_original(context->name);
 END LOOP;
 IF truss.row_touch_artifact_original(context->'originalOperationDefinition') IS DISTINCT FROM op.original_definition_bytes THEN
  RAISE EXCEPTION 'original definition correspondence required' USING ERRCODE='55000';END IF;
 execution:=truss.row_touch_json_original(truss.row_touch_artifact_original(context->'originalExecutionContext'));
 -- Component invoker capture remains native0.2; never re-label that object as
 -- the nine-artifact context. Protected PA01–04 must register its own route.
 IF execution->>'interfaceVersion' IS DISTINCT FROM 'truss-native-operation-context/0.2'
  OR (SELECT count(*) FROM jsonb_object_keys(execution))<>9
  OR NOT execution ?& ARRAY['interfaceVersion','xid','ordinal','sessionUser','actingUser','database','backendPid','actorRoleOid','sessionRoleOid']
  OR EXISTS(SELECT 1 FROM jsonb_each(execution) e WHERE jsonb_typeof(e.value)<>'string')
  OR execution->>'xid' IS DISTINCT FROM op.original_writer_xid::text
  OR execution->>'ordinal' IS DISTINCT FROM op.operation_ordinal::text
  OR execution->>'sessionUser' IS DISTINCT FROM session_user::text
  OR execution->>'database' IS DISTINCT FROM current_database()
  OR execution->>'backendPid' IS DISTINCT FROM pg_backend_pid()::text
  OR execution->>'sessionRoleOid' IS DISTINCT FROM (SELECT oid::text FROM pg_roles WHERE rolname=session_user)
  OR truss.row_touch_artifact_original(context->'originalActingRoleContext') IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalExecutionContext') THEN
  RAISE EXCEPTION 'original selected native actor capture correspondence required' USING ERRCODE='55000';END IF;
 group_value:=truss.row_touch_json_original(op.original_group_custody_bytes);
 IF (SELECT count(*) FROM jsonb_object_keys(group_value))<>8
  OR NOT group_value ?& ARRAY['interfaceVersion','profile','addressDomain','operationIdentity','operationKind','originalGroupAdmission','authority','completionEvidence']
  OR group_value->>'interfaceVersion' IS DISTINCT FROM 'truss-row-group-custody/0.1.0'
  OR group_value->>'addressDomain' IS DISTINCT FROM 'truss-row-operation-address/0.1.0'
  OR group_value->>'authority' IS DISTINCT FROM 'actual-original-operation-admission-not-caller-address'
  OR group_value->>'completionEvidence' IS DISTINCT FROM 'resolved-independently-not-embedded-future-digest'
  OR group_value->'profile' IS DISTINCT FROM context->'profile'
  OR group_value->>'operationKind' IS DISTINCT FROM op.operation_kind
  OR group_value->'originalGroupAdmission' IS DISTINCT FROM context->'originalGroupAdmission' THEN
  RAISE EXCEPTION 'original native group/context correspondence required' USING ERRCODE='55000';END IF;
 -- Canonical array wire uses the same literal-scalar/compact JSON address recipe
 -- as the independent Python address encoder, including literal non-ASCII.
 address:=jsonb_build_array('truss-row-operation-address/0.1.0',context->>'installationIdentity',op.original_writer_xid::text,op.operation_ordinal::text);
 expected_address:='['||to_json('truss-row-operation-address/0.1.0'::text)::text||','||to_json(context->>'installationIdentity')::text||','||to_json(op.original_writer_xid::text)::text||','||to_json(op.operation_ordinal::text)::text||']';
 IF group_value->>'operationIdentity' IS DISTINCT FROM expected_address THEN
  RAISE EXCEPTION 'original canonical native operation address required' USING ERRCODE='55000';END IF;
 RETURN context;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_registry_original(truss.row_home_operation) FROM PUBLIC;
-- Historical actor capture is retained evidence, never current permission.
-- Only the selected unfinished operation passes this active actor predicate.
CREATE FUNCTION truss.row_touch_active_context_original(context jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE execution jsonb;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none' THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original active invoker boundary required' USING ERRCODE='55000';END IF;
 execution:=truss.row_touch_json_original(truss.row_touch_artifact_original(context->'originalExecutionContext'));
 IF execution->>'actingUser' IS DISTINCT FROM current_user::text
  OR execution->>'actorRoleOid' IS DISTINCT FROM (SELECT oid::text FROM pg_roles WHERE rolname=current_user) THEN
  RAISE EXCEPTION 'original active actor correspondence required' USING ERRCODE='55000';END IF;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_active_context_original(jsonb) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_event_owner_original(kind text,image bytea,scope jsonb)
RETURNS TABLE(owner_kind text,owner_id bigint,discriminator_id int,property_owner_type_id int,property_id int,home_bytes bytea)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE c bytea[]; state_image bytea; node_image bytea; state_value truss.row_home_state%ROWTYPE;
 node_value truss.row_home_node%ROWTYPE; association record;
BEGIN
 c:=truss.row_touch_image_cells_original(kind,image);
 IF truss.row_touch_scope_image_original(scope,kind,truss.row_touch_integer_original(c[1]),
  CASE WHEN kind='state' THEN NULL ELSE truss.row_touch_integer_original(c[2]) END) IS DISTINCT FROM image THEN
  RAISE EXCEPTION 'complete original event image correspondence required' USING ERRCODE='55000';END IF;
 state_image:=truss.row_touch_scope_image_original(scope,'state',truss.row_touch_integer_original(c[1]),NULL);
 state_value:=truss.row_touch_state_from_image_original(state_image);
 SELECT a.* INTO STRICT association FROM truss.row_image_state_owner_original(state_value) a;
 IF kind='node' THEN
  node_value:=truss.row_touch_node_from_image_original(image);
  PERFORM * FROM truss.row_image_node_owner_original(node_value,image,state_value,state_image);
 ELSIF kind='scalar' THEN
  node_image:=truss.row_touch_scope_image_original(scope,'node',truss.row_touch_integer_original(c[1]),truss.row_touch_integer_original(c[2]));
  node_value:=truss.row_touch_node_from_image_original(node_image);
  PERFORM * FROM truss.row_image_node_owner_original(node_value,node_image,state_value,state_image);
 END IF;
 owner_kind:=association.owner_kind;owner_id:=association.owner_id;discriminator_id:=association.discriminator_id;
 property_owner_type_id:=association.property_owner_type_id;property_id:=association.property_id;home_bytes:=state_value.home_profile_bytes;
 RETURN NEXT;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_event_owner_original(text,bytea,jsonb) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_member_original(context jsonb,association jsonb) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE owner_union jsonb; member jsonb; result jsonb; tuple_key jsonb; seen jsonb[]:=ARRAY[]::jsonb[]; name text; value text;
BEGIN
 owner_union:=truss.row_touch_json_original(truss.row_touch_artifact_original(context->'originalOwnerUnion'));
 IF (SELECT count(*) FROM jsonb_object_keys(owner_union))<>2 OR NOT owner_union ?& ARRAY['interfaceVersion','members']
  OR owner_union->>'interfaceVersion' IS DISTINCT FROM 'truss-row-owner-property-union/0.1'
  OR jsonb_typeof(owner_union->'members') IS DISTINCT FROM 'array' OR jsonb_array_length(owner_union->'members') NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'complete original owner/property union required' USING ERRCODE='0A000';END IF;
 FOR member IN SELECT e.value FROM jsonb_array_elements(owner_union->'members') AS e(value) LOOP
  IF jsonb_typeof(member) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(member))<>7
   OR NOT member ?& ARRAY['ownerKind','ownerId','discriminatorId','propertyOwnerTypeId','propertyId','originalHome','originalOwnerProperty']
   OR jsonb_typeof(member->'ownerKind') IS DISTINCT FROM 'string'
   OR member->>'ownerKind' NOT IN ('object','edge') THEN RAISE EXCEPTION 'complete original owner member required' USING ERRCODE='22023';END IF;
  FOREACH name IN ARRAY ARRAY['ownerId','discriminatorId','propertyOwnerTypeId','propertyId'] LOOP
   value:=member->>name;
   IF jsonb_typeof(member->name) IS DISTINCT FROM 'string' OR value !~ '^(0|-?[1-9][0-9]{0,18})$'
    OR (name='ownerId' AND value::numeric NOT BETWEEN -9223372036854775808 AND 9223372036854775807)
    OR (name<>'ownerId' AND value::numeric NOT BETWEEN -2147483648 AND 2147483647) THEN
    RAISE EXCEPTION 'original native owner tuple grammar required' USING ERRCODE='22023';END IF;
  END LOOP;
  PERFORM truss.row_touch_artifact_original(member->'originalHome');PERFORM truss.row_touch_artifact_original(member->'originalOwnerProperty');
  tuple_key:=member-ARRAY['originalHome','originalOwnerProperty'];
  IF tuple_key=ANY(seen) THEN RAISE EXCEPTION 'duplicate original owner union member' USING ERRCODE='22023';END IF;
  seen:=array_append(seen,tuple_key);
  IF tuple_key=association THEN result:=member;END IF;
 END LOOP;
 IF result IS NULL THEN RAISE EXCEPTION 'actual event outside original owner union' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_member_original(jsonb,jsonb) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_manifest_original(context jsonb,member jsonb,op truss.row_home_operation,prior bytea) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE manifest jsonb; entry jsonb; group_value jsonb; row_value jsonb; contributor truss.row_home_operation%ROWTYPE;
 original_context jsonb; seen text[]:=ARRAY[]::text[]; position int:=0; contains_current boolean:=false; value bytea;
BEGIN
 group_value:=truss.row_touch_json_original(op.original_group_custody_bytes);
 IF prior IS NULL THEN
  manifest:=jsonb_build_object('interfaceVersion','truss-row-operation-custody/0.1.0','profile',context->'profile',
   'originalLayout',context->'originalLayout','originalHome',member->'originalHome','originalOwnerProperty',member->'originalOwnerProperty',
   'operations','[]'::jsonb,'groupResolution','original-native-effects-readiness-before-seal',
   'completionEvidence','resolved-independently-not-embedded-future-digest','transactionAuthority','actual-native-touch-context-not-caller-manifest');
 ELSE
  manifest:=truss.row_touch_json_original(prior);
  IF (SELECT count(*) FROM jsonb_object_keys(manifest))<>9
   OR NOT manifest ?& ARRAY['interfaceVersion','profile','originalLayout','originalHome','originalOwnerProperty','operations','groupResolution','completionEvidence','transactionAuthority']
   OR manifest->>'interfaceVersion' IS DISTINCT FROM 'truss-row-operation-custody/0.1.0'
   OR manifest->'profile' IS DISTINCT FROM context->'profile' OR manifest->'originalLayout' IS DISTINCT FROM context->'originalLayout'
   OR manifest->'originalHome' IS DISTINCT FROM member->'originalHome' OR manifest->'originalOwnerProperty' IS DISTINCT FROM member->'originalOwnerProperty'
   OR manifest->>'groupResolution' IS DISTINCT FROM 'original-native-effects-readiness-before-seal'
   OR manifest->>'completionEvidence' IS DISTINCT FROM 'resolved-independently-not-embedded-future-digest'
   OR manifest->>'transactionAuthority' IS DISTINCT FROM 'actual-native-touch-context-not-caller-manifest'
   OR jsonb_typeof(manifest->'operations') IS DISTINCT FROM 'array' OR jsonb_array_length(manifest->'operations') NOT BETWEEN 1 AND 1024 THEN
   RAISE EXCEPTION 'complete original prior contributor manifest required' USING ERRCODE='55000';END IF;
  FOR entry IN SELECT item FROM jsonb_array_elements(manifest->'operations') item LOOP
   IF jsonb_typeof(entry) IS DISTINCT FROM 'object' OR (SELECT count(*) FROM jsonb_object_keys(entry))<>9
    OR NOT entry ?& ARRAY['ordinal','operationIdentity','operationKind','originalOperationDefinition','originalInput','originalPrestate','admittedCandidate','nativeGroupCustodyIdentity','effectObligationDefinition']
    OR EXISTS(SELECT 1 FROM jsonb_each(entry) e WHERE e.key IN ('ordinal','operationIdentity','operationKind','nativeGroupCustodyIdentity') AND jsonb_typeof(e.value)<>'string')
    OR entry->>'ordinal' IS DISTINCT FROM position::text OR entry->>'operationIdentity'=ANY(seen)
    OR entry->>'nativeGroupCustodyIdentity' IS DISTINCT FROM entry->>'operationIdentity' THEN
    RAISE EXCEPTION 'original ordered contributor union required' USING ERRCODE='55000';END IF;
   SELECT o.* INTO STRICT contributor FROM truss.row_home_operation o
    WHERE o.original_writer_xid=op.original_writer_xid
     AND truss.row_touch_json_original(o.original_group_custody_bytes)->>'operationIdentity'=entry->>'operationIdentity';
   original_context:=truss.row_touch_registry_original(contributor);
   IF truss.row_touch_member_original(original_context,member-ARRAY['originalHome','originalOwnerProperty']) IS DISTINCT FROM member
    OR entry->'originalInput'->>'identity' IS DISTINCT FROM (entry->>'operationIdentity')||'/input'
    OR entry->'originalPrestate'->>'identity' IS DISTINCT FROM (entry->>'operationIdentity')||'/prestate'
    OR entry->'admittedCandidate'->>'identity' IS DISTINCT FROM (entry->>'operationIdentity')||'/candidate'
    OR entry->'effectObligationDefinition'->>'identity' IS DISTINCT FROM (entry->>'operationIdentity')||'/obligation'
    OR original_context->>'installationIdentity' IS DISTINCT FROM context->>'installationIdentity'
    OR original_context->'profile' IS DISTINCT FROM context->'profile' OR original_context->'originalLayout' IS DISTINCT FROM context->'originalLayout'
    OR entry->>'operationKind' IS DISTINCT FROM contributor.operation_kind
    OR entry->'originalOperationDefinition' IS DISTINCT FROM original_context->'originalOperationDefinition'
    OR truss.row_touch_artifact_original(entry->'originalInput') IS DISTINCT FROM contributor.original_input_bytes
    OR truss.row_touch_artifact_original(entry->'originalPrestate') IS DISTINCT FROM contributor.original_prestate_bytes
    OR truss.row_touch_artifact_original(entry->'admittedCandidate') IS DISTINCT FROM contributor.admitted_candidate_bytes
    OR truss.row_touch_artifact_original(entry->'effectObligationDefinition') IS DISTINCT FROM contributor.effect_obligation_bytes THEN
    RAISE EXCEPTION 'complete original registry contributor bytes required' USING ERRCODE='55000';END IF;
   seen:=array_append(seen,entry->>'operationIdentity');position:=position+1;
   IF contributor.operation_ordinal=op.operation_ordinal THEN contains_current:=true;END IF;
  END LOOP;
 END IF;
 IF NOT contains_current THEN
  IF position>=1024 THEN RAISE EXCEPTION 'original contributor bound exceeded' USING ERRCODE='54000';END IF;
  entry:=jsonb_build_object('ordinal',position::text,'operationIdentity',group_value->>'operationIdentity','operationKind',op.operation_kind,
   'originalOperationDefinition',context->'originalOperationDefinition','nativeGroupCustodyIdentity',group_value->>'operationIdentity');
  -- Exact retained registry bytes are artifact payloads; identities are the
  -- native original address plus a fixed producer-owned artifact role.
  entry:=entry||jsonb_build_object(
   'originalInput',jsonb_build_object('identity',(group_value->>'operationIdentity')||'/input','bytesBase64',replace(encode(op.original_input_bytes,'base64'),E'\n',''),'sha256',encode(sha256(op.original_input_bytes),'hex')),
   'originalPrestate',jsonb_build_object('identity',(group_value->>'operationIdentity')||'/prestate','bytesBase64',replace(encode(op.original_prestate_bytes,'base64'),E'\n',''),'sha256',encode(sha256(op.original_prestate_bytes),'hex')),
   'admittedCandidate',jsonb_build_object('identity',(group_value->>'operationIdentity')||'/candidate','bytesBase64',replace(encode(op.admitted_candidate_bytes,'base64'),E'\n',''),'sha256',encode(sha256(op.admitted_candidate_bytes),'hex')),
   'effectObligationDefinition',jsonb_build_object('identity',(group_value->>'operationIdentity')||'/obligation','bytesBase64',replace(encode(op.effect_obligation_bytes,'base64'),E'\n',''),'sha256',encode(sha256(op.effect_obligation_bytes),'hex')));
  manifest:=jsonb_set(manifest,'{operations}',(manifest->'operations')||jsonb_build_array(entry));
 END IF;
 value:=convert_to(manifest::text,'UTF8');
 IF octet_length(value)>8388608 THEN RAISE EXCEPTION 'original contributor retention bound exceeded' USING ERRCODE='54000';END IF;
 RETURN value;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_manifest_original(jsonb,jsonb,truss.row_home_operation,bytea) FROM PUBLIC;
CREATE FUNCTION truss.row_touch_observe() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; op_after truss.row_home_operation%ROWTYPE; op_expected truss.row_home_operation%ROWTYPE; context jsonb; before_scope jsonb; after_scope jsonb; kind text;
 old_image bytea; new_image bytea; event_images bytea[]; event_scopes jsonb[]; association record; tuple_key jsonb;
 tuples jsonb[]:=ARRAY[]::jsonb[]; homes bytea[]:=ARRAY[]::bytea[]; members jsonb[]:=ARRAY[]::jsonb[];
 planned truss.row_home_touch[]:=ARRAY[]::truss.row_home_touch[]; existed boolean[]:=ARRAY[]::boolean[];
 prior_touch truss.row_home_touch%ROWTYPE; next_touch truss.row_home_touch%ROWTYPE; ledger truss.row_home_capacity%ROWTYPE;
 member jsonb; i int; bytes_before bigint; bytes_after bigint; growth bigint:=0; new_rows bigint:=0;
 retained_state truss.row_home_state%ROWTYPE; retained_node truss.row_home_node%ROWTYPE; state_image bytea; node_image bytea; c bytea[];
 actual_xid xid8:=pg_current_xact_id_if_assigned(); routine oid;
BEGIN
 IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP NOT IN ('INSERT','UPDATE','DELETE') OR TG_NARGS<>0 OR TG_TABLE_SCHEMA<>'truss'
  OR actual_xid IS NULL OR TG_RELID NOT IN ('truss.row_home_state'::regclass,'truss.row_home_node'::regclass,'truss.row_home_scalar'::regclass) THEN
  RAISE EXCEPTION 'registered original row touch event required' USING ERRCODE='55000';END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=TG_RELID AND t.tgname=TG_NAME
  AND t.tgfoid='truss.row_touch_observe()'::regprocedure AND t.tgtype=29 AND t.tgenabled='A'
  AND t.tgnargs=0 AND t.tgattr=''::int2vector AND t.tgqual IS NULL AND NOT t.tgisinternal
  AND t.tgconstraint=0 AND NOT t.tgdeferrable AND NOT t.tginitdeferred AND t.tgoldtable IS NULL AND t.tgnewtable IS NULL)
  OR EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=TG_RELID AND NOT t.tgisinternal
   AND t.tgname IN ('runtime_state_generation','runtime_node_generation','runtime_scalar_generation','runtime_existing_string_pending_scalar')) THEN
  RAISE EXCEPTION 'original nonoverlapping immediate row observer required' USING ERRCODE='55000';END IF;
 BEGIN
  SELECT o.* INTO STRICT op FROM truss.row_home_operation o WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized' FOR UPDATE;
 EXCEPTION WHEN no_data_found OR too_many_rows THEN
  RAISE EXCEPTION 'exactly one original unfinished operation required' USING ERRCODE='55000';
 END;
 IF op.phase NOT IN ('admitted','effects_ready','row_sealed') OR op.operation_kind NOT IN ('mutation','import','catalog-transform','catalog-acceptance','home-migration','administrative-repair')
  OR op.effect_generation=9223372036854775807 THEN RAISE EXCEPTION 'original unfinished event frontier required' USING ERRCODE='55000';END IF;
 op_expected:=op;op_expected.effect_generation:=op.effect_generation+1;op_expected.phase:='admitted';
 op_expected.readiness_generation:=NULL;op_expected.sealed_generation:=NULL;op_expected.application_generation:=NULL;op_expected.application_result_bytes:=NULL;
 context:=truss.row_touch_registry_original(op);
 PERFORM truss.row_touch_active_context_original(context);
 before_scope:=truss.row_touch_frame_original(op.original_prestate_bytes,op.effect_generation);
 after_scope:=truss.row_touch_frame_original(op.admitted_candidate_bytes,op.effect_generation);
 SELECT l.* INTO STRICT ledger FROM truss.row_home_capacity l WHERE l.singleton_id=1;
 IF ledger.reservation_writer_xid IS DISTINCT FROM actual_xid OR ledger.reservation_operation_ordinal IS DISTINCT FROM op.operation_ordinal
  OR ledger.reservation_context_bytes IS DISTINCT FROM op.original_context_bytes
  OR ledger.reservation_plan_bytes IS DISTINCT FROM op.effect_obligation_bytes
  OR ledger.original_layout_bytes IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalLayout')
  OR ledger.original_resource_profile_bytes IS DISTINCT FROM truss.row_touch_artifact_original(context->'originalResourceProfile') THEN
  RAISE EXCEPTION 'original before-effects reservation required' USING ERRCODE='55000';END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks l WHERE l.pid=pg_backend_pid() AND l.granted AND l.relation='truss.schema_head'::regclass
  AND l.mode IN ('RowShareLock','ShareLock','ShareRowExclusiveLock','ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'original retained catalog admission required' USING ERRCODE='55000';END IF;
 -- Capacity hooks own exact physical row-byte transfers. This observer prechecks
 -- every tuple before any proof-state write; it never reserves a lower-order lock.
 IF EXISTS(SELECT 1 FROM (VALUES
  ('row_home_operation','capacity_operation_update','truss.capacity_operation_observe_original()',19),
  ('row_home_touch','capacity_touch_insert','truss.capacity_touch_observe_original()',5),
  ('row_home_touch','capacity_touch_update','truss.capacity_touch_observe_original()',19)) v(relation_name,trigger_name,function_name,trigger_type)
  WHERE NOT EXISTS(SELECT 1 FROM pg_trigger t WHERE t.tgrelid=to_regclass('truss.'||v.relation_name)
   AND t.tgname=v.trigger_name AND t.tgfoid=to_regprocedure(v.function_name) AND t.tgtype=v.trigger_type
   AND t.tgenabled='A' AND t.tgnargs=0 AND t.tgattr=''::int2vector AND t.tgqual IS NULL)) THEN
  RAISE EXCEPTION 'complete original capacity observation required' USING ERRCODE='55000';END IF;
 CASE TG_TABLE_NAME
 WHEN 'row_home_state' THEN kind:='state';IF TG_OP<>'INSERT' THEN old_image:=truss.row_image_state_original(OLD);END IF;IF TG_OP<>'DELETE' THEN new_image:=truss.row_image_state_original(NEW);END IF;
 WHEN 'row_home_node' THEN kind:='node';IF TG_OP<>'INSERT' THEN old_image:=truss.row_image_node_original(OLD);END IF;IF TG_OP<>'DELETE' THEN new_image:=truss.row_image_node_original(NEW);END IF;
 WHEN 'row_home_scalar' THEN kind:='scalar';IF TG_OP<>'INSERT' THEN old_image:=truss.row_image_scalar_original(OLD);END IF;IF TG_OP<>'DELETE' THEN new_image:=truss.row_image_scalar_original(NEW);END IF;
 END CASE;
 IF before_scope->'_event' IS DISTINCT FROM after_scope->'_event'
  OR before_scope->'_event' IS DISTINCT FROM jsonb_build_object('kind',kind,'opcode',TG_OP,'oldImageHex',encode(old_image,'hex'),'newImageHex',encode(new_image,'hex')) THEN
  RAISE EXCEPTION 'actual event descriptor mismatch at generation %, kind %, opcode %',op.effect_generation,kind,TG_OP USING ERRCODE='55000';END IF;
 event_images:=ARRAY[old_image,new_image];event_scopes:=ARRAY[before_scope,after_scope];
 FOR i IN 1..2 LOOP
  IF event_images[i] IS NULL THEN CONTINUE;END IF;
  SELECT a.* INTO STRICT association FROM truss.row_touch_event_owner_original(kind,event_images[i],event_scopes[i]) a;
  IF kind='scalar' THEN
   c:=truss.row_touch_image_cells_original(kind,event_images[i]);
   state_image:=truss.row_touch_scope_image_original(event_scopes[i],'state',truss.row_touch_integer_original(c[1]),NULL);
   node_image:=truss.row_touch_scope_image_original(event_scopes[i],'node',truss.row_touch_integer_original(c[1]),truss.row_touch_integer_original(c[2]));
   retained_state:=truss.row_touch_state_from_image_original(state_image);retained_node:=truss.row_touch_node_from_image_original(node_image);
   IF i=1 THEN PERFORM * FROM truss.row_image_scalar_owner_original(OLD,event_images[i],retained_node,node_image,retained_state,state_image);
   ELSE PERFORM * FROM truss.row_image_scalar_owner_original(NEW,event_images[i],retained_node,node_image,retained_state,state_image);END IF;
  END IF;
  tuple_key:=jsonb_build_object('ownerKind',association.owner_kind,'ownerId',association.owner_id::text,'discriminatorId',association.discriminator_id::text,
   'propertyOwnerTypeId',association.property_owner_type_id::text,'propertyId',association.property_id::text);
  member:=truss.row_touch_member_original(context,tuple_key);
  IF truss.row_touch_artifact_original(member->'originalHome') IS DISTINCT FROM association.home_bytes THEN
   RAISE EXCEPTION 'original native home correspondence required' USING ERRCODE='55000';END IF;
  IF NOT tuple_key=ANY(tuples) THEN tuples:=array_append(tuples,tuple_key);members:=array_append(members,member);END IF;
 END LOOP;
 IF coalesce(array_length(tuples,1),0) NOT BETWEEN 1 AND 2 THEN RAISE EXCEPTION 'complete event-local tuple set required' USING ERRCODE='55000';END IF;
 FOR i IN 1..array_length(tuples,1) LOOP
  SELECT t.* INTO prior_touch FROM truss.row_home_touch t WHERE t.transaction_id=actual_xid
   AND t.owner_kind=tuples[i]->>'ownerKind' AND t.owner_id=(tuples[i]->>'ownerId')::bigint
   AND t.owner_discriminator_id=(tuples[i]->>'discriminatorId')::int
   AND t.property_owner_type_id=(tuples[i]->>'propertyOwnerTypeId')::int AND t.property_id=(tuples[i]->>'propertyId')::int FOR UPDATE;
  existed:=array_append(existed,FOUND);bytes_before:=0;
  IF FOUND THEN
   IF prior_touch.dirty_generation=9223372036854775807 OR prior_touch.original_layout_bytes IS DISTINCT FROM ledger.original_layout_bytes
    OR prior_touch.original_home_bytes IS DISTINCT FROM truss.row_touch_artifact_original(members[i]->'originalHome')
    OR prior_touch.original_owner_property_bytes IS DISTINCT FROM truss.row_touch_artifact_original(members[i]->'originalOwnerProperty') THEN
    RAISE EXCEPTION 'original touch generation/artifact frontier required' USING ERRCODE='55000';END IF;
   bytes_before:=truss.custody_touch_size_original(prior_touch);next_touch:=prior_touch;next_touch.dirty_generation:=prior_touch.dirty_generation+1;
  ELSE
   next_touch.transaction_id:=actual_xid;next_touch.owner_kind:=tuples[i]->>'ownerKind';next_touch.owner_id:=(tuples[i]->>'ownerId')::bigint;
   next_touch.owner_discriminator_id:=(tuples[i]->>'discriminatorId')::int;next_touch.property_owner_type_id:=(tuples[i]->>'propertyOwnerTypeId')::int;
   next_touch.property_id:=(tuples[i]->>'propertyId')::int;next_touch.dirty_generation:=1;
   next_touch.original_layout_bytes:=ledger.original_layout_bytes;next_touch.original_home_bytes:=truss.row_touch_artifact_original(members[i]->'originalHome');
   next_touch.original_owner_property_bytes:=truss.row_touch_artifact_original(members[i]->'originalOwnerProperty');new_rows:=new_rows+1;
  END IF;
  next_touch.sealed_generation:=NULL;
  next_touch.original_operation_bytes:=truss.row_touch_manifest_original(context,members[i],op,CASE WHEN existed[i] THEN prior_touch.original_operation_bytes ELSE NULL END);
  bytes_after:=truss.custody_touch_size_original(next_touch);growth:=growth+greatest(bytes_after-bytes_before,0);planned:=array_append(planned,next_touch);
 END LOOP;
 growth:=growth+greatest(truss.custody_operation_size_original(op_expected)-truss.custody_operation_size_original(op),0);
 IF new_rows>ledger.reserved_rows OR growth>ledger.reserved_custody_bytes THEN RAISE EXCEPTION 'complete event reservation exhausted' USING ERRCODE='54000';END IF;
 FOR i IN 1..array_length(planned,1) LOOP
  next_touch:=planned[i];
  BEGIN
  IF existed[i] THEN
   UPDATE truss.row_home_touch t SET dirty_generation=next_touch.dirty_generation,sealed_generation=NULL,original_operation_bytes=next_touch.original_operation_bytes
    WHERE t.transaction_id=next_touch.transaction_id AND t.owner_kind=next_touch.owner_kind AND t.owner_id=next_touch.owner_id
     AND t.owner_discriminator_id=next_touch.owner_discriminator_id AND t.property_owner_type_id=next_touch.property_owner_type_id AND t.property_id=next_touch.property_id RETURNING t.* INTO STRICT prior_touch;
  ELSE INSERT INTO truss.row_home_touch SELECT (next_touch).* RETURNING * INTO STRICT prior_touch;END IF;
  EXCEPTION WHEN no_data_found OR too_many_rows THEN
   RAISE EXCEPTION 'exactly one actual touch effect required' USING ERRCODE='55000';
  END;
  IF prior_touch IS DISTINCT FROM next_touch THEN RAISE EXCEPTION 'actual touch effect parity required' USING ERRCODE='55000';END IF;
 END LOOP;
 UPDATE truss.row_home_operation o SET effect_generation=op.effect_generation+1,phase='admitted',readiness_generation=NULL,sealed_generation=NULL,
  application_generation=NULL,application_result_bytes=NULL WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal AND o.effect_generation=op.effect_generation RETURNING o.* INTO op_after;
 IF NOT FOUND THEN RAISE EXCEPTION 'original operation event frontier changed' USING ERRCODE='55000';END IF;
 IF op_after IS DISTINCT FROM op_expected THEN RAISE EXCEPTION 'actual operation effect parity required' USING ERRCODE='55000';END IF;
 FOR i IN 1..array_length(planned,1) LOOP
  next_touch:=planned[i];
  SELECT t.* INTO prior_touch FROM truss.row_home_touch t WHERE t.transaction_id=next_touch.transaction_id
   AND t.owner_kind=next_touch.owner_kind AND t.owner_id=next_touch.owner_id AND t.owner_discriminator_id=next_touch.owner_discriminator_id
   AND t.property_owner_type_id=next_touch.property_owner_type_id AND t.property_id=next_touch.property_id;
  IF NOT FOUND OR prior_touch IS DISTINCT FROM next_touch THEN RAISE EXCEPTION 'final actual touch parity required' USING ERRCODE='55000';END IF;
 END LOOP;
 SELECT o.* INTO op_after FROM truss.row_home_operation o WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal;
 IF NOT FOUND OR op_after IS DISTINCT FROM op_expected THEN RAISE EXCEPTION 'final actual operation parity required' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.row_touch_observe() FROM PUBLIC;
-- The complete bundle replaces overlapping historical generation observers;
-- this source does not silently drop them or grant any consumer privileges.
CREATE TRIGGER runtime_row_touch_observe AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_state FOR EACH ROW EXECUTE FUNCTION truss.row_touch_observe();
ALTER TABLE truss.row_home_state ENABLE ALWAYS TRIGGER runtime_row_touch_observe;
CREATE TRIGGER runtime_row_touch_observe AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_node FOR EACH ROW EXECUTE FUNCTION truss.row_touch_observe();
ALTER TABLE truss.row_home_node ENABLE ALWAYS TRIGGER runtime_row_touch_observe;
CREATE TRIGGER runtime_row_touch_observe AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_scalar FOR EACH ROW EXECUTE FUNCTION truss.row_touch_observe();
ALTER TABLE truss.row_home_scalar ENABLE ALWAYS TRIGGER runtime_row_touch_observe;
