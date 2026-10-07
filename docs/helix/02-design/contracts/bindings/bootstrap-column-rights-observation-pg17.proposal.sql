-- Unexecuted PG17 column rights; original role/relation/attribute arrays <=256.
-- Equal nonnull one-dimensional unique tuples; original native class/kind admitted.
WITH scope AS (
 SELECT f.role_oid,f.relation_oid,f.attribute_number
 FROM ROWS FROM (pg_catalog.unnest($1::pg_catalog.oid[]),
                 pg_catalog.unnest($2::pg_catalog.oid[]),
                 pg_catalog.unnest($3::pg_catalog.int2[])) AS f(role_oid,relation_oid,attribute_number)
)
SELECT r.oid::pg_catalog.text AS role_oid,
       c.oid::pg_catalog.text AS relation_oid,
       a.attnum::pg_catalog.text AS attribute_number,
       p.privilege,
       pg_catalog.has_column_privilege(r.oid,c.oid,a.attnum,p.privilege) AS has_privilege,
       pg_catalog.has_column_privilege(r.oid,c.oid,a.attnum,p.privilege || ' WITH GRANT OPTION') AS has_grant_option
FROM scope AS f
JOIN pg_catalog.pg_roles AS r ON r.oid = f.role_oid
JOIN pg_catalog.pg_class AS c ON c.oid = f.relation_oid
JOIN pg_catalog.pg_attribute AS a ON a.attrelid = c.oid AND a.attnum = f.attribute_number
CROSS JOIN (VALUES ('SELECT'::pg_catalog.text),('INSERT'::pg_catalog.text),('UPDATE'::pg_catalog.text),('REFERENCES'::pg_catalog.text)) AS p(privilege)
WHERE c.relkind IN ('r','p','v','m','f') AND NOT a.attisdropped
ORDER BY r.oid,c.oid,a.attnum,p.privilege;
