-- Internal whole-key batch; original source interpretation remains the UMF producer's.
-- A failing declaration rolls back every effect of this native statement.
CREATE FUNCTION truss.runtime_stage_new_keys(revision int,candidates jsonb)
RETURNS TABLE(owner_type_id text,key_id text,key_number text)
LANGUAGE plpgsql VOLATILE SECURITY INVOKER
SET search_path = pg_catalog, pg_temp
AS $$
DECLARE
  candidate jsonb;
  components int[];
  assigned text;
BEGIN
  IF revision IS NULL OR candidates IS NULL OR jsonb_typeof(candidates)<>'array'
      OR jsonb_array_length(candidates) NOT BETWEEN 1 AND 4096
      OR octet_length(candidates::text)>1048576 THEN
    RAISE EXCEPTION 'original key batch required' USING ERRCODE='22023';
  END IF;
  FOR candidate IN SELECT value FROM jsonb_array_elements(candidates) LOOP
    IF jsonb_typeof(candidate)<>'object' OR NOT candidate ?& ARRAY['ownerTypeId','keyId','propertyIds','primary']
        OR (SELECT count(*) FROM jsonb_object_keys(candidate))<>4
        OR jsonb_typeof(candidate->'ownerTypeId')<>'string'
        OR candidate->>'ownerTypeId' !~ '^[1-9][0-9]{0,9}$'
        OR (candidate->>'ownerTypeId')::bigint>2147483647
        OR jsonb_typeof(candidate->'keyId')<>'string'
        OR octet_length(candidate->>'keyId') NOT BETWEEN 1 AND 4096
        OR jsonb_typeof(candidate->'primary')<>'boolean'
        OR jsonb_typeof(candidate->'propertyIds')<>'array' THEN
      RAISE EXCEPTION 'original key batch carrier' USING ERRCODE='22023';
    END IF;
    IF jsonb_array_length(candidate->'propertyIds') NOT BETWEEN 1 AND 256 THEN
      RAISE EXCEPTION 'original key component bound' USING ERRCODE='22023';
    END IF;
    IF EXISTS(SELECT 1 FROM jsonb_array_elements(candidate->'propertyIds') p WHERE
        jsonb_typeof(p)<>'string' OR p #>> '{}' !~ '^[1-9][0-9]{0,9}$') THEN
      RAISE EXCEPTION 'original key component carrier' USING ERRCODE='22023';
    END IF;
    IF EXISTS(SELECT 1 FROM jsonb_array_elements_text(candidate->'propertyIds') p WHERE p::bigint>2147483647) THEN
      RAISE EXCEPTION 'original key component capacity' USING ERRCODE='22023';
    END IF;
  END LOOP;
  IF (SELECT count(*) FROM (SELECT DISTINCT value->>'ownerTypeId',value->>'keyId' FROM jsonb_array_elements(candidates)) q)<>jsonb_array_length(candidates) THEN
    RAISE EXCEPTION 'duplicate owner key declaration' USING ERRCODE='22023';
  END IF;
  -- Resolve/check every owner through the scalar producer; never drop a missing owner in a join.
  FOR candidate IN SELECT value FROM jsonb_array_elements(candidates)
      ORDER BY (value->>'ownerTypeId')::int,(value->>'keyId') COLLATE "C" LOOP
    SELECT array_agg(p.value::int ORDER BY p.ordinality) INTO components
      FROM jsonb_array_elements_text(candidate->'propertyIds') WITH ORDINALITY p(value,ordinality);
    assigned:=truss.runtime_stage_new_key(revision,(candidate->>'ownerTypeId')::int,
      candidate->>'keyId',components,(candidate->>'primary')::boolean);
    RETURN QUERY SELECT candidate->>'ownerTypeId',candidate->>'keyId',assigned;
  END LOOP;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_stage_new_keys(int,jsonb) FROM PUBLIC;
