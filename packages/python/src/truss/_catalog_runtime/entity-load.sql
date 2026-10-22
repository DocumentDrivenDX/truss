-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Additive import-load projection for the next installed runtime 0.35.
-- This source is not activated by the current runtime 0.34 bundle.
CREATE FUNCTION truss.query_object_load_id(binding jsonb,selected_type int,selected_id bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path=pg_catalog,pg_temp SET row_security=off SET TimeZone='UTC' AS $$
DECLARE selected_load text;current_object truss.object%ROWTYPE;root_identity jsonb;
BEGIN
 -- Prove the complete original creation/current attribution, immutable import
 -- ledger, payload and load-origin correspondence in this statement snapshot.
 PERFORM truss.query_object_attribution(binding,selected_type,selected_id);
 SELECT load_id INTO selected_load FROM truss.record_source
  WHERE entity_kind='o' AND entity_id=selected_id;
 SELECT * INTO STRICT current_object FROM truss.object WHERE id=selected_id AND type_id=selected_type;
 root_identity:=truss.query_object_root(binding,current_object);
 PERFORM truss.query_scope(binding);
 IF root_identity IS NOT NULL AND NOT truss.runtime_can_read(root_identity->'owner'->>'documentId',root_identity->'owner'->>'moduleId') THEN RAISE EXCEPTION 'current metadata aggregate root reader required' USING ERRCODE='P1403';END IF;
 -- A proved ordinary creation has JSON null, never a SQL NULL result carrier.
 RETURN jsonb_build_object('_load_id',selected_load);
END;
$$;
REVOKE ALL ON FUNCTION truss.query_object_load_id(jsonb,int,bigint) FROM PUBLIC;
