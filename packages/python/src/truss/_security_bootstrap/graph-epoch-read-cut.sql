-- SPDX-License-Identifier: MIT OR Apache-2.0
-- Fixed no-input epoch/archive/guard cut for an ordinary private graph reader.
CREATE FUNCTION truss.acquire_graph_epoch_read_cut() RETURNS pg_catalog.void
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,pg_temp AS $$
BEGIN
 LOCK TABLE ONLY truss.source_epoch_current IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.source_epoch_registry IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.installation_archive IN SHARE MODE NOWAIT;
 LOCK TABLE ONLY truss.policy_generation_guard IN SHARE MODE NOWAIT;
END;
$$;
REVOKE ALL ON FUNCTION truss.acquire_graph_epoch_read_cut() FROM PUBLIC;
