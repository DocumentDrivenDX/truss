-- SPIKE-002 option C: ONE generic deferred constraint trigger enforces every minimum multiplicity in c.rel_def
-- (Order.customer min 1, Order.lines min 1, OrderLine<-lines min 1, OrderLine.product min 1, ...). Written once;
-- a new relationship needs only catalog rows. Same READ COMMITTED concurrency caveat as option A's HAND-12.
CREATE OR REPLACE FUNCTION c.check_min_multiplicity(obj bigint) RETURNS void LANGUAGE plpgsql AS $$
DECLARE t int; r record; n int;
BEGIN
  SELECT type_id INTO t FROM c.object WHERE id = obj;
  IF NOT FOUND THEN RETURN; END IF;
  FOR r IN SELECT d.rel_type_id, d.rel_id, d.target_min AS mn, 'out' AS dir FROM c.rel_def d JOIN c.rel_endpoint e USING (rel_type_id)
             WHERE e.source_type = t AND d.target_min > 0
           UNION ALL
           SELECT d.rel_type_id, d.rel_id, d.source_min, 'in' FROM c.rel_def d JOIN c.rel_endpoint e USING (rel_type_id)
             WHERE e.target_type = t AND d.source_min > 0 LOOP
    IF r.dir = 'out' THEN
      SELECT count(*) INTO n FROM (SELECT 1 FROM c.edge WHERE source_id = obj AND rel_type_id = r.rel_type_id LIMIT r.mn) s;
    ELSE
      SELECT count(*) INTO n FROM (SELECT 1 FROM c.edge WHERE target_id = obj AND rel_type_id = r.rel_type_id LIMIT r.mn) s;
    END IF;
    IF n < r.mn THEN
      RAISE EXCEPTION 'relationship %: object % has % % edge(s) (min %)', r.rel_id, obj, n, r.dir, r.mn USING ERRCODE = '23514';
    END IF;
  END LOOP;
END $$;
CREATE OR REPLACE FUNCTION c.trg_min_multiplicity() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_TABLE_NAME = 'object' THEN PERFORM c.check_min_multiplicity(NEW.id);
  ELSE PERFORM c.check_min_multiplicity(OLD.source_id); PERFORM c.check_min_multiplicity(OLD.target_id); END IF;
  RETURN NULL;
END $$;
DROP TRIGGER IF EXISTS object_min_multiplicity ON c.object;
DROP TRIGGER IF EXISTS edge_min_multiplicity ON c.edge;
CREATE CONSTRAINT TRIGGER object_min_multiplicity AFTER INSERT ON c.object
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION c.trg_min_multiplicity();
CREATE CONSTRAINT TRIGGER edge_min_multiplicity AFTER DELETE OR UPDATE OF source_id, target_id ON c.edge
  DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION c.trg_min_multiplicity();
