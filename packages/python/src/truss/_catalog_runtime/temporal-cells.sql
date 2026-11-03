-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Explicit selected local family. Ordinary timestamp and ExactValue rules stay
-- unchanged. Enrollment/CRUD composition requires the complete fresh0.76 route.
CREATE FUNCTION truss.valid_local_timestamp_cell(cell jsonb,allow_null boolean DEFAULT false) RETURNS boolean
LANGUAGE plpgsql IMMUTABLE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF cell='{"kind":"null"}'::jsonb THEN RETURN allow_null;END IF;
 IF jsonb_typeof(cell) IS DISTINCT FROM 'object' OR cell->>'kind' IS DISTINCT FROM 'localTimestamp'
  OR jsonb_typeof(cell->'text') IS DISTINCT FROM 'string'
  OR cell IS DISTINCT FROM jsonb_build_object('kind','localTimestamp','text',cell->'text')
  OR octet_length(cell->>'text')<>26 THEN RETURN false;END IF;
 RETURN cell->>'text'=truss.query_temporal_canonical_text('local',cell->>'text');
EXCEPTION WHEN invalid_parameter_value THEN RETURN false;
END;
$$;
REVOKE ALL ON FUNCTION truss.valid_local_timestamp_cell(jsonb,boolean) FROM PUBLIC;
