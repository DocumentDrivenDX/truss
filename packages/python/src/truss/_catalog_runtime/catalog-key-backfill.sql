-- Registration-owned alternate-key effects; object images remain unchanged.
-- This source is not installed until the native62 public acceptance path lands.
CREATE TABLE truss.runtime_catalog_key_backfill (
 transition_id bigint PRIMARY KEY DEFAULT nextval('truss.runtime_object_transition_seq'),
 registration_id uuid NOT NULL REFERENCES truss.catalog_registration_request(registration_id) DEFERRABLE INITIALLY DEFERRED,
 writer_xid xid8 NOT NULL,actor_oid oid NOT NULL,
 revision int NOT NULL REFERENCES truss.schema_rev(rev),
 object_id bigint NOT NULL,type_id int NOT NULL,
 object_image jsonb NOT NULL,after_keys jsonb NOT NULL,effects jsonb NOT NULL,
 UNIQUE(registration_id,object_id,type_id),
 CHECK(jsonb_typeof(object_image)='object' AND jsonb_typeof(after_keys)='array'
  AND jsonb_typeof(effects)='array' AND jsonb_array_length(effects)>0)
);
CREATE INDEX runtime_catalog_key_backfill_owner ON truss.runtime_catalog_key_backfill(object_id,type_id,transition_id DESC);
CREATE INDEX runtime_catalog_key_backfill_writer ON truss.runtime_catalog_key_backfill(writer_xid);
CREATE TRIGGER runtime_catalog_key_backfill_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_catalog_key_backfill
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_catalog_key_backfill FROM PUBLIC;

CREATE CONSTRAINT TRIGGER runtime_catalog_key_backfill_commit AFTER INSERT ON truss.runtime_catalog_key_backfill
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION truss.runtime_object_commit_check();
ALTER TABLE truss.runtime_catalog_key_backfill ENABLE ALWAYS TRIGGER runtime_catalog_key_backfill_commit;
ALTER TABLE truss.runtime_catalog_key_backfill ENABLE ALWAYS TRIGGER runtime_catalog_key_backfill_immutable;

-- Planned basis and original UMF key receipts follow.
CREATE FUNCTION truss.catalog_key_backfill_candidates(planned_basis jsonb,selected_revision int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE definition truss.key_def%ROWTYPE;owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;
 object_row truss.object%ROWTYPE;component int;values_cells jsonb;archive truss.schema_doc%ROWTYPE;result jsonb:='[]';candidate_count int:=0;head int;selected_cell jsonb;
BEGIN
 PERFORM truss.catalog_actor();
 SELECT rev INTO STRICT head FROM truss.schema_head WHERE id=1 FOR UPDATE NOWAIT;
 IF selected_revision IS DISTINCT FROM head+1 OR planned_basis IS NULL THEN
  RAISE EXCEPTION 'original locked next catalog basis required' USING ERRCODE='55000';END IF;
 FOR definition IN SELECT k.* FROM jsonb_populate_recordset(NULL::truss.key_def,planned_basis->'key_def') k
  WHERE k.since_rev=selected_revision AND EXISTS(SELECT 1 FROM truss.type_def t WHERE t.type_id=k.type_id)
  AND NOT EXISTS(SELECT 1 FROM truss.key_def old WHERE old.type_id=k.type_id AND old.key_id=k.key_id)
  ORDER BY k.type_id,k.key_num LOOP
  IF definition.is_primary OR cardinality(definition.prop_ids) NOT BETWEEN 1 AND 127 THEN
   RAISE EXCEPTION 'new bounded alternate key required' USING ERRCODE='0A000';END IF;
  SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=definition.type_id AND retired_rev IS NULL;
  PERFORM truss.runtime_module_writer(owner.document_id,owner.module);
  IF truss.runtime_object_values_readable(owner.type_id) IS NOT TRUE THEN
   RAISE EXCEPTION 'current key backfill reader required' USING ERRCODE='42501';END IF;
  FOREACH component IN ARRAY definition.prop_ids LOOP
   SELECT * INTO STRICT property FROM jsonb_populate_recordset(NULL::truss.prop_def,planned_basis->'prop_def') p WHERE p.prop_id=component AND p.type_id=owner.type_id AND p.retired_rev IS NULL;
   IF property.nullability IS DISTINCT FROM 'required' OR property.cardinality IS DISTINCT FROM 'one'
    OR property.scalar_type NOT IN ('string','integer','decimal','boolean','binary') THEN
    RAISE EXCEPTION 'required scalar key components required' USING ERRCODE='0A000';END IF;
   IF truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE THEN
    RAISE EXCEPTION 'current planned key component reader required' USING ERRCODE='42501';END IF;
  END LOOP;
  SELECT * INTO STRICT archive FROM jsonb_populate_recordset(NULL::truss.schema_doc,planned_basis->'schema_doc') d
   WHERE d.rev=definition.definition_rev AND d.ord=definition.definition_doc_ord AND d.doc_id=definition.definition_document_id;
  IF archive.content_sha256 IS DISTINCT FROM encode(sha256(convert_to(archive.document,'UTF8')),'hex') THEN
   RAISE EXCEPTION 'original planned document bytes required' USING ERRCODE='55000';END IF;
  IF EXISTS(SELECT 1 FROM truss.object o WHERE o.type_id=owner.type_id AND (o.root_id IS NOT NULL OR o.root_type IS NOT NULL)) THEN RAISE EXCEPTION 'owned catalog key backfill requires a supported ownership profile' USING ERRCODE='0A000';END IF;
  FOR object_row IN SELECT o.* FROM truss.object o WHERE o.type_id=owner.type_id ORDER BY o.id FOR UPDATE LOOP
   candidate_count:=candidate_count+1;values_cells:='[]';
   IF candidate_count>10000 THEN RAISE EXCEPTION 'bounded key backfill inventory required' USING ERRCODE='54000';END IF;
   FOREACH component IN ARRAY definition.prop_ids LOOP
    SELECT * INTO STRICT property FROM jsonb_populate_recordset(NULL::truss.prop_def,planned_basis->'prop_def') p WHERE p.prop_id=component AND p.type_id=owner.type_id;
    IF EXISTS(SELECT 1 FROM truss.prop_def p WHERE p.prop_id=component AND p.type_id=owner.type_id) THEN
     selected_cell:=object_row.props->component::text;
    ELSE
     IF property.since_rev IS DISTINCT FROM selected_revision OR object_row.props ? component::text THEN
      RAISE EXCEPTION 'genuinely new absent key destination required' USING ERRCODE='55000';END IF;
     selected_cell:=object_row.retained->property.name;
    END IF;
    IF truss.valid_scalar_property(selected_cell,property.scalar_type,false,property.facets) IS NOT TRUE THEN
     RAISE EXCEPTION 'valid complete key candidate values required' USING ERRCODE='22023';END IF;
    values_cells:=values_cells||jsonb_build_array(selected_cell);
   END LOOP;
   result:=result||jsonb_build_array(jsonb_build_object('documentId',owner.document_id,'moduleId',owner.module,
    'recordId',owner.element,'keyId',definition.key_id,'keyNumber',definition.key_num::text,'typeId',owner.type_id::text,
    'objectId',object_row.id::text,'objectVersion',object_row.ver::text,'sourceRevision',archive.rev::text,'sourceOrdinal',archive.ord::text,
    'sourceDocumentId',archive.doc_id,'sourceSha256',archive.content_sha256,
    'objectImageSha256',encode(sha256(convert_to(to_jsonb(object_row)::text,'UTF8')),'hex'),'values',values_cells));
   IF octet_length(convert_to(result::text,'UTF8'))>8388608 THEN
    RAISE EXCEPTION 'bounded original key candidate bytes required' USING ERRCODE='54000';END IF;
  END LOOP;
 END LOOP;
 PERFORM truss.catalog_actor();
 FOR owner IN SELECT t.* FROM truss.type_def t WHERE EXISTS(SELECT 1 FROM jsonb_array_elements(result) c WHERE c.value->>'typeId'=t.type_id::text) ORDER BY t.type_id LOOP
  PERFORM truss.runtime_module_writer(owner.document_id,owner.module);
  IF truss.runtime_object_values_readable(owner.type_id) IS NOT TRUE THEN
   RAISE EXCEPTION 'current key backfill disclosure reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 FOR property IN SELECT p.* FROM jsonb_populate_recordset(NULL::truss.prop_def,planned_basis->'prop_def') p
  WHERE EXISTS(SELECT 1 FROM jsonb_populate_recordset(NULL::truss.key_def,planned_basis->'key_def') k
   WHERE k.since_rev=selected_revision AND k.type_id=p.type_id AND p.prop_id=ANY(k.prop_ids)
    AND NOT k.is_primary
    AND EXISTS(SELECT 1 FROM truss.type_def t WHERE t.type_id=k.type_id)
    AND NOT EXISTS(SELECT 1 FROM truss.key_def old WHERE old.type_id=k.type_id AND old.key_id=k.key_id)) LOOP
  SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=property.type_id;
  IF truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE THEN
   RAISE EXCEPTION 'current planned key component disclosure reader required' USING ERRCODE='42501';END IF;
 END LOOP;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_candidates(jsonb,int) FROM PUBLIC;

CREATE FUNCTION truss.catalog_key_backfill_verify(planned_basis jsonb,selected_revision int,original_receipts bytea) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE candidates jsonb;entry jsonb;result jsonb:='[]';tuple_bytes bytea;
BEGIN
 IF original_receipts IS NOT NULL AND original_receipts<>convert_to('[]','UTF8') THEN
  RAISE EXCEPTION 'client key receipts are no longer accepted' USING ERRCODE='22023';END IF;
 candidates:=truss.catalog_key_backfill_candidates(planned_basis,selected_revision);
 FOR entry IN SELECT value FROM jsonb_array_elements(candidates) LOOP
  tuple_bytes:=truss.derive_catalog_key_tuple((entry->>'typeId')::int,(entry->>'keyNumber')::smallint,entry->'values',planned_basis);
  result:=result||jsonb_build_array(entry||jsonb_build_object('tupleHex',encode(tuple_bytes,'hex')));
  IF octet_length(result::text)>8388608 THEN RAISE EXCEPTION 'bounded native key backfill required' USING ERRCODE='54000';END IF;
 END LOOP;
 IF truss.catalog_key_backfill_candidates(planned_basis,selected_revision) IS DISTINCT FROM candidates THEN
  RAISE EXCEPTION 'key candidates changed during native derivation' USING ERRCODE='55000';END IF;
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_verify(jsonb,int,bytea) FROM PUBLIC;

CREATE FUNCTION truss.catalog_key_backfill_violations(verified_receipts jsonb) RETURNS bytea
LANGUAGE sql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
 WITH collisions AS (
  SELECT r.value->>'documentId' document_id,r.value->>'moduleId' module_id,r.value->>'recordId' record_id,
   r.value->>'keyId' key_id,r.value->>'typeId' type_id,r.value->>'keyNumber' key_number,r.value->>'tupleHex' tuple_hex,count(*) participants
  FROM jsonb_array_elements(verified_receipts) r
  GROUP BY 1,2,3,4,5,6,7 HAVING count(*)>1
 ), counts AS (
  SELECT document_id,module_id,record_id,key_id,sum(participants) affected FROM collisions GROUP BY 1,2,3,4
 )
 SELECT CASE WHEN count(*)=0 THEN NULL ELSE convert_to(jsonb_agg(jsonb_build_object(
  'documentId',document_id,'moduleId',module_id,'recordId',record_id,'keyId',key_id,
  'rule','key.duplicate','affectedObjectCount',affected::text)
  ORDER BY document_id COLLATE "C",module_id COLLATE "C",record_id COLLATE "C",key_id COLLATE "C")::text,'UTF8') END FROM counts;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_violations(jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_key_backfill_apply(request truss.catalog_registration_request,verified_receipts jsonb) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE selected record;entry jsonb;owner truss.type_def%ROWTYPE;object_row truss.object%ROWTYPE;
 definition truss.key_def%ROWTYPE;installation truss.catalog_runtime_installation%ROWTYPE;pin record;observed record;
 original_image jsonb;keys jsonb;effects jsonb;values_cells jsonb;facets jsonb;property truss.prop_def%ROWTYPE;component int;
 ns bytea;transport bytea;context_bytes bytea;reservation_bytes bytea;member_id bigint;reservation_id bigint;prior_generation bigint;membership truss.object_key_bucket%ROWTYPE;reservation truss.object_key_reservation_bucket%ROWTYPE;actual_row jsonb;
BEGIN
 IF request.actor_oid IS DISTINCT FROM truss.catalog_actor() OR request.actor_name IS DISTINCT FROM session_user::text
  OR request.writer_xid IS DISTINCT FROM pg_current_xact_id() OR request.registration_id IS NULL THEN
  RAISE EXCEPTION 'current original catalog key registration required' USING ERRCODE='55000';END IF;
 SELECT * INTO STRICT installation FROM truss.runtime_current_installation();
 IF truss.catalog_key_backfill_violations(verified_receipts) IS NOT NULL THEN
  RAISE EXCEPTION 'unique complete backfill tuples required' USING ERRCODE='23505';END IF;
 FOR selected IN SELECT DISTINCT (r.value->>'typeId')::int type_id,(r.value->>'objectId')::bigint object_id
  FROM jsonb_array_elements(verified_receipts) r ORDER BY 1,2 LOOP
  SELECT * INTO STRICT owner FROM truss.type_def WHERE type_id=selected.type_id AND retired_rev IS NULL;
  PERFORM truss.runtime_module_writer(owner.document_id,owner.module);
  IF truss.runtime_object_values_readable(owner.type_id) IS NOT TRUE THEN
   RAISE EXCEPTION 'current key backfill reader required' USING ERRCODE='42501';END IF;
  SELECT * INTO STRICT object_row FROM truss.object WHERE id=selected.object_id AND type_id=selected.type_id FOR UPDATE;
  original_image:=to_jsonb(object_row);effects:='[]';
  FOR entry IN SELECT r.value FROM jsonb_array_elements(verified_receipts) r
   WHERE r.value->>'typeId'=selected.type_id::text AND r.value->>'objectId'=selected.object_id::text
   ORDER BY (r.value->>'keyNumber')::smallint LOOP
   IF encode(sha256(convert_to(original_image::text,'UTF8')),'hex') IS DISTINCT FROM entry->>'objectImageSha256'
    AND NOT EXISTS(SELECT 1 FROM truss.runtime_catalog_rebind_transition t WHERE t.registration_id=request.registration_id
     AND t.object_id=selected.object_id AND t.type_id=selected.type_id AND t.after_object=original_image
     AND encode(sha256(convert_to(t.before_object::text,'UTF8')),'hex')=entry->>'objectImageSha256') THEN
    RAISE EXCEPTION 'original locked backfill object image required' USING ERRCODE='55000';END IF;
   SELECT * INTO STRICT definition FROM truss.key_def WHERE type_id=selected.type_id AND key_num=(entry->>'keyNumber')::smallint
    AND key_id=entry->>'keyId' AND since_rev=request.revision AND retired_rev IS NULL AND NOT is_primary;
   values_cells:='[]';facets:='[]';
   FOREACH component IN ARRAY definition.prop_ids LOOP
    SELECT * INTO STRICT property FROM truss.prop_def WHERE type_id=selected.type_id AND prop_id=component AND retired_rev IS NULL;
    values_cells:=values_cells||jsonb_build_array(object_row.props->component::text);facets:=facets||jsonb_build_array(coalesce(property.facets,'{}'));
   END LOOP;
   IF values_cells IS DISTINCT FROM entry->'values' OR truss.verify_umf_scalar_key_tuple(decode(entry->>'tupleHex','hex'),values_cells,facets) IS NOT TRUE THEN
    RAISE EXCEPTION 'unchanged exact final key values required' USING ERRCODE='55000';END IF;
   SELECT * INTO STRICT pin FROM truss.runtime_definition('key',selected.type_id,definition.key_num);
   ns:=convert_to(jsonb_build_object('profile','truss-string-key-namespace/0.2','installationId',installation.installation_id::text,
    'sourceEpoch',installation.source_epoch::text,'typeId',selected.type_id::text,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'encoding','umf-key-tuple-v1')::text,'UTF8');
   transport:=convert_to('umf-key-tuple-v1:hex:'||(entry->>'tupleHex'),'UTF8');
   SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(ns,transport);prior_generation:=observed.generation;
   IF cardinality(observed.member_ids)>0 OR cardinality(observed.reservation_ids)>0 THEN
    RAISE EXCEPTION 'new key already allocated or reserved' USING ERRCODE='23505';END IF;
   context_bytes:=convert_to(jsonb_build_object('profile','truss-catalog-key-backfill-context/0.2','registrationId',request.registration_id::text,
    'objectId',selected.object_id::text,'xid',request.writer_xid::text,'derivation','postgresql-umf-key-tuple-v1')::text,'UTF8');
   reservation_bytes:=convert_to(jsonb_build_object('profile','truss-catalog-key-backfill-reservation/0.1','registrationId',request.registration_id::text,
    'objectId',selected.object_id::text,'typeId',selected.type_id::text,'keyNumber',definition.key_num::text,'xid',request.writer_xid::text)::text,'UTF8');
   membership.storage_row_id:=nextval('truss.key_storage_row_seq');membership.type_id:=selected.type_id;
   membership.key_num:=definition.key_num;membership.object_id:=selected.object_id;membership.namespace_bytes:=ns;
   membership.key_bytes:=transport;membership.original_context_bytes:=context_bytes;
   membership.namespace_sha256:=sha256(ns);membership.key_sha256:=sha256(transport);member_id:=membership.storage_row_id;
   INSERT INTO truss.object_key_bucket(storage_row_id,type_id,key_num,object_id,namespace_bytes,key_bytes,original_context_bytes)
    VALUES(member_id,selected.type_id,definition.key_num,selected.object_id,ns,transport,context_bytes) RETURNING to_jsonb(object_key_bucket) INTO actual_row;
   IF actual_row IS DISTINCT FROM to_jsonb(membership) THEN RAISE EXCEPTION 'exact backfill membership insert required' USING ERRCODE='55000';END IF;
   reservation.storage_row_id:=nextval('truss.key_storage_row_seq');reservation.namespace_bytes:=ns;reservation.key_bytes:=transport;
   reservation.original_reservation_bytes:=reservation_bytes;reservation.namespace_sha256:=sha256(ns);reservation.key_sha256:=sha256(transport);reservation_id:=reservation.storage_row_id;
   INSERT INTO truss.object_key_reservation_bucket(storage_row_id,namespace_bytes,key_bytes,original_reservation_bytes)
    VALUES(reservation_id,ns,transport,reservation_bytes) RETURNING to_jsonb(object_key_reservation_bucket) INTO actual_row;
   IF actual_row IS DISTINCT FROM to_jsonb(reservation) THEN RAISE EXCEPTION 'exact backfill reservation insert required' USING ERRCODE='55000';END IF;
   UPDATE truss.key_bucket_guard SET generation=generation+1 WHERE namespace_sha256=sha256(ns) AND key_sha256=sha256(transport);
   SELECT * INTO STRICT observed FROM truss.lock_string_key_bucket(ns,transport);
   IF observed.generation IS DISTINCT FROM prior_generation+1 OR observed.member_ids IS DISTINCT FROM ARRAY[member_id]
    OR observed.reservation_ids IS DISTINCT FROM ARRAY[reservation_id] THEN
    RAISE EXCEPTION 'exact applied backfill key bucket required' USING ERRCODE='55000';END IF;
   effects:=effects||jsonb_build_array(jsonb_build_object('keyId',definition.key_id,'keyNumber',definition.key_num::text,
    'definitionPin',pin.definition_pin,'namespaceBase64',replace(encode(ns,'base64'),chr(10),''),'tupleHex',entry->>'tupleHex',
    'derivation','postgresql-umf-key-tuple-v1','memberId',member_id::text,'reservationId',reservation_id::text,
    'priorGeneration',prior_generation::text,'generation',observed.generation::text,
    'contextBase64',replace(encode(context_bytes,'base64'),chr(10),''),'reservationBase64',replace(encode(reservation_bytes,'base64'),chr(10),'')));
  END LOOP;
  IF (SELECT to_jsonb(o) FROM truss.object o WHERE o.id=selected.object_id AND o.type_id=selected.type_id) IS DISTINCT FROM original_image THEN
   RAISE EXCEPTION 'key-only backfill preserves exact object image' USING ERRCODE='55000';END IF;
  SELECT coalesce(jsonb_agg(to_jsonb(k) ORDER BY k.key_num),'[]') INTO keys FROM truss.object_key_bucket k
   WHERE k.object_id=selected.object_id AND k.type_id=selected.type_id;
  INSERT INTO truss.runtime_catalog_key_backfill(registration_id,writer_xid,actor_oid,revision,object_id,type_id,object_image,after_keys,effects)
   VALUES(request.registration_id,request.writer_xid,request.actor_oid,request.revision,selected.object_id,selected.type_id,original_image,keys,effects);
 END LOOP;
 PERFORM truss.catalog_actor();
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_apply(truss.catalog_registration_request,jsonb) FROM PUBLIC;

CREATE FUNCTION truss.catalog_key_backfill_transition_reader(transition truss.runtime_catalog_key_backfill,planned_basis jsonb DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE basis jsonb;owner truss.type_def%ROWTYPE;definition truss.key_def%ROWTYPE;property truss.prop_def%ROWTYPE;
 effect jsonb;component int;pin record;
BEGIN
 basis:=coalesce(planned_basis,truss.catalog_all_expected_records(transition.revision));
 SELECT * INTO STRICT owner FROM jsonb_populate_recordset(NULL::truss.type_def,basis->'type_def') t WHERE t.type_id=transition.type_id;
 IF truss.runtime_can_read(owner.document_id,owner.module) IS NOT TRUE THEN
  RAISE EXCEPTION 'current original backfill owner reader required' USING ERRCODE='42501';END IF;
 FOR effect IN SELECT value FROM jsonb_array_elements(transition.effects) LOOP
  SELECT * INTO STRICT definition FROM jsonb_populate_recordset(NULL::truss.key_def,basis->'key_def') k
   WHERE k.type_id=transition.type_id AND k.key_num=(effect->>'keyNumber')::smallint AND k.key_id=effect->>'keyId';
  SELECT * INTO STRICT pin FROM truss.catalog_rebind_definition('key',transition.type_id,definition.key_num,basis);
  IF pin.definition_pin IS DISTINCT FROM effect->>'definitionPin' THEN
   RAISE EXCEPTION 'original backfill key definition required' USING ERRCODE='55000';END IF;
  FOREACH component IN ARRAY definition.prop_ids LOOP
   SELECT * INTO STRICT property FROM jsonb_populate_recordset(NULL::truss.prop_def,basis->'prop_def') p WHERE p.prop_id=component AND p.type_id=transition.type_id;
   IF truss.runtime_can_read(owner.document_id,property.declaration_module) IS NOT TRUE THEN
    RAISE EXCEPTION 'current original key component reader required' USING ERRCODE='42501';END IF;
  END LOOP;
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_transition_reader(truss.runtime_catalog_key_backfill,jsonb) FROM PUBLIC;
CREATE FUNCTION truss.catalog_key_backfill_report_reader(selected_registration uuid,planned_basis jsonb DEFAULT NULL) RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE transition truss.runtime_catalog_key_backfill%ROWTYPE;
BEGIN
 FOR transition IN SELECT * FROM truss.runtime_catalog_key_backfill WHERE registration_id=selected_registration LOOP
  PERFORM truss.catalog_key_backfill_transition_reader(transition,planned_basis);
 END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_report_reader(uuid,jsonb) FROM PUBLIC;
