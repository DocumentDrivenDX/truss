-- One complete chunk per page. The metadata-only projection requires separate
-- audit-role membership over the entire source-derived owner union.
CREATE FUNCTION truss.read_import_load_chunk(selected_invocation uuid,selected_chunk int,
 page_limit int,expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor oid;installation truss.catalog_runtime_installation%ROWTYPE;selected truss.runtime_import_load_chunk%ROWTYPE;
 item jsonb;owner jsonb;chunks jsonb;state_value text;all_count int;
 created_count int;skipped_count int;rejected_count int;load_created int;load_skipped int;load_rejected int;
BEGIN
 actor:=truss.runtime_person(false);
 IF selected_invocation IS NULL OR selected_chunk IS NULL OR selected_chunk<0 OR page_limit IS NULL OR page_limit NOT BETWEEN 1 AND 128 THEN
  RAISE EXCEPTION 'bounded import audit page required' USING ERRCODE='22023';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest THEN
  RAISE EXCEPTION 'current import audit release required' USING ERRCODE='0A000';END IF;
 SELECT * INTO selected FROM truss.runtime_import_load_chunk c WHERE c.invocation_id=selected_invocation
  AND c.chunk_index=selected_chunk AND c.writer_xid<>pg_current_xact_id();
 -- Hide whether an unqualified invocation/chunk identifier exists.
 IF NOT FOUND THEN RAISE EXCEPTION 'qualified import audit scope unavailable' USING ERRCODE='P1403';END IF;
 IF selected.owner_inventory_complete IS NOT TRUE THEN
  RAISE EXCEPTION 'complete original load owner inventory required' USING ERRCODE='P1403';END IF;
 IF jsonb_array_length(selected.original_owners)=0 THEN
  -- An admitted empty load has no module scope from which to derive an audit
  -- role, so only an enrolled installation registrar may inspect its metadata.
  PERFORM truss.runtime_person(true);
 END IF;
 FOR owner IN SELECT value FROM jsonb_array_elements(selected.original_owners) LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
    AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
   RAISE EXCEPTION 'complete original load audit membership required' USING ERRCODE='P1403';END IF;
 END LOOP;
 SELECT count(*),coalesce(jsonb_agg(chunk_index::text ORDER BY chunk_index),'[]'::jsonb) INTO all_count,chunks
  FROM truss.runtime_import_load_chunk WHERE invocation_id=selected_invocation AND writer_xid<>pg_current_xact_id();
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(selected.entries) e GROUP BY e.value->>'inputIndex' HAVING count(*)>1) THEN
  RAISE EXCEPTION 'duplicate original load index refused' USING ERRCODE='55000';END IF;
 IF jsonb_array_length(selected.entries)>page_limit THEN RAISE EXCEPTION 'whole load chunk exceeds page limit' USING ERRCODE='54000';END IF;
 state_value:=CASE WHEN all_count=selected.total_chunks AND
  (SELECT count(DISTINCT chunk_index)=selected.total_chunks FROM truss.runtime_import_load_chunk
    WHERE invocation_id=selected_invocation AND writer_xid<>pg_current_xact_id()) THEN 'complete' ELSE 'partial' END;
 SELECT count(*) FILTER(WHERE e.value->>'outcome'='created'),
  count(*) FILTER(WHERE e.value->>'outcome'='skipped'),
  count(*) FILTER(WHERE e.value->>'outcome'='rejected')
  INTO created_count,skipped_count,rejected_count FROM jsonb_array_elements(selected.entries) e(value);
 IF state_value='complete' THEN
  SELECT count(*) FILTER(WHERE e.value->>'outcome'='created'),
   count(*) FILTER(WHERE e.value->>'outcome'='skipped'),
   count(*) FILTER(WHERE e.value->>'outcome'='rejected')
   INTO load_created,load_skipped,load_rejected
   FROM truss.runtime_import_load_chunk c CROSS JOIN LATERAL jsonb_array_elements(c.entries) e(value)
   WHERE c.invocation_id=selected_invocation AND c.writer_xid<>pg_current_xact_id();
 END IF;
 -- Freshly check the full authority union immediately before disclosure.
 FOR owner IN SELECT value FROM jsonb_array_elements(selected.original_owners) LOOP
  IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
   AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
   RAISE EXCEPTION 'load audit authority changed before release' USING ERRCODE='P1403';END IF;
 END LOOP;
 IF jsonb_array_length(selected.original_owners)=0 THEN
  -- Repeat the registrar-only empty-scope admission at the disclosure edge;
  -- the earlier check may have preceded a same-transaction role revocation.
  PERFORM truss.runtime_person(true);
 END IF;
 PERFORM truss.runtime_person(false);
 RETURN convert_to(jsonb_build_object('outcome','page','invocationId',selected.invocation_id::text,
  'loadId',selected.load_id,'assertedOriginSha256',selected.asserted_origin_sha256,'nativeActor',selected.native_actor::text,
  'observedAt',to_char(selected.audit_observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'createdCount',created_count::text,
  'skippedCount',skipped_count::text,'rejectedCount',rejected_count::text,
  'loadCreatedCount',CASE WHEN state_value='complete' THEN load_created::text ELSE NULL END,
  'loadSkippedCount',CASE WHEN state_value='complete' THEN load_skipped::text ELSE NULL END,
  'loadRejectedCount',CASE WHEN state_value='complete' THEN load_rejected::text ELSE NULL END,
  'inputSha256',selected.input_sha256,'inputCount',selected.input_count::text,
  'totalChunks',selected.total_chunks::text,'observedChunks',chunks,'state',state_value,
  'entries',selected.entries,'nextChunk',CASE WHEN selected.chunk_index+1<selected.total_chunks
    THEN (selected.chunk_index+1)::text ELSE NULL END)::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.read_import_load_chunk(uuid,int,int,text,text) FROM PUBLIC;

-- A listing cursor freezes the visibility frontier and exact filters. Pages
-- identify one invocation, never one chunk masquerading as a load.
CREATE FUNCTION truss.runtime_import_load_audit_cursor(selected_installation uuid,
 selected_epoch uuid,selected_release text,selected_digest text,frontier xid8,
 selected_filters_sha text,last_observed timestamptz,last_invocation uuid) RETURNS bytea
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 SELECT convert_to(jsonb_build_object('profile','truss-import-load-audit-cursor/0.2',
  'installationId',selected_installation::text,'sourceEpoch',selected_epoch,
  'releaseId',selected_release,'releaseSha256',selected_digest,
  'frontierXid',frontier::text,'filtersSha256',selected_filters_sha,
  'afterObservedAt',to_char(last_observed AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
  'afterInvocationId',last_invocation::text)::text,'UTF8');
$$;
REVOKE ALL ON FUNCTION truss.runtime_import_load_audit_cursor(uuid,uuid,text,text,xid8,text,timestamptz,uuid) FROM PUBLIC;

CREATE FUNCTION truss.page_import_load_audit(filters jsonb,maximum_entries int,original_cursor bytea,
 expected_release text,expected_digest text) RETURNS bytea
LANGUAGE plpgsql VOLATILE SECURITY DEFINER SET search_path=pg_catalog,pg_temp
 SET row_security=off SET TimeZone='UTC' AS $$
DECLARE actor oid;installation truss.catalog_runtime_installation%ROWTYPE;
 filter_sha text;cursor_value jsonb;frontier xid8;last_observed timestamptz;last_invocation uuid;
 candidate record;cursor_bytes bytea;owner jsonb;owners jsonb;entries jsonb;observed_chunks jsonb;
 source_row truss.runtime_import_load_chunk%ROWTYPE;visible_count int;expected_chunks int;state_value text;
 created_count int;skipped_count int;rejected_count int;observed_from timestamptz;observed_until timestamptz;
 release_check boolean;from_time timestamptz;until_time timestamptz;selected_owners jsonb;
BEGIN
 actor:=truss.runtime_person(false);
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a
   WHERE truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
  RAISE EXCEPTION 'current import audit enrollment required' USING ERRCODE='P1403';END IF;
 IF filters IS NULL OR jsonb_typeof(filters) IS DISTINCT FROM 'object'
  OR filters-ARRAY['invocationId','loadId','nativeActorOid','documentId','moduleId','observedAtFrom','observedAtUntil']<>'{}'::jsonb
  OR maximum_entries IS NULL OR maximum_entries NOT BETWEEN 1 AND 1024 THEN
  RAISE EXCEPTION 'bounded import audit listing required' USING ERRCODE='22023';END IF;
 IF filters ? 'invocationId' AND (jsonb_typeof(filters->'invocationId') IS DISTINCT FROM 'string'
  OR filters->>'invocationId' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
  OR filters ? 'loadId' AND (jsonb_typeof(filters->'loadId') IS DISTINCT FROM 'string'
   OR octet_length(filters->>'loadId') NOT BETWEEN 1 AND 4096)
  OR filters ? 'nativeActorOid' AND (jsonb_typeof(filters->'nativeActorOid') IS DISTINCT FROM 'string'
   OR filters->>'nativeActorOid' !~ '^[1-9][0-9]{0,9}$' OR (filters->>'nativeActorOid')::numeric>4294967295)
  OR (filters ? 'documentId') IS DISTINCT FROM (filters ? 'moduleId')
  OR filters ? 'documentId' IS NOT TRUE OR filters ? 'moduleId' IS NOT TRUE
  OR filters ? 'documentId' AND (jsonb_typeof(filters->'documentId') IS DISTINCT FROM 'string'
   OR octet_length(filters->>'documentId') NOT BETWEEN 1 AND 4096
   OR jsonb_typeof(filters->'moduleId') IS DISTINCT FROM 'string'
   OR octet_length(filters->>'moduleId') NOT BETWEEN 1 AND 4096)
  OR filters ? 'observedAtFrom' AND (jsonb_typeof(filters->'observedAtFrom') IS DISTINCT FROM 'string'
   OR filters->>'observedAtFrom' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})$')
  OR filters ? 'observedAtUntil' AND (jsonb_typeof(filters->'observedAtUntil') IS DISTINCT FROM 'string'
   OR filters->>'observedAtUntil' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+-][0-9]{2}:[0-9]{2})$') THEN
  RAISE EXCEPTION 'canonical import audit listing filters required' USING ERRCODE='22023';END IF;
 IF filters ? 'observedAtFrom' OR filters ? 'observedAtUntil' THEN
  BEGIN
   from_time:=CASE WHEN filters ? 'observedAtFrom' THEN (filters->>'observedAtFrom')::timestamptz END;
   until_time:=CASE WHEN filters ? 'observedAtUntil' THEN (filters->>'observedAtUntil')::timestamptz END;
  EXCEPTION WHEN SQLSTATE '22007' OR SQLSTATE '22008' THEN
   RAISE EXCEPTION 'canonical import audit time filters required' USING ERRCODE='22023';END;
  IF from_time IS NOT NULL AND until_time IS NOT NULL AND from_time>=until_time THEN
   RAISE EXCEPTION 'ordered import audit observed-time range required' USING ERRCODE='22023';END IF;
 END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a
   WHERE a.document_id=filters->>'documentId' AND a.module=filters->>'moduleId'
    AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
  RAISE EXCEPTION 'qualified import audit module enrollment required' USING ERRCODE='P1403';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF installation.release_id IS DISTINCT FROM expected_release OR installation.release_sha256 IS DISTINCT FROM expected_digest
  OR pg_is_in_recovery() THEN RAISE EXCEPTION 'current import audit release required' USING ERRCODE='0A000';END IF;
 filter_sha:=encode(sha256(convert_to(filters::text,'UTF8')),'hex');
 frontier:=pg_catalog.pg_snapshot_xmin(pg_catalog.pg_current_snapshot());
 IF original_cursor IS NOT NULL THEN
  IF octet_length(original_cursor) NOT BETWEEN 1 AND 65536
   OR (convert_from(original_cursor,'UTF8') IS JSON OBJECT WITH UNIQUE KEYS) IS NOT TRUE THEN
   RAISE EXCEPTION 'bounded exact import audit listing cursor required' USING ERRCODE='22023';END IF;
  cursor_value:=convert_from(original_cursor,'UTF8')::jsonb;
  IF cursor_value-ARRAY['profile','installationId','sourceEpoch','releaseId','releaseSha256','frontierXid',
       'filtersSha256','afterObservedAt','afterInvocationId']<>'{}'::jsonb
   OR cursor_value->>'profile' IS DISTINCT FROM 'truss-import-load-audit-cursor/0.2'
   OR cursor_value->>'installationId' IS DISTINCT FROM installation.installation_id::text
   OR cursor_value->>'sourceEpoch' IS DISTINCT FROM installation.source_epoch::text
   OR cursor_value->>'releaseId' IS DISTINCT FROM expected_release
   OR cursor_value->>'releaseSha256' IS DISTINCT FROM expected_digest
   OR cursor_value->>'filtersSha256' IS DISTINCT FROM filter_sha
   OR jsonb_typeof(cursor_value->'frontierXid') IS DISTINCT FROM 'string'
   OR cursor_value->>'frontierXid' !~ '^[1-9][0-9]{0,19}$'
   OR (cursor_value->>'frontierXid')::numeric>18446744073709551615
   OR jsonb_typeof(cursor_value->'afterObservedAt') IS DISTINCT FROM 'string'
   OR cursor_value->>'afterObservedAt' !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$'
   OR jsonb_typeof(cursor_value->'afterInvocationId') IS DISTINCT FROM 'string'
   OR cursor_value->>'afterInvocationId' !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$' THEN
   RAISE EXCEPTION 'current import audit listing cursor context required' USING ERRCODE='P1002';END IF;
  frontier:=(cursor_value->>'frontierXid')::xid8;
  BEGIN last_observed:=(cursor_value->>'afterObservedAt')::timestamptz;
  EXCEPTION WHEN SQLSTATE '22007' OR SQLSTATE '22008' THEN
   RAISE EXCEPTION 'canonical import audit cursor time required' USING ERRCODE='22023';END;
  last_invocation:=(cursor_value->>'afterInvocationId')::uuid;
  IF cursor_value IS DISTINCT FROM convert_from(truss.runtime_import_load_audit_cursor(
    installation.installation_id,installation.source_epoch,expected_release,expected_digest,
    frontier,filter_sha,last_observed,last_invocation),'UTF8')::jsonb
   OR frontier>pg_catalog.pg_snapshot_xmin(pg_catalog.pg_current_snapshot()) THEN
   RAISE EXCEPTION 'exact frozen import audit listing cursor required' USING ERRCODE='P1002';END IF;
 ELSE
  last_observed:='infinity'::timestamptz;last_invocation:='ffffffff-ffff-ffff-ffff-ffffffffffff'::uuid;
 END IF;
 FOR candidate IN
  SELECT c.invocation_id,max(c.audit_observed_at) observed_until
   FROM truss.runtime_import_load_chunk c
   WHERE c.writer_xid<frontier
   GROUP BY c.invocation_id
   HAVING (original_cursor IS NULL OR (max(c.audit_observed_at),c.invocation_id)<(last_observed,last_invocation))
    AND (NOT filters ? 'documentId' OR bool_or(c.original_owners @> jsonb_build_array(
      jsonb_build_object('documentId',filters->>'documentId','moduleId',filters->>'moduleId'))))
    AND (from_time IS NULL OR max(c.audit_observed_at)>=from_time)
    AND (until_time IS NULL OR min(c.audit_observed_at)<until_time)
   ORDER BY max(c.audit_observed_at) DESC,c.invocation_id DESC
 LOOP
  SELECT * INTO STRICT source_row FROM truss.runtime_import_load_chunk c
   WHERE c.invocation_id=candidate.invocation_id AND c.writer_xid<frontier ORDER BY c.chunk_index LIMIT 1;
  -- Each invocation must retain one exact origin/input/owner/actor basis.
  IF EXISTS(SELECT 1 FROM truss.runtime_import_load_chunk c WHERE c.invocation_id=candidate.invocation_id
    AND c.writer_xid<frontier AND (c.load_id IS DISTINCT FROM source_row.load_id
     OR c.original_asserted_origin IS DISTINCT FROM source_row.original_asserted_origin
     OR c.asserted_origin_sha256 IS DISTINCT FROM source_row.asserted_origin_sha256
     OR c.input_sha256 IS DISTINCT FROM source_row.input_sha256 OR c.input_count IS DISTINCT FROM source_row.input_count
     OR c.total_chunks IS DISTINCT FROM source_row.total_chunks OR c.original_owners IS DISTINCT FROM source_row.original_owners
     OR c.owner_inventory_complete IS DISTINCT FROM source_row.owner_inventory_complete
     OR c.native_actor IS DISTINCT FROM source_row.native_actor OR c.native_actor_name IS DISTINCT FROM source_row.native_actor_name)) THEN
   RAISE EXCEPTION 'inconsistent retained import invocation' USING ERRCODE='P1010';END IF;
  IF source_row.owner_inventory_complete IS NOT TRUE THEN
   RAISE EXCEPTION 'complete original import owner inventory required' USING ERRCODE='P1403';END IF;
  owners:=source_row.original_owners;
  IF jsonb_array_length(owners)=0 THEN PERFORM truss.runtime_person(true);END IF;
  FOR owner IN SELECT value FROM jsonb_array_elements(owners) LOOP
   IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
     AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
    RAISE EXCEPTION 'complete original load audit membership required' USING ERRCODE='P1403';END IF;
  END LOOP;
  IF filters ? 'invocationId' AND candidate.invocation_id::text IS DISTINCT FROM filters->>'invocationId' THEN CONTINUE;END IF;
  IF filters ? 'loadId' AND source_row.load_id IS DISTINCT FROM filters->>'loadId' THEN CONTINUE;END IF;
  IF filters ? 'nativeActorOid' AND source_row.native_actor::text IS DISTINCT FROM filters->>'nativeActorOid' THEN CONTINUE;END IF;
  SELECT coalesce(jsonb_agg(c.chunk_index::text ORDER BY c.chunk_index),'[]'::jsonb),count(*),min(c.audit_observed_at),max(c.audit_observed_at)
   INTO observed_chunks,visible_count,observed_from,observed_until
   FROM truss.runtime_import_load_chunk c WHERE c.invocation_id=candidate.invocation_id AND c.writer_xid<frontier;
  expected_chunks:=source_row.total_chunks;
  state_value:=CASE WHEN visible_count=expected_chunks AND
   (SELECT count(DISTINCT c.chunk_index)=expected_chunks FROM truss.runtime_import_load_chunk c
    WHERE c.invocation_id=candidate.invocation_id AND c.writer_xid<frontier) THEN 'complete' ELSE 'partial' END;
  SELECT count(*) FILTER(WHERE e.value->>'outcome'='created'),
   count(*) FILTER(WHERE e.value->>'outcome'='skipped'),
   count(*) FILTER(WHERE e.value->>'outcome'='rejected')
   INTO created_count,skipped_count,rejected_count
   FROM truss.runtime_import_load_chunk c CROSS JOIN LATERAL jsonb_array_elements(c.entries) e(value)
   WHERE c.invocation_id=candidate.invocation_id AND c.writer_xid<frontier;
  SELECT coalesce(jsonb_agg(jsonb_build_object('chunkIndex',c.chunk_index::text,
     'observedAt',to_char(c.audit_observed_at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
     'createdCount',(SELECT count(*) FROM jsonb_array_elements(c.entries) e(value) WHERE e.value->>'outcome'='created')::text,
     'skippedCount',(SELECT count(*) FROM jsonb_array_elements(c.entries) e(value) WHERE e.value->>'outcome'='skipped')::text,
     'rejectedCount',(SELECT count(*) FROM jsonb_array_elements(c.entries) e(value) WHERE e.value->>'outcome'='rejected')::text)
     ORDER BY c.chunk_index),'[]'::jsonb)
   INTO entries FROM truss.runtime_import_load_chunk c
   WHERE c.invocation_id=candidate.invocation_id AND c.writer_xid<frontier;
  IF jsonb_array_length(entries)>maximum_entries THEN RAISE EXCEPTION 'whole import audit invocation exceeds page limit' USING ERRCODE='54000';END IF;
  cursor_bytes:=truss.runtime_import_load_audit_cursor(installation.installation_id,installation.source_epoch,
    expected_release,expected_digest,frontier,filter_sha,candidate.observed_until,candidate.invocation_id);
  -- Freshly recheck the complete owner union before release.
  IF jsonb_array_length(owners)=0 THEN PERFORM truss.runtime_person(true);END IF;
  FOR owner IN SELECT value FROM jsonb_array_elements(owners) LOOP
   IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a WHERE a.document_id=owner->>'documentId'
     AND a.module=owner->>'moduleId' AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
    RAISE EXCEPTION 'load audit authority changed before listing release' USING ERRCODE='P1403';END IF;
  END LOOP;
  PERFORM truss.runtime_person(false);
  RETURN convert_to(jsonb_build_object('outcome','summary','invocationId',candidate.invocation_id::text,
   'loadId',source_row.load_id,'assertedOriginSha256',source_row.asserted_origin_sha256,
   'nativeActorOid',source_row.native_actor::text,'nativeActorName',source_row.native_actor_name,
   'inputSha256',source_row.input_sha256,'inputCount',source_row.input_count::text,
   'totalChunks',expected_chunks::text,'observedChunkCount',visible_count::text,'observedChunks',observed_chunks,
   'state',state_value,'observedAtFrom',to_char(observed_from AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'observedAtUntil',to_char(observed_until AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
   'createdCount',created_count::text,'skippedCount',skipped_count::text,'rejectedCount',rejected_count::text,
   'chunks',entries,'nextPageCursor',convert_from(cursor_bytes,'UTF8')::jsonb)::text,'UTF8');
 END LOOP;
 IF NOT EXISTS(SELECT 1 FROM truss.runtime_import_audit_access a
   WHERE a.document_id=filters->>'documentId' AND a.module=filters->>'moduleId'
    AND truss.runtime_audit_role_member(actor,a.auditor_oid)) THEN
  RAISE EXCEPTION 'load audit module authority changed before empty-page release' USING ERRCODE='P1403';END IF;
 PERFORM truss.runtime_person(false);
 RETURN convert_to('{"outcome":"end","nextPageCursor":null}'::text,'UTF8');
END;
$$;
REVOKE ALL ON FUNCTION truss.page_import_load_audit(jsonb,int,bytea,text,text) FROM PUBLIC;
