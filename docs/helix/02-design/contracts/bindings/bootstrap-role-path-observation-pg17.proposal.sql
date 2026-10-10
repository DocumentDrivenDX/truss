-- Unexecuted PG17 explicit role inquiry; original root/target oid[] pairs <=256.
-- Equal unique nonnull one-dimensional pairs; complete root/target scope admitted.
WITH pairs AS (
 SELECT f.root_oid,f.target_oid
 FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                 pg_catalog.unnest($2::pg_catalog.oid[])) AS f(root_oid,target_oid)
)
SELECT r.oid::pg_catalog.text AS root_oid,
       t.oid::pg_catalog.text AS target_oid,
       pg_catalog.pg_has_role(r.oid,t.oid,'MEMBER') AS is_member,
       pg_catalog.pg_has_role(r.oid,t.oid,'USAGE') AS has_immediate_rights,
       pg_catalog.pg_has_role(r.oid,t.oid,'SET') AS has_set_role_right
FROM pairs AS f
JOIN pg_catalog.pg_roles AS r ON r.oid = f.root_oid
JOIN pg_catalog.pg_roles AS t ON t.oid = f.target_oid
ORDER BY r.oid,t.oid;
