-- Private inert-tree codec component; not an admitted AcceptanceReport producer.
-- Strings/keys carry original UTF-8 as lowercase hex. Numbers are unsupported.
CREATE FUNCTION truss.runtime_canonical_tree_bytes(tree jsonb) RETURNS bytea
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE tasks jsonb[]:=ARRAY[jsonb_build_object('node',tree,'depth','0')]; task jsonb;
 node jsonb; member jsonb; children jsonb; tag text; piece bytea; chunk bytea:=decode('','hex');
 chunks bytea[]:=ARRAY[]::bytea[]; output bytea; i int; depth int; steps int:=0; emitted bigint:=0;
BEGIN
 IF tree IS NULL OR octet_length(tree::text)>4194304 THEN RAISE EXCEPTION 'bounded inert tree required' USING ERRCODE='22023'; END IF;
 WHILE cardinality(tasks)>0 LOOP
  steps:=steps+1;
  IF steps>32768 OR cardinality(tasks)>16384 THEN RAISE EXCEPTION 'tree task capacity' USING ERRCODE='54000'; END IF;
  task:=tasks[cardinality(tasks)];tasks:=tasks[1:cardinality(tasks)-1];piece:=NULL;
  IF task ? 'emit' THEN piece:=decode(task->>'emit','hex');
  ELSE
   node:=task->'node';depth:=(task->>'depth')::int;
   IF depth>256 THEN RAISE EXCEPTION 'tree depth capacity' USING ERRCODE='54000'; END IF;
   IF node IS NULL OR jsonb_typeof(node)<>'object' OR jsonb_typeof(node->'kind') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'inert node shape' USING ERRCODE='22023'; END IF;
   tag:=node->>'kind';
   IF tag='null' AND (SELECT count(*) FROM jsonb_object_keys(node))=1 THEN piece:=convert_to('null','UTF8');
   ELSIF tag='boolean' AND (SELECT count(*) FROM jsonb_object_keys(node))=2 AND jsonb_typeof(node->'value')='boolean' THEN piece:=convert_to(node->>'value','UTF8');
   ELSIF tag='string' AND (SELECT count(*) FROM jsonb_object_keys(node))=2 AND jsonb_typeof(node->'utf8Hex')='string' AND node->>'utf8Hex' ~ '^([0-9a-f]{2})*$' THEN piece:=truss.runtime_canonical_string_bytes(decode(node->>'utf8Hex','hex'));
   ELSIF tag IN ('array','object') AND (SELECT count(*) FROM jsonb_object_keys(node))=2 THEN
    children:=node->CASE WHEN tag='array' THEN 'items' ELSE 'members' END;
    IF jsonb_typeof(children) IS DISTINCT FROM 'array' OR jsonb_array_length(children)>4096 THEN RAISE EXCEPTION 'container inventory' USING ERRCODE='22023'; END IF;
    IF tag='object' THEN
     FOR member IN SELECT value FROM jsonb_array_elements(children) LOOP
      IF jsonb_typeof(member)<>'object' OR (SELECT count(*) FROM jsonb_object_keys(member))<>2
       OR NOT member ?& ARRAY['keyUtf8Hex','node'] OR jsonb_typeof(member->'keyUtf8Hex') IS DISTINCT FROM 'string'
       OR member->>'keyUtf8Hex' !~ '^([0-9a-f]{2})*$' THEN RAISE EXCEPTION 'object member shape' USING ERRCODE='22023'; END IF;
      PERFORM truss.runtime_canonical_string_bytes(decode(member->>'keyUtf8Hex','hex'));
     END LOOP;
     IF (SELECT count(DISTINCT decode(value->>'keyUtf8Hex','hex')) FROM jsonb_array_elements(children))<>jsonb_array_length(children) THEN RAISE EXCEPTION 'duplicate original object key' USING ERRCODE='22023'; END IF;
     SELECT coalesce(jsonb_agg(value ORDER BY decode(value->>'keyUtf8Hex','hex')),'[]'::jsonb) INTO children FROM jsonb_array_elements(children);
    END IF;
    tasks:=array_append(tasks,jsonb_build_object('emit',CASE WHEN tag='array' THEN '5d' ELSE '7d' END));
    IF jsonb_array_length(children)>0 THEN
     FOR i IN REVERSE jsonb_array_length(children)-1..0 LOOP
      member:=children->i;
      tasks:=array_append(tasks,jsonb_build_object('node',CASE WHEN tag='array' THEN member ELSE member->'node' END,'depth',(depth+1)::text));
      IF tag='object' THEN
       tasks:=array_append(tasks,jsonb_build_object('emit','3a'));
       tasks:=array_append(tasks,jsonb_build_object('node',jsonb_build_object('kind','string','utf8Hex',member->>'keyUtf8Hex'),'depth',(depth+1)::text));
      END IF;
      IF i>0 THEN tasks:=array_append(tasks,jsonb_build_object('emit','2c')); END IF;
     END LOOP;
    END IF;
    piece:=decode(CASE WHEN tag='array' THEN '5b' ELSE '7b' END,'hex');
   ELSE RAISE EXCEPTION 'unsupported inert node or extra content' USING ERRCODE='22023'; END IF;
  END IF;
  emitted:=emitted+octet_length(piece);
  IF emitted>4194304 THEN RAISE EXCEPTION 'complete tree output capacity' USING ERRCODE='54000'; END IF;
  WHILE octet_length(piece)>0 LOOP
   i:=least(65536-octet_length(chunk),octet_length(piece));chunk:=chunk||substr(piece,1,i);piece:=substr(piece,i+1);
   IF octet_length(chunk)=65536 THEN chunks:=array_append(chunks,chunk);chunk:=decode('','hex'); END IF;
  END LOOP;
 END LOOP;
 chunks:=array_append(chunks,chunk);
 SELECT string_agg(value,decode('','hex') ORDER BY ordinal) INTO output FROM unnest(chunks) WITH ORDINALITY AS c(value,ordinal);
 IF octet_length(output)<>emitted THEN RAISE EXCEPTION 'complete tree byte parity' USING ERRCODE='55000'; END IF;
 RETURN output;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_canonical_tree_bytes(jsonb) FROM PUBLIC;
