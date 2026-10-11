-- Private catalog-only semantic body under explicit native test custody.
-- Whole-catalog maximum-one OCCURRENCE marker correspondence, not UMF participation.
-- Not an installed authority/resource profile, ordinary API or commit grant.
CREATE FUNCTION truss.edge_limit_verify_current_scope() RETURNS void
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path=pg_catalog,pg_temp
SET row_security=off AS $$
DECLARE actual_xid xid8:=pg_current_xact_id_if_assigned();
        operation truss.row_home_operation%ROWTYPE;
        relationships bigint; definition_rows bigint; edge_rows bigint; marker_rows bigint;
BEGIN
 -- Explicit test-only caller custody. Production capture/issuer is still absent.
 IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=session_user AND rolsuper)
    OR session_user<>current_user OR actual_xid IS NULL THEN
  RAISE EXCEPTION 'original native test custody required' USING ERRCODE='55000';
 END IF;
 IF NOT EXISTS(SELECT 1 FROM pg_locks WHERE pid=pg_backend_pid() AND granted
       AND relation='truss.schema_head'::regclass
       AND mode IN ('ExclusiveLock','AccessExclusiveLock')) THEN
  RAISE EXCEPTION 'original exclusive catalog head required' USING ERRCODE='55000';
 END IF;
 -- No LIMIT/latest-ordinal choice; STRICT refuses zero or multiple candidates.
 SELECT o.* INTO STRICT operation FROM truss.row_home_operation o
  WHERE o.original_writer_xid=actual_xid AND o.phase<>'application_finalized';
 IF operation.operation_kind<>'catalog-acceptance'
    OR operation.phase NOT IN ('admitted','effects_ready','row_sealed') THEN
  RAISE EXCEPTION 'original catalog operation required' USING ERRCODE='55000';
 END IF;
 -- Static whole-catalog source profile: ordinary physical tables, no partitions,
 -- inheritance, views, foreign sources or RLS-filtered observations.
 IF EXISTS(SELECT 1 FROM unnest(ARRAY['truss.rel_def'::regclass,'truss.edge'::regclass,
              'truss.edge_limit'::regclass]) AS r(oid)
     JOIN pg_class c ON c.oid=r.oid
     WHERE c.relkind<>'r' OR EXISTS(SELECT 1 FROM pg_inherits i
            WHERE i.inhrelid=c.oid OR i.inhparent=c.oid)) THEN
  RAISE EXCEPTION 'unsupported original relationship source' USING ERRCODE='0A000';
 END IF;
 -- Exact selected native input columns: no text/numeric coercion, NULL-filtered
 -- scope or char-width trimming may silently change the observed meaning.
 IF EXISTS(SELECT 1 FROM (VALUES
   ('truss.rel_def'::regclass,'rel_type_id','int4'::regtype,true,-1),
   ('truss.rel_def'::regclass,'source_min','int4'::regtype,true,-1),
   ('truss.rel_def'::regclass,'source_max','int4'::regtype,false,-1),
   ('truss.rel_def'::regclass,'target_min','int4'::regtype,true,-1),
   ('truss.rel_def'::regclass,'target_max','int4'::regtype,false,-1),
   ('truss.edge'::regclass,'id','int8'::regtype,true,-1),
   ('truss.edge'::regclass,'rel_type_id','int4'::regtype,true,-1),
   ('truss.edge'::regclass,'source_id','int8'::regtype,true,-1),
   ('truss.edge'::regclass,'target_id','int8'::regtype,true,-1),
   ('truss.edge_limit'::regclass,'rel_type_id','int8'::regtype,true,-1),
   ('truss.edge_limit'::regclass,'side','bpchar'::regtype,true,5),
   ('truss.edge_limit'::regclass,'endpoint_id','int8'::regtype,true,-1),
   ('truss.edge_limit'::regclass,'edge_id','int8'::regtype,true,-1)
  ) AS expected(relation,name,type,not_null,typmod)
  LEFT JOIN pg_attribute a ON a.attrelid=expected.relation AND a.attname=expected.name
   AND a.attnum>0 AND NOT a.attisdropped
  WHERE a.attnum IS NULL OR a.atttypid<>expected.type OR a.attnotnull<>expected.not_null
    OR a.atttypmod<>expected.typmod) THEN
  RAISE EXCEPTION 'unsupported original relationship columns' USING ERRCODE='0A000';
 END IF;
 -- Counts include every physical row. These logical cardinality bounds do not
 -- claim bounded executor heap, whole-operation work or production admission.
 SELECT count(*) INTO definition_rows FROM truss.rel_def;
 SELECT count(*) INTO edge_rows FROM truss.edge;
 SELECT count(*) INTO marker_rows FROM truss.edge_limit;
 SELECT count(*) INTO relationships FROM (
  SELECT rel_type_id::bigint FROM truss.rel_def
  UNION SELECT rel_type_id::bigint FROM truss.edge
  UNION SELECT rel_type_id::bigint FROM truss.edge_limit) AS universe;
 IF relationships>256 OR definition_rows>256 OR edge_rows>16384 OR marker_rows>32768 THEN
  RAISE EXCEPTION 'relationship correspondence capacity exceeded' USING ERRCODE='54000';
 END IF;
 IF EXISTS(SELECT 1 FROM truss.rel_def GROUP BY rel_type_id HAVING count(*)<>1)
    OR EXISTS(SELECT 1 FROM truss.edge GROUP BY id HAVING count(*)<>1) THEN
  RAISE EXCEPTION 'unsupported original relationship identity' USING ERRCODE='0A000';
 END IF;
 -- Whole universe includes orphan/wrong-relationship markers and canonical edges.
 IF EXISTS(SELECT 1 FROM (
   SELECT rel_type_id::bigint AS id FROM truss.edge
   UNION SELECT rel_type_id::bigint FROM truss.edge_limit) AS referenced
   WHERE NOT EXISTS(SELECT 1 FROM truss.rel_def d WHERE d.rel_type_id=referenced.id)) THEN
  RAISE EXCEPTION 'original relationship definition unavailable' USING ERRCODE='55000';
 END IF;
 IF EXISTS(SELECT 1 FROM truss.rel_def d WHERE d.source_min<0 OR d.target_min<0
    OR (d.source_max IS NOT NULL AND d.source_max<d.source_min)
    OR (d.target_max IS NOT NULL AND d.target_max<d.target_min)) THEN
  RAISE EXCEPTION 'unsupported relationship bounds' USING ERRCODE='0A000';
 END IF;
 -- Required marker key conflicts are detected independently of actual markers.
 IF EXISTS(WITH required AS (
   SELECT e.rel_type_id::bigint AS rel,'s'::text COLLATE pg_catalog."C" AS side,e.source_id AS endpoint,e.id
     FROM truss.edge e JOIN truss.rel_def d USING(rel_type_id) WHERE d.target_max=1
   UNION ALL
   SELECT e.rel_type_id::bigint,'t'::text COLLATE pg_catalog."C",e.target_id,e.id
     FROM truss.edge e JOIN truss.rel_def d USING(rel_type_id) WHERE d.source_max=1)
   SELECT 1 FROM required GROUP BY rel,side,endpoint HAVING count(*)>1) THEN
  RAISE EXCEPTION 'required marker key conflict' USING ERRCODE='23505';
 END IF;
 -- EXCEPT ALL preserves multiplicity; both directions must be empty.
 IF EXISTS(WITH required AS (
   SELECT e.rel_type_id::bigint AS rel,'s'::text COLLATE pg_catalog."C" AS side,e.source_id AS endpoint,e.id
     FROM truss.edge e JOIN truss.rel_def d USING(rel_type_id) WHERE d.target_max=1
   UNION ALL
   SELECT e.rel_type_id::bigint,'t'::text COLLATE pg_catalog."C",e.target_id,e.id
     FROM truss.edge e JOIN truss.rel_def d USING(rel_type_id) WHERE d.source_max=1),
   actual AS (SELECT m.rel_type_id::bigint AS rel,m.side::text COLLATE pg_catalog."C" AS side,m.endpoint_id AS endpoint,m.edge_id AS id
     FROM truss.edge_limit m),
   missing AS (SELECT * FROM required EXCEPT ALL SELECT * FROM actual),
   extra AS (SELECT * FROM actual EXCEPT ALL SELECT * FROM required)
   SELECT 1 FROM missing UNION ALL SELECT 1 FROM extra) THEN
  RAISE EXCEPTION 'relationship marker mismatch' USING ERRCODE='55000';
 END IF;
 -- Deliberately no mutation/seal/result token, including the all-three-empty case.
END;
$$;
REVOKE ALL ON FUNCTION truss.edge_limit_verify_current_scope() FROM PUBLIC;
