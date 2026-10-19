-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Derived immutable coordinates and pins; original fragments remain only in schema_doc.
CREATE TABLE truss.runtime_definition_source (
 rev int NOT NULL,ord int NOT NULL,doc_id text NOT NULL,module_id text NOT NULL,
 element_id text NOT NULL,kind text NOT NULL,key_id text NOT NULL DEFAULT '',
 pointer text NOT NULL,definition_pin text NOT NULL,
 PRIMARY KEY(rev,ord,pointer),UNIQUE(rev,ord,module_id,element_id,kind,key_id),
 FOREIGN KEY(rev,ord) REFERENCES truss.schema_doc(rev,ord));
CREATE INDEX runtime_definition_source_pin ON truss.runtime_definition_source(definition_pin);
CREATE FUNCTION truss.runtime_owned_index_definition_source() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 WITH modules AS MATERIALIZED (
  SELECT value->>'id' module_id,value->'elements' module_elements,value->'relationships' module_relationships,ordinality::int-1 mi
  FROM json_array_elements(NEW.document::json->'modules') WITH ORDINALITY),
 elements AS MATERIALIZED (
  SELECT m.module_id,e.value element,e.value->>'id' element_id,'element' kind,
   '/modules/'||m.mi||'/elements/'||(e.ordinality-1) pointer
  FROM modules m CROSS JOIN LATERAL json_array_elements(m.module_elements) WITH ORDINALITY e
  UNION ALL
  SELECT m.module_id,e.value,e.value->>'id','relationship',
   '/modules/'||m.mi||'/relationships/'||(e.ordinality-1)
  FROM modules m CROSS JOIN LATERAL json_array_elements(m.module_relationships) WITH ORDINALITY e),
 fragments AS (
  SELECT module_id,element_id,kind,'' key_id,pointer,convert_to(element::text,'UTF8') fragment FROM elements
  UNION ALL
  SELECT e.module_id,e.element_id,'key',k.value->>'id',e.pointer||'/keys/'||(k.ordinality-1),convert_to(k.value::text,'UTF8')
  FROM elements e CROSS JOIN LATERAL json_array_elements(e.element->'keys') WITH ORDINALITY k WHERE e.kind='element')
 INSERT INTO truss.runtime_definition_source
 SELECT NEW.rev,NEW.ord,NEW.doc_id,module_id,element_id,kind,key_id,pointer,
  encode(sha256(convert_to('['||NEW.rev||','||NEW.ord||',"'||NEW.content_sha256||'","'||pointer
  ||'",{"identity":"truss-original-json-definition","sha256":"08c2ec8c520b39ded40f270be0b26812db1d240d5bac1a00339b437200a2f58d","version":"0.1"},"'
  ||encode(sha256(fragment),'hex')||'"]','UTF8')),'hex') FROM fragments;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_index_definition_source() FROM PUBLIC;
CREATE TRIGGER runtime_definition_source_capture AFTER INSERT ON truss.schema_doc
 FOR EACH ROW EXECUTE FUNCTION truss.runtime_owned_index_definition_source();
CREATE TRIGGER runtime_definition_source_immutable BEFORE UPDATE OR DELETE ON truss.runtime_definition_source
 FOR EACH ROW EXECUTE FUNCTION truss.catalog_immutable();
CREATE TRIGGER runtime_definition_source_no_truncate BEFORE TRUNCATE ON truss.runtime_definition_source
 FOR EACH STATEMENT EXECUTE FUNCTION truss.catalog_immutable();
REVOKE ALL ON TABLE truss.runtime_definition_source FROM PUBLIC;

-- All row writers join one transaction gate; autovacuum takes no such gate.
CREATE FUNCTION truss.runtime_owned_graph_write_exclusion() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 IF NOT pg_try_advisory_xact_lock(1953658227,1735549296) THEN
  RAISE EXCEPTION 'graph writer in flight' USING ERRCODE='55P03';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION truss.runtime_owned_graph_write_exclusion() FROM PUBLIC;
CREATE TRIGGER runtime_graph_write_exclusion BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.object
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_owned_graph_write_exclusion();
CREATE TRIGGER runtime_graph_write_exclusion BEFORE INSERT OR UPDATE OR DELETE OR TRUNCATE ON truss.edge
 FOR EACH STATEMENT EXECUTE FUNCTION truss.runtime_owned_graph_write_exclusion();
