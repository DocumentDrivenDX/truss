CREATE FUNCTION truss.runtime_manifest_artifact_tree_bytes_candidate(tree jsonb, original_documents bytea[], original_configuration bytea) RETURNS bytea LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path TO pg_catalog, pg_temp AS $$
DECLARE tasks jsonb[]:=ARRAY[jsonb_build_object('node',tree,'depth','0','path','root')]; task jsonb;
 node jsonb; member jsonb; children jsonb; tag text; piece bytea; chunk bytea:=decode('','hex');
 chunks bytea[]:=ARRAY[]::bytea[]; output bytea; i int; depth int; steps int:=0; emitted bigint:=0; configuration_base64 bytea; document_base64 bytea[]:=ARRAY[]::bytea[]; document_seen int[]; configuration_seen int:=0; original_document bytea; original_total bigint:=0; artifact_index int; expected_base64 bytea;
BEGIN
 IF original_documents IS NULL OR array_ndims(original_documents)<>1 OR array_lower(original_documents,1)<>1
  OR cardinality(original_documents) NOT BETWEEN 1 AND 512 OR original_configuration IS NULL
  OR octet_length(original_configuration) NOT BETWEEN 1 AND 4194304 THEN
  RAISE EXCEPTION 'bounded complete original manifest artifacts required' USING ERRCODE='54000'; END IF;
 FOREACH original_document IN ARRAY original_documents LOOP
  IF original_document IS NULL OR octet_length(original_document) NOT BETWEEN 1 AND 1048576 THEN
   RAISE EXCEPTION 'bounded original document required' USING ERRCODE='54000'; END IF;
  original_total:=original_total+octet_length(original_document);
 END LOOP;
 IF original_total>1048576 THEN RAISE EXCEPTION 'aggregate original document capacity' USING ERRCODE='54000'; END IF;
 FOREACH original_document IN ARRAY original_documents LOOP
  document_base64:=array_append(document_base64,convert_to(replace(encode(original_document,'base64'),chr(10),''),'UTF8'));
 END LOOP;
 document_seen:=array_fill(0,ARRAY[cardinality(original_documents)]);
 configuration_base64:=convert_to(replace(encode(original_configuration,'base64'),chr(10),''),'UTF8');
 IF tree IS NULL THEN RAISE EXCEPTION 'inert tree required' USING ERRCODE='22023'; END IF;
 IF octet_length(tree::text)>25165824 THEN RAISE EXCEPTION 'tree input capacity' USING ERRCODE='54000'; END IF;
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
    tasks:=array_append(tasks,jsonb_build_object('node',CASE WHEN tag='array' THEN member ELSE member->'node' END,'depth',(depth+1)::text, 'path',CASE
     WHEN tag='object' AND task->>'path'='root' AND member->>'keyUtf8Hex'='70726572657175697369746573' THEN 'catalogList'
     WHEN tag='object' AND task->>'path'='root' AND member->>'keyUtf8Hex'='636f6e66696775726174696f6e50726572657175697369746573' THEN 'configurationList'
     WHEN tag='array' AND task->>'path'='catalogList' THEN 'catalog:'||i::text
     WHEN tag='array' AND task->>'path'='configurationList' THEN 'configuration:'||i::text
     WHEN tag='object' AND task->>'path' LIKE 'catalog:%' AND member->>'keyUtf8Hex'='6172746966616374' THEN 'catalogArtifact:'||split_part(task->>'path',':',2)
     WHEN tag='object' AND task->>'path'='configuration:0' AND member->>'keyUtf8Hex'='6172746966616374' THEN 'configurationArtifact'
     WHEN tag='object' AND task->>'path' LIKE 'catalogArtifact:%' AND member->>'keyUtf8Hex'='6279746573426173653634' THEN 'catalogBytes:'||split_part(task->>'path',':',2)
     WHEN tag='object' AND task->>'path'='configurationArtifact' AND member->>'keyUtf8Hex'='6279746573426173653634' THEN 'configurationBytes'
     ELSE 'other' END));
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
   IF task->>'path'='root' AND tag IS DISTINCT FROM 'object'
    OR task->>'path' IN ('catalogList','configurationList') AND tag IS DISTINCT FROM 'array'
    OR (task->>'path' LIKE 'catalog:%' OR task->>'path' LIKE 'configuration:%'
     OR task->>'path' LIKE 'catalogArtifact:%' OR task->>'path'='configurationArtifact') AND tag IS DISTINCT FROM 'object'
    OR (task->>'path' LIKE 'catalogBytes:%' OR task->>'path'='configurationBytes') AND tag IS DISTINCT FROM 'string' THEN
    RAISE EXCEPTION 'closed original manifest artifact path kind required' USING ERRCODE='22023'; END IF;
   IF tag='null' AND (SELECT count(*) FROM jsonb_object_keys(node))=1 THEN piece:=convert_to('null','UTF8');
   ELSIF tag='boolean' AND (SELECT count(*) FROM jsonb_object_keys(node))=2 AND jsonb_typeof(node->'value')='boolean' THEN piece:=convert_to(node->>'value','UTF8');
   ELSIF tag='string' AND (SELECT count(*) FROM jsonb_object_keys(node))=2 AND jsonb_typeof(node->'utf8Hex')='string' AND node->>'utf8Hex' ~ '^([0-9a-f]{2})*$' THEN
    IF task->>'path' LIKE 'catalogBytes:%' OR task->>'path'='configurationBytes' THEN
     IF task->>'path'='configurationBytes' THEN expected_base64:=configuration_base64;configuration_seen:=configuration_seen+1;
     ELSE
      artifact_index:=split_part(task->>'path',':',2)::int+1;
      IF artifact_index NOT BETWEEN 1 AND cardinality(document_base64) THEN
       RAISE EXCEPTION 'original document slot correspondence required' USING ERRCODE='55000'; END IF;
      expected_base64:=document_base64[artifact_index];document_seen[artifact_index]:=document_seen[artifact_index]+1;
     END IF;
     IF decode(node->>'utf8Hex','hex') IS DISTINCT FROM expected_base64 THEN
      RAISE EXCEPTION 'exact original manifest artifact base64 required' USING ERRCODE='55000'; END IF;
     piece:=decode('22','hex')||expected_base64||decode('22','hex');
    ELSE piece:=truss.runtime_canonical_string_bytes(decode(node->>'utf8Hex','hex')); END IF;
   ELSIF tag IN ('array','object') AND (SELECT count(*) FROM jsonb_object_keys(node))=2 THEN
    children:=node->CASE WHEN tag='array' THEN 'items' ELSE 'members' END;
    IF jsonb_typeof(children) IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'container inventory' USING ERRCODE='22023'; END IF;
    IF task->>'path'='catalogList' AND jsonb_array_length(children)<>cardinality(original_documents)
     OR task->>'path'='configurationList' AND jsonb_array_length(children)<>1 THEN
     RAISE EXCEPTION 'complete exact manifest artifact array cardinality required' USING ERRCODE='55000'; END IF;
    IF jsonb_array_length(children)>4096 THEN RAISE EXCEPTION 'container inventory capacity' USING ERRCODE='54000'; END IF;
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
    tasks:=array_append(tasks,jsonb_build_object('frame',tag,'children',children,'index','0','depth',depth::text,'path',coalesce(task->>'path','other')));
    piece:=decode(CASE WHEN tag='array' THEN '5b' ELSE '7b' END,'hex');
   ELSE RAISE EXCEPTION 'unsupported inert node or extra content' USING ERRCODE='22023'; END IF;
  END IF;
  emitted:=emitted+octet_length(piece);
  IF emitted>8388608 THEN RAISE EXCEPTION 'complete tree output capacity' USING ERRCODE='54000'; END IF;
  WHILE octet_length(piece)>0 LOOP
   i:=least(65536-octet_length(chunk),octet_length(piece));chunk:=chunk||substr(piece,1,i);piece:=substr(piece,i+1);
   IF octet_length(chunk)=65536 THEN chunks:=array_append(chunks,chunk);chunk:=decode('','hex'); END IF;
  END LOOP;
 END LOOP;
 chunks:=array_append(chunks,chunk);
 SELECT string_agg(value,decode('','hex') ORDER BY ordinal) INTO output FROM unnest(chunks) WITH ORDINALITY AS c(value,ordinal);
 IF configuration_seen<>1 OR EXISTS(SELECT 1 FROM unnest(document_seen) n WHERE n<>1) THEN
  RAISE EXCEPTION 'one exact slot for every original manifest artifact required' USING ERRCODE='55000'; END IF;
 IF octet_length(output)<>emitted THEN RAISE EXCEPTION 'complete tree byte parity' USING ERRCODE='55000'; END IF;
 RETURN output;
END;
$$; REVOKE ALL ON FUNCTION truss.runtime_manifest_artifact_tree_bytes_candidate(jsonb, bytea[], bytea) FROM public