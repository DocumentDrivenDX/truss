-- Test-only trusted host extension, not Truss bootstrap or a production migration.
-- Prerequisites: disposable qualified truss-layout 0.2 namespace, admitted
-- fixture installer and dedicated non-superuser host owner. Install under that
-- owner with separately authorized trigger-creation rights on canonical tables.
-- Ownership/ACL/search-path inventory and cleanup are harness-owned evidence.
CREATE SCHEMA truss_host_fixture;
REVOKE ALL ON SCHEMA truss_host_fixture FROM PUBLIC;
CREATE TABLE truss_host_fixture.ledger (
  ledger_id pg_catalog.int8 GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  relation_name pg_catalog.text NOT NULL,
  operation pg_catalog.text NOT NULL CHECK (operation IN ('INSERT','UPDATE','DELETE')),
  record_id pg_catalog.text NOT NULL,
  producing_xid pg_catalog.text NOT NULL,
  before_native pg_catalog.jsonb,
  after_native pg_catalog.jsonb
);
REVOKE ALL ON TABLE truss_host_fixture.ledger FROM PUBLIC;
CREATE TABLE truss_host_fixture.control (
  singleton pg_catalog.bool PRIMARY KEY CHECK (singleton),
  fail_writes pg_catalog.bool NOT NULL
);
INSERT INTO truss_host_fixture.control VALUES (true, false);
REVOKE ALL ON TABLE truss_host_fixture.control FROM PUBLIC;
CREATE FUNCTION truss_host_fixture.capture_change()
RETURNS pg_catalog.trigger
LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
SET search_path = pg_catalog, pg_temp
AS $body$
DECLARE
  old_value pg_catalog.jsonb;
  new_value pg_catalog.jsonb;
  captured_id pg_catalog.text;
  failure_enabled pg_catalog.bool;
BEGIN
  IF TG_TABLE_SCHEMA <> 'truss' OR TG_TABLE_NAME NOT IN ('object','edge')
     OR TG_OP NOT IN ('INSERT','UPDATE','DELETE')
     OR TG_WHEN <> 'AFTER' OR TG_LEVEL <> 'ROW' OR TG_NARGS <> 0 THEN
    RAISE EXCEPTION 'unsupported host fixture invocation';
  END IF;
  SELECT c.fail_writes INTO STRICT failure_enabled
  FROM truss_host_fixture.control AS c WHERE c.singleton;
  IF failure_enabled THEN
    RAISE EXCEPTION 'host fixture requested failure';
  END IF;
  IF TG_OP <> 'INSERT' THEN
    old_value := pg_catalog.to_jsonb(OLD);
    captured_id := OLD.id::pg_catalog.text;
  END IF;
  IF TG_OP <> 'DELETE' THEN
    new_value := pg_catalog.to_jsonb(NEW);
    captured_id := NEW.id::pg_catalog.text;
  END IF;
  INSERT INTO truss_host_fixture.ledger
    (relation_name, operation, record_id, producing_xid, before_native, after_native)
  VALUES (TG_TABLE_NAME, TG_OP, captured_id,
    pg_catalog.pg_current_xact_id()::pg_catalog.text, old_value, new_value);
  RETURN NULL;
END;
$body$;
REVOKE ALL ON FUNCTION truss_host_fixture.capture_change() FROM PUBLIC;
CREATE TRIGGER truss_host_fixture_object
AFTER INSERT OR UPDATE OR DELETE ON truss.object
FOR EACH ROW EXECUTE FUNCTION truss_host_fixture.capture_change();
CREATE TRIGGER truss_host_fixture_edge
AFTER INSERT OR UPDATE OR DELETE ON truss.edge
FOR EACH ROW EXECUTE FUNCTION truss_host_fixture.capture_change();
