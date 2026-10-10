-- Observation fixture only; this is not row_touch_observe or a semantic guard.
CREATE TABLE cascade_prestate AS
SELECT state_id,owner_kind,object_id,object_type_id,edge_id,relationship_type_id,
 property_owner_type_id,property_id,root_node_id,definition_bytes,home_profile_bytes,
 value_profile_bytes,source_bytes FROM truss.row_home_state;
CREATE TABLE cascade_events (
 relation_name text,relation_oid oid,event_kind text,writer_xid xid8,state_id bigint,
 node_id bigint,old_owner_kind text,old_owner_id bigint,old_discriminator int,
 old_property_owner int,old_property_id int,live_state boolean,live_node boolean,
 retained_owner_kind text,retained_owner_id bigint,retained_discriminator int,
 retained_property_owner int,retained_property_id int,original_image bytea);
CREATE FUNCTION cascade_attribution_probe() RETURNS trigger
LANGUAGE plpgsql VOLATILE SECURITY INVOKER SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE s bigint; n bigint; k text; o bigint; d int; po int; p int; image bytea;
BEGIN
 IF TG_LEVEL<>'ROW' OR TG_WHEN<>'AFTER' OR TG_OP<>'DELETE' OR TG_TABLE_SCHEMA<>'truss'
  OR TG_TABLE_NAME NOT IN ('row_home_state','row_home_node','row_home_scalar') OR TG_NARGS<>0 THEN
  RAISE EXCEPTION 'unsupported probe event';
 END IF;
 s:=OLD.state_id;
 IF TG_TABLE_NAME='row_home_state' THEN image:=truss.row_image_state_original(OLD);
 ELSIF TG_TABLE_NAME='row_home_node' THEN image:=truss.row_image_node_original(OLD);
 ELSE image:=truss.row_image_scalar_original(OLD);END IF;
 IF TG_TABLE_NAME='row_home_state' THEN
  k:=OLD.owner_kind;po:=OLD.property_owner_type_id;p:=OLD.property_id;
  IF k='object' THEN o:=OLD.object_id;d:=OLD.object_type_id;
  ELSE o:=OLD.edge_id;d:=OLD.relationship_type_id;END IF;
 ELSE n:=OLD.node_id;END IF;
 INSERT INTO public.cascade_events
 SELECT TG_TABLE_NAME,TG_RELID,TG_OP,pg_current_xact_id_if_assigned(),s,n,k,o,d,po,p,
  EXISTS(SELECT 1 FROM truss.row_home_state WHERE state_id=s),
  CASE WHEN n IS NULL THEN NULL ELSE EXISTS(SELECT 1 FROM truss.row_home_node WHERE state_id=s AND node_id=n) END,
  c.owner_kind,CASE WHEN c.owner_kind='object' THEN c.object_id ELSE c.edge_id END,
  CASE WHEN c.owner_kind='object' THEN c.object_type_id ELSE c.relationship_type_id END,
  c.property_owner_type_id,c.property_id,image
 FROM public.cascade_prestate c WHERE c.state_id=s;
 IF NOT FOUND THEN RAISE EXCEPTION 'retained probe prestate missing';END IF;
 RETURN NULL;
END;
$$;
REVOKE ALL ON FUNCTION cascade_attribution_probe() FROM PUBLIC;
CREATE TRIGGER cascade_probe_state AFTER DELETE ON truss.row_home_state FOR EACH ROW EXECUTE FUNCTION cascade_attribution_probe();
CREATE TRIGGER cascade_probe_node AFTER DELETE ON truss.row_home_node FOR EACH ROW EXECUTE FUNCTION cascade_attribution_probe();
CREATE TRIGGER cascade_probe_scalar AFTER DELETE ON truss.row_home_scalar FOR EACH ROW EXECUTE FUNCTION cascade_attribution_probe();
