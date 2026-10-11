-- Complete JSONB row-image shape; numeric casts occur only after bounds checks.
CREATE FUNCTION truss.edge_limit_image_original(relation_name text,image jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE names text[]; types text[]; nullable text[]; i int; value jsonb; text_value text;
BEGIN
 CASE relation_name
 WHEN 'edge' THEN
  names:=ARRAY['id','rel_type_id','source_id','source_type','target_id','target_type','props','order_key','rev','ver','created_at','updated_at','retained'];
  types:=ARRAY['bigint','int','bigint','int','bigint','int','object','string','int','bigint','timestamp','timestamp','object'];
  nullable:=ARRAY['order_key','retained'];
 WHEN 'edge_limit' THEN
  names:=ARRAY['rel_type_id','side','endpoint_id','edge_id'];
  types:=ARRAY['bigint','side','bigint','bigint'];nullable:=ARRAY[]::text[];
 WHEN 'rel_def' THEN
  names:=ARRAY['document_id','rel_type_id','module','rel_id','name','source_min','source_max','target_min','target_max','lifecycle','directed','target_key','composition','assoc_type_id','inverse','since_rev','doc_ord','retired_rev','definition_source_kind','definition_rev','definition_doc_ord','definition_document_id','binding_source_rev','binding_source_pointer','binding_source_bytes'];
  types:=ARRAY['string','int','string','string','string','int','int','int','int','string','boolean','string','boolean','int','string','int','int','int','string','int','int','string','int','string','bytes'];
  nullable:=ARRAY['source_max','target_max','target_key','assoc_type_id','inverse','retired_rev','definition_source_kind','definition_rev','definition_doc_ord','definition_document_id','binding_source_rev','binding_source_pointer','binding_source_bytes'];
 ELSE RAISE EXCEPTION 'original relation image family required' USING ERRCODE='22023';
 END CASE;
 IF jsonb_typeof(image) IS DISTINCT FROM 'object' THEN
  RAISE EXCEPTION 'original row image object required' USING ERRCODE='22023';
 END IF;
 IF (SELECT count(*) FROM jsonb_object_keys(image))<>cardinality(names) OR NOT image ?& names THEN
  RAISE EXCEPTION 'closed complete original row image required' USING ERRCODE='22023';
 END IF;
 FOR i IN 1..cardinality(names) LOOP
  value:=image->names[i];text_value:=image->>names[i];
  IF value='null'::jsonb AND names[i]=ANY(nullable) THEN CONTINUE;END IF;
  CASE types[i]
  WHEN 'int','bigint' THEN
   IF jsonb_typeof(value) IS DISTINCT FROM 'number' OR length(text_value)>20
    OR text_value !~ '^(0|-?[1-9][0-9]*)$' THEN
    RAISE EXCEPTION 'exact native integral image required' USING ERRCODE='22023';
   END IF;
   IF (types[i]='int' AND text_value::numeric NOT BETWEEN -2147483648 AND 2147483647)
    OR text_value::numeric NOT BETWEEN -9223372036854775808 AND 9223372036854775807 THEN
    RAISE EXCEPTION 'native integral image range required' USING ERRCODE='22023';
   END IF;
  WHEN 'timestamp' THEN
   IF jsonb_typeof(value) IS DISTINCT FROM 'string' OR length(text_value)>64
    OR (text_value NOT IN ('infinity','-infinity') AND text_value !~ '^[0-9]{4,6}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?[+-][0-9]{2}:[0-9]{2}( BC)?$') THEN
    RAISE EXCEPTION 'native timestamp image required' USING ERRCODE='22023';
   END IF;
   BEGIN PERFORM text_value::timestamptz;
   EXCEPTION WHEN OTHERS THEN RAISE EXCEPTION 'valid native timestamp image required' USING ERRCODE='22023';END;
  WHEN 'bytes' THEN
   IF jsonb_typeof(value) IS DISTINCT FROM 'string' OR text_value !~ '^\\x([0-9a-f]{2})*$' THEN
    RAISE EXCEPTION 'native bytea image required' USING ERRCODE='22023';
   END IF;
  WHEN 'side' THEN
   IF jsonb_typeof(value) IS DISTINCT FROM 'string' OR text_value NOT IN ('s','t') THEN
    RAISE EXCEPTION 'native marker side required' USING ERRCODE='22023';
   END IF;
  ELSE
   IF jsonb_typeof(value) IS DISTINCT FROM types[i] THEN
    RAISE EXCEPTION 'exact native image cell type required' USING ERRCODE='22023';
   END IF;
  END CASE;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.edge_limit_image_original(text,jsonb) FROM PUBLIC;
-- Retained before/after facts; these are not proof that native guards were acquired.
CREATE FUNCTION truss.edge_limit_scope_original(original bytea,event jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE scope jsonb; member text; side jsonb; image jsonb; edge_image jsonb; definition jsonb;
BEGIN
 scope:=truss.row_touch_json_original(original);
 IF (SELECT count(*) FROM jsonb_object_keys(scope))<>3
  OR NOT scope ?& ARRAY['interfaceVersion','old','new']
  OR scope->>'interfaceVersion' IS DISTINCT FROM 'truss-native-edge-event-scope/0.1' THEN
  RAISE EXCEPTION 'closed retained edge scope required' USING ERRCODE='22023';
 END IF;
 FOREACH member IN ARRAY ARRAY['old','new'] LOOP
  image:=event->(member||'Image');side:=scope->member;
  IF image='null'::jsonb THEN
   IF side IS DISTINCT FROM 'null'::jsonb THEN
    RAISE EXCEPTION 'absent event side scope required' USING ERRCODE='22023';
   END IF;
   CONTINUE;
  END IF;
  IF jsonb_typeof(side) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'retained event side scope required' USING ERRCODE='22023';
  END IF;
  IF (SELECT count(*) FROM jsonb_object_keys(side))<>3
   OR NOT side ?& ARRAY['edge','definition','originalGuard'] THEN
   RAISE EXCEPTION 'closed event side attribution required' USING ERRCODE='22023';
  END IF;
  PERFORM truss.row_touch_artifact_original(side->'originalGuard');
  definition:=side->'definition';edge_image:=side->'edge';
  PERFORM truss.edge_limit_image_original('rel_def',definition);
  IF event->>'relation'='rel_def' THEN
   IF definition IS DISTINCT FROM image OR edge_image IS DISTINCT FROM 'null'::jsonb THEN
    RAISE EXCEPTION 'original catalog event scope correspondence required' USING ERRCODE='55000';
   END IF;
  ELSE
   PERFORM truss.edge_limit_image_original('edge',edge_image);
   IF definition->'rel_type_id' IS DISTINCT FROM edge_image->'rel_type_id' THEN
    RAISE EXCEPTION 'retained relationship attribution required' USING ERRCODE='55000';
   END IF;
   IF event->>'relation'='edge' THEN
    IF edge_image IS DISTINCT FROM image THEN
     RAISE EXCEPTION 'original edge scope correspondence required' USING ERRCODE='55000';
    END IF;
   ELSIF image->'edge_id' IS DISTINCT FROM edge_image->'id'
    OR image->'rel_type_id' IS DISTINCT FROM edge_image->'rel_type_id'
    OR (image->>'side'='s' AND (image->'endpoint_id' IS DISTINCT FROM edge_image->'source_id'
        OR definition->'target_max' IS DISTINCT FROM '1'::jsonb))
    OR (image->>'side'='t' AND (image->'endpoint_id' IS DISTINCT FROM edge_image->'target_id'
        OR definition->'source_max' IS DISTINCT FROM '1'::jsonb)) THEN
    RAISE EXCEPTION 'original marker parent bound correspondence required' USING ERRCODE='55000';
   END IF;
  END IF;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.edge_limit_scope_original(bytea,jsonb) FROM PUBLIC;
-- Component projection only: this decoder does not confer admission authority.
-- Requires row-touch/observe.sql original JSON and artifact decoders.
CREATE FUNCTION truss.edge_limit_frame_original(original bytea,generation bigint) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE plan jsonb; frame jsonb; selected jsonb; counter text;
 seen text[]:=ARRAY[]::text[]; event jsonb; member text;
BEGIN
 IF generation IS NULL OR generation<0 THEN
  RAISE EXCEPTION 'actual nonnegative global generation required' USING ERRCODE='22023';
 END IF;
 plan:=truss.row_touch_json_original(original);
 IF (SELECT count(*) FROM jsonb_object_keys(plan))<>2
  OR NOT plan ?& ARRAY['interfaceVersion','frames']
  OR plan->>'interfaceVersion' IS DISTINCT FROM 'truss-native-edge-event-frames/0.1'
  OR jsonb_typeof(plan->'frames') IS DISTINCT FROM 'array' THEN
  RAISE EXCEPTION 'closed original edge event projection required' USING ERRCODE='22023';
 END IF;
 IF jsonb_array_length(plan->'frames') NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'bounded original edge event schedule required' USING ERRCODE='54000';
 END IF;
 FOR frame IN SELECT value FROM jsonb_array_elements(plan->'frames') LOOP
  IF jsonb_typeof(frame) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'original event frame object required' USING ERRCODE='22023';
  END IF;
  IF (SELECT count(*) FROM jsonb_object_keys(frame))<>3
   OR NOT frame ?& ARRAY['effectGeneration','event','scope']
   OR jsonb_typeof(frame->'effectGeneration') IS DISTINCT FROM 'string' THEN
   RAISE EXCEPTION 'closed original event frame required' USING ERRCODE='22023';
  END IF;
  counter:=frame->>'effectGeneration';
  IF length(counter)>19 OR counter !~ '^(0|[1-9][0-9]*)$' THEN
   RAISE EXCEPTION 'canonical bounded event generation required' USING ERRCODE='22023';
  END IF;
  IF counter::numeric>9223372036854775807 OR counter=ANY(seen) THEN
   RAISE EXCEPTION 'unique signed-bigint event generation required' USING ERRCODE='22023';
  END IF;
  seen:=array_append(seen,counter);
  event:=frame->'event';
  IF jsonb_typeof(event) IS DISTINCT FROM 'object' THEN
   RAISE EXCEPTION 'original event object required' USING ERRCODE='22023';
  END IF;
  IF (SELECT count(*) FROM jsonb_object_keys(event))<>4
   OR NOT event ?& ARRAY['relation','opcode','oldImage','newImage']
   OR jsonb_typeof(event->'relation') IS DISTINCT FROM 'string'
   OR jsonb_typeof(event->'opcode') IS DISTINCT FROM 'string'
   OR event->>'relation' NOT IN ('edge','edge_limit','rel_def')
   OR event->>'opcode' NOT IN ('INSERT','UPDATE','DELETE') THEN
   RAISE EXCEPTION 'closed original native edge event required' USING ERRCODE='22023';
  END IF;
  FOREACH member IN ARRAY ARRAY['oldImage','newImage'] LOOP
   IF (member='oldImage' AND event->>'opcode'='INSERT')
    OR (member='newImage' AND event->>'opcode'='DELETE') THEN
    IF event->member IS DISTINCT FROM 'null'::jsonb THEN
     RAISE EXCEPTION 'absent native event image required' USING ERRCODE='22023';
    END IF;
   ELSE
    PERFORM truss.edge_limit_image_original(event->>'relation',event->member);
   END IF;
  END LOOP;
  -- Scope bytes retain deleted-parent attribution independently of later reads.
  -- The family producer and trigger must validate their semantic correspondence.
  PERFORM truss.edge_limit_scope_original(truss.row_touch_artifact_original(frame->'scope'),event);
  IF counter=generation::text THEN selected:=frame;END IF;
 END LOOP;
 IF selected IS NULL THEN
  RAISE EXCEPTION 'actual global edge generation not planned' USING ERRCODE='55000';
 END IF;
 RETURN selected;
END;
$$;
REVOKE ALL ON FUNCTION truss.edge_limit_frame_original(bytea,bigint) FROM PUBLIC;
