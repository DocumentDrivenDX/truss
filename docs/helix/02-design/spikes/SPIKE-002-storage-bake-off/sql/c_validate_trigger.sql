-- SPIKE-002 option C, third enforcement variant: ONE catalog-driven BEFORE trigger validates every object's props
-- against c.prop_def (nullability, scalar family, length, integer width, precision/scale, timestamp and base64
-- shape, array/map items, declared-only). A schema revision changes catalog rows only; no DDL.
-- Not covered: record invariants (opaque in UMF; would need an expression language) and cross-row rules.
CREATE OR REPLACE FUNCTION c.validate_scalar(scalar text, facets jsonb, v jsonb) RETURNS text
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE t text := v #>> '{}'; n numeric; b int; lo numeric; hi numeric;
BEGIN
  IF scalar IN ('string', 'timestamp', 'binary') AND jsonb_typeof(v) <> 'string' THEN RETURN 'not a string'; END IF;
  IF scalar IN ('integer', 'decimal') AND jsonb_typeof(v) <> 'number' THEN RETURN 'not a number'; END IF;
  IF scalar = 'boolean' AND jsonb_typeof(v) <> 'boolean' THEN RETURN 'not a boolean'; END IF;
  IF scalar = 'string' AND facets ? 'length' AND length(t) > (facets #>> '{length,max}')::int THEN
    RETURN format('length %s > %s', length(t), facets #>> '{length,max}'); END IF;
  IF scalar = 'integer' THEN
    n := t::numeric;
    IF scale(n) <> 0 THEN RETURN 'not an integer token'; END IF;
    IF facets ? 'integerWidth' THEN
      b := (facets #>> '{integerWidth,bits}')::int;
      IF (facets #>> '{integerWidth,signed}')::boolean THEN lo := -power(2::numeric, b - 1); hi := power(2::numeric, b - 1) - 1;
      ELSE lo := 0; hi := power(2::numeric, b) - 1; END IF;
      IF n < lo OR n > hi THEN RETURN format('outside %s-bit range', b); END IF;
    END IF;
  END IF;
  IF scalar = 'decimal' AND facets ? 'precision' THEN
    n := t::numeric;
    IF scale(n) > (facets->>'scale')::int THEN RETURN format('scale %s > %s', scale(n), facets->>'scale'); END IF;
    IF abs(n) >= power(10::numeric, (facets->>'precision')::int - (facets->>'scale')::int) THEN RETURN 'precision exceeded'; END IF;
  END IF;
  IF scalar = 'timestamp' AND t !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,9})?(Z|[+-][0-9]{2}:[0-9]{2})?$' THEN
    RETURN 'not an RFC 3339 timestamp'; END IF;
  IF scalar = 'binary' THEN
    IF t !~ '^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$' THEN RETURN 'not canonical base64'; END IF;
    IF facets ? 'length' AND length(decode(t, 'base64')) > (facets #>> '{length,max}')::int THEN RETURN 'byte length exceeded'; END IF;
  END IF;
  RETURN NULL;
END $$;

CREATE OR REPLACE FUNCTION c.trg_validate_props() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE p record; v jsonb; msg text; it jsonb;
BEGIN
  FOR p IN SELECT prop_id, element, scalar_type, nullability, cardinality, facets, item FROM c.prop_def WHERE type_id = NEW.type_id LOOP
    v := NEW.props -> p.prop_id::text; msg := NULL;
    IF v IS NULL OR jsonb_typeof(v) = 'null' THEN
      IF p.nullability = 'required' THEN
        RAISE EXCEPTION 'rule %:required violated (object %)', p.element, NEW.id USING ERRCODE = '23514'; END IF;
      CONTINUE;
    END IF;
    IF p.cardinality = 'one' THEN msg := c.validate_scalar(p.scalar_type, p.facets, v);
    ELSIF p.cardinality = 'array' THEN
      IF jsonb_typeof(v) <> 'array' THEN msg := 'not an array';
      ELSE FOR it IN SELECT value FROM jsonb_array_elements(v) LOOP
        msg := c.validate_scalar(p.item->>'scalar', p.item->'facets', it); EXIT WHEN msg IS NOT NULL; END LOOP; END IF;
    ELSIF p.cardinality = 'map' THEN
      IF jsonb_typeof(v) <> 'object' THEN msg := 'not an object';
      ELSE FOR it IN SELECT value FROM jsonb_each(v) LOOP
        msg := c.validate_scalar(p.item->>'scalar', p.item->'facets', it); EXIT WHEN msg IS NOT NULL; END LOOP; END IF;
    END IF;
    IF msg IS NOT NULL THEN
      RAISE EXCEPTION 'rule %:% violated (object %): %', p.element, p.cardinality, NEW.id, msg USING ERRCODE = '23514'; END IF;
  END LOOP;
  IF EXISTS (SELECT 1 FROM jsonb_object_keys(NEW.props) k
             WHERE NOT EXISTS (SELECT 1 FROM c.prop_def d WHERE d.type_id = NEW.type_id AND d.prop_id::text = k)) THEN
    RAISE EXCEPTION 'rule type %:declared-properties violated (object %)', NEW.type_id, NEW.id USING ERRCODE = '23514';
  END IF;
  RETURN NEW;
END $$;
DROP TRIGGER IF EXISTS object_validate ON c.object;
CREATE TRIGGER object_validate BEFORE INSERT OR UPDATE OF props, type_id ON c.object
  FOR EACH ROW EXECUTE FUNCTION c.trg_validate_props();
