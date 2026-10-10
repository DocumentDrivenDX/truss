CREATE FUNCTION truss.runtime_report_tree_bytes_v0_2(tree jsonb) RETURNS bytea LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE tasks jsonb[]:=ARRAY[jsonb_build_object('node',tree,'depth','0')]; task jsonb;
 node jsonb; member jsonb; children jsonb; tag text; piece bytea; chunk bytea:=decode('','hex');
 chunks bytea[]:=ARRAY[]::bytea[]; output bytea; i int; depth int; steps int:=0; emitted bigint:=0;
BEGIN
 IF tree IS NULL THEN RAISE EXCEPTION 'inert tree required' USING ERRCODE='22023'; END IF;
 IF octet_length(tree::text)>4194304 THEN RAISE EXCEPTION 'tree input capacity' USING ERRCODE='54000'; END IF;
 WHILE cardinality(tasks)>0 LOOP
  steps:=steps+1;
  IF steps>32768 OR cardinality(tasks)>16384 THEN RAISE EXCEPTION 'tree task capacity' USING ERRCODE='54000'; END IF;
  task:=tasks[cardinality(tasks)];tasks:=tasks[1:cardinality(tasks)-1];piece:=decode('','hex');
  IF task ? 'emit' THEN piece:=decode(task->>'emit','hex');
  ELSIF task ? 'frame' THEN
   children:=task->'children';tag:=task->>'frame';i:=(task->>'index')::int;depth:=(task->>'depth')::int;
   IF i=jsonb_array_length(children) THEN piece:=decode(CASE WHEN tag='array' THEN '5d' ELSE '7d' END,'hex');
   ELSE
    member:=children->i;
    tasks:=array_append(tasks,jsonb_set(task,'{index}',to_jsonb((i+1)::text)));
    tasks:=array_append(tasks,jsonb_build_object('node',CASE WHEN tag='array' THEN member ELSE member->'node' END,'depth',(depth+1)::text));
    IF tag='object' THEN
     tasks:=array_append(tasks,jsonb_build_object('emit','3a'));
     tasks:=array_append(tasks,jsonb_build_object('node',jsonb_build_object('kind','string','utf8Hex',member->>'keyUtf8Hex'),'depth',(depth+1)::text));
    END IF;
    IF i>0 THEN piece:=decode('2c','hex'); END IF;
   END IF;
  ELSE
   node:=task->'node';depth:=(task->>'depth')::int;
   IF depth>256 THEN RAISE EXCEPTION 'tree depth capacity' USING ERRCODE='54000'; END IF;
   IF node IS NULL OR jsonb_typeof(node)<>'object' OR jsonb_typeof(node->'kind') IS DISTINCT FROM 'string' THEN RAISE EXCEPTION 'inert node shape' USING ERRCODE='22023'; END IF;
   tag:=node->>'kind';
   IF tag='null' AND (SELECT count(*) FROM jsonb_object_keys(node))=1 THEN piece:=convert_to('null','UTF8');
   ELSIF tag='boolean' AND (SELECT count(*) FROM jsonb_object_keys(node))=2 AND jsonb_typeof(node->'value')='boolean' THEN piece:=convert_to(node->>'value','UTF8');
   ELSIF tag='string' AND (SELECT count(*) FROM jsonb_object_keys(node))=2 AND jsonb_typeof(node->'utf8Hex')='string' AND node->>'utf8Hex' ~ '^([0-9a-f]{2})*$' THEN piece:=truss.runtime_report_scalar_bytes_v0_2(decode(node->>'utf8Hex','hex'));
   ELSIF tag IN ('array','object') AND (SELECT count(*) FROM jsonb_object_keys(node))=2 THEN
    children:=node->CASE WHEN tag='array' THEN 'items' ELSE 'members' END;
    IF jsonb_typeof(children) IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'container inventory' USING ERRCODE='22023'; END IF;
    IF jsonb_array_length(children)>4096 THEN RAISE EXCEPTION 'container inventory capacity' USING ERRCODE='54000'; END IF;
    IF tag='object' THEN
     FOR member IN SELECT value FROM jsonb_array_elements(children) LOOP
      IF jsonb_typeof(member)<>'object' OR (SELECT count(*) FROM jsonb_object_keys(member))<>2
       OR NOT member ?& ARRAY['keyUtf8Hex','node'] OR jsonb_typeof(member->'keyUtf8Hex') IS DISTINCT FROM 'string'
       OR member->>'keyUtf8Hex' !~ '^([0-9a-f]{2})*$' THEN RAISE EXCEPTION 'object member shape' USING ERRCODE='22023'; END IF;
      PERFORM truss.runtime_report_scalar_bytes_v0_2(decode(member->>'keyUtf8Hex','hex'));
     END LOOP;
     IF (SELECT count(DISTINCT decode(value->>'keyUtf8Hex','hex')) FROM jsonb_array_elements(children))<>jsonb_array_length(children) THEN RAISE EXCEPTION 'duplicate original object key' USING ERRCODE='22023'; END IF;
     SELECT coalesce(jsonb_agg(value ORDER BY decode(value->>'keyUtf8Hex','hex')),'[]'::jsonb) INTO children FROM jsonb_array_elements(children);
    END IF;
    tasks:=array_append(tasks,jsonb_build_object('frame',tag,'children',children,'index','0','depth',depth::text));
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
$$; REVOKE ALL ON FUNCTION truss.runtime_report_tree_bytes_v0_2(jsonb) FROM public