-- Fresh installations have one immutable runtime identity; live catalog revisions remain separate.
CREATE FUNCTION truss.runtime_current_installation() RETURNS SETOF truss.catalog_runtime_installation
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
DECLARE installation truss.catalog_runtime_installation%ROWTYPE;
BEGIN
 SELECT * INTO STRICT installation FROM truss.catalog_runtime_installation;
 RETURN NEXT installation;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_current_installation() FROM PUBLIC;
