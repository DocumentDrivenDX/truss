-- Additive runtime releases never rewrite immutable genesis or producer facts.
CREATE SEQUENCE truss.runtime_release_generation;
CREATE TABLE truss.runtime_release (
 generation bigint PRIMARY KEY DEFAULT nextval('truss.runtime_release_generation'),
 previous_release_id text NOT NULL,previous_release_sha256 text NOT NULL,
 release_id text NOT NULL UNIQUE,release_sha256 text NOT NULL,
 manifest_bytes bytea NOT NULL,actor_oid oid NOT NULL,installed_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TRIGGER runtime_release_immutable BEFORE UPDATE OR DELETE OR TRUNCATE ON truss.runtime_release
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
ALTER TABLE truss.runtime_release ENABLE ALWAYS TRIGGER runtime_release_immutable;
CREATE FUNCTION truss.runtime_current_installation() RETURNS SETOF truss.catalog_runtime_installation
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;active truss.runtime_release%ROWTYPE;
BEGIN
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 SELECT * INTO active FROM truss.runtime_release ORDER BY generation DESC LIMIT 1;
 IF FOUND THEN installation.release_id:=active.release_id;installation.release_sha256:=active.release_sha256;installation.layout_profile:=convert_from(active.manifest_bytes,'UTF8')::jsonb->'layoutProfile';END IF;
 IF installation.release_id='truss-catalog-runtime/0.69-candidate' THEN
  installation.preparation_configuration:=jsonb_set(installation.preparation_configuration,'{layoutProfile}',installation.layout_profile);
  installation.preparation_configuration:=jsonb_set(installation.preparation_configuration,'{supportProfile}','{"identity":"truss-fresh-catalog-support","version":"0.6.0","sha256":"c188429e07667bd1ba6a13da5d89f9c584e517163b948e9ec4cf02810b420369"}'::jsonb);
 END IF;
 RETURN NEXT installation;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_current_installation() FROM PUBLIC;
