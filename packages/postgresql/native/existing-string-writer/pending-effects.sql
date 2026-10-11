-- Connected administrative effects candidate. Not the installed writer or the
-- full row_touch_observe body. No ordinary grant, readiness or finalization.
-- Actual context below is native0.2 actor observation, never row-context0.1.
-- The unconditional commit barrier must remain in the eventual composition.
CREATE FUNCTION truss.runtime_existing_string_pending_observer() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE op truss.row_home_operation%ROWTYPE; before_scope jsonb; after_scope jsonb;
        actual_xid xid8:=pg_current_xact_id_if_assigned(); count_ops bigint;
BEGIN
 IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP<>'UPDATE'
    OR TG_TABLE_SCHEMA<>'truss' OR TG_TABLE_NAME<>'row_home_scalar'
    OR TG_NARGS<>0 OR actual_xid IS NULL THEN
  RAISE EXCEPTION 'unregistered pending string event' USING ERRCODE='55000';
 END IF;
 SELECT count(*) INTO count_ops FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized';
 IF count_ops<>1 THEN RAISE EXCEPTION 'one original pending operation required' USING ERRCODE='55000';END IF;
 SELECT o.* INTO STRICT op FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized';
 before_scope:=convert_from(op.original_prestate_bytes,'UTF8')::jsonb;
 after_scope:=convert_from(op.admitted_candidate_bytes,'UTF8')::jsonb;
 IF op.operation_kind<>'mutation' OR op.phase<>'admitted' OR op.effect_generation<>0
    OR before_scope->>'interfaceVersion' IS DISTINCT FROM 'truss-existing-string-pending-effects/0.1.0'
    OR after_scope->>'interfaceVersion' IS DISTINCT FROM 'truss-existing-string-pending-effects/0.1.0'
    OR before_scope->>'stateId' IS DISTINCT FROM OLD.state_id::text
    OR before_scope->>'nodeId' IS DISTINCT FROM OLD.node_id::text
    OR after_scope->>'stateId' IS DISTINCT FROM NEW.state_id::text
    OR after_scope->>'nodeId' IS DISTINCT FROM NEW.node_id::text
    OR truss.row_image_scalar_original(OLD) IS DISTINCT FROM decode(before_scope->>'scalarHex','hex')
    OR truss.row_image_scalar_original(NEW) IS DISTINCT FROM decode(after_scope->>'scalarHex','hex') THEN
  RAISE EXCEPTION 'original pending event correspondence required' USING ERRCODE='55000';
 END IF;
 -- Parent corroboration is additional to the complete retained OLD/NEW images.
 IF (SELECT count(*) FROM truss.row_home_node n WHERE n.state_id=NEW.state_id)<>1
    OR (SELECT count(*) FROM truss.row_home_scalar c WHERE c.state_id=NEW.state_id)<>1
    OR NOT EXISTS(SELECT 1 FROM truss.row_home_state s WHERE s.state_id=NEW.state_id
      AND truss.row_image_state_original(s)=decode(after_scope->>'stateHex','hex'))
    OR NOT EXISTS(SELECT 1 FROM truss.row_home_node n WHERE n.state_id=NEW.state_id AND n.node_id=NEW.node_id
      AND truss.row_image_node_original(n)=decode(after_scope->>'nodeHex','hex')) THEN
  RAISE EXCEPTION 'complete pending side correspondence required' USING ERRCODE='55000';
 END IF;
 UPDATE truss.row_home_operation o SET effect_generation=1
  WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=op.operation_ordinal
    AND o.phase='admitted' AND o.effect_generation=0;
 IF NOT FOUND THEN RAISE EXCEPTION 'original pending generation changed' USING ERRCODE='55000';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_existing_string_pending_observer() FROM PUBLIC;
CREATE TRIGGER runtime_existing_string_pending_scalar AFTER INSERT OR UPDATE OR DELETE ON truss.row_home_scalar
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_existing_string_pending_observer();
ALTER TABLE truss.row_home_scalar ENABLE ALWAYS TRIGGER runtime_existing_string_pending_scalar;

CREATE FUNCTION truss.runtime_write_existing_string_pending(
 issued_ordinal bigint, selected_state bigint, expected_version bigint,
 replacement text, replacement_token bytea)
RETURNS TABLE(writer_xid text, ordinal text, original_prestate bytea, admitted_candidate bytea, context_hex text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE state_row truss.row_home_state%ROWTYPE; node_row truss.row_home_node%ROWTYPE;
 scalar_row truss.row_home_scalar%ROWTYPE; object_row truss.object%ROWTYPE; planned_object truss.object%ROWTYPE; observed_object truss.object%ROWTYPE;
 property_row truss.prop_def%ROWTYPE; type_row truss.type_def%ROWTYPE;
 images record; before_scope bytea; after_scope bytea; original_input bytea;
 definition bytea; obligations bytea; original_group bytea; admitted record;
 token jsonb; actual_xid xid8; head_revision integer;
BEGIN
 IF current_user::text IS DISTINCT FROM (CASE WHEN current_setting('role')='none'
    THEN session_user::text ELSE current_setting('role') END) THEN
  RAISE EXCEPTION 'original invoker boundary required' USING ERRCODE='55000';END IF;
 IF issued_ordinal IS NULL OR issued_ordinal<0 OR selected_state IS NULL OR selected_state<=0
    OR expected_version IS NULL OR expected_version<1 OR expected_version=9223372036854775807
    OR replacement IS NULL OR octet_length(replacement)>65536
    OR replacement_token IS NULL OR octet_length(replacement_token) NOT BETWEEN 1 AND 262144 THEN
  RAISE EXCEPTION 'bounded pending replacement required' USING ERRCODE='22023';END IF;
 token:=convert_from(replacement_token,'UTF8')::jsonb;
 IF jsonb_typeof(token)<>'string' OR (token#>>'{}') COLLATE pg_catalog."C" IS DISTINCT FROM replacement COLLATE pg_catalog."C" THEN
  RAISE EXCEPTION 'lossless original string token required' USING ERRCODE='22023';END IF;
 -- Do not layer this candidate over the old generation observer.
 IF EXISTS(SELECT 1 FROM pg_catalog.pg_trigger t WHERE t.tgrelid='truss.row_home_scalar'::regclass
    AND NOT t.tgisinternal AND t.tgname='runtime_scalar_generation') THEN
  RAISE EXCEPTION 'competing generation observer' USING ERRCODE='55000';END IF;
 SELECT h.rev INTO STRICT head_revision FROM truss.schema_head h WHERE h.id=1 FOR SHARE;
 -- This candidate lacks the complete capacity/authority producer. It acquires
 -- no capacity lock after an owner lock and cannot issue ready/finalized state.
 SELECT s.* INTO STRICT state_row FROM truss.row_home_state s WHERE s.state_id=selected_state;
 IF state_row.owner_kind<>'object' THEN RAISE EXCEPTION 'existing object state required' USING ERRCODE='22023';END IF;
 SELECT o.* INTO STRICT object_row FROM truss.object o
  WHERE o.id=state_row.object_id AND o.type_id=state_row.object_type_id FOR UPDATE;
 IF object_row.ver<>expected_version THEN RAISE EXCEPTION 'stale object version' USING ERRCODE='40001';END IF;
 SELECT s.* INTO STRICT state_row FROM truss.row_home_state s WHERE s.state_id=selected_state FOR UPDATE;
 IF state_row.owner_kind<>'object' OR state_row.object_id IS DISTINCT FROM object_row.id
    OR state_row.object_type_id IS DISTINCT FROM object_row.type_id THEN
  RAISE EXCEPTION 'original owner changed' USING ERRCODE='55000';END IF;
 SELECT p.* INTO STRICT property_row FROM truss.prop_def p WHERE p.prop_id=state_row.property_id;
 SELECT t.* INTO STRICT type_row FROM truss.type_def t WHERE t.type_id=object_row.type_id;
 IF state_row.property_owner_type_id<>object_row.type_id OR property_row.type_id<>object_row.type_id
    OR property_row.home<>'row' OR property_row.scalar_type IS DISTINCT FROM 'string'
    OR property_row.facets IS NOT NULL AND property_row.facets<>'{}'::jsonb
    OR property_row.retired_rev IS NOT NULL OR type_row.retired_rev IS NOT NULL
    OR EXISTS(SELECT 1 FROM truss.key_def k WHERE k.type_id=object_row.type_id AND state_row.property_id=ANY(k.prop_ids)) THEN
  RAISE EXCEPTION 'unsupported pending property definition' USING ERRCODE='22023';END IF;
 IF (SELECT count(*) FROM truss.row_home_node n WHERE n.state_id=selected_state)<>1
    OR (SELECT count(*) FROM truss.row_home_scalar c WHERE c.state_id=selected_state)<>1 THEN
  RAISE EXCEPTION 'complete single-root membership required' USING ERRCODE='55000';END IF;
 SELECT n.* INTO STRICT node_row FROM truss.row_home_node n WHERE n.state_id=selected_state FOR UPDATE;
 SELECT c.* INTO STRICT scalar_row FROM truss.row_home_scalar c WHERE c.state_id=selected_state FOR UPDATE;
 SELECT c.* INTO STRICT images FROM truss.row_image_existing_string_candidate_original(
  state_row,node_row,scalar_row,truss.row_image_state_original(state_row),
  truss.row_image_node_original(node_row),truss.row_image_scalar_original(scalar_row),replacement,replacement_token) c;
 before_scope:=convert_to(jsonb_build_object('interfaceVersion','truss-existing-string-pending-effects/0.1.0',
  'stateId',selected_state::text,'nodeId',node_row.node_id::text,'objectId',object_row.id::text,
  'typeId',object_row.type_id::text,'version',object_row.ver::text,
  'documentId',type_row.document_id,'propertyId',property_row.prop_id::text,
  'stateHex',encode(images.old_state_image,'hex'),'nodeHex',encode(images.old_node_image,'hex'),
  'scalarHex',encode(images.old_scalar_image,'hex'),'objectHex',encode(record_send(object_row),'hex'))::text,'UTF8');
 planned_object:=object_row;
 planned_object.ver:=object_row.ver+1;
 planned_object.updated_at:=clock_timestamp();
 after_scope:=convert_to(jsonb_build_object('interfaceVersion','truss-existing-string-pending-effects/0.1.0',
  'stateId',selected_state::text,'nodeId',node_row.node_id::text,'objectId',object_row.id::text,
  'typeId',object_row.type_id::text,'version',(object_row.ver+1)::text,
  'documentId',type_row.document_id,'propertyId',property_row.prop_id::text,
  'stateHex',encode(images.new_state_image,'hex'),'nodeHex',encode(images.new_node_image,'hex'),
  'scalarHex',encode(images.new_scalar_image,'hex'),'objectHex',encode(record_send(planned_object),'hex'))::text,'UTF8');
 original_input:=convert_to(jsonb_build_object('expectedVersion',expected_version::text,
  'replacementTokenHex',encode(replacement_token,'hex'))::text,'UTF8');
 definition:=convert_to(pg_get_functiondef('truss.runtime_write_existing_string_pending(bigint,bigint,bigint,text,bytea)'::regprocedure),'UTF8');
 -- Pending obligations make incompleteness explicit; these are not registered
 -- family artifacts, row-context0.1, or effects-ready/application proof.
 obligations:=convert_to('{"pending":["registered-source-meaning","capacity","touch-contributions","key-parity","journal","feed","authority","finalization"]}','UTF8');
 original_group:=convert_to('{"scope":"administrative-pending-effects-only","requestParticipation":"none"}','UTF8');
 SELECT a.* INTO STRICT admitted FROM truss.runtime_admit_operation(issued_ordinal,'mutation',definition,
  original_input,before_scope,after_scope,obligations,original_group) a;
 actual_xid:=pg_current_xact_id_if_assigned();
 UPDATE truss.row_home_scalar SET text_value=replacement,original_source_bytes=replacement_token
  WHERE state_id=selected_state AND node_id=node_row.node_id;
 IF NOT FOUND THEN RAISE EXCEPTION 'original scalar disappeared' USING ERRCODE='55000';END IF;
 UPDATE truss.object SET ver=planned_object.ver,updated_at=planned_object.updated_at
  WHERE id=object_row.id AND type_id=object_row.type_id AND ver=expected_version;
 IF NOT FOUND THEN RAISE EXCEPTION 'original object changed' USING ERRCODE='55000';END IF;
 IF NOT EXISTS(SELECT 1 FROM truss.row_home_operation o
   WHERE o.original_writer_xid=actual_xid AND o.operation_ordinal=issued_ordinal
     AND o.phase='admitted' AND o.effect_generation=1
     AND o.original_prestate_bytes=before_scope AND o.admitted_candidate_bytes=after_scope) THEN
  RAISE EXCEPTION 'original pending operation was not observed' USING ERRCODE='55000';END IF;
 SELECT o.* INTO STRICT observed_object FROM truss.object o WHERE o.id=object_row.id AND o.type_id=object_row.type_id;
 IF record_send(observed_object) IS DISTINCT FROM record_send(planned_object) THEN
  RAISE EXCEPTION 'complete planned object correspondence required' USING ERRCODE='55000';END IF;
 IF (SELECT count(*) FROM truss.row_home_node n WHERE n.state_id=selected_state)<>1
    OR (SELECT count(*) FROM truss.row_home_scalar c WHERE c.state_id=selected_state)<>1
    OR NOT EXISTS(SELECT 1 FROM truss.row_home_state s WHERE s.state_id=selected_state
      AND truss.row_image_state_original(s)=images.new_state_image)
    OR NOT EXISTS(SELECT 1 FROM truss.row_home_node n WHERE n.state_id=selected_state
      AND n.node_id=node_row.node_id AND truss.row_image_node_original(n)=images.new_node_image)
    OR NOT EXISTS(SELECT 1 FROM truss.row_home_scalar c WHERE c.state_id=selected_state
      AND c.node_id=node_row.node_id AND truss.row_image_scalar_original(c)=images.new_scalar_image) THEN
  RAISE EXCEPTION 'complete final candidate correspondence required' USING ERRCODE='55000';END IF;
 RETURN QUERY SELECT actual_xid::text,issued_ordinal::text,before_scope,after_scope,admitted.context_hex;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_write_existing_string_pending(bigint,bigint,bigint,text,bytea) FROM PUBLIC;
