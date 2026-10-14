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
CREATE TRIGGER runtime_catalog_key_backfill_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_catalog_key_backfill
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_catalog_key_backfill FROM PUBLIC;

-- Planned basis and original UMF key receipts follow.
CREATE FUNCTION truss.catalog_key_backfill_candidates(planned_basis jsonb,selected_revision int) RETURNS jsonb
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp SET TimeZone='UTC' SET bytea_output=hex AS $$
DECLARE definition truss.key_def%ROWTYPE;owner truss.type_def%ROWTYPE;property truss.prop_def%ROWTYPE;
 object_row truss.object%ROWTYPE;component int;values_cells jsonb;archive truss.schema_doc%ROWTYPE;result jsonb:='[]';candidate_count int:=0;head int;
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
   SELECT * INTO STRICT property FROM truss.prop_def WHERE prop_id=component AND type_id=owner.type_id AND retired_rev IS NULL;
   IF property.nullability IS DISTINCT FROM 'required' OR property.cardinality IS DISTINCT FROM 'one'
    OR property.scalar_type NOT IN ('string','integer','decimal','boolean','binary') THEN
    RAISE EXCEPTION 'existing required scalar key components required' USING ERRCODE='0A000';END IF;
  END LOOP;
  SELECT * INTO STRICT archive FROM jsonb_populate_recordset(NULL::truss.schema_doc,planned_basis->'schema_doc') d
   WHERE d.rev=definition.definition_rev AND d.ord=definition.definition_doc_ord AND d.doc_id=definition.definition_document_id;
  IF archive.content_sha256 IS DISTINCT FROM encode(sha256(convert_to(archive.document,'UTF8')),'hex') THEN
   RAISE EXCEPTION 'original planned document bytes required' USING ERRCODE='55000';END IF;
  FOR object_row IN SELECT o.* FROM truss.object o WHERE o.type_id=owner.type_id ORDER BY o.id FOR UPDATE LOOP
   candidate_count:=candidate_count+1;values_cells:='[]';
   IF candidate_count>10000 THEN RAISE EXCEPTION 'bounded key backfill inventory required' USING ERRCODE='54000';END IF;
   FOREACH component IN ARRAY definition.prop_ids LOOP
    SELECT * INTO STRICT property FROM truss.prop_def WHERE prop_id=component AND type_id=owner.type_id;
    IF truss.valid_scalar_property(object_row.props->component::text,property.scalar_type,false,property.facets) IS NOT TRUE THEN
     RAISE EXCEPTION 'valid complete key candidate values required' USING ERRCODE='22023';END IF;
    values_cells:=values_cells||jsonb_build_array(object_row.props->component::text);
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
 RETURN result;
END;
$$;
REVOKE ALL ON FUNCTION truss.catalog_key_backfill_candidates(jsonb,int) FROM PUBLIC;
