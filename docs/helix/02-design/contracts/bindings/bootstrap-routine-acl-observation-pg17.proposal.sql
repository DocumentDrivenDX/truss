-- Unexecuted PostgreSQL 17 routine ACL expansion proposal.
-- $1: independently admitted unique one-dimensional nonnull pg_proc OIDs,
-- at most 256, with original class/subobject=0 custody. No namespace filter.
-- LEFT JOIN retains routines whose explicit ACL expands to no grants.
SELECT p.tableoid::pg_catalog.oid::pg_catalog.text AS catalog_class_oid,
       p.oid::pg_catalog.text AS object_oid,
       p.pronamespace::pg_catalog.text AS namespace_oid,
       p.proowner::pg_catalog.text AS owner_oid,
       p.proacl IS NULL AS original_acl_is_null,
       p.proacl::pg_catalog.text AS original_acl_native_text,
       pg_catalog.array_dims(p.proacl) AS original_acl_native_dimensions,
       pg_catalog.cardinality(COALESCE(p.proacl,
           pg_catalog.acldefault('f'::pg_catalog."char", p.proowner))) AS assumed_acl_item_count,
       a.grantor IS NOT NULL AS has_expanded_grant,
       a.grantor::pg_catalog.text AS grantor_oid,
       a.grantee::pg_catalog.text AS grantee_oid,
       a.privilege_type,
       a.is_grantable
FROM pg_catalog.pg_proc AS p
LEFT JOIN LATERAL pg_catalog.aclexplode(COALESCE(p.proacl,
    pg_catalog.acldefault('f'::pg_catalog."char", p.proowner))) AS a ON true
WHERE p.oid = ANY($1::pg_catalog.oid[])
ORDER BY p.oid, a.grantor, a.grantee, a.privilege_type, a.is_grantable;
